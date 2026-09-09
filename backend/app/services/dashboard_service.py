from collections import Counter

from sqlalchemy.orm import Session

from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.conversion_repository import ConversionRepository
from app.repositories.model_repository import ModelRepository


class DashboardService:
    def __init__(self, db: Session):
        self.models = ModelRepository(db)
        self.jobs = ConversionRepository(db)
        self.benchmarks = BenchmarkRepository(db)

    def get_stats(self, user_id: str) -> dict:
        active_jobs = self.jobs.list_active_for_user(user_id)
        recent_models, _ = self.models.list_for_user(user_id, limit=5, offset=0)
        all_jobs, _ = self.jobs.list_for_user(user_id, limit=1000, offset=0)

        format_counts = Counter(job.target_format.value for job in all_jobs)

        return {
            "stats": {
                "total_models": self.models.count_for_user(user_id),
                "active_jobs": len(active_jobs),
                "completed_conversions": self.jobs.count_completed_for_user(user_id),
                "average_latency_ms": self.benchmarks.average_latency_for_user(user_id),
            },
            "active_jobs": active_jobs,
            "recent_models": recent_models,
            "format_distribution": [{"format": fmt, "count": count} for fmt, count in format_counts.items()],
        }
