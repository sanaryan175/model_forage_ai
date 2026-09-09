from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.model import ModelFramework, ModelStatus


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    original_filename: str
    framework: ModelFramework
    version: str
    size: int
    status: ModelStatus
    input_shape: str | None = None
    output_shape: str | None = None
    input_names: str | None = None
    output_names: str | None = None
    validation_error: str | None = None
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseModel):
    items: list[ModelResponse]
    total: int


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    format: str
    file_path: str
    file_size: int
    checksum: str
    created_at: datetime
    model_name: str | None = None
    optimization: str | None = None


class ArtifactListResponse(BaseModel):
    items: list[ArtifactResponse]
    total: int
