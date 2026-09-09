from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.conversion_repository import ConversionRepository
from app.schemas.model import ArtifactListResponse
from app.storage.factory import get_storage_provider

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("", response_model=ArtifactListResponse)
def list_artifacts(
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ArtifactListResponse:
    items, total = ConversionRepository(db).list_artifacts_for_user(current_user.id, limit, offset)
    return ArtifactListResponse(items=items, total=total)


@router.get("/{artifact_id}/download")
def download_artifact(artifact_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    artifact = ConversionRepository(db).get_artifact_by_id(artifact_id)
    if artifact is None or artifact.job.model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    storage = get_storage_provider()
    if not storage.exists(artifact.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file is missing from storage")

    url = storage.get_download_url(artifact.file_path)
    if url.startswith("/api/"):
        return FileResponse(storage.open_path(artifact.file_path), filename=artifact.file_path.split("/")[-1])
    return RedirectResponse(url)
