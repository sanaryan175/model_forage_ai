from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.benchmark import BenchmarkListResponse, BenchmarkResponse, ComparisonRequest, ComparisonResponse
from app.services.benchmark_service import BenchmarkService

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("", response_model=BenchmarkListResponse)
def list_benchmarks(
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BenchmarkListResponse:
    items, total = BenchmarkService(db).list_for_user(current_user.id, limit, offset)
    return BenchmarkListResponse(items=items, total=total)


@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
def get_benchmark(benchmark_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> BenchmarkResponse:
    benchmark = BenchmarkService(db).get(benchmark_id)
    if benchmark is None or benchmark.job.model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")
    return benchmark


@router.post("/compare", response_model=ComparisonResponse)
def compare_benchmarks(
    payload: ComparisonRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ComparisonResponse:
    result = BenchmarkService(db).compare(payload.job_ids, current_user.id)
    return result
