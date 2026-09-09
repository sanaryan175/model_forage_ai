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
    """Publishes the job onto the format-specific SQS queue; EventBridge + Lambda + ECS
    (see infrastructure/aws) pick it up and run the same `run_conversion_job` pipeline
    inside a container image built from workers/Dockerfile.<format>.
    """

    def __init__(self, queue: QueueProvider):
        self.queue = queue
        self._queue_name_by_format = {
            "tflite": get_settings().sqs_tflite_queue,
            "tensorrt": get_settings().sqs_tensorrt_queue,
            "coreml": get_settings().sqs_coreml_queue,
        }

    def submit(self, job_id: str) -> None:
        from app.database import SessionLocal
        from app.models.conversion_job import ConversionJob

        db = SessionLocal()
        try:
            job = db.get(ConversionJob, job_id)
            queue_name = self._queue_name_by_format[job.target_format.value]
        finally:
            db.close()
        self.queue.publish(queue_name, {"job_id": job_id})

    def cancel(self, job_id: str) -> None:
        # Production cancellation stops the ECS task via the AWS API; documented in
        # infrastructure/aws/README.md. Marking CANCELLED here is handled by the API layer.
        pass


@lru_cache
def get_job_executor() -> JobExecutor:
    settings = get_settings()
    if settings.is_mock_mode:
        return LocalJobExecutor()

    from app.queue.factory import get_queue_provider

    return AWSJobExecutor(get_queue_provider())
