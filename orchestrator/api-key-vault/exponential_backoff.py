"""
exponential_backoff.py – Retry logic with exponential backoff and jitter.
"""

import asyncio
import random
import time
from functools import wraps
from typing import TypeVar, Callable, Optional, Tuple, Any

T = TypeVar('T')


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class ExponentialBackoffRetry:
    """
    Exponential backoff retry decorator for async functions.
    """

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retry_on: Tuple[type, ...] = (RateLimitError,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_on = retry_on

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(self.max_retries):
                try:
                    return await func(*args, **kwargs)
                except self.retry_on as e:
                    last_exception = e

                    if attempt == self.max_retries - 1:
                        raise

                    delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                    if self.jitter:
                        delay = delay * (0.5 + random.random())

                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper


def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """Decorator factory for exponential backoff."""
    return ExponentialBackoffRetry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
    )
