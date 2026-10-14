import threading
from abc import ABC, abstractmethod
from functools import lru_cache

from app.config import get_settings
from app.queue.base import QueueProvider
from app.workers.conversion_worker import request_cancel, run_conversion_job


class JobExecutor(ABC):
    """Dispatches a queued conversion job to whatever actually runs the conversion:
    an in-process thread in mock mode, or an ECS task in production.
    """

    @abstractmethod
    def submit(self, job_id: str) -> None: ...

    @abstractmethod
    def cancel(self, job_id: str) -> None: ...


class LocalJobExecutor(JobExecutor):
    """Runs each conversion job on its own daemon thread, simulating the isolation an
    ECS task would provide in production without requiring Docker/AWS locally.
    """

    def submit(self, job_id: str) -> None:
        thread = threading.Thread(target=run_conversion_job, args=(job_id,), daemon=True, name=f"job-{job_id}")
        thread.start()

    def cancel(self, job_id: str) -> None:
        request_cancel(job_id)


class AWSJobExecutor(JobExecutor):
    """Publishes the job to SQS: TensorRT jobs go to the queue the laptop GPU worker polls,
    everything else to the queue the ECS Fargate CPU worker polls. Both run the same
    `run_conversion_job` pipeline.
    """

    def __init__(self, queue: QueueProvider):
        self.queue = queue
        settings = get_settings()
        self._tensorrt_queue = settings.sqs_tensorrt_queue
        self._cpu_queue = settings.sqs_cpu_queue  # tflite, onnx baseline, coreml (reports "needs macOS")

    def submit(self, job_id: str) -> None:
        from app.database import SessionLocal
        from app.models.conversion_job import ConversionJob

        db = SessionLocal()
        try:
            job = db.get(ConversionJob, job_id)
            queue_name = self._tensorrt_queue if job.target_format.value == "tensorrt" else self._cpu_queue
        finally:
            db.close()
        self.queue.publish(queue_name, {"job_id": job_id})

    def cancel(self, job_id: str) -> None:
        # Nothing to signal: the API marks the job CANCELLED in the shared database, and the
        # worker checks that status before every stage (see conversion_worker.advance).
        pass


@lru_cache
def get_job_executor() -> JobExecutor:
    settings = get_settings()
    if settings.is_mock_mode:
        return LocalJobExecutor()

    from app.queue.factory import get_queue_provider

    return AWSJobExecutor(get_queue_provider())
