from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class QueueProvider(ABC):
    """Common interface for job queues, backed by an in-process queue in mock mode
    or Amazon SQS (fed by EventBridge rules in production).
    """

    @abstractmethod
    def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        """Enqueue a message for a worker to pick up."""

    @abstractmethod
    def subscribe(self, queue_name: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register a handler that consumes messages from `queue_name`."""
