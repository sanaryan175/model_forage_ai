import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # ENV_FILE picks the config: ".env" (local mock mode, default) or ".env.aws" (S3/SQS/RDS).
    # Resolved against backend/, so workers started from any folder read the same file.
    model_config = SettingsConfigDict(env_file=_BACKEND_DIR / os.getenv("ENV_FILE", ".env"), extra="ignore")

    app_env: str = "development"
    aws_mode: str = "mock"  # "mock" | "aws"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://modelforge:modelforge@localhost:5432/modelforge"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    local_storage_root: str = "./storage"

    aws_region: str = "ap-south-1"
    # Laptop: the `aws configure --profile` name. ECS: leave empty, the task role provides credentials.
    aws_profile: str = ""
    s3_bucket: str = "modelforge-models"
    sqs_cpu_queue: str = "modelforge-cpu"  # TFLite, ONNX baseline, Core ML
    sqs_tensorrt_queue: str = "modelforge-tensorrt"  # laptop GPU worker
    ecr_repository: str = "modelforge"

    max_upload_size_mb: int = 512

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def boto3_session(self):
        import boto3

        return boto3.Session(profile_name=self.aws_profile or None, region_name=self.aws_region)

    @property
    def is_mock_mode(self) -> bool:
        return self.aws_mode.lower() != "aws"


@lru_cache
def get_settings() -> Settings:
    return Settings()
