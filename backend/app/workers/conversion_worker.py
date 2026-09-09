"""The actual conversion pipeline: validate -> convert -> optimize -> benchmark -> persist.

Shared by the in-process LocalJobExecutor (used in AWS_MODE=mock) and the standalone
worker entrypoints under workers/ that run inside ECS tasks in production. Both call
`run_conversion_job` with a job id; only how the job gets picked up differs.
"""

import hashlib
import os
import tempfile
import threading

import structlog
from sqlalchemy.orm import Session

from app.converters.base import ConversionConfig
from app.converters.registry import get_converter
from app.database import SessionLocal
from app.models.benchmark import Benchmark
from app.models.conversion_artifact import ConversionArtifact
from app.models.conversion_job import ConversionJob, JobStatus
from app.models.job_log import LogLevel
from app.models.model import Model, ModelFramework
from app.repositories.conversion_repository import ConversionRepository
from app.storage.factory import get_storage_provider
from app.utils.pytorch_export import PyTorchExportError, export_pytorch_to_onnx

logger = structlog.get_logger(__name__)

_cancel_flags: dict[str, threading.Event] = {}


def request_cancel(job_id: str) -> None:
    _cancel_flags.setdefault(job_id, threading.Event()).set()


def _is_cancelled(job_id: str) -> bool:
    return _cancel_flags.get(job_id, threading.Event()).is_set()


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

    model: Model = db.get(Model, job.model_id)

    def log(message: str, level: LogLevel = LogLevel.INFO) -> None:
        repo.add_log(job_id, message, level)
        logger.info("worker.log", job_id=job_id, message=message)

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
        repo.update_status(job, JobStatus.VALIDATING, progress=10)

        if model.framework == ModelFramework.PYTORCH:
            log(f"Loading PyTorch (TorchScript) model from {model.storage_path}")
            export_dir = tempfile.mkdtemp(prefix=f"modelforge-export-{job_id}-")
            onnx_local_path = os.path.join(export_dir, "exported.onnx")
            try:
                export_pytorch_to_onnx(local_path, parsed_shape, onnx_local_path)
                log("Exported PyTorch model to ONNX")
            except PyTorchExportError as exc:
                log(str(exc), level=LogLevel.ERROR)
                repo.update_status(job, JobStatus.FAILED, progress=10, error_message=str(exc))
                return
        else:
            log(f"Loading ONNX model from {model.storage_path}")
            onnx_local_path = local_path

        if _is_cancelled(job_id):
            return _finalize_cancelled(repo, job, log)
        converter.validate(onnx_local_path, config)
        log("ONNX graph validated successfully")

        # ── CONVERTING ───────────────────────────────────────
        repo.update_status(job, JobStatus.CONVERTING, progress=35)
        log(f"Starting conversion to {job.target_format.value}")
        if _is_cancelled(job_id):
            return _finalize_cancelled(repo, job, log)

        with tempfile.TemporaryDirectory(prefix=f"modelforge-{job_id}-") as work_dir:
            result = converter.convert(onnx_local_path, work_dir, config)
            if not result.success:
                level = LogLevel.WARNING if result.is_environment_limited else LogLevel.ERROR
                log(result.error or "Conversion failed", level=level)
                repo.update_status(job, JobStatus.FAILED, progress=35, error_message=result.error)
                return
            log(f"Conversion produced {result.output_path}")

            # ── OPTIMIZING ───────────────────────────────────
            repo.update_status(job, JobStatus.OPTIMIZING, progress=60)
            log(f"Applying {job.optimization.value.upper()} optimization")
            if _is_cancelled(job_id):
                return _finalize_cancelled(repo, job, log)
            opt_result = converter.optimize(result.output_path, config)
            if opt_result.applied:
                log(f"Optimization {opt_result.optimization} applied")
            else:
                log(f"Optimization unavailable in current environment: {opt_result.note}", level=LogLevel.WARNING)

            # ── BENCHMARKING ─────────────────────────────────
            repo.update_status(job, JobStatus.BENCHMARKING, progress=85)
            log("Running benchmark suite")
            if _is_cancelled(job_id):
                return _finalize_cancelled(repo, job, log)
            bench = converter.benchmark(result.output_path, onnx_local_path, config)

            # ── PERSIST ARTIFACT ─────────────────────────────
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
                    accuracy_pct=bench.accuracy_pct,
                    memory_usage_mb=bench.memory_usage_mb,
                    benchmark_device=bench.device,
                    unsupported_metrics=",".join(bench.unsupported_metrics) or None,
                )
            )
            repo.db.commit()

            converter.cleanup([result.output_path])

        log("Conversion completed")
        repo.update_status(job, JobStatus.COMPLETED, progress=100)

    except Exception as exc:
        logger.exception("worker.job_failed", job_id=job_id)
        log(f"Unexpected error: {exc}", level=LogLevel.ERROR)
        repo.update_status(job, JobStatus.FAILED, error_message=str(exc))
    finally:
        _cancel_flags.pop(job_id, None)
        db.close()


def _finalize_cancelled(repo: ConversionRepository, job: ConversionJob, log) -> None:
    log("Job cancelled by user", level=LogLevel.WARNING)
    repo.update_status(job, JobStatus.CANCELLED)
