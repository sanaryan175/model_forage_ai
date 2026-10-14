"""ECS Fargate worker: TFLite, ONNX baseline and Core ML jobs from the cpu queue."""

from _runner import run_worker
from app.config import get_settings

if __name__ == "__main__":
    run_worker(get_settings().sqs_cpu_queue)
