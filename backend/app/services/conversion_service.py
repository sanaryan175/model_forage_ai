from sqlalchemy.orm import Session

from app.models.conversion_job import ConversionJob, JobStatus, OptimizationType, TargetFormat
from app.models.model import Model, ModelStatus
from app.repositories.conversion_repository import ConversionRepository
from app.workers.job_executor import get_job_executor


class ModelNotReadyError(ValueError):
    pass


class InvalidJobStateError(ValueError):
    pass


class ConversionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversionRepository(db)
        self.executor = get_job_executor()

    def create_jobs(
        self,
        model: Model,
        target_formats: list[TargetFormat],
        optimization: OptimizationType,
        batch_size: int,
        target_device: str,
        input_shape: list[int] | None,
    ) -> list[ConversionJob]:
        if model.status != ModelStatus.READY:
            raise ModelNotReadyError(
                f"Model '{model.name}' is not ready for conversion (status: {model.status.value})"
            )

        jobs = []
        shape_str = ",".join(str(d) for d in input_shape) if input_shape else None
        for target_format in target_formats:
            job = ConversionJob(
                model_id=model.id,
                target_format=target_format,
                optimization=optimization,
                batch_size=batch_size,
                target_device=target_device,
                input_shape=shape_str,
            )
            job = self.repo.create(job)
            self.repo.add_log(job.id, f"Job queued for {target_format.value} conversion")
            self.executor.submit(job.id)
            jobs.append(job)
        return jobs

    def get(self, job_id: str) -> ConversionJob | None:
        return self.repo.get_by_id(job_id)

    def list_for_user(self, user_id: str, limit: int, offset: int) -> tuple[list[ConversionJob], int]:
        return self.repo.list_for_user(user_id, limit=limit, offset=offset)

    def cancel(self, job: ConversionJob) -> ConversionJob:
        if job.status not in (JobStatus.QUEUED, JobStatus.VALIDATING, JobStatus.CONVERTING, JobStatus.OPTIMIZING, JobStatus.BENCHMARKING):
            raise InvalidJobStateError(f"Cannot cancel a job in status '{job.status.value}'")
        self.executor.cancel(job.id)
        return self.repo.update_status(job, JobStatus.CANCELLED)

    def retry(self, job: ConversionJob) -> ConversionJob:
        if job.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
            raise InvalidJobStateError(f"Cannot retry a job in status '{job.status.value}'")
        job.status = JobStatus.QUEUED
        job.progress = 0
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        self.db.commit()
        self.db.refresh(job)
        self.repo.add_log(job.id, "Job re-queued by user")
        self.executor.submit(job.id)
        return job

    def get_logs(self, job_id: str):
        return self.repo.list_logs(job_id)
