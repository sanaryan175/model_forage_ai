from sqlalchemy.orm import Session

from app.models.benchmark import Benchmark
from app.models.conversion_job import ConversionJob
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.conversion_repository import ConversionRepository


class BenchmarkService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BenchmarkRepository(db)
        self.jobs = ConversionRepository(db)

    def list_for_user(self, user_id: str, limit: int, offset: int) -> tuple[list[Benchmark], int]:
        return self.repo.list_for_user(user_id, limit=limit, offset=offset)

    def get(self, benchmark_id: str) -> Benchmark | None:
        return self.repo.get_by_id(benchmark_id)

    def compare(self, job_ids: list[str], user_id: str) -> dict:
        rows = []
        best_latency, smallest_size, highest_accuracy = None, None, None
        best_latency_val, smallest_size_val, highest_accuracy_val = None, None, None

        for job_id in job_ids:
            job: ConversionJob | None = self.jobs.get_by_id(job_id)
            if job is None or job.model.user_id != user_id:
                continue
            benchmark = self.repo.get_by_job_id(job_id)
            rows.append(
                {
                    "job_id": job_id,
                    "model_name": job.model.name,
                    "target_format": job.target_format.value,
                    "optimization": job.optimization.value,
                    "benchmark": benchmark,
                }
            )
            if benchmark is None:
                continue
            if benchmark.latency_mean_ms is not None and (
                best_latency_val is None or benchmark.latency_mean_ms < best_latency_val
            ):
                best_latency_val, best_latency = benchmark.latency_mean_ms, job_id
            if benchmark.model_size_bytes is not None and (
                smallest_size_val is None or benchmark.model_size_bytes < smallest_size_val
            ):
                smallest_size_val, smallest_size = benchmark.model_size_bytes, job_id
            if benchmark.accuracy_pct is not None and (
                highest_accuracy_val is None or benchmark.accuracy_pct > highest_accuracy_val
            ):
                highest_accuracy_val, highest_accuracy = benchmark.accuracy_pct, job_id

        # "Best overall" favors the job that wins the most metrics; ties broken by latency.
        scores: dict[str, int] = {}
        for winner in (best_latency, smallest_size, highest_accuracy):
            if winner:
                scores[winner] = scores.get(winner, 0) + 1
        best_overall = max(scores, key=lambda k: (scores[k], -1)) if scores else best_latency

        return {
            "rows": rows,
            "best_latency_job_id": best_latency,
            "smallest_size_job_id": smallest_size,
            "highest_accuracy_job_id": highest_accuracy,
            "best_overall_job_id": best_overall,
        }
