import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.model import ArtifactResponse, ModelListResponse, ModelResponse
from app.services.model_service import ModelService, ModelUploadTooLargeError
from app.storage.factory import get_storage_provider
from app.utils.files import InvalidFileError

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelListResponse)
def list_models(
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModelListResponse:
    items, total = ModelService(db).list_for_user(current_user.id, search, limit, offset)
    return ModelListResponse(items=items, total=total)


@router.post("/upload", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    name: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModelResponse:
    settings = get_settings()
    contents = await file.read()
    try:
        model = ModelService(db).upload(
            user_id=current_user.id,
            name=name,
            filename=file.filename or "model",
            file=io.BytesIO(contents),
            size=len(contents),
            max_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
        )
    except InvalidFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ModelUploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    return model


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ModelResponse:
    model = ModelService(db).get(model_id)
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    service = ModelService(db)
    model = service.get(model_id)
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    service.delete(model)


@router.get("/{model_id}/artifacts", response_model=list[ArtifactResponse])
def list_model_artifacts(
    model_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ArtifactResponse]:
    model = ModelService(db).get(model_id)
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    artifacts = [artifact for job in model.conversion_jobs for artifact in job.artifacts]
    return artifacts


@router.get("/artifacts/download-local")
def download_local_artifact(key: str) -> FileResponse:
    """Only reachable in AWS_MODE=mock; production downloads use signed S3 URLs instead."""
    storage = get_storage_provider()
    if not storage.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return FileResponse(storage.open_path(key), filename=key.split("/")[-1])
