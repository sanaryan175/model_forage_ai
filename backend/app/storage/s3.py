import tempfile
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.storage.base import StorageProvider


class S3StorageProvider(StorageProvider):
    """Production storage provider backed by Amazon S3."""

    def __init__(self, bucket: str, region: str):
        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)
        self._tmp_dir = Path(tempfile.gettempdir()) / "modelforge-s3-cache"
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, file: BinaryIO) -> str:
        self.client.upload_fileobj(file, self.bucket, key)
        return f"s3://{self.bucket}/{key}"

    def read(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def open_path(self, key: str) -> str:
        local_path = self._tmp_dir / key.replace("/", "_")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, str(local_path))
        return str(local_path)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def size(self, key: str) -> int:
        return self.client.head_object(Bucket=self.bucket, Key=key)["ContentLength"]

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
