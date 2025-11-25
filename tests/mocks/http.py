"""HTTP mocking utilities using aioresponses.

This module provides utilities for mocking aiohttp HTTP calls in tests,
particularly for testing backend integrations without making real API calls.
"""

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import aiohttp
from aioresponses import aioresponses


def mock_aiohttp_response(
    status: int = 200,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    exception: Optional[Exception] = None,
) -> Dict[str, Any]:
    """Create a mock aiohttp response configuration.

    Args:
        status: HTTP status code (default: 200)
        payload: JSON response body (default: None)
        headers: HTTP response headers (default: None)
        exception: Exception to raise instead of returning response

    Returns:
        Dictionary with response configuration

    Example:
        >>> response = mock_aiohttp_response(200, {"result": "ok"})
        >>> # Use with aioresponses
        >>> with aioresponses() as m:
        ...     m.post("http://api.test", **response)
    """
    config = {}

    if exception:
        config["exception"] = exception
    else:
        config["status"] = status
        if payload is not None:
            config["payload"] = payload
        if headers:
            config["headers"] = headers

    return config


def setup_mock_http_session(
    post_response: Optional[Dict[str, Any]] = None,
    post_exception: Optional[Exception] = None,
) -> MagicMock:
    """Create a mock aiohttp ClientSession for testing.

    This creates a mock session that can be used in place of a real
    aiohttp.ClientSession in tests. It provides basic mocking for
    the post() method.

    Args:
        post_response: Mock response data for POST requests
        post_exception: Exception to raise on POST

    Returns:
        Mock ClientSession object

    Example:
        >>> session = setup_mock_http_session(
        ...     post_response={"choices": [{"message": {"content": "test"}}]}
        ... )
        >>> backend._session = session
        >>> # Test backend with mocked session
    """
    session = MagicMock(spec=aiohttp.ClientSession)

    # Create mock response context manager
    mock_response = MagicMock()
    mock_response.__aenter__ = AsyncMock()
    mock_response.__aexit__ = AsyncMock()

    if post_exception:
        # Raise exception on post
        mock_response.__aenter__.side_effect = post_exception
    else:
        # Return successful response
        response_obj = MagicMock()
        response_obj.status = 200
        response_obj.json = AsyncMock(return_value=post_response or {})
        response_obj.text = AsyncMock(return_value=json.dumps(post_response or {}))
        mock_response.__aenter__.return_value = response_obj

    session.post = MagicMock(return_value=mock_response)
    session.close = AsyncMock()
    session.closed = False

    return session


class MockHTTPContext:
    """Context manager for HTTP mocking with aioresponses.

    This provides a convenient way to set up multiple mock responses
    for different endpoints in tests.

    Example:
        >>> with MockHTTPContext() as mock_http:
        ...     mock_http.add_post(
        ...         "https://api.test/v1/chat",
        ...         status=200,
        ...         payload={"result": "ok"}
        ...     )
        ...     # Run test code that makes HTTP calls
    """

    def __init__(self):
        """Initialize the mock HTTP context."""
        self._aioresponses = aioresponses()

    def __enter__(self):
        """Enter the context."""
        self._aioresponses.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        return self._aioresponses.__exit__(exc_type, exc_val, exc_tb)

    def add_post(
        self,
        url: str,
        status: int = 200,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        exception: Optional[Exception] = None,
        repeat: bool = False,
    ):
        """Add a mock POST endpoint.

        Args:
            url: URL pattern to match
            status: HTTP status code
            payload: JSON response body
            headers: Response headers
            exception: Exception to raise
            repeat: Allow multiple calls to same URL
        """
        config = mock_aiohttp_response(status, payload, headers, exception)
        self._aioresponses.post(url, repeat=repeat, **config)

    def add_get(
        self,
        url: str,
        status: int = 200,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        exception: Optional[Exception] = None,
        repeat: bool = False,
    ):
        """Add a mock GET endpoint.

        Args:
            url: URL pattern to match
            status: HTTP status code
            payload: JSON response body
            headers: Response headers
            exception: Exception to raise
            repeat: Allow multiple calls to same URL
        """
        config = mock_aiohttp_response(status, payload, headers, exception)
        self._aioresponses.get(url, repeat=repeat, **config)
