# Build from the repo root: docker build -f infrastructure/docker/coreml-worker.Dockerfile .
#
# coremltools can convert graphs on Linux, but Core ML inference (used for benchmarking)
# only runs on macOS. This container correctly reports latency/accuracy/memory as N/A
# when not running on macOS (see app/converters/coreml.py) rather than fabricating them.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ml.txt

COPY backend ./backend
COPY workers ./workers

WORKDIR /app/workers
CMD ["python", "coreml_worker.py"]
