FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ML deps (torch/tensorflow/onnx2tf/coremltools) are heavy; installed in a separate layer
# so application code changes don't invalidate this cache.
ARG INSTALL_ML_DEPS=true
RUN if [ "$INSTALL_ML_DEPS" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
