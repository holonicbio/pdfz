# Test Utilities Documentation

This directory contains reusable test utilities for the docling-hybrid-ocr test suite. These utilities simplify async testing, particularly for mocking aiohttp responses and backend interactions.

## Overview

The test utilities are organized into three main modules:

1. **`mock_helpers.py`** - Mock classes and factory functions for aiohttp components
2. **`async_fixtures.py`** - Pytest fixtures for common async testing patterns
3. **`__init__.py`** - Package exports for easy imports

## Quick Start

### Basic Usage

```python
from tests.utils import create_mock_aiohttp_response, create_mock_aiohttp_session

# Create a mock response
response = create_mock_aiohttp_response(
    status=200,
    json_data={"result": "success"}
)

# Create a mock session with the response
session = create_mock_aiohttp_session(default_response=response)

# Use in tests with patch
with patch.object(backend, "_get_session", return_value=session):
    result = await backend._post_chat(messages)
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_backend_call(mock_http_response, mock_http_session):
    """Test using pytest fixtures."""
    response = mock_http_response(
        status=200,
        json_data={"choices": [{"message": {"content": "Hello"}}]}
    )
    session = mock_http_session(default_response=response)

    # Use session in test...
```

## Mock Helpers (`mock_helpers.py`)

### AsyncContextManagerMock

The core building block for mocking async context managers. Properly implements `__aenter__` and `__aexit__`.

**Usage:**
```python
from tests.utils import AsyncContextManagerMock

# Create a basic async context manager
mock = AsyncContextManagerMock(status=200, data="test")

async with mock as m:
    assert m.status == 200
    assert m.data == "test"
```

### create_mock_aiohttp_response()

Factory function for creating mock aiohttp response objects.

**Signature:**
```python
def create_mock_aiohttp_response(
    status: int = 200,
    json_data: Optional[dict] = None,
    text_data: Optional[str] = None,
    headers: Optional[dict] = None,
) -> AsyncContextManagerMock
```

**Examples:**

```python
# JSON response
response = create_mock_aiohttp_response(
    status=200,
    json_data={"key": "value"}
)
data = await response.json()  # Returns {"key": "value"}

# Text response
response = create_mock_aiohttp_response(
    status=500,
    text_data="Server Error"
)
text = await response.text()  # Returns "Server Error"

# With headers
response = create_mock_aiohttp_response(
    status=200,
    headers={"Content-Type": "application/json"}
)
assert response.headers["Content-Type"] == "application/json"
```

### create_mock_aiohttp_session()

Factory function for creating mock aiohttp ClientSession objects.

**Signature:**
```python
def create_mock_aiohttp_session(
    default_response: Optional[AsyncContextManagerMock] = None,
    post_side_effect: Optional[Callable] = None,
) -> MagicMock
```

**Examples:**

```python
# Session with default successful response
session = create_mock_aiohttp_session()

# Session with custom response
response = create_mock_aiohttp_response(status=404)
session = create_mock_aiohttp_session(default_response=response)

# Session with side effect
def custom_post(*args, **kwargs):
    return create_mock_aiohttp_response(status=200)

session = create_mock_aiohttp_session(post_side_effect=custom_post)
```

### MockResponseBuilder

Fluent API for building complex mock responses.

**Example:**
```python
from tests.utils import MockResponseBuilder

response = (MockResponseBuilder()
    .with_status(200)
    .with_json({"data": "value"})
    .with_header("Content-Type", "application/json")
    .with_header("X-Request-ID", "123")
    .build())
```

### create_mock_error_response()

Helper for creating error responses (4xx, 5xx).

**Example:**
```python
# 500 error
error_response = create_mock_error_response(500, "Internal Server Error")

# 404 error
not_found = create_mock_error_response(404, "Not Found")
```

### create_mock_rate_limit_response()

Helper for creating rate limit (429) responses with Retry-After header.

**Example:**
```python
rate_limit = create_mock_rate_limit_response(
    retry_after=5.0,
    error_message="Too Many Requests"
)

# Access retry after
assert rate_limit.headers["Retry-After"] == "5.0"
```

## Async Fixtures (`async_fixtures.py`)

### Response Fixtures

#### `mock_http_response` (factory)
Creates mock HTTP responses with custom parameters.

```python
def test_something(mock_http_response):
    response = mock_http_response(status=200, json_data={"ok": True})
```

