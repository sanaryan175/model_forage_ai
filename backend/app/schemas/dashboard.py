from pydantic import BaseModel

from app.schemas.conversion import ConversionJobResponse
from app.schemas.model import ModelResponse


class DashboardStats(BaseModel):
    total_models: int
    active_jobs: int
    completed_conversions: int
    average_latency_ms: float | None = None


class FormatDistributionItem(BaseModel):
    format: str
    count: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    active_jobs: list[ConversionJobResponse]
    recent_models: list[ModelResponse]
    format_distribution: list[FormatDistributionItem]
