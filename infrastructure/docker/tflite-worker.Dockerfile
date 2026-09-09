# Build from the repo root: docker build -f infrastructure/docker/tflite-worker.Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ml.txt

COPY backend ./backend
COPY workers ./workers

WORKDIR /app/workers
CMD ["python", "tflite_worker.py"]
