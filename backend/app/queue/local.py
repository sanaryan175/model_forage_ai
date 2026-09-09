import queue
import threading
from collections.abc import Callable
from typing import Any

import structlog

from app.queue.base import QueueProvider

logger = structlog.get_logger(__name__)


class LocalQueueProvider(QueueProvider):
    """In-process simulation of EventBridge -> SQS -> Lambda fan-out for local/mock mode.

    Each `queue_name` gets its own FIFO queue and a dedicated consumer thread, mirroring
    the isolation SQS queues provide between the tflite/tensorrt/coreml pipelines.
    """

    def __init__(self):
        self._queues: dict[str, queue.Queue] = {}
        self._threads: dict[str, threading.Thread] = {}

    def _get_queue(self, queue_name: str) -> queue.Queue:
        if queue_name not in self._queues:
            self._queues[queue_name] = queue.Queue()
        return self._queues[queue_name]

    def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        logger.info("queue.publish", queue=queue_name, message=message)
        self._get_queue(queue_name).put(message)

    def subscribe(self, queue_name: str, handler: Callable[[dict[str, Any]], None]) -> None:
        q = self._get_queue(queue_name)

        def _run():
            while True:
                message = q.get()
                try:
                    handler(message)
                except Exception:
                    logger.exception("queue.handler_failed", queue=queue_name, message=message)
                finally:
                    q.task_done()

        thread = threading.Thread(target=_run, name=f"queue-worker-{queue_name}", daemon=True)
        thread.start()
        self._threads[queue_name] = thread


_local_queue_singleton = LocalQueueProvider()


def get_local_queue() -> LocalQueueProvider:
    return _local_queue_singleton
