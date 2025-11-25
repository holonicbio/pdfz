"""Unit tests for retry utilities."""

import asyncio
from typing import Any

import pytest

from docling_hybrid.common.retry import retry_async, retry_with_rate_limit


class RetryTestError(Exception):
    """Test exception for retry tests."""

    pass


class NonRetryableTestError(Exception):
    """Non-retryable test exception."""

    pass


class RateLimitError(Exception):
    """Test exception for rate limiting."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@pytest.mark.asyncio
class TestRetryAsync:
    """Tests for retry_async function."""

    async def test_success_on_first_try(self):
        """Should return immediately if function succeeds on first try."""
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(succeed, max_retries=3)

        assert result == "success"
        assert call_count == 1

    async def test_success_after_retries(self):
        """Should retry and eventually succeed."""
        call_count = 0

        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryTestError("Temporary failure")
            return "success"

        result = await retry_async(
            fail_twice,
            max_retries=3,
            initial_delay=0.01,  # Small delay for fast tests
            retryable_exceptions=(RetryTestError,),
        )

        assert result == "success"
        assert call_count == 3

    async def test_exhausted_retries(self):
        """Should raise exception after max retries exhausted."""
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise RetryTestError("Always fails")

        with pytest.raises(RetryTestError, match="Always fails"):
            await retry_async(
                always_fail,
                max_retries=2,
                initial_delay=0.01,
                retryable_exceptions=(RetryTestError,),
            )

        assert call_count == 3  # Initial + 2 retries

    async def test_non_retryable_exception(self):
        """Should propagate non-retryable exceptions immediately."""
        call_count = 0

        async def fail_non_retryable():
            nonlocal call_count
            call_count += 1
            raise NonRetryableTestError("Cannot retry")

        with pytest.raises(NonRetryableTestError, match="Cannot retry"):
            await retry_async(
                fail_non_retryable,
                max_retries=3,
                initial_delay=0.01,
                retryable_exceptions=(RetryTestError,),  # Different exception type
            )

        assert call_count == 1  # No retries

    async def test_exponential_backoff(self):
        """Should use exponential backoff between retries."""
        call_times: list[float] = []

        async def fail_with_timing():
            call_times.append(asyncio.get_event_loop().time())
            raise RetryTestError("Fail")

        with pytest.raises(RetryTestError):
            await retry_async(
                fail_with_timing,
                max_retries=3,
                initial_delay=0.1,
                exponential_base=2.0,
                retryable_exceptions=(RetryTestError,),
            )

        # Check we made the right number of attempts
        assert len(call_times) == 4  # Initial + 3 retries

        # Check delays are roughly exponential (with tolerance for timing jitter)
        delays = [call_times[i + 1] - call_times[i] for i in range(len(call_times) - 1)]

        assert delays[0] >= 0.08  # First delay ~0.1s
        assert delays[1] >= 0.18  # Second delay ~0.2s (0.1 * 2)
        assert delays[2] >= 0.38  # Third delay ~0.4s (0.2 * 2)

    async def test_max_delay_cap(self):
        """Should cap delay at max_delay."""
        call_times: list[float] = []

        async def fail_with_timing():
            call_times.append(asyncio.get_event_loop().time())
            raise RetryTestError("Fail")

        with pytest.raises(RetryTestError):
            await retry_async(
                fail_with_timing,
                max_retries=5,
                initial_delay=1.0,
                exponential_base=10.0,  # Very high base
                max_delay=2.0,  # Cap at 2 seconds
                retryable_exceptions=(RetryTestError,),
            )

        # Check delays don't exceed max_delay
        delays = [call_times[i + 1] - call_times[i] for i in range(len(call_times) - 1)]

        # After first retry, all delays should be capped at max_delay
        for delay in delays[1:]:
            assert delay <= 2.5  # 2.0 + tolerance

    async def test_context_logging(self):
        """Should include context in log messages."""
        async def fail_once():
            raise RetryTestError("Contextual failure")

        # This should not raise (just testing it accepts context)
        with pytest.raises(RetryTestError):
            await retry_async(
                fail_once,
                max_retries=0,
                retryable_exceptions=(RetryTestError,),
                context={"doc_id": "test-123", "page_num": 5},
            )

    async def test_multiple_retryable_exception_types(self):
        """Should retry on any of the specified exception types."""
        call_count = 0

        async def fail_with_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RetryTestError("First error")
            elif call_count == 2:
                raise ValueError("Second error")
            return "success"

        result = await retry_async(
            fail_with_different_errors,
            max_retries=3,
            initial_delay=0.01,
            retryable_exceptions=(RetryTestError, ValueError),
        )

        assert result == "success"
        assert call_count == 3


@pytest.mark.asyncio
class TestRetryWithRateLimit:
    """Tests for retry_with_rate_limit function."""

    async def test_rate_limit_with_retry_after(self):
        """Should respect Retry-After hint from rate limit exception."""
        call_times: list[float] = []

        async def fail_with_rate_limit():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 2:
                raise RateLimitError("Rate limited", retry_after=0.2)
            return "success"

        def extract_retry_after(exc: Exception) -> float | None:
            if isinstance(exc, RateLimitError):
                return exc.retry_after
            return None

        result = await retry_with_rate_limit(
            fail_with_rate_limit,
            max_retries=2,
            initial_delay=1.0,  # Would normally wait 1s
            rate_limit_exception_type=RateLimitError,
            extract_retry_after=extract_retry_after,
            retryable_exceptions=(RateLimitError,),
        )

        assert result == "success"
        assert len(call_times) == 2

        # Check delay respected Retry-After (0.2s) instead of initial_delay (1.0s)
        delay = call_times[1] - call_times[0]
        assert 0.18 <= delay <= 0.3  # ~0.2s with tolerance

    async def test_rate_limit_without_retry_after(self):
        """Should use exponential backoff if Retry-After not provided."""
        call_times: list[float] = []

        async def fail_with_rate_limit_no_hint():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 2:
                raise RateLimitError("Rate limited", retry_after=None)
            return "success"

        def extract_retry_after(exc: Exception) -> float | None:
            if isinstance(exc, RateLimitError):
                return exc.retry_after
            return None

        result = await retry_with_rate_limit(
            fail_with_rate_limit_no_hint,
            max_retries=2,
            initial_delay=0.1,
            rate_limit_exception_type=RateLimitError,
            extract_retry_after=extract_retry_after,
            retryable_exceptions=(RateLimitError,),
        )

        assert result == "success"
        assert len(call_times) == 2

        # Check used exponential backoff
        delay = call_times[1] - call_times[0]
        assert delay >= 0.08  # ~0.1s with tolerance

    async def test_rate_limit_respects_max_delay(self):
        """Should cap Retry-After at max_delay."""
        call_times: list[float] = []

        async def fail_with_huge_retry_after():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 2:
                raise RateLimitError("Rate limited", retry_after=100.0)  # 100 seconds!
            return "success"

        def extract_retry_after(exc: Exception) -> float | None:
            if isinstance(exc, RateLimitError):
                return exc.retry_after
            return None

        result = await retry_with_rate_limit(
            fail_with_huge_retry_after,
            max_retries=2,
            max_delay=0.5,  # Cap at 0.5s
            rate_limit_exception_type=RateLimitError,
            extract_retry_after=extract_retry_after,
            retryable_exceptions=(RateLimitError,),
        )

        assert result == "success"
        assert len(call_times) == 2

        # Check delay was capped at max_delay
        delay = call_times[1] - call_times[0]
        assert delay <= 0.7  # 0.5s + tolerance

    async def test_non_rate_limit_error(self):
        """Should use exponential backoff for non-rate-limit errors."""
        call_count = 0

        async def fail_with_regular_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryTestError("Regular error")
            return "success"

        result = await retry_with_rate_limit(
            fail_with_regular_error,
            max_retries=2,
            initial_delay=0.05,
            rate_limit_exception_type=RateLimitError,
            retryable_exceptions=(RetryTestError, RateLimitError),
        )

        assert result == "success"
        assert call_count == 2

    async def test_exhausted_rate_limit_retries(self):
        """Should raise after exhausting retries on rate limit."""
        call_count = 0

        async def always_rate_limited():
            nonlocal call_count
            call_count += 1
            raise RateLimitError("Always rate limited", retry_after=0.01)

        def extract_retry_after(exc: Exception) -> float | None:
            if isinstance(exc, RateLimitError):
                return exc.retry_after
            return None

        with pytest.raises(RateLimitError, match="Always rate limited"):
            await retry_with_rate_limit(
                always_rate_limited,
                max_retries=2,
                rate_limit_exception_type=RateLimitError,
                extract_retry_after=extract_retry_after,
                retryable_exceptions=(RateLimitError,),
            )

        assert call_count == 3  # Initial + 2 retries
