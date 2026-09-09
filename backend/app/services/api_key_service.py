import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.utils.security import hash_password, verify_password

_KEY_PREFIX = "mfk_"


class ApiKeyService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, name: str) -> tuple[ApiKey, str]:
        raw_key = f"{_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        key = ApiKey(
            user_id=user_id,
            name=name,
            key_prefix=raw_key[:12],
            key_hash=hash_password(raw_key),
        )
        self.db.add(key)
        self.db.commit()
        self.db.refresh(key)
        return key, raw_key

    def list_for_user(self, user_id: str) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def revoke(self, key_id: str, user_id: str) -> bool:
        key = self.db.get(ApiKey, key_id)
        if key is None or key.user_id != user_id:
            return False
        self.db.delete(key)
        self.db.commit()
        return True

    def verify(self, raw_key: str) -> ApiKey | None:
        """Used by future API-key-authenticated endpoints; not wired into request auth yet."""
        prefix = raw_key[:12]
        stmt = select(ApiKey).where(ApiKey.key_prefix == prefix)
        for key in self.db.execute(stmt).scalars().all():
            if verify_password(raw_key, key.key_hash):
                return key
        return None
