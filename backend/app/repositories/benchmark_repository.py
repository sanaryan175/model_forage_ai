from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.benchmark import Benchmark
from app.models.conversion_job import ConversionJob
from app.models.model import Model

_WITH_JOB_AND_MODEL = joinedload(Benchmark.job).joinedload(ConversionJob.model)


class BenchmarkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, benchmark: Benchmark) -> Benchmark:
        self.db.add(benchmark)
        self.db.commit()
        self.db.refresh(benchmark)
        return benchmark

    def get_by_job_id(self, job_id: str) -> Benchmark | None:
        stmt = select(Benchmark).options(_WITH_JOB_AND_MODEL).where(Benchmark.job_id == job_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, benchmark_id: str) -> Benchmark | None:
        stmt = select(Benchmark).options(_WITH_JOB_AND_MODEL).where(Benchmark.id == benchmark_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: str, limit: int = 100, offset: int = 0) -> tuple[list[Benchmark], int]:
        stmt = (
            select(Benchmark)
            .join(ConversionJob, Benchmark.job_id == ConversionJob.id)
            .join(Model, ConversionJob.model_id == Model.id)
            .options(_WITH_JOB_AND_MODEL)
            .where(Model.user_id == user_id)
        )
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        stmt = stmt.order_by(Benchmark.created_at.desc()).limit(limit).offset(offset)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def average_latency_for_user(self, user_id: str) -> float | None:
        stmt = (
            select(func.avg(Benchmark.latency_mean_ms))
            .join(ConversionJob, Benchmark.job_id == ConversionJob.id)
            .join(Model, ConversionJob.model_id == Model.id)
            .where(Model.user_id == user_id, Benchmark.latency_mean_ms.is_not(None))
        )
        return self.db.execute(stmt).scalar_one_or_none()
