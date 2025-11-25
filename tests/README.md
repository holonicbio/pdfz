# Tests

Comprehensive test suite for Docling Hybrid OCR.

## Overview

**Test Coverage:** Unit, integration, and benchmark tests
**Framework:** pytest with pytest-asyncio

## Directory Structure

```
tests/
├── __init__.py                  # Test package
├── conftest.py                  # Shared fixtures
├── unit/                        # Fast, isolated unit tests
│   ├── __init__.py
│   ├── test_common.py           # Common utilities
│   ├── test_backends.py         # Backend tests
│   ├── test_renderer.py         # Renderer tests
│   ├── test_pipeline.py         # Pipeline tests
│   ├── test_cli.py              # CLI tests
│   ├── test_retry.py            # Retry logic tests
│   ├── backends/                # Backend-specific tests
│   │   ├── test_fallback.py
│   │   ├── test_retry.py
│   │   └── test_deepseek_vllm.py
│   ├── orchestrator/            # Orchestrator tests
│   │   ├── test_callbacks.py
│   │   └── test_progress.py
│   ├── cli/                     # CLI tests
│   │   └── test_batch.py
│   └── common/                  # Common tests
│       └── test_retry.py
├── integration/                 # Integration tests (may use mocks)
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_openrouter_integration.py
│   ├── test_openrouter_fallback.py
│   ├── test_backend_http.py
│   ├── test_pipeline_e2e.py
│   └── test_pipeline_integration.py
├── benchmarks/                  # Performance benchmarks
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_performance.py
│   └── test_memory.py
├── mocks/                       # Mock helpers
│   ├── __init__.py
│   ├── http.py                  # HTTP mocking
│   └── responses.py             # Mock responses
├── utils/                       # Test utilities
│   ├── __init__.py
│   ├── async_fixtures.py
│   └── mock_helpers.py
└── fixtures/                    # Test data
    ├── sample_pdfs/             # Sample PDF files
    └── expected_outputs/        # Expected results
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Unit Tests Only
```bash
pytest tests/unit -v
```

### Integration Tests
```bash
pytest tests/integration -v
```

### Benchmarks
```bash
pytest tests/benchmarks -v
```

### Specific Test File
```bash
pytest tests/unit/test_backends.py -v
```

### Specific Test
```bash
pytest tests/unit/test_backends.py::test_openrouter_backend -v
```

### With Coverage
```bash
pytest tests/ --cov=src/docling_hybrid --cov-report=html
open htmlcov/index.html
```

## Test Categories

### Unit Tests (`tests/unit/`)
Fast, isolated tests with no external dependencies.

**Characteristics:**
- No network calls
- No file I/O (or minimal with temp files)
- Uses mocks for external dependencies
- Fast execution (< 1s per test)

**Coverage:**
- Configuration loading
- Data model validation
- ID generation
- Error handling
- Backend interface
- Renderer functions
- Pipeline logic

### Integration Tests (`tests/integration/`)
Tests that verify components work together.

**Characteristics:**
- May use HTTP mocking
- May use real file I/O
- Tests component interactions
- Slower than unit tests (1-10s per test)

**Coverage:**
- Backend HTTP communication (mocked)
- Pipeline end-to-end flow
- Fallback chains
- Progress callbacks

### Benchmark Tests (`tests/benchmarks/`)
Performance and resource usage tests.

**Characteristics:**
- Measure execution time
- Track memory usage
- May use real PDFs
- Slowest tests (10s-60s)

**Coverage:**
- Rendering performance
- OCR throughput
- Memory consumption
- Concurrent processing

## Key Fixtures

### From `conftest.py`

**`tmp_path`** (pytest built-in)
Temporary directory for test files.

**`sample_config`**
Sample configuration object.

**`mock_backend`**
Mocked OCR backend for testing.

**`sample_pdf_path`**
Path to a sample PDF file.

## Test Patterns

### Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Mocking HTTP Requests

```python
from tests.mocks.http import MockHttpClient

@pytest.mark.asyncio
async def test_backend_with_mock_http():
    mock_client = MockHttpClient()
    mock_client.add_response(200, {"result": "success"})

    result = await backend.call_api(client=mock_client)
    assert result == "success"
```

### Testing Error Handling

```python
from docling_hybrid.common.errors import BackendError

@pytest.mark.asyncio
async def test_backend_error_handling():
    with pytest.raises(BackendError) as exc_info:
        await backend.page_to_markdown(b"invalid", 1, "doc-123")

    assert "error message" in str(exc_info.value)
```

### Using Temporary Files

```python
def test_with_temp_file(tmp_path):
    # tmp_path is a Path object to a temporary directory
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    result = process_file(test_file)
    assert result is not None
```

## Markers

```python
# Mark as slow test
@pytest.mark.slow
def test_slow_operation():
    pass

# Mark as requiring network
@pytest.mark.network
def test_with_network():
    pass

# Mark as benchmark
@pytest.mark.benchmark
def test_performance():
    pass
```

Run specific markers:
```bash
pytest tests/ -m "not slow"  # Skip slow tests
pytest tests/ -m network     # Only network tests
```

## Mock Data

### Mock Responses (`tests/mocks/responses.py`)

Provides realistic mock responses for testing:
- OpenRouter API responses
- DeepSeek API responses
- Error responses

### Mock HTTP Client (`tests/mocks/http.py`)

HTTP client mock for testing without real network calls.

## Test Data

### Sample PDFs (`tests/fixtures/sample_pdfs/`)

Small sample PDFs for testing:
- `simple.pdf` - Single page, simple text
- `multi_page.pdf` - Multiple pages
- `with_tables.pdf` - Contains tables
- `with_images.pdf` - Contains images

### Expected Outputs (`tests/fixtures/expected_outputs/`)

Known-good outputs for comparison testing.

## Best Practices

1. **Test one thing per test:** Each test should verify a single behavior
2. **Use descriptive names:** `test_backend_retries_on_timeout` not `test_backend_1`
3. **Arrange-Act-Assert:** Structure tests clearly
4. **Clean up resources:** Use fixtures and context managers
5. **Don't test implementation details:** Test behavior, not internals
6. **Mock external dependencies:** No real API calls in unit tests
7. **Use parametrize for similar tests:**

```python
@pytest.mark.parametrize("dpi,expected_size", [
    (72, 100_000),
    (150, 300_000),
    (200, 500_000),
])
def test_rendering_with_dpi(dpi, expected_size):
    image = render_page(dpi=dpi)
    assert abs(len(image) - expected_size) < 50_000  # Allow tolerance
```

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Pushes to main
- Scheduled nightly builds

## See Also

- [../CLAUDE.md](../CLAUDE.md) - Development context
- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - System architecture
- [pytest documentation](https://docs.pytest.org/)
