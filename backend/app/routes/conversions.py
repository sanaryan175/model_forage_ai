from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.conversion import (
    ConversionJobListResponse,
    ConversionJobResponse,
    CreateConversionRequest,
    JobLogListResponse,
)
from app.services.conversion_service import ConversionService, InvalidJobStateError, ModelNotReadyError
from app.services.model_service import ModelService

router = APIRouter(prefix="/api/conversions", tags=["conversions"])


def _ensure_owned_job(db: Session, job_id: str, user: User):
    job = ConversionService(db).get(job_id)
    if job is None or job.model.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion job not found")
    return job


@router.post("", response_model=list[ConversionJobResponse], status_code=status.HTTP_201_CREATED)
def create_conversion(
    payload: CreateConversionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversionJobResponse]:
    model = ModelService(db).get(payload.model_id)
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    try:
        jobs = ConversionService(db).create_jobs(
            model=model,
            target_formats=payload.target_formats,
            optimization=payload.optimization,
            batch_size=payload.batch_size,
            target_device=payload.target_device,
            input_shape=payload.input_shape,
        )
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return jobs


@router.get("", response_model=ConversionJobListResponse)
def list_conversions(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversionJobListResponse:
    items, total = ConversionService(db).list_for_user(current_user.id, limit, offset)
    return ConversionJobListResponse(items=items, total=total)


@router.get("/{job_id}", response_model=ConversionJobResponse)
def get_conversion(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversionJobResponse:
    return _ensure_owned_job(db, job_id, current_user)


@router.post("/{job_id}/cancel", response_model=ConversionJobResponse)
def cancel_conversion(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversionJobResponse:
    job = _ensure_owned_job(db, job_id, current_user)
    try:
        return ConversionService(db).cancel(job)
    except InvalidJobStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{job_id}/retry", response_model=ConversionJobResponse)
def retry_conversion(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversionJobResponse:
    job = _ensure_owned_job(db, job_id, current_user)
    try:
        return ConversionService(db).retry(job)
    except InvalidJobStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{job_id}/logs", response_model=JobLogListResponse)
def get_conversion_logs(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobLogListResponse:
    _ensure_owned_job(db, job_id, current_user)
    logs = ConversionService(db).get_logs(job_id)
    return JobLogListResponse(items=logs)


@router.get("/{job_id}/stream")
async def stream_conversion_progress(job_id: str, token: str | None = None, db: Session = Depends(get_db)):
    """Server-Sent Events stream of job status/progress, polled from the DB every second
    until the job reaches a terminal state. Used by the frontend for real-time updates.

    Browser EventSource cannot send an Authorization header, so this route accepts the
    JWT as a `?token=` query parameter instead of the usual Bearer header.
    """
    import asyncio
    import json

    from fastapi.responses import StreamingResponse
    from jwt import InvalidTokenError

    from app.models.conversion_job import JobStatus
    from app.repositories.user_repository import UserRepository
    from app.utils.security import decode_access_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = decode_access_token(token)["sub"]
    except (InvalidTokenError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    current_user = UserRepository(db).get_by_id(user_id)
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    _ensure_owned_job(db, job_id, current_user)

    async def event_generator():
        terminal = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
        while True:
            db.expire_all()
            job = ConversionService(db).get(job_id)
            if job is None:
                break
            payload = {
                "status": job.status.value,
                "progress": job.progress,
                "error_message": job.error_message,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if job.status in terminal:
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
