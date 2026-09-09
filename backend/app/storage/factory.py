from functools import lru_cache

from app.config import get_settings
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider


@lru_cache
def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    if settings.is_mock_mode:
        return LocalStorageProvider(root=settings.local_storage_root)

    from app.storage.s3 import S3StorageProvider

    return S3StorageProvider(bucket=settings.s3_bucket, region=settings.aws_region)
