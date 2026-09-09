from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import artifacts, auth, benchmarks, conversions, dashboard, health, models
from app.utils.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="ModelForge AI API",
    description=(
        "Cloud-based deep learning model compiler & deployment platform. "
        "Convert ONNX/PyTorch models to TFLite, TensorRT, and Core ML, then "
        "benchmark and compare them from a single API."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(models.router)
app.include_router(conversions.router)
app.include_router(artifacts.router)
app.include_router(benchmarks.router)
app.include_router(dashboard.router)