#### `mock_api_success_response`
Pre-configured successful API response.

```python
def test_success(mock_api_success_response):
    session = create_mock_aiohttp_session(mock_api_success_response)
```

#### `mock_api_error_response`
Pre-configured 500 error response.

#### `mock_api_rate_limit_response`
Pre-configured 429 rate limit response.

### Session Fixtures

#### `mock_http_session` (factory)
Creates mock aiohttp sessions.

```python
def test_backend(mock_http_session, mock_http_response):
    response = mock_http_response(status=200)
    session = mock_http_session(default_response=response)
```

### Testing Utilities

#### `async_context_manager_mock` (factory)
Creates basic async context managers.

```python
def test_context_manager(async_context_manager_mock):
    mock = async_context_manager_mock(value=42)
    async with mock as m:
        assert m.value == 42
```

#### `async_sleep_mock`
Mocks `asyncio.sleep` for faster tests.

```python
@pytest.mark.asyncio
async def test_timing(async_sleep_mock):
    await asyncio.sleep(10)  # Returns immediately
    assert async_sleep_mock.called
```

#### `call_counter` (factory)
Tracks function call counts for retry testing.

```python
def test_retries(call_counter):
    counter = call_counter()

    async def mock_func():
        counter.increment()
        if counter.value < 3:
            raise Exception("Retry")
        return "Success"

    result = await retry_logic(mock_func)
    assert counter.value == 3
```

#### `mock_response_sequence` (factory)
Creates sequences of responses for testing retries.

```python
def test_retry_sequence(mock_response_sequence, mock_http_response):
    responses = mock_response_sequence([
        mock_http_response(status=500),
        mock_http_response(status=500),
        mock_http_response(status=200, json_data={"ok": True}),
    ])

    session.post = MagicMock(side_effect=responses)
    # First two calls fail with 500, third succeeds
```

#### `timing_tracker`
Tracks timing for verifying delays and rate limits.

```python
@pytest.mark.asyncio
async def test_rate_limit_delay(timing_tracker):
    timing_tracker.mark()
    await handle_rate_limit(retry_after=0.1)
    timing_tracker.mark()

    delay = timing_tracker.get_delay()
    assert 0.09 <= delay <= 0.15  # ~100ms with tolerance
```

## Common Patterns

### Testing Backend Retry Logic

```python
@pytest.mark.asyncio
async def test_retry_on_500(retry_config):
    """Test that backend retries on 500 errors."""
    backend = OpenRouterNemotronBackend(retry_config)
    call_count = 0

    async def mock_post_inner(messages, context):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise BackendResponseError(
                "Server error",
                backend_name=backend.name,
                status_code=500,
            )
        return "Success after retry"

    with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
        result = await backend._post_chat(messages)
        assert result == "Success after retry"
        assert call_count == 3

    await backend.close()
```

### Testing Rate Limiting

```python
@pytest.mark.asyncio
async def test_rate_limit(backend_config):
    """Test rate limit handling."""
    backend = OpenRouterNemotronBackend(backend_config)

    # Create rate limit response
    rate_limit_response = create_mock_rate_limit_response(
        retry_after=5.0,
        error_message="Rate Limited"
    )

    session = create_mock_aiohttp_session(default_response=rate_limit_response)

    with patch.object(backend, "_get_session", return_value=session):
        with pytest.raises(RateLimitError) as exc_info:
            await backend._post_chat_inner(messages, {})

        assert exc_info.value.retry_after == 5.0
        assert exc_info.value.status_code == 429

    await backend.close()
```

### Testing Successful Requests

```python
@pytest.mark.asyncio
async def test_successful_request(backend_config, mock_http_response, mock_http_session):
    """Test successful API request."""
    backend = OpenRouterNemotronBackend(backend_config)

    # Create successful response
    response = mock_http_response(
        status=200,
        json_data={"choices": [{"message": {"content": "Success"}}]}
    )

    session = mock_http_session(default_response=response)

    with patch.object(backend, "_get_session", return_value=session):
        result = await backend._post_chat(messages)
        assert result == "Success"
        assert session.post.call_count == 1

    await backend.close()
```

### Testing Response Sequences

