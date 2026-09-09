from sqlalchemy import BigInteger, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Benchmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "benchmarks"

    job_id: Mapped[str] = mapped_column(
        ForeignKey("conversion_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    model_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    latency_mean_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_median_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_p95_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    throughput_ips: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_device: Mapped[str] = mapped_column(String(100), default="cpu")
    unsupported_metrics: Mapped[str | None] = mapped_column(
        String(500), nullable=True, doc="Comma-separated metrics unavailable in this environment (shown as N/A)"
    )

    job: Mapped["ConversionJob"] = relationship(back_populates="benchmarks")  # noqa: F821

    @property
    def model_name(self) -> str:
        return self.job.model.name

    @property
    def target_format(self) -> str:
        return self.job.target_format.value

    @property
    def optimization(self) -> str:
        return self.job.optimization.value
