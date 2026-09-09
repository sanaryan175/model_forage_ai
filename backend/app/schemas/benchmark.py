from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BenchmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    model_name: str
    target_format: str
    optimization: str
    model_size_bytes: int | None = None
    latency_mean_ms: float | None = None
    latency_median_ms: float | None = None
    latency_p95_ms: float | None = None
    throughput_ips: float | None = None
    accuracy_pct: float | None = None
    memory_usage_mb: float | None = None
    benchmark_device: str
    unsupported_metrics: str | None = None
    created_at: datetime


class BenchmarkListResponse(BaseModel):
    items: list[BenchmarkResponse]
    total: int


class ComparisonRequest(BaseModel):
    job_ids: list[str]


class ComparisonRow(BaseModel):
    job_id: str
    model_name: str
    target_format: str
    optimization: str
    benchmark: BenchmarkResponse | None = None


class ComparisonResponse(BaseModel):
    rows: list[ComparisonRow]
    best_latency_job_id: str | None = None
    smallest_size_job_id: str | None = None
    highest_accuracy_job_id: str | None = None
    best_overall_job_id: str | None = None
