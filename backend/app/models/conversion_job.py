import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TargetFormat(str, enum.Enum):
    TFLITE = "tflite"
    TENSORRT = "tensorrt"
    COREML = "coreml"


class OptimizationType(str, enum.Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    CONVERTING = "converting"
    OPTIMIZING = "optimizing"
    BENCHMARKING = "benchmarking"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversionJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversion_jobs"

    model_id: Mapped[str] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    target_format: Mapped[TargetFormat] = mapped_column(Enum(TargetFormat), nullable=False)
    optimization: Mapped[OptimizationType] = mapped_column(Enum(OptimizationType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    batch_size: Mapped[int] = mapped_column(Integer, default=1)
    target_device: Mapped[str] = mapped_column(String(100), default="cpu")
    input_shape: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Comma-separated dims, required to export PyTorch (.pt) models to ONNX"
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    model: Mapped["Model"] = relationship(back_populates="conversion_jobs")  # noqa: F821
    artifacts: Mapped[list["ConversionArtifact"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan"
    )
    benchmarks: Mapped[list["Benchmark"]] = relationship(back_populates="job", cascade="all, delete-orphan")  # noqa: F821
    logs: Mapped[list["JobLog"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan", order_by="JobLog.timestamp"
    )
