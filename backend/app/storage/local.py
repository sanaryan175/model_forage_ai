import shutil
from pathlib import Path
from typing import BinaryIO

from app.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Simulates S3 using the local filesystem, mirroring the AWS bucket layout:
    models/{user_id}/{model_id}/{original|onnx|converted|benchmarks|logs}/...
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents and path != self.root.resolve():
            raise ValueError(f"Path traversal detected for key: {key}")
        return path

    def save(self, key: str, file: BinaryIO) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as out:
            shutil.copyfileobj(file, out)
        return str(path)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def open_path(self, key: str) -> str:
        return str(self._path(key))

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def size(self, key: str) -> int:
        return self._path(key).stat().st_size

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        # In mock mode, downloads are proxied through the API's own artifact-download route.
        return f"/api/artifacts/download-local?key={key}"
