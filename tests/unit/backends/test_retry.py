"""Unit tests for backend retry logic."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from docling_hybrid.backends.openrouter_nemotron import (
    OpenRouterNemotronBackend,
    RateLimitError,
)
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendResponseError,
    BackendTimeoutError,
)
from docling_hybrid.common.models import OcrBackendConfig
from tests.utils import (
    create_mock_aiohttp_response,
    create_mock_aiohttp_session,
    create_mock_error_response,
    create_mock_rate_limit_response,
)


@pytest.fixture
def retry_config():
    """Backend config with fast retry settings for testing."""
    return OcrBackendConfig(
        name="nemotron-openrouter",
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key="test-key",
        max_retries=3,
        retry_initial_delay=0.1,  # Minimum allowed by model validation
        retry_exponential_base=2.0,
        retry_max_delay=1.0,
    )


@pytest.mark.asyncio
class TestBackendRetry:
    """Tests for backend retry functionality."""

    async def test_successful_request_no_retry(self, retry_config, sample_image_bytes):
        """Should not retry when request succeeds immediately."""
        backend = OpenRouterNemotronBackend(retry_config)

        # Create mock response using helper
        mock_response = create_mock_aiohttp_response(
            status=200,
            json_data={"choices": [{"message": {"content": "Success"}}]}
        )

        # Create mock session with the response
        mock_session = create_mock_aiohttp_session(default_response=mock_response)

        with patch.object(backend, "_get_session", return_value=mock_session):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success"
            # Should only be called once (no retries)
            assert mock_session.post.call_count == 1

        await backend.close()

    async def test_retry_on_500_error(self, retry_config):
        """Should retry on 500 server errors."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # Fail twice with 500
                raise BackendResponseError(
                    "API server error 500",
                    backend_name=backend.name,
                    status_code=500,
                )
            # Succeed on third try
            return "Success after retry"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success after retry"
            assert call_count == 3

        await backend.close()

    async def test_retry_on_rate_limit(self, retry_config):
        """Should retry on 429 rate limit errors."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # Fail once with rate limit
                raise RateLimitError(
                    "API rate limit exceeded",
                    backend_name=backend.name,
                    retry_after=0.01,  # Fast retry
                    status_code=429,
                )
            # Succeed on second try
            return "Success after rate limit"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success after rate limit"
            assert call_count == 2

        await backend.close()

    async def test_no_retry_on_400_error(self, retry_config):
        """Should NOT retry on 400 client errors."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            # Create non-retryable error
            error = BackendResponseError(
                "API client error 400",
                backend_name=backend.name,
                status_code=400,
            )
            error._retryable = False
            raise error

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]

            with pytest.raises(BackendResponseError) as exc_info:
                await backend._post_chat(messages)

            assert "client error 400" in str(exc_info.value)
            # Should only be called once (no retries)
            assert call_count == 1

        await backend.close()

    async def test_retry_on_connection_error(self, retry_config):
        """Should retry on connection errors."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise BackendConnectionError(
                    "Cannot connect",
                    backend_name=backend.name,
                )
            return "Success after reconnect"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success after reconnect"
            assert call_count == 2

        await backend.close()

    async def test_retry_on_timeout(self, retry_config):
        """Should retry on timeout errors."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise BackendTimeoutError(
                    "Request timed out",
                    backend_name=backend.name,
                )
            return "Success after timeout"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success after timeout"
            assert call_count == 2

        await backend.close()

    async def test_exhausted_retries(self, retry_config):
        """Should raise error after all retries exhausted."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            raise BackendResponseError(
                "API server error 503",
                backend_name=backend.name,
                status_code=503,
            )

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]

            with pytest.raises(BackendResponseError) as exc_info:
                await backend._post_chat(messages)

            assert "503" in str(exc_info.value)
            # Should be called initial + max_retries times
            assert call_count == retry_config.max_retries + 1

        await backend.close()

    async def test_rate_limit_respects_retry_after(self, retry_config):
        """Should respect Retry-After header from rate limit response."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_times = []

        async def mock_post_inner(messages, context):
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 2:
                raise RateLimitError(
                    "Rate limited",
                    backend_name=backend.name,
                    retry_after=0.1,  # 100ms
                    status_code=429,
                )
            return "Success"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success"
            assert len(call_times) == 2

            # Check delay was roughly 100ms
            delay = call_times[1] - call_times[0]
            assert 0.08 <= delay <= 0.2  # Allow tolerance

        await backend.close()

    async def test_exponential_backoff_on_retries(self, retry_config):
        """Should use exponential backoff for retries."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_times = []

        async def mock_post_inner(messages, context):
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise BackendResponseError(
                    "Server error",
                    backend_name=backend.name,
                    status_code=500,
                )
            return "Success"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Success"
            assert len(call_times) == 3

            # Check delays are roughly exponential
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]

            # First delay ~0.01s, second delay ~0.02s (0.01 * 2)
            assert delay1 >= 0.008  # ~0.01s with tolerance
            assert delay2 >= 0.015  # ~0.02s with tolerance
            assert delay2 > delay1  # Should be increasing

        await backend.close()

    async def test_mixed_errors_with_retries(self, retry_config):
        """Should handle mixed error types with appropriate retry logic."""
        backend = OpenRouterNemotronBackend(retry_config)
        call_count = 0

        async def mock_post_inner(messages, context):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(
                    "Rate limited",
                    backend_name=backend.name,
                    retry_after=0.01,
                    status_code=429,
                )
            elif call_count == 2:
                raise BackendResponseError(
                    "Server error 502",
                    backend_name=backend.name,
                    status_code=502,
                )
            elif call_count == 3:
                raise BackendConnectionError(
                    "Connection failed",
                    backend_name=backend.name,
                )
            return "Final success"

        with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
            messages = [{"role": "user", "content": "test"}]
            result = await backend._post_chat(messages)

            assert result == "Final success"
            assert call_count == 4

        await backend.close()


@pytest.mark.asyncio
class TestRateLimitErrorCreation:
    """Tests for RateLimitError exception."""

    async def test_rate_limit_error_with_retry_after(self, retry_config):
        """Should create RateLimitError with Retry-After header."""
        backend = OpenRouterNemotronBackend(retry_config)

        # Create mock rate limit response using helper
        mock_response = create_mock_rate_limit_response(
            retry_after=5.0,
            error_message="Rate limited"
        )

        mock_session = create_mock_aiohttp_session(default_response=mock_response)

        with patch.object(backend, "_get_session", return_value=mock_session):
            messages = [{"role": "user", "content": "test"}]

            with pytest.raises(RateLimitError) as exc_info:
                # Call inner method to trigger rate limit error
                await backend._post_chat_inner(messages, {})

            error = exc_info.value
            assert error.retry_after == 5.0
            assert error.status_code == 429

        await backend.close()

    async def test_rate_limit_error_without_retry_after(self, retry_config):
        """Should create RateLimitError without Retry-After header."""
        backend = OpenRouterNemotronBackend(retry_config)

        # Create mock 429 response without Retry-After header
        mock_response = create_mock_aiohttp_response(
            status=429,
            text_data="Rate limited",
            headers={}
        )

        mock_session = create_mock_aiohttp_session(default_response=mock_response)

        with patch.object(backend, "_get_session", return_value=mock_session):
            messages = [{"role": "user", "content": "test"}]

            with pytest.raises(RateLimitError) as exc_info:
                await backend._post_chat_inner(messages, {})

            error = exc_info.value
            assert error.retry_after is None
            assert error.status_code == 429

        await backend.close()

    async def test_rate_limit_error_invalid_retry_after(self, retry_config):
        """Should handle invalid Retry-After header gracefully."""
        backend = OpenRouterNemotronBackend(retry_config)

        # Create mock 429 response with invalid Retry-After header
        mock_response = create_mock_aiohttp_response(
            status=429,
            text_data="Rate limited",
            headers={"Retry-After": "invalid"}
        )

        mock_session = create_mock_aiohttp_session(default_response=mock_response)

        with patch.object(backend, "_get_session", return_value=mock_session):
            messages = [{"role": "user", "content": "test"}]

            with pytest.raises(RateLimitError) as exc_info:
                await backend._post_chat_inner(messages, {})

            error = exc_info.value
            # Should be None since parsing failed
            assert error.retry_after is None
            assert error.status_code == 429

        await backend.close()
