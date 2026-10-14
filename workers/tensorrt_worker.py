"""GPU worker for TensorRT jobs. Runs on a machine with an NVIDIA GPU (the team laptop):

    cd backend
    $env:ENV_FILE=".env.aws"; ..\.venv\Scripts\python.exe ..\workers\tensorrt_worker.py
"""

from _runner import run_worker
from app.config import get_settings

if __name__ == "__main__":
    run_worker(get_settings().sqs_tensorrt_queue)
