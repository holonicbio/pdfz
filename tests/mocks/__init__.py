"""Mock utilities for testing.

This module provides HTTP mocking infrastructure and response factories
for testing backend integrations without making real API calls.
"""

from .http import (
    mock_aiohttp_response,
    setup_mock_http_session,
)
from .responses import (
    mock_openrouter_success,
    mock_openrouter_rate_limit,
    mock_openrouter_error,
    mock_openrouter_timeout,
    mock_openrouter_invalid_json,
    mock_openrouter_empty_content,
)

__all__ = [
    # HTTP utilities
    "mock_aiohttp_response",
    "setup_mock_http_session",
    # Response factories
    "mock_openrouter_success",
    "mock_openrouter_rate_limit",
    "mock_openrouter_error",
    "mock_openrouter_timeout",
    "mock_openrouter_invalid_json",
    "mock_openrouter_empty_content",
]
