import json
import threading
import time
from collections.abc import Callable
from typing import Any

import structlog

from app.queue.base import QueueProvider

logger = structlog.get_logger(__name__)


class SQSQueueProvider(QueueProvider):
    """Production queue provider backed by Amazon SQS. The API publishes {"job_id": ...}
    when a user starts a conversion; workers poll their queue (resolved by name). A message
    whose handler crashes is retried, then moved to the queue's DLQ after 3 attempts.
    """

    def __init__(self, client):
        self.client = client
        self._url_cache: dict[str, str] = {}

    def _queue_url(self, queue_name: str) -> str:
        if queue_name not in self._url_cache:
            self._url_cache[queue_name] = self.client.get_queue_url(QueueName=queue_name)["QueueUrl"]
        return self._url_cache[queue_name]

    def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        self.client.send_message(QueueUrl=self._queue_url(queue_name), MessageBody=json.dumps(message))

    def subscribe(self, queue_name: str, handler: Callable[[dict[str, Any]], None]) -> None:
        def _poll():
            url = self._queue_url(queue_name)
            while True:
                response = self.client.receive_message(
                    QueueUrl=url, MaxNumberOfMessages=1, WaitTimeSeconds=10
                )
                for msg in response.get("Messages", []):
                    try:
                        handler(json.loads(msg["Body"]))
                        self.client.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
                    except Exception:
                        logger.exception("sqs.handler_failed", queue=queue_name)
                if not response.get("Messages"):
                    time.sleep(1)

        threading.Thread(target=_poll, name=f"sqs-worker-{queue_name}", daemon=True).start()
