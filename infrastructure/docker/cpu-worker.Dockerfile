# ECS Fargate CPU worker: TFLite, ONNX baseline and Core ML jobs from the cpu SQS queue.
# Build from the repo root:
#   docker build -f infrastructure/docker/cpu-worker.Dockerfile -t modelforge-cpu-worker .
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY backend/requirements.txt backend/requirements-ml.txt ./
# CPU-only PyTorch first: the default Linux wheel pulls ~2.5 GB of CUDA libraries this
# worker can't use. 2.14.0+cpu then satisfies requirements-ml's torch==2.14.0 pin.
RUN pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt -r requirements-ml.txt

COPY backend ./backend
COPY workers ./workers

WORKDIR /app/workers
CMD ["python", "cpu_worker.py"]
