import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any

from src.core.exceptions import FetchError

logger = logging.getLogger(__name__)


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (FetchError,),
) -> Callable:
    """지수 백오프 재시도 async 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor**attempt)
                        logger.warning(
                            "재시도 %d/%d (%s), %.1f초 후 재시도",
                            attempt + 1,
                            max_retries,
                            e,
                            delay,
                        )
                        await asyncio.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
