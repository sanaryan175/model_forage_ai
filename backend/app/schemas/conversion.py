from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversion_job import JobStatus, OptimizationType, TargetFormat
from app.models.job_log import LogLevel


class CreateConversionRequest(BaseModel):
    model_id: str
    target_formats: list[TargetFormat] = Field(min_length=1)
    optimization: OptimizationType = OptimizationType.FP32
    batch_size: int = Field(default=1, ge=1, le=256)
    target_device: str = "cpu"
    input_shape: list[int] | None = Field(
        default=None, description="Required when converting a PyTorch (.pt) model, e.g. [1, 3, 224, 224]"
    )


class ConversionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_id: str
    target_format: TargetFormat
    optimization: OptimizationType
    status: JobStatus
    progress: int
    batch_size: int
    target_device: str
    input_shape: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime


class ConversionJobListResponse(BaseModel):
    items: list[ConversionJobResponse]
    total: int


class JobLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    level: LogLevel
    message: str
    timestamp: datetime


class JobLogListResponse(BaseModel):
    items: list[JobLogResponse]
