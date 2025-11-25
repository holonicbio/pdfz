"""Retry utilities for async operations.

This module provides utilities for retrying async operations with exponential
backoff. It's designed for use with HTTP requests and other I/O operations
that may fail transiently.

The retry logic supports:
- Exponential backoff with configurable base and max delay
- Exception filtering (retry only specific exceptions)
- Configurable max retries
- Structured logging of retry attempts

Usage:
    from docling_hybrid.common.retry import retry_async

    async def fetch_data():
        async with session.get(url) as response:
            return await response.json()

    # Retry up to 3 times with exponential backoff
    result = await retry_async(
        fetch_data,
        max_retries=3,
        initial_delay=1.0,
        exponential_base=2.0,
        retryable_exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
    )

You can also use it as a decorator:
    from functools import wraps
    from docling_hybrid.common.retry import retry_async

    def with_retry(**retry_kwargs):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await retry_async(
                    lambda: func(*args, **kwargs),
                    **retry_kwargs
                )
            return wrapper
        return decorator

    @with_retry(max_retries=3, initial_delay=1.0)
    async def fetch_data(url: str):
        ...
"""

import asyncio
from typing import Any, Awaitable, Callable, TypeVar

from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    context: dict[str, Any] | None = None,
) -> T:
    """Retry an async function with exponential backoff.

    This function will call `func` and retry on failure with exponential
    backoff. The delay between retries increases exponentially:
    - Attempt 1: initial_delay
    - Attempt 2: initial_delay * exponential_base
    - Attempt 3: initial_delay * exponential_base^2
    - etc.

    The delay is capped at max_delay to prevent excessive waiting.

    Args:
        func: Async function to retry (takes no arguments, use lambda if needed)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        retryable_exceptions: Tuple of exception types to retry on (default: all)
        context: Optional logging context (e.g., {"doc_id": "123", "page": 1})

    Returns:
        Result of calling func()

    Raises:
        The last exception raised by func if all retries are exhausted
        Non-retryable exceptions are raised immediately

    Example:
        >>> async def fetch_data():
        ...     async with session.get(url) as response:
        ...         return await response.json()
        >>>
        >>> result = await retry_async(
        ...     fetch_data,
        ...     max_retries=3,
        ...     initial_delay=1.0,
        ...     exponential_base=2.0,
        ...     retryable_exceptions=(aiohttp.ClientError,),
        ... )
    """
    context = context or {}
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):  # +1 because first attempt is not a retry
        try:
            # Try to execute the function
            result = await func()

            # If we get here, it succeeded
            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    attempt=attempt,
                    max_retries=max_retries,
                    **context,
                )

            return result

        except Exception as e:
            # Check if this exception is retryable
            if not isinstance(e, retryable_exceptions):
                # Non-retryable exception, raise immediately
                logger.debug(
                    "non_retryable_exception",
                    exception_type=type(e).__name__,
                    error=str(e),
                    **context,
                )
                raise

            last_exception = e

            # If this was the last attempt, raise the exception
            if attempt >= max_retries:
                logger.error(
                    "retry_exhausted",
                    attempts=attempt + 1,
                    max_retries=max_retries,
                    exception_type=type(e).__name__,
                    error=str(e),
                    **context,
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** attempt), max_delay)

            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_seconds=delay,
                exception_type=type(e).__name__,
                error=str(e),
                **context,
            )

            # Wait before retrying
            await asyncio.sleep(delay)

    # This should never be reached, but type checker needs it
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected: retry loop exited without result or exception")


def should_retry_on_status(status_code: int) -> bool:
    """Determine if an HTTP status code is retryable.

    Retryable status codes are:
    - 408 Request Timeout
    - 429 Too Many Requests (rate limiting)
    - 500 Internal Server Error
    - 502 Bad Gateway
    - 503 Service Unavailable
    - 504 Gateway Timeout

    Args:
        status_code: HTTP status code

    Returns:
        True if the status code indicates a retryable error

    Example:
        >>> if response.status != 200:
        ...     if should_retry_on_status(response.status):
        ...         # Retry the request
        ...     else:
        ...         # Permanent error, don't retry
    """
    return status_code in (408, 429, 500, 502, 503, 504)


def get_retry_after_delay(headers: dict[str, str], default: float = 60.0) -> float:
    """Extract retry delay from Retry-After header.

    The Retry-After header can be either:
    - A number of seconds (integer)
    - An HTTP date (not currently supported)

    Args:
        headers: HTTP response headers (case-insensitive dict)
        default: Default delay if header is missing or invalid

    Returns:
        Delay in seconds before retrying

    Example:
        >>> if response.status == 429:
        ...     delay = get_retry_after_delay(response.headers)
        ...     await asyncio.sleep(delay)
    """
    # Try to get Retry-After header (case-insensitive)
    retry_after = None
    for key, value in headers.items():
        if key.lower() == "retry-after":
            retry_after = value
            break

    if retry_after is None:
        return default

    # Try to parse as integer (seconds)
    try:
        delay = int(retry_after)
        # Sanity check: don't wait more than 5 minutes
        return min(float(delay), 300.0)
    except ValueError:
        # Could be an HTTP date, but we don't support that yet
        logger.warning(
            "retry_after_parse_failed",
            retry_after=retry_after,
            using_default=default,
        )
        return default
