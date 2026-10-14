"""The actual conversion pipeline: validate -> convert -> optimize -> benchmark -> persist.

Shared by the in-process LocalJobExecutor (used in AWS_MODE=mock) and the standalone
worker entrypoints under workers/ that run inside ECS tasks in production. Both call
`run_conversion_job` with a job id; only how the job gets picked up differs.
"""

import hashlib
import os
import shutil
import tempfile
import threading

import structlog
from sqlalchemy.orm import Session

from app.converters.base import ConversionConfig
from app.converters.registry import get_converter
from app.database import SessionLocal
from app.models.benchmark import Benchmark
from app.models.conversion_artifact import ConversionArtifact
from app.models.conversion_job import ConversionJob, JobStatus, TargetFormat
from app.models.job_log import LogLevel
from app.models.model import Model, ModelFramework
from app.repositories.conversion_repository import ConversionRepository
from app.storage.factory import get_storage_provider
from app.utils.pytorch_export import PyTorchExportError, export_pytorch_to_onnx

logger = structlog.get_logger(__name__)

# ponytail: in-process cancel flags only work for the local thread executor; ECS workers would need a DB poll.
_running: set[str] = set()
_cancel_flags: dict[str, threading.Event] = {}
# One job at a time, so a benchmark never shares the CPU with another conversion and latencies stay comparable.
# ponytail: per-process lock; separate ECS workers would each run one job anyway.
_pipeline_lock = threading.Lock()


def request_cancel(job_id: str) -> None:
    # Only flag jobs with a live thread, otherwise a stale flag would cancel the next retry instantly.
    if job_id in _running:
        _cancel_flags.setdefault(job_id, threading.Event()).set()


def is_running(job_id: str) -> bool:
    return job_id in _running


def _is_cancelled(job_id: str) -> bool:
    return _cancel_flags.get(job_id, threading.Event()).is_set()


class _Cancelled(Exception):
    pass


