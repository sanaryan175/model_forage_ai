from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = "modelforge-models"
    sqs_tflite_queue: str = "modelforge-tflite"
    sqs_tensorrt_queue: str = "modelforge-tensorrt"
    sqs_coreml_queue: str = "modelforge-coreml"
    ecr_repository: str = "modelforge"

    max_upload_size_mb: int = 512

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_mock_mode(self) -> bool:
        return self.aws_mode.lower() != "aws"


@lru_cache
def get_settings() -> Settings:
    return Settings()
