from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageProvider(ABC):
    """Common interface for object storage, backed by local disk in mock mode or S3 in production."""

    @abstractmethod
    def save(self, key: str, file: BinaryIO) -> str:
        """Persist a file under `key`. Returns the storage path/URI actually used."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Read the full contents of the object at `key`."""

    @abstractmethod
    def open_path(self, key: str) -> str:
        """Return a local filesystem path usable by ML libraries (downloads from S3 if needed)."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object at `key`."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check whether an object exists at `key`."""

    @abstractmethod
    def size(self, key: str) -> int:
        """Return the size in bytes of the object at `key`."""

    @abstractmethod
    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a URL the client can use to download the object (signed URL in production)."""
