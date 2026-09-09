"""Shared entrypoint logic for the format-specific worker processes.

Each worker subscribes to its own SQS queue (mirroring the isolated
modelforge-tflite / modelforge-tensorrt / modelforge-coreml queues from the AWS
architecture) and runs the same conversion pipeline used by the in-process
LocalJobExecutor, so behavior is identical locally and in production ECS tasks.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import structlog  # noqa: E402

from app.queue.factory import get_queue_provider  # noqa: E402
from app.workers.conversion_worker import run_conversion_job  # noqa: E402

logger = structlog.get_logger(__name__)


def run_worker(queue_name: str) -> None:
    logger.info("worker.starting", queue=queue_name)
    queue = get_queue_provider()

    def handle(message: dict) -> None:
        job_id = message["job_id"]
        logger.info("worker.received_job", queue=queue_name, job_id=job_id)
        run_conversion_job(job_id)

    queue.subscribe(queue_name, handle)

    # subscribe() spawns a background thread; keep the process alive.
    while True:
        time.sleep(3600)
