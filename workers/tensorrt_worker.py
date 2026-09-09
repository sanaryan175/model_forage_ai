from _runner import run_worker
from app.config import get_settings

if __name__ == "__main__":
    run_worker(get_settings().sqs_tensorrt_queue)
