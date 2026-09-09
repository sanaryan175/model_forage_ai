import importlib.util

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()

    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception as exc:
        database_status = f"error: {exc}"

    capabilities = {
        "tflite": importlib.util.find_spec("tensorflow") is not None and importlib.util.find_spec("onnx2tf") is not None,
        "tensorrt": importlib.util.find_spec("tensorrt") is not None,
        "coreml": importlib.util.find_spec("coremltools") is not None,
        "pytorch_export": importlib.util.find_spec("torch") is not None,
    }

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "app_env": settings.app_env,
        "aws_mode": settings.aws_mode,
        "database": database_status,
        "converter_capabilities": capabilities,
    }
