from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.api_key import ApiKeyCreatedResponse, ApiKeyResponse, CreateApiKeyRequest
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.api_key_service import ApiKeyService
from app.services.auth_service import AuthService, EmailAlreadyRegisteredError, InvalidCredentialsError

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        _, token = AuthService(db).register(payload.name, payload.email, payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        _, token = AuthService(db).login(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: CreateApiKeyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ApiKeyCreatedResponse:
    key, raw_key = ApiKeyService(db).create(current_user.id, payload.name)
    return ApiKeyCreatedResponse(
        id=key.id, name=key.name, key_prefix=key.key_prefix, created_at=key.created_at, key=raw_key
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ApiKeyResponse]:
    return ApiKeyService(db).list_for_user(current_user.id)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(key_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not ApiKeyService(db).revoke(key_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
