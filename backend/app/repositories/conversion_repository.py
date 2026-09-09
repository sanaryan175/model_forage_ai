from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.conversion_artifact import ConversionArtifact
from app.models.conversion_job import ConversionJob, JobStatus
from app.models.job_log import JobLog, LogLevel
from app.models.model import Model

_ARTIFACT_WITH_JOB_AND_MODEL = joinedload(ConversionArtifact.job).joinedload(ConversionJob.model)


class ConversionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job: ConversionJob) -> ConversionJob:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: str) -> ConversionJob | None:
        return self.db.get(ConversionJob, job_id)

    def list_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> tuple[list[ConversionJob], int]:
        stmt = (
            select(ConversionJob)
            .join(Model, ConversionJob.model_id == Model.id)
            .where(Model.user_id == user_id)
            .options(joinedload(ConversionJob.model))
        )
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        stmt = stmt.order_by(ConversionJob.created_at.desc()).limit(limit).offset(offset)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def list_active_for_user(self, user_id: str) -> list[ConversionJob]:
        active_states = [
            JobStatus.QUEUED,
            JobStatus.VALIDATING,
            JobStatus.CONVERTING,
            JobStatus.OPTIMIZING,
            JobStatus.BENCHMARKING,
        ]
        stmt = (
            select(ConversionJob)
            .join(Model, ConversionJob.model_id == Model.id)
            .where(Model.user_id == user_id, ConversionJob.status.in_(active_states))
            .order_by(ConversionJob.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_status(
        self,
        job: ConversionJob,
        status: JobStatus,
        progress: int | None = None,
        error_message: str | None = None,
    ) -> ConversionJob:
        job.status = status
        if progress is not None:
            job.progress = progress
        if error_message is not None:
            job.error_message = error_message
        if status in (
            JobStatus.VALIDATING,
            JobStatus.CONVERTING,
        ) and job.started_at is None:
            job.started_at = datetime.utcnow()
        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def add_log(self, job_id: str, message: str, level: LogLevel = LogLevel.INFO) -> JobLog:
        log = JobLog(job_id=job_id, message=message, level=level)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(self, job_id: str) -> list[JobLog]:
        stmt = select(JobLog).where(JobLog.job_id == job_id).order_by(JobLog.timestamp)
        return list(self.db.execute(stmt).scalars().all())

    def add_artifact(self, artifact: ConversionArtifact) -> ConversionArtifact:
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def get_artifact_by_id(self, artifact_id: str) -> ConversionArtifact | None:
        stmt = (
            select(ConversionArtifact).options(_ARTIFACT_WITH_JOB_AND_MODEL).where(ConversionArtifact.id == artifact_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_artifacts_for_user(self, user_id: str, limit: int = 100, offset: int = 0) -> tuple[list[ConversionArtifact], int]:
        stmt = (
            select(ConversionArtifact)
            .join(ConversionJob, ConversionArtifact.job_id == ConversionJob.id)
            .join(Model, ConversionJob.model_id == Model.id)
            .options(_ARTIFACT_WITH_JOB_AND_MODEL)
            .where(Model.user_id == user_id)
        )
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        stmt = stmt.order_by(ConversionArtifact.created_at.desc()).limit(limit).offset(offset)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def count_completed_for_user(self, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ConversionJob)
            .join(Model, ConversionJob.model_id == Model.id)
            .where(Model.user_id == user_id, ConversionJob.status == JobStatus.COMPLETED)
        )
        return self.db.execute(stmt).scalar_one()
