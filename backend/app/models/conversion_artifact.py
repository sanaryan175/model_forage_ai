from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.conversion_job import TargetFormat


class ConversionArtifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversion_artifacts"

    job_id: Mapped[str] = mapped_column(
        ForeignKey("conversion_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    format: Mapped[TargetFormat] = mapped_column(nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    job: Mapped["ConversionJob"] = relationship(back_populates="artifacts")  # noqa: F821

    @property
    def model_name(self) -> str:
        return self.job.model.name

    @property
    def optimization(self) -> str:
        return self.job.optimization.value
