from functools import lru_cache

from app.config import get_settings
from app.queue.base import QueueProvider
from app.queue.local import get_local_queue


@lru_cache
def get_queue_provider() -> QueueProvider:
    settings = get_settings()
    if settings.is_mock_mode:
        return get_local_queue()

    from app.queue.sqs import SQSQueueProvider

    return SQSQueueProvider(region=settings.aws_region)
