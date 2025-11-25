"""Unit tests for retry utilities."""

import asyncio
import time
from typing import Any

import pytest

from docling_hybrid.common.retry import (
    retry_async,
    should_retry_on_status,
    get_retry_after_delay,
)


class TestRetryAsync:
    """Tests for retry_async function."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """Test that successful function doesn't retry."""
        call_count = 0

        async def succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(succeeds, max_retries=3)

        assert result == "success"
        assert call_count == 1  # Should only be called once

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test that function succeeds after some retries."""
        call_count = 0

        async def fails_twice_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_async(
            fails_twice_then_succeeds,
            max_retries=3,
            initial_delay=0.01,  # Fast for testing
        )

        assert result == "success"
        assert call_count == 3  # Called 3 times (2 failures + 1 success)

    @pytest.mark.asyncio
    async def test_retryable_exception_retries(self):
        """Test that retryable exceptions trigger retries."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_async(
                always_fails,
                max_retries=2,
                initial_delay=0.01,
                retryable_exceptions=(ValueError,),
            )

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception_no_retry(self):
        """Test that non-retryable exceptions don't trigger retries."""
        call_count = 0

        async def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable")

        with pytest.raises(TypeError, match="Non-retryable"):
            await retry_async(
                raises_type_error,
                max_retries=3,
                initial_delay=0.01,
                retryable_exceptions=(ValueError,),  # Only ValueError is retryable
            )

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test that delays increase exponentially."""
        call_times = []

        async def always_fails():
            call_times.append(time.time())
            raise ValueError("Test")

        with pytest.raises(ValueError):
            await retry_async(
                always_fails,
                max_retries=3,
                initial_delay=0.1,
                exponential_base=2.0,
            )

        # Check that delays increase (within some tolerance)
        # Expected delays: 0.1, 0.2, 0.4
        assert len(call_times) == 4  # Initial + 3 retries

        # Calculate actual delays
        delays = [call_times[i + 1] - call_times[i] for i in range(len(call_times) - 1)]

        # Check delays are approximately correct (with some tolerance for timing)
        assert 0.05 < delays[0] < 0.15  # ~0.1s
        assert 0.15 < delays[1] < 0.25  # ~0.2s
        assert 0.35 < delays[2] < 0.45  # ~0.4s

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        call_times = []

        async def always_fails():
            call_times.append(time.time())
            raise ValueError("Test")

        with pytest.raises(ValueError):
            await retry_async(
                always_fails,
                max_retries=3,
                initial_delay=1.0,
                exponential_base=10.0,  # Would grow very large
                max_delay=0.5,  # But capped at 0.5s
            )

        # Calculate actual delays
        delays = [call_times[i + 1] - call_times[i] for i in range(len(call_times) - 1)]

        # All delays should be at most max_delay (with some tolerance)
        for delay in delays:
            assert delay < 0.6  # max_delay + small tolerance

    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """Test that max_retries=0 means no retries."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Fail")

        with pytest.raises(ValueError):
            await retry_async(
                always_fails,
                max_retries=0,
                initial_delay=0.01,
            )

        assert call_count == 1  # Only initial call, no retries

    @pytest.mark.asyncio
    async def test_context_passed_through(self):
        """Test that context is used in logging (no errors)."""
        async def succeeds():
            return "ok"

        # Should not raise any errors
        result = await retry_async(
            succeeds,
            context={"doc_id": "test-123", "page": 1},
        )

        assert result == "ok"

    @pytest.mark.asyncio
    async def test_multiple_exception_types_retryable(self):
        """Test that multiple exception types can be retryable."""
        call_count = 0
        exceptions = [ValueError("One"), TypeError("Two"), RuntimeError("Three")]

        async def raises_different_errors():
            nonlocal call_count
            if call_count < len(exceptions):
                error = exceptions[call_count]
                call_count += 1
                raise error
            call_count += 1
            return "success"

        result = await retry_async(
            raises_different_errors,
            max_retries=3,
            initial_delay=0.01,
            retryable_exceptions=(ValueError, TypeError, RuntimeError),
        )

        assert result == "success"
        assert call_count == 4  # 3 failures + 1 success

    @pytest.mark.asyncio
    async def test_default_retryable_exceptions(self):
        """Test that default retryable_exceptions is all exceptions."""
        call_count = 0

        async def raises_custom_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Custom error")
            return "success"

        # Default retryable_exceptions=(Exception,) should catch all
        result = await retry_async(
            raises_custom_error,
            max_retries=2,
            initial_delay=0.01,
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_function_with_await(self):
        """Test that async operations work correctly."""
        async def async_operation():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await retry_async(async_operation, max_retries=2)

        assert result == "async_result"


class TestShouldRetryOnStatus:
    """Tests for should_retry_on_status function."""

    def test_retryable_status_codes(self):
        """Test that retryable status codes return True."""
        retryable_codes = [408, 429, 500, 502, 503, 504]

        for code in retryable_codes:
            assert should_retry_on_status(code), f"Status {code} should be retryable"

    def test_non_retryable_status_codes(self):
        """Test that non-retryable status codes return False."""
        non_retryable_codes = [200, 201, 400, 401, 403, 404, 405, 422]

        for code in non_retryable_codes:
            assert not should_retry_on_status(code), f"Status {code} should not be retryable"

    def test_success_codes_not_retryable(self):
        """Test that 2xx success codes are not retryable."""
        for code in range(200, 300):
            assert not should_retry_on_status(code)

    def test_client_error_codes_not_retryable(self):
        """Test that most 4xx client error codes are not retryable."""
        # Most 4xx should not be retried (except 408, 429)
        non_retryable_4xx = [400, 401, 403, 404, 405, 406, 410, 422, 451]

        for code in non_retryable_4xx:
            assert not should_retry_on_status(code)


class TestGetRetryAfterDelay:
    """Tests for get_retry_after_delay function."""

    def test_no_retry_after_header(self):
        """Test default delay when header is missing."""
        headers = {"Content-Type": "application/json"}

        delay = get_retry_after_delay(headers, default=30.0)

        assert delay == 30.0

    def test_retry_after_integer_seconds(self):
        """Test parsing integer seconds from header."""
        headers = {"Retry-After": "60"}

        delay = get_retry_after_delay(headers)

        assert delay == 60.0

    def test_retry_after_case_insensitive(self):
        """Test that header name is case-insensitive."""
        headers = {"retry-after": "45"}

        delay = get_retry_after_delay(headers)

        assert delay == 45.0

    def test_retry_after_mixed_case(self):
        """Test mixed case header name."""
        headers = {"ReTrY-AfTeR": "30"}

        delay = get_retry_after_delay(headers)

        assert delay == 30.0

    def test_retry_after_max_capped(self):
        """Test that delay is capped at 5 minutes (300s)."""
        headers = {"Retry-After": "1000"}  # 16+ minutes

        delay = get_retry_after_delay(headers)

        assert delay == 300.0  # Capped at 5 minutes

    def test_retry_after_invalid_format(self):
        """Test handling of invalid header format."""
        headers = {"Retry-After": "invalid"}

        delay = get_retry_after_delay(headers, default=42.0)

        assert delay == 42.0  # Should use default

    def test_retry_after_http_date_format(self):
        """Test handling of HTTP date format (not currently supported)."""
        # HTTP date format is not currently supported, should fall back to default
        headers = {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}

        delay = get_retry_after_delay(headers, default=60.0)

        assert delay == 60.0  # Should use default

    def test_retry_after_zero(self):
        """Test handling of zero delay."""
        headers = {"Retry-After": "0"}

        delay = get_retry_after_delay(headers)

        assert delay == 0.0

    def test_empty_headers(self):
        """Test with empty headers dict."""
        headers = {}

        delay = get_retry_after_delay(headers, default=10.0)

        assert delay == 10.0


class TestRetryAsyncEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_function_returns_none(self):
        """Test that function can return None."""
        async def returns_none():
            return None

        result = await retry_async(returns_none, max_retries=2)

        assert result is None

    @pytest.mark.asyncio
    async def test_function_returns_complex_object(self):
        """Test that function can return complex objects."""
        expected = {"key": "value", "list": [1, 2, 3]}

        async def returns_dict():
            return expected

        result = await retry_async(returns_dict, max_retries=2)

        assert result == expected

    @pytest.mark.asyncio
    async def test_immediate_success_with_zero_delay(self):
        """Test with zero initial delay."""
        async def succeeds():
            return "ok"

        result = await retry_async(succeeds, initial_delay=0.0, max_retries=2)

        assert result == "ok"

    @pytest.mark.asyncio
    async def test_exponential_base_one(self):
        """Test that exponential_base=1.0 results in constant delay."""
        call_times = []

        async def always_fails():
            call_times.append(time.time())
            raise ValueError("Test")

        with pytest.raises(ValueError):
            await retry_async(
                always_fails,
                max_retries=3,
                initial_delay=0.1,
                exponential_base=1.0,  # No growth
            )

        delays = [call_times[i + 1] - call_times[i] for i in range(len(call_times) - 1)]

        # All delays should be approximately the same
        for delay in delays:
            assert 0.05 < delay < 0.15  # ~0.1s with tolerance
