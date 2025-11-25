"""Mock helper utilities for async testing.

This module provides utilities for mocking aiohttp and other async components
in tests, particularly for handling async context managers and HTTP responses.
"""

from typing import Any, Callable, Optional
from unittest.mock import AsyncMock, MagicMock


class AsyncContextManagerMock:
    """Mock for async context managers (like aiohttp responses).

    This class properly implements __aenter__ and __aexit__ for use with
    async with statements. It's particularly useful for mocking aiohttp
    response objects which are used as async context managers.

    Example:
        >>> mock_response = AsyncContextManagerMock(status=200)
        >>> mock_response.json = AsyncMock(return_value={"key": "value"})
        >>> async with session.post(...) as resp:  # mock returns mock_response
        ...     data = await resp.json()
    """

    def __init__(self, **kwargs):
        """Initialize the mock with arbitrary attributes.

        Args:
            **kwargs: Attributes to set on the mock (e.g., status=200)
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def __aenter__(self):
        """Enter async context - return self."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - return None (don't suppress exceptions)."""
        return None


def create_mock_aiohttp_response(
    status: int = 200,
    json_data: Optional[dict] = None,
    text_data: Optional[str] = None,
    headers: Optional[dict] = None,
) -> AsyncContextManagerMock:
    """Create a mock aiohttp response object.

    Creates a properly configured mock that can be used as an async context
    manager, with json() and text() methods that return AsyncMocks.

    Args:
        status: HTTP status code (default: 200)
        json_data: Data to return from json() method
        text_data: Data to return from text() method
        headers: HTTP headers dict (default: {})

    Returns:
        AsyncContextManagerMock configured as an aiohttp response

    Example:
        >>> response = create_mock_aiohttp_response(
        ...     status=200,
        ...     json_data={"result": "success"}
        ... )
        >>> mock_session.post.return_value = response
        >>> async with mock_session.post(...) as resp:
        ...     data = await resp.json()  # Returns {"result": "success"}
    """
    mock_response = AsyncContextManagerMock(
        status=status,
        headers=headers or {},
    )

    # Add json() method
    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)

    # Add text() method
    if text_data is not None:
        mock_response.text = AsyncMock(return_value=text_data)

    return mock_response


def create_mock_aiohttp_session(
    default_response: Optional[AsyncContextManagerMock] = None,
    post_side_effect: Optional[Callable] = None,
) -> MagicMock:
    """Create a mock aiohttp ClientSession.

    Creates a session mock with properly configured post() method that
    returns async context managers.

    Args:
        default_response: Default response to return from post() calls
        post_side_effect: Optional side effect function for post() method

    Returns:
        MagicMock configured as an aiohttp ClientSession

    Example:
        >>> response = create_mock_aiohttp_response(status=200, json_data={"ok": True})
        >>> session = create_mock_aiohttp_session(default_response=response)
        >>> # Use in tests:
        >>> with patch.object(backend, "_get_session", return_value=session):
        ...     result = await backend._post_chat(messages)
    """
    session = MagicMock()
    session.closed = False
    session.close = AsyncMock()

    # Configure post method
    if post_side_effect:
        session.post = MagicMock(side_effect=post_side_effect)
    elif default_response:
        session.post = MagicMock(return_value=default_response)
    else:
        # Default to a successful empty response
        default_response = create_mock_aiohttp_response(
            status=200,
            json_data={"choices": [{"message": {"content": "mock response"}}]}
        )
        session.post = MagicMock(return_value=default_response)

    return session


class MockResponseBuilder:
    """Builder for creating mock aiohttp responses with fluent API.

    Provides a more readable way to construct complex mock responses,
    especially useful when you need to configure multiple aspects.

    Example:
        >>> response = (MockResponseBuilder()
        ...     .with_status(200)
        ...     .with_json({"data": "value"})
        ...     .with_header("Content-Type", "application/json")
        ...     .build())
    """

    def __init__(self):
        """Initialize builder with defaults."""
        self._status = 200
        self._json_data = None
        self._text_data = None
        self._headers = {}

    def with_status(self, status: int) -> "MockResponseBuilder":
        """Set HTTP status code."""
        self._status = status
        return self

    def with_json(self, data: dict) -> "MockResponseBuilder":
        """Set JSON response data."""
        self._json_data = data
        return self

    def with_text(self, text: str) -> "MockResponseBuilder":
        """Set text response data."""
        self._text_data = text
        return self

    def with_header(self, key: str, value: str) -> "MockResponseBuilder":
        """Add a response header."""
        self._headers[key] = value
        return self

    def with_headers(self, headers: dict) -> "MockResponseBuilder":
        """Set multiple response headers."""
        self._headers.update(headers)
        return self

    def build(self) -> AsyncContextManagerMock:
        """Build and return the mock response."""
        return create_mock_aiohttp_response(
            status=self._status,
            json_data=self._json_data,
            text_data=self._text_data,
            headers=self._headers,
        )


def create_mock_error_response(
    status: int,
    error_message: str,
    headers: Optional[dict] = None,
) -> AsyncContextManagerMock:
    """Create a mock error response.

    Helper for creating error responses (4xx, 5xx) with text content.

    Args:
        status: HTTP error status code (e.g., 400, 500)
        error_message: Error message text
        headers: Optional headers dict

    Returns:
        AsyncContextManagerMock configured as an error response

    Example:
        >>> error_response = create_mock_error_response(500, "Internal Server Error")
        >>> session = create_mock_aiohttp_session(default_response=error_response)
    """
    return create_mock_aiohttp_response(
        status=status,
        text_data=error_message,
        headers=headers or {},
    )


def create_mock_rate_limit_response(
    retry_after: float,
    error_message: str = "Rate Limited",
) -> AsyncContextManagerMock:
    """Create a mock rate limit (429) response.

    Args:
        retry_after: Retry-After header value in seconds
        error_message: Error message text

    Returns:
        AsyncContextManagerMock configured as a 429 response

    Example:
        >>> rate_limit = create_mock_rate_limit_response(retry_after=5.0)
    """
    return create_mock_aiohttp_response(
        status=429,
        text_data=error_message,
        headers={"Retry-After": str(retry_after)},
    )
