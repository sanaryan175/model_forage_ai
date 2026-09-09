from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateApiKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str  # only ever returned once, at creation time
