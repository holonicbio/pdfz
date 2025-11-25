"""Mock response factories for testing backend integrations.

This module provides factory functions that create mock API responses
for different scenarios (success, errors, rate limiting, etc.).
"""

from typing import Any, Dict, Optional

import aiohttp


def mock_openrouter_success(
    content: str = "# Test Heading\n\nThis is test content.",
    model: str = "nvidia/nemotron-nano-12b-v2-vl:free",
) -> Dict[str, Any]:
    """Create a successful OpenRouter API response.

    Args:
        content: The content to return in the response
        model: The model name to include in the response

    Returns:
        Mock response payload matching OpenRouter's format

    Example:
        >>> payload = mock_openrouter_success("# Page Title\\n\\nContent here.")
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            status=200, payload=payload)
    """
    return {
        "id": "gen-test-123456",
        "model": model,
        "object": "chat.completion",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


def mock_openrouter_list_content(
    content_parts: list[str],
    model: str = "nvidia/nemotron-nano-12b-v2-vl:free",
) -> Dict[str, Any]:
    """Create a successful OpenRouter response with content as a list.

    Some models return content as a list of objects instead of a single string.
    This factory creates such responses for testing.

    Args:
        content_parts: List of content strings
        model: The model name to include in the response

    Returns:
        Mock response payload with content as list

    Example:
        >>> payload = mock_openrouter_list_content(["Part 1", "Part 2"])
    """
    return {
        "id": "gen-test-123456",
        "model": model,
        "object": "chat.completion",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": part} for part in content_parts
                    ],
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


def mock_openrouter_rate_limit(
    retry_after: int = 60, message: str = "Rate limit exceeded"
) -> tuple[int, Dict[str, Any], Dict[str, str]]:
    """Create a rate limit error response (429).

    Args:
        retry_after: Seconds to wait before retry
        message: Error message

    Returns:
        Tuple of (status_code, payload, headers)

    Example:
        >>> status, payload, headers = mock_openrouter_rate_limit(30)
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            status=status, payload=payload, headers=headers)
    """
    return (
        429,
        {
            "error": {
                "message": message,
                "type": "rate_limit_error",
                "code": "rate_limit_exceeded",
            }
        },
        {"Retry-After": str(retry_after)},
    )


def mock_openrouter_error(
    status: int = 500,
    error_type: str = "server_error",
    message: str = "Internal server error",
) -> tuple[int, Dict[str, Any]]:
    """Create an error response (4xx or 5xx).

    Args:
        status: HTTP status code
        error_type: Error type identifier
        message: Error message

    Returns:
        Tuple of (status_code, payload)

    Example:
        >>> status, payload = mock_openrouter_error(503, "service_unavailable")
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            status=status, payload=payload)
    """
    return (
        status,
        {
            "error": {
                "message": message,
                "type": error_type,
                "code": error_type,
            }
        },
    )


def mock_openrouter_timeout() -> Exception:
    """Create a timeout exception.

    Returns:
        aiohttp timeout exception

    Example:
        >>> exception = mock_openrouter_timeout()
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            exception=exception)
    """
    return aiohttp.ServerTimeoutError("Request timeout")


def mock_openrouter_connection_error() -> Exception:
    """Create a connection error exception.

    Returns:
        aiohttp connection error

    Example:
        >>> exception = mock_openrouter_connection_error()
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            exception=exception)
    """
    return aiohttp.ClientConnectionError("Connection failed")


def mock_openrouter_invalid_json() -> tuple[int, str]:
    """Create an invalid JSON response.

    Returns:
        Tuple of (status_code, invalid_body)

    Example:
        >>> status, body = mock_openrouter_invalid_json()
        >>> # Note: aioresponses expects payload to be dict,
        >>> # so this is used differently in actual tests
    """
    return (200, "This is not valid JSON{{{")


def mock_openrouter_empty_content() -> Dict[str, Any]:
    """Create a response with empty content.

    This simulates a successful response but with no actual content,
    which should be handled as an error.

    Returns:
        Mock response with empty content

    Example:
        >>> payload = mock_openrouter_empty_content()
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            status=200, payload=payload)
    """
    return {
        "id": "gen-test-123456",
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "object": "chat.completion",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 0,
            "total_tokens": 100,
        },
    }


def mock_openrouter_missing_choices() -> Dict[str, Any]:
    """Create a malformed response missing 'choices' field.

    Returns:
        Mock response with missing required fields

    Example:
        >>> payload = mock_openrouter_missing_choices()
    """
    return {
        "id": "gen-test-123456",
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "object": "chat.completion",
        "created": 1234567890,
        # Missing 'choices' field
    }


def mock_openrouter_auth_error() -> tuple[int, Dict[str, Any]]:
    """Create an authentication error response (401).

    Returns:
        Tuple of (status_code, payload)

    Example:
        >>> status, payload = mock_openrouter_auth_error()
        >>> with aioresponses() as m:
        ...     m.post("https://openrouter.ai/api/v1/chat/completions",
        ...            status=status, payload=payload)
    """
    return (
        401,
        {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error",
                "code": "invalid_api_key",
            }
        },
    )


# Convenience function for creating custom responses
def mock_openrouter_custom(
    content: Optional[str] = None,
    status: int = 200,
    error_message: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Create a custom OpenRouter response.

    This is a flexible factory for creating custom responses.

    Args:
        content: Response content (if success)
        status: HTTP status code
        error_message: Error message (if error)
        headers: Response headers

    Returns:
        Mock response configuration

    Example:
        >>> payload = mock_openrouter_custom(
        ...     content="Custom content",
        ...     status=200
        ... )
    """
    if status >= 400:
        # Error response
        return {
            "error": {
                "message": error_message or f"Error {status}",
                "type": "error",
                "code": f"error_{status}",
            }
        }
    else:
        # Success response
        return mock_openrouter_success(content or "# Default content")
