"""Async retry utilities with exponential backoff.

This module provides utilities for retrying async operations with configurable
exponential backoff, particularly useful for HTTP requests to external APIs.

Features:
- Exponential backoff with configurable base and max delay
- Selective exception filtering
- Retry count limiting
- Detailed logging of retry attempts

Example:
    >>> async def fetch_data():
    ...     async with session.get(url) as resp:
    ...         return await resp.json()
    >>>
    >>> result = await retry_async(
    ...     fetch_data,
    ...     max_retries=3,
    ...     retryable_exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
    ... )
"""

import asyncio
from typing import Any, Awaitable, Callable, Type, TypeVar

from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
    context: dict[str, Any] | None = None,
) -> T:
    """Retry an async function with exponential backoff.

    This function attempts to execute an async callable up to `max_retries + 1` times
    (initial attempt + retries). Between attempts, it waits for an exponentially
    increasing delay.

    Args:
        func: Async callable to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        retryable_exceptions: Tuple of exception types to retry on (default: all)
        context: Optional context dict for logging (e.g., {"doc_id": "...", "page_num": 1})

    Returns:
        The result of the successful function call

    Raises:
        The last exception encountered if all retries are exhausted
        Non-retryable exceptions are propagated immediately

    Example:
        >>> async def flaky_api_call():
        ...     # May fail with ClientError
        ...     return await session.get(url)
        >>>
        >>> result = await retry_async(
        ...     flaky_api_call,
        ...     max_retries=3,
        ...     retryable_exceptions=(aiohttp.ClientError,),
        ...     context={"endpoint": "/api/ocr"},
        ... )
    """
    context = context or {}
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            result = await func()

            # Log successful retry if not first attempt
            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    attempt=attempt,
                    total_attempts=attempt + 1,
                    **context,
                )

            return result

        except retryable_exceptions as e:
            last_exception = e

            # If this is the last attempt, don't wait
            if attempt >= max_retries:
                logger.error(
                    "retry_exhausted",
                    max_retries=max_retries,
                    total_attempts=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                    **context,
                )
                break

            # Log retry attempt
            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_seconds=delay,
                error=str(e),
                error_type=type(e).__name__,
                **context,
            )

            # Wait before retrying
            await asyncio.sleep(delay)

            # Calculate next delay with exponential backoff
            delay = min(delay * exponential_base, max_delay)

        except Exception as e:
            # Non-retryable exception - propagate immediately
            logger.error(
                "non_retryable_exception",
                attempt=attempt + 1,
                error=str(e),
                error_type=type(e).__name__,
                **context,
            )
            raise

    # All retries exhausted
    if last_exception:
        raise last_exception

    # This should never happen, but make type checker happy
    raise RuntimeError("retry_async: unexpected state")


async def retry_with_rate_limit(
    func: Callable[..., Awaitable[T]],
    *,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
    rate_limit_exception_type: Type[Exception] | None = None,
    extract_retry_after: Callable[[Exception], float | None] | None = None,
    context: dict[str, Any] | None = None,
) -> T:
    """Retry an async function with rate limit awareness.

    This is an enhanced version of retry_async that can recognize rate limit
    exceptions and respect Retry-After hints from the exception or response.

    Args:
        func: Async callable to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        exponential_base: Base for exponential backoff calculation
        max_delay: Maximum delay between retries in seconds
        retryable_exceptions: Tuple of exception types to retry on
        rate_limit_exception_type: Exception type that indicates rate limiting (e.g., custom 429 error)
        extract_retry_after: Function to extract retry-after delay from exception
        context: Optional context dict for logging

    Returns:
        The result of the successful function call

    Raises:
        The last exception encountered if all retries are exhausted

    Example:
        >>> def get_retry_after(exc):
        ...     # Extract Retry-After from custom exception
        ...     if hasattr(exc, 'retry_after'):
        ...         return float(exc.retry_after)
        ...     return None
        >>>
        >>> result = await retry_with_rate_limit(
        ...     api_call,
        ...     rate_limit_exception_type=RateLimitError,
        ...     extract_retry_after=get_retry_after,
        ... )
    """
    context = context or {}
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            result = await func()

            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    attempt=attempt,
                    total_attempts=attempt + 1,
                    **context,
                )

            return result

        except retryable_exceptions as e:
            last_exception = e

            # If this is the last attempt, don't wait
            if attempt >= max_retries:
                logger.error(
                    "retry_exhausted",
                    max_retries=max_retries,
                    total_attempts=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                    **context,
                )
                break

            # Check if this is a rate limit error with Retry-After hint
            actual_delay = delay
            is_rate_limit = (
                rate_limit_exception_type is not None
                and isinstance(e, rate_limit_exception_type)
            )

            if is_rate_limit and extract_retry_after:
                retry_after = extract_retry_after(e)
                if retry_after is not None:
                    actual_delay = min(retry_after, max_delay)
                    logger.warning(
                        "rate_limit_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        retry_after_seconds=actual_delay,
                        error=str(e),
                        **context,
                    )
                else:
                    logger.warning(
                        "rate_limit_retry_no_hint",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=actual_delay,
                        error=str(e),
                        **context,
                    )
            else:
                logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=actual_delay,
                    error=str(e),
                    error_type=type(e).__name__,
                    **context,
                )

            # Wait before retrying
            await asyncio.sleep(actual_delay)

            # Calculate next delay with exponential backoff (unless we used Retry-After)
            if not (is_rate_limit and extract_retry_after and extract_retry_after(e)):
                delay = min(delay * exponential_base, max_delay)

        except Exception as e:
            # Non-retryable exception - propagate immediately
            logger.error(
                "non_retryable_exception",
                attempt=attempt + 1,
                error=str(e),
                error_type=type(e).__name__,
                **context,
            )
            raise

    # All retries exhausted
    if last_exception:
        raise last_exception

    raise RuntimeError("retry_with_rate_limit: unexpected state")
