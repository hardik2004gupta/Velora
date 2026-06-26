"""
Async retry helper with exponential back-off.

Used by the provider layer to retry failed HTTP calls to LLM APIs before
marking a provider as degraded.

Usage::

    from app.utils.retry import retry_async

    result = await retry_async(call_openai, max_attempts=2, base_delay=0.5)
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from app.core.logging import get_logger

log = get_logger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_attempts: int = 2,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retriable_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """
    Call *func* with *args* / *kwargs*, retrying on failure.

    Args:
        func: Async callable to execute.
        max_attempts: Maximum number of attempts (including the first).
        base_delay: Seconds to wait before the first retry.
        backoff_factor: Multiplier applied to the delay on each subsequent retry.
        retriable_exceptions: Only retry on these exception types.

    Returns:
        The return value of *func* on success.

    Raises:
        The last exception if all attempts are exhausted.
    """
    last_exc: Exception | None = None
    delay = base_delay

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except retriable_exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                log.warning(
                    "retry_exhausted",
                    func=func.__qualname__,
                    attempts=attempt,
                    error=str(exc),
                )
                break

            log.info(
                "retry_attempt",
                func=func.__qualname__,
                attempt=attempt,
                delay=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)
            delay *= backoff_factor

    raise last_exc  # type: ignore[misc]


def with_retry(
    max_attempts: int = 2,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retriable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator version of ``retry_async``."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_async(
                func,
                *args,
                max_attempts=max_attempts,
                base_delay=base_delay,
                backoff_factor=backoff_factor,
                retriable_exceptions=retriable_exceptions,
                **kwargs,
            )

        return wrapper

    return decorator
