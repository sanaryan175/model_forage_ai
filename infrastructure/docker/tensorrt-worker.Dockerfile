# Build from the repo root: docker build -f infrastructure/docker/tensorrt-worker.Dockerfile .
#
# Requires an NVIDIA GPU + the NVIDIA Container Toolkit on the Docker host to actually
# build TensorRT engines — this is why it is a separate ECS+GPU task in production
# (see infrastructure/aws). Without a GPU, this container still starts and correctly
# reports every job as environment-limited (see app/converters/tensorrt.py) instead of
# fabricating a conversion.
FROM nvcr.io/nvidia/tensorrt:24.08-py3

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY workers ./workers

WORKDIR /app/workers
CMD ["python3", "tensorrt_worker.py"]