```python
@pytest.mark.asyncio
async def test_mixed_failures(backend_config, mock_response_sequence, mock_http_response):
    """Test handling of mixed error types."""
    backend = OpenRouterNemotronBackend(backend_config)
    call_count = 0

    async def mock_post_inner(messages, context):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RateLimitError("Rate limited", backend_name=backend.name, retry_after=0.01)
        elif call_count == 2:
            raise BackendResponseError("Server error", backend_name=backend.name, status_code=502)
        elif call_count == 3:
            raise BackendConnectionError("Connection failed", backend_name=backend.name)
        return "Final success"

    with patch.object(backend, "_post_chat_inner", side_effect=mock_post_inner):
        result = await backend._post_chat(messages)
        assert result == "Final success"
        assert call_count == 4

    await backend.close()
```

## Best Practices

### 1. Use Factory Fixtures for Flexibility

Factory fixtures (those that return a function) allow you to create multiple instances with different configurations:

```python
def test_multiple_responses(mock_http_response):
    success = mock_http_response(status=200, json_data={"ok": True})
    error = mock_http_response(status=500, text_data="Error")
    # Can create as many as needed
```

### 2. Use Helpers for Common Patterns

Instead of manually creating mock responses, use the helper functions:

```python
# Good
response = create_mock_rate_limit_response(retry_after=5.0)

# Avoid
response = create_mock_aiohttp_response(
    status=429,
    text_data="Rate Limited",
    headers={"Retry-After": "5.0"}
)
```

### 3. Mock at the Right Level

Mock at the highest level that makes sense for your test:

```python
# For unit tests - mock the inner method
with patch.object(backend, "_post_chat_inner", side_effect=mock_func):
    result = await backend._post_chat(messages)

# For integration tests - mock the session
with patch.object(backend, "_get_session", return_value=mock_session):
    result = await backend._post_chat(messages)
```

### 4. Use async_sleep_mock for Tests with Delays

Always mock `asyncio.sleep` in tests to keep them fast:

```python
@pytest.mark.asyncio
async def test_retry_delay(async_sleep_mock):
    # Test runs instantly instead of waiting for actual delays
    await retry_with_backoff()
    assert async_sleep_mock.call_count > 0
```

### 5. Clean Up Resources

Always close backends and sessions in tests:

```python
@pytest.mark.asyncio
async def test_something(backend_config):
    backend = OpenRouterNemotronBackend(backend_config)
    try:
        # Test code here
        pass
    finally:
        await backend.close()
```

Or use context managers:

```python
@pytest.mark.asyncio
async def test_something(backend_config):
    async with OpenRouterNemotronBackend(backend_config) as backend:
        # Test code here
        pass
```

## Troubleshooting

### Issue: "object AsyncMock can't be used in 'await' expression"

**Solution:** Make sure you're using `AsyncMock()` not `MagicMock()` for async functions.

```python
# Wrong
mock_func = MagicMock(return_value="result")

# Right
mock_func = AsyncMock(return_value="result")
```

### Issue: "TypeError: object MagicMock can't be used in 'async with' statement"

**Solution:** Use `AsyncContextManagerMock` or the helper functions:

```python
# Wrong
mock_response = MagicMock(status=200)

# Right
mock_response = AsyncContextManagerMock(status=200)
# Or
mock_response = create_mock_aiohttp_response(status=200)
```

### Issue: Mock not being called

**Solution:** Make sure you're patching at the right location and that the mock is returned correctly:

```python
# Check the patch target
with patch.object(backend, "_get_session", return_value=mock_session):
    # Not patch("docling_hybrid.backends.openrouter_nemotron._get_session")
```

### Issue: Tests failing with real API calls

**Solution:** Ensure all external calls are mocked:

```python
# Mock the session
with patch.object(backend, "_get_session", return_value=mock_session):
    # Now all HTTP calls use the mock
    result = await backend._post_chat(messages)
```

## Examples in the Codebase

See these test files for real-world usage examples:

- `tests/unit/backends/test_retry.py` - Retry logic and error handling
- `tests/unit/backends/test_openrouter.py` - Backend API testing
- `tests/unit/test_pipeline.py` - Pipeline orchestration

## Contributing

When adding new mock utilities:

1. Add the function/class to the appropriate module (`mock_helpers.py` or `async_fixtures.py`)
2. Export it from `__init__.py`
3. Add documentation with examples
4. Add usage examples in tests
5. Update this README

## Questions?

For questions or issues with test utilities, check:
- This README
- Inline docstrings in the utility modules
- Example usage in existing tests
- Sprint 3 planning documentation
