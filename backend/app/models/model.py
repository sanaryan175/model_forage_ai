import enum

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ModelFramework(str, enum.Enum):
    PYTORCH = "pytorch"
    ONNX = "onnx"


class ModelStatus(str, enum.Enum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    READY = "ready"
    INVALID = "invalid"


class Model(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "models"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    framework: Mapped[ModelFramework] = mapped_column(Enum(ModelFramework), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.UPLOADING, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    input_shape: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output_shape: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_names: Mapped[str | None] = mapped_column(String(500), nullable=True)
    output_names: Mapped[str | None] = mapped_column(String(500), nullable=True)
    validation_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="models")  # noqa: F821
    conversion_jobs: Mapped[list["ConversionJob"]] = relationship(  # noqa: F821
        back_populates="model", cascade="all, delete-orphan"
    )
