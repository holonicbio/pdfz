"""Async test fixtures for pytest.

This module provides reusable pytest fixtures for async testing,
particularly for testing aiohttp-based backends and async workflows.
"""

import asyncio
from typing import Callable
from unittest.mock import AsyncMock

import pytest

from .mock_helpers import (
    AsyncContextManagerMock,
    create_mock_aiohttp_response,
    create_mock_aiohttp_session,
)


@pytest.fixture
def async_context_manager_mock():
    """Factory fixture for creating async context manager mocks.

    Returns:
        Function that creates AsyncContextManagerMock instances

    Example:
        >>> def test_something(async_context_manager_mock):
        ...     mock = async_context_manager_mock(status=200, data={"ok": True})
        ...     async with mock as resp:
        ...         assert resp.status == 200
    """
    def _create(**kwargs):
        return AsyncContextManagerMock(**kwargs)

    return _create


@pytest.fixture
def mock_http_response():
    """Factory fixture for creating mock HTTP responses.

    Returns:
        Function that creates mock aiohttp response objects

    Example:
        >>> def test_api_call(mock_http_response):
        ...     response = mock_http_response(
        ...         status=200,
        ...         json_data={"result": "success"}
        ...     )
        ...     mock_session.post.return_value = response
    """
    def _create(
        status=200,
        json_data=None,
        text_data=None,
        headers=None,
    ):
        return create_mock_aiohttp_response(
            status=status,
            json_data=json_data,
            text_data=text_data,
            headers=headers,
        )

    return _create


@pytest.fixture
def mock_http_session():
    """Factory fixture for creating mock aiohttp sessions.

    Returns:
        Function that creates mock ClientSession objects

    Example:
        >>> def test_backend(mock_http_session, mock_http_response):
        ...     response = mock_http_response(status=200)
        ...     session = mock_http_session(default_response=response)
        ...     backend._session = session
    """
    def _create(default_response=None, post_side_effect=None):
        return create_mock_aiohttp_session(
            default_response=default_response,
            post_side_effect=post_side_effect,
        )

    return _create


@pytest.fixture
def mock_api_success_response():
    """Fixture for a standard successful API response.

    Returns:
        Mock response with status 200 and standard content structure

    Example:
        >>> def test_success(mock_api_success_response):
        ...     session = create_mock_aiohttp_session(mock_api_success_response)
        ...     async with session.post(...) as resp:
        ...         data = await resp.json()
        ...         assert data["choices"][0]["message"]["content"]
    """
    return create_mock_aiohttp_response(
        status=200,
        json_data={
            "choices": [
                {
                    "message": {
                        "content": "# Test Document\n\nTest content."
                    }
                }
            ]
        },
    )


@pytest.fixture
def mock_api_error_response():
    """Fixture for a standard API error response (500).

    Returns:
        Mock response with status 500 and error text

    Example:
        >>> def test_error_handling(mock_api_error_response):
        ...     session = create_mock_aiohttp_session(mock_api_error_response)
        ...     # Test error handling logic
    """
    return create_mock_aiohttp_response(
        status=500,
        text_data="Internal Server Error",
    )


@pytest.fixture
def mock_api_rate_limit_response():
    """Fixture for an API rate limit response (429).

    Returns:
        Mock response with status 429 and Retry-After header

    Example:
        >>> def test_rate_limiting(mock_api_rate_limit_response):
        ...     session = create_mock_aiohttp_session(mock_api_rate_limit_response)
        ...     # Test rate limit handling
    """
    return create_mock_aiohttp_response(
        status=429,
        text_data="Rate Limited",
        headers={"Retry-After": "5.0"},
    )


@pytest.fixture
def async_sleep_mock(monkeypatch):
    """Mock asyncio.sleep to make tests faster.

    Returns:
        AsyncMock that replaces asyncio.sleep

    Example:
        >>> @pytest.mark.asyncio
        ... async def test_with_sleep(async_sleep_mock):
        ...     await asyncio.sleep(10)  # Returns immediately
        ...     assert async_sleep_mock.called
    """
    mock = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", mock)
    return mock


@pytest.fixture
def call_counter():
    """Factory fixture for creating call counters.

    Useful for tracking how many times a function or method is called,
    particularly in retry logic tests.

    Returns:
        Function that creates a counter with increment and value methods

    Example:
        >>> def test_retries(call_counter):
        ...     counter = call_counter()
        ...     async def mock_func():
        ...         counter.increment()
        ...         if counter.value < 3:
        ...             raise Exception("Retry")
        ...         return "Success"
        ...     result = await retry_logic(mock_func)
        ...     assert counter.value == 3
    """
    def _create():
        class Counter:
            def __init__(self):
                self.value = 0

            def increment(self):
                self.value += 1
                return self.value

            def reset(self):
                self.value = 0

        return Counter()

    return _create


@pytest.fixture
def mock_response_sequence():
    """Factory fixture for creating sequences of mock responses.

    Useful for testing retry logic where different responses are
    returned on successive calls.

    Returns:
        Function that creates a callable returning responses in sequence

    Example:
        >>> def test_retry_sequence(mock_response_sequence, mock_http_response):
        ...     responses = mock_response_sequence([
        ...         mock_http_response(status=500),
        ...         mock_http_response(status=500),
        ...         mock_http_response(status=200, json_data={"ok": True}),
        ...     ])
        ...     session.post = MagicMock(side_effect=responses)
        ...     # First two calls return 500, third returns 200
    """
    def _create(responses: list):
        class ResponseSequence:
            def __init__(self, response_list):
                self.responses = response_list
                self.index = 0

            def __call__(self, *args, **kwargs):
                if self.index >= len(self.responses):
                    raise RuntimeError("No more responses in sequence")
                response = self.responses[self.index]
                self.index += 1
                return response

        return ResponseSequence(responses)

    return _create


@pytest.fixture
def timing_tracker():
    """Fixture for tracking timing in async tests.

    Useful for verifying retry delays and rate limit handling.

    Returns:
        Object with mark() and get_delay() methods

    Example:
        >>> @pytest.mark.asyncio
        ... async def test_timing(timing_tracker):
        ...     timing_tracker.mark()
        ...     await asyncio.sleep(0.1)
        ...     delay = timing_tracker.get_delay()
        ...     assert delay >= 0.09
    """
    class TimingTracker:
        def __init__(self):
            self.marks = []

        def mark(self):
            """Record current time."""
            self.marks.append(asyncio.get_event_loop().time())

        def get_delay(self, start_index=0, end_index=None):
            """Get delay between two marks."""
            if len(self.marks) < 2:
                raise ValueError("Need at least 2 marks to calculate delay")
            end_index = end_index or len(self.marks) - 1
            return self.marks[end_index] - self.marks[start_index]

        def reset(self):
            """Clear all marks."""
            self.marks = []

    return TimingTracker()