def _checksum(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_conversion_job(job_id: str) -> None:
    db: Session = SessionLocal()
    repo = ConversionRepository(db)
    storage = get_storage_provider()

    job: ConversionJob | None = repo.get_by_id(job_id)
    if job is None:
        logger.error("worker.job_not_found", job_id=job_id)
        db.close()
        return
    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
        # SQS delivers at-least-once; a finished job must not be converted twice. (Retry resets to QUEUED.)
        logger.info("worker.skip_finished_job", job_id=job_id, status=job.status.value)
        db.close()
        return

    _running.add(job_id)
    model: Model = db.get(Model, job.model_id)
    export_dir: str | None = None

    def log(message: str, level: LogLevel = LogLevel.INFO) -> None:
        repo.add_log(job_id, message, level)
        logger.info("worker.log", job_id=job_id, message=message)

    def check_cancelled() -> None:
        # Local flag (same process) or the shared DB status (API on another machine, AWS mode).
        db.refresh(job)
        if _is_cancelled(job_id) or job.status == JobStatus.CANCELLED:
            raise _Cancelled

    def advance(status: JobStatus, progress: int) -> None:
        # Checked before every status write so a cancel is never overwritten by a later stage.
        check_cancelled()
        repo.update_status(job, status, progress=progress)

    def fail(message: str, progress: int, level: LogLevel = LogLevel.ERROR) -> None:
        log(message, level=level)
        repo.update_status(job, JobStatus.FAILED, progress=progress, error_message=message)

    _pipeline_lock.acquire()  # queued jobs wait here; registered in _running first so they stay cancellable
    try:
        local_path = storage.open_path(model.storage_path)
        parsed_shape = [int(d) for d in job.input_shape.split(",")] if job.input_shape else None
        config = ConversionConfig(
            optimization=job.optimization.value,
            batch_size=job.batch_size,
            target_device=job.target_device,
            input_shape=parsed_shape,
        )
        converter = get_converter(job.target_format.value)

        # ── VALIDATING ───────────────────────────────────────
        advance(JobStatus.VALIDATING, 10)

        if model.framework == ModelFramework.PYTORCH:
            log(f"Loading PyTorch (TorchScript) model from {model.storage_path}")
            export_dir = tempfile.mkdtemp(prefix=f"modelforge-export-{job_id}-")
            onnx_local_path = os.path.join(export_dir, "exported.onnx")
            try:
                export_pytorch_to_onnx(local_path, parsed_shape, onnx_local_path)
                log("Exported PyTorch model to ONNX")
            except PyTorchExportError as exc:
                return fail(str(exc), 10)
        else:
            log(f"Loading ONNX model from {model.storage_path}")
            onnx_local_path = local_path

        converter.validate(onnx_local_path, config)
        log("ONNX graph validated successfully")

        # ── CONVERTING ───────────────────────────────────────
        advance(JobStatus.CONVERTING, 35)
        log(f"Starting conversion to {job.target_format.value}")

        with tempfile.TemporaryDirectory(prefix=f"modelforge-{job_id}-") as work_dir:
            result = converter.convert(onnx_local_path, work_dir, config)
            if not result.success:
                level = LogLevel.WARNING if result.is_environment_limited else LogLevel.ERROR
                return fail(result.error or "Conversion failed", 35, level)
            log(f"Conversion produced {result.output_path}")

            # ── OPTIMIZING ───────────────────────────────────
            advance(JobStatus.OPTIMIZING, 60)
            log(f"Applying {job.optimization.value.upper()} optimization")
            opt_result = converter.optimize(result.output_path, config)
            if not opt_result.applied:
                # Never ship an unoptimized file labelled with the requested precision.
                return fail(f"{opt_result.optimization.upper()} optimization not applied: {opt_result.note}", 60)
            log(f"Optimization {opt_result.optimization} applied")

            # ── BENCHMARKING ─────────────────────────────────
            advance(JobStatus.BENCHMARKING, 85)
            log("Running benchmark suite")
            bench = converter.benchmark(result.output_path, onnx_local_path, config)
            check_cancelled()

            # ── PERSIST ARTIFACT ─────────────────────────────
            # The ONNX baseline is the user's own upload; storing a second copy as a "generated model" is waste.
            if job.target_format != TargetFormat.ONNX:
                artifact_key = f"models/{model.user_id}/{model.id}/converted/{job_id}_{os.path.basename(result.output_path)}"
                with open(result.output_path, "rb") as f:
                    storage.save(artifact_key, f)
                repo.add_artifact(
                    ConversionArtifact(
                        job_id=job_id,
                        format=job.target_format,
                        file_path=artifact_key,
                        file_size=os.path.getsize(result.output_path),
                        checksum=_checksum(result.output_path),
                    )
                )

            repo.db.add(
                Benchmark(
                    job_id=job_id,
                    model_size_bytes=bench.model_size_bytes,
                    latency_mean_ms=bench.latency_mean_ms,
                    latency_median_ms=bench.latency_median_ms,
                    latency_p95_ms=bench.latency_p95_ms,
                    throughput_ips=bench.throughput_ips,
                    fidelity_pct=bench.fidelity_pct,
                    benchmark_device=bench.device,
                    unsupported_metrics=",".join(bench.unsupported_metrics) or None,
                )
            )
            repo.db.commit()

        log("Conversion completed")
        repo.update_status(job, JobStatus.COMPLETED, progress=100)

    except _Cancelled:
        log("Job cancelled by user", level=LogLevel.WARNING)
        repo.update_status(job, JobStatus.CANCELLED)
    except Exception as exc:
        logger.exception("worker.job_failed", job_id=job_id)
        fail(f"Unexpected error: {exc}", job.progress)
    finally:
        _pipeline_lock.release()
        _running.discard(job_id)
        _cancel_flags.pop(job_id, None)
        if export_dir:
            shutil.rmtree(export_dir, ignore_errors=True)
        db.close()
