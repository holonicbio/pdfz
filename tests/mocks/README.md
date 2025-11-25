# HTTP Mocking Infrastructure

This directory contains HTTP mocking utilities for testing backend integrations without making real API calls.

## Overview

The mocking infrastructure uses `aioresponses` to mock aiohttp HTTP calls, allowing us to test:
- Successful API responses
- Various error conditions (4xx, 5xx)
- Network errors (timeouts, connection failures)
- Rate limiting scenarios
- Malformed responses

## Modules

### `http.py`

Provides utilities for setting up HTTP mocks:

- **`mock_aiohttp_response()`**: Create response configurations for aioresponses
- **`setup_mock_http_session()`**: Create a mock aiohttp ClientSession
- **`MockHTTPContext`**: Context manager for setting up multiple mock endpoints

### `responses.py`

Factory functions for creating mock API responses:

#### Success Responses
- **`mock_openrouter_success(content)`**: Standard successful response
- **`mock_openrouter_list_content(parts)`**: Response with content as list

#### Error Responses
- **`mock_openrouter_rate_limit(retry_after)`**: 429 rate limit error
- **`mock_openrouter_error(status, type, message)`**: Generic error response
- **`mock_openrouter_auth_error()`**: 401 authentication error

#### Network Errors
- **`mock_openrouter_timeout()`**: Timeout exception
- **`mock_openrouter_connection_error()`**: Connection failure exception

#### Edge Cases
- **`mock_openrouter_empty_content()`**: Response with empty content
- **`mock_openrouter_missing_choices()`**: Malformed response

## Usage Examples

### Basic Success Test

```python
from aioresponses import aioresponses
from tests.mocks import mock_openrouter_success

@pytest.mark.asyncio
async def test_page_to_markdown(backend, image_bytes):
    with aioresponses() as mock_http:
        mock_http.post(
            "https://openrouter.ai/api/v1/chat/completions",
            status=200,
            payload=mock_openrouter_success("# Page Title")
        )

        async with backend:
            result = await backend.page_to_markdown(image_bytes, 1, "doc-123")

        assert result == "# Page Title"
```

### Error Handling Test

```python
from tests.mocks import mock_openrouter_rate_limit

@pytest.mark.asyncio
async def test_rate_limit_handling(backend, image_bytes):
    status, payload, headers = mock_openrouter_rate_limit(retry_after=30)

    with aioresponses() as mock_http:
        mock_http.post(
            "https://openrouter.ai/api/v1/chat/completions",
            status=status,
            payload=payload,
            headers=headers
        )

        async with backend:
            with pytest.raises(BackendError) as exc_info:
                await backend.page_to_markdown(image_bytes, 1, "doc-123")

            assert "rate limit" in str(exc_info.value).lower()
```

### Using MockHTTPContext

```python
from tests.mocks.http import MockHTTPContext
from tests.mocks import mock_openrouter_success

@pytest.mark.asyncio
async def test_multiple_requests():
    with MockHTTPContext() as mock_http:
        # Setup multiple mock endpoints
        mock_http.add_post(
            "https://api.test/endpoint1",
            payload=mock_openrouter_success("Response 1")
        )
        mock_http.add_post(
            "https://api.test/endpoint2",
            payload=mock_openrouter_success("Response 2")
        )

        # Run test code
        # ...
```

## Testing Coverage

The integration tests in `tests/integration/test_backend_http.py` cover:

### ✅ Success Scenarios
- Standard string content response
- List-based content response
- Multiple sequential requests
- Custom headers

### ✅ Error Scenarios
- Rate limiting (429)
- Server errors (500)
- Authentication errors (401)
- Timeout errors
- Connection errors

### ✅ Edge Cases
- Empty content responses
- Malformed responses (missing fields)
- Invalid JSON responses

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_backend_http.py -v

# Run with coverage
pytest tests/integration/ --cov=src/docling_hybrid --cov-report=html
```

## Adding New Mock Responses

To add a new mock response factory:

1. Add the factory function to `responses.py`
2. Export it in `__init__.py`
3. Add tests using the new factory
4. Update this README

Example:

```python
# In responses.py
def mock_openrouter_custom_error() -> tuple[int, Dict[str, Any]]:
    """Create a custom error response."""
    return (
        503,
        {
            "error": {
                "message": "Service temporarily unavailable",
                "type": "service_error",
                "code": "service_unavailable",
            }
        },
    )

# In __init__.py
from .responses import mock_openrouter_custom_error

__all__ = [
    # ... existing exports
    "mock_openrouter_custom_error",
]
```

## Dependencies

- `aioresponses>=0.7.0` - For mocking aiohttp requests
- `pytest-asyncio>=0.21.0` - For async test support
- `aiohttp>=3.9.0` - HTTP client library (mocked in tests)

## Best Practices

1. **Use appropriate factories**: Choose the right factory for your test scenario
2. **Test error paths**: Don't just test success cases
3. **Verify error messages**: Ensure errors are informative
4. **Clean up resources**: Use context managers for backends
5. **Isolate tests**: Each test should be independent

## Related Documentation

- [tests/integration/test_backend_http.py](../integration/test_backend_http.py) - Integration test suite
- [docs/TESTING.md](../../docs/TESTING.md) - Overall testing strategy
- [tests/conftest.py](../conftest.py) - Shared test fixtures
