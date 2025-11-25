# OCR/VLM Backends

This module provides pluggable OCR/VLM backend implementations for converting document images to structured text.

## Overview

**Status:** ✅ Core complete, additional backends in progress
**Purpose:** Abstract interface for multiple OCR/VLM providers

The backends module implements a pluggable architecture that allows seamless switching between different Vision-Language Model (VLM) providers for OCR tasks. All backends implement the same interface, making them interchangeable.

## Architecture

```
backends/
├── __init__.py                  # Package exports
├── base.py                      # Abstract OcrVlmBackend interface
├── factory.py                   # Backend registry and factory
├── openrouter_nemotron.py       # ✅ OpenRouter/Nemotron (working)
├── deepseek_vllm.py             # ✅ DeepSeek vLLM (implemented)
├── deepseek_vllm_stub.py        # ○ DeepSeek vLLM stub (deprecated)
├── deepseek_mlx_stub.py         # ○ DeepSeek MLX stub (future)
├── fallback.py                  # ✅ Multi-backend fallback chain
└── health.py                    # ✅ Backend health checking
```

**Legend:**
- ✅ = Implemented and tested
- ○ = Stub/planned for future

## Backend Interface

All backends inherit from `OcrVlmBackend` and implement these methods:

### Base Class: `OcrVlmBackend`

```python
class OcrVlmBackend(ABC):
    """Abstract base class for OCR/VLM backends."""

    def __init__(self, config: OcrBackendConfig):
        """Initialize with configuration."""
        self.config = config
        self.name = config.name

    @abstractmethod
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert full page image to Markdown.

        Args:
            image_bytes: PNG image bytes
            page_num: Page number (1-indexed)
            doc_id: Document identifier

        Returns:
            Markdown string

        Raises:
            BackendError: On backend failures
        """
        pass

    # Extended scope (not yet required)
    async def table_to_markdown(
        self,
        image_bytes: bytes,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Convert table image to Markdown table."""
        pass

    async def formula_to_latex(
        self,
        image_bytes: bytes,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Convert formula image to LaTeX."""
        pass

    # Context manager support
    async def __aenter__(self):
        """Setup resources (HTTP sessions, etc.)"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        pass
```

## Available Backends

### 1. OpenRouter Nemotron (`openrouter_nemotron.py`)

**Status:** ✅ Fully implemented
**Provider:** OpenRouter API
**Model:** `nvidia/nemotron-nano-12b-v2-vl:free`

The primary production backend using OpenRouter's API with the Nemotron-nano vision-language model.

#### Configuration

```python
OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.environ["OPENROUTER_API_KEY"],
    extra_headers={
        "HTTP-Referer": "https://github.com/your-org/docling-hybrid-ocr",
    },
    temperature=0.0,
    max_tokens=8192,
    timeout_s=120,
    retry_attempts=3,
)
```

#### Features

- **OpenAI-compatible API:** Uses standard chat completion format
- **Base64 image encoding:** Images sent as data URLs
- **Retry logic:** Automatic retry with exponential backoff
- **Rate limit handling:** Respects 429 responses with Retry-After
- **Response parsing:** Handles both string and list content formats
- **Specialized prompts:** Optimized prompts for page/table/formula extraction

#### Implementation Details

**Image Encoding:**
```python
def _encode_image(image_bytes: bytes) -> str:
    """Encode image as base64 data URL."""
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/png;base64,{b64}"
```

**Request Format:**
```json
{
  "model": "nvidia/nemotron-nano-12b-v2-vl:free",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "You are a document OCR system..."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,..."
          }
        }
      ]
    }
  ],
  "temperature": 0.0,
  "max_tokens": 8192
}
```

**Response Handling:**
```python
# Handles both formats:
# 1. String content
{"choices": [{"message": {"content": "markdown here"}}]}

# 2. List content (from some providers)
{"choices": [{"message": {"content": [{"text": "markdown here"}]}}]}
```

#### Error Handling

```python
try:
    markdown = await backend.page_to_markdown(image_bytes, 1, doc_id)
except BackendConnectionError:
    # Cannot reach API
except BackendTimeoutError:
    # Request took too long
except RateLimitError as e:
    # Rate limited, e.retry_after has wait time
except BackendResponseError as e:
    # Bad response (4xx/5xx)
    # e.status_code, e.response_body available
```

#### Prompts

**Page to Markdown:**
```
You are a document OCR system. Convert the document page image to GitHub-flavored Markdown.

RULES:
1. Extract ALL text exactly as it appears - do not paraphrase or summarize
2. Preserve document structure:
   - Use # ## ### for headings based on visual hierarchy
   - Use - or * for bullet lists
   - Use 1. 2. 3. for numbered lists
   - Use | syntax for tables
   - Use $...$ for inline math, $$...$$ for block math
3. For figures/images/charts: insert placeholder <FIGURE>
4. For formulas: transcribe as LaTeX
5. Do NOT add commentary or explanations

Output ONLY the Markdown content. No preamble, no explanations.
```

### 2. DeepSeek vLLM (`deepseek_vllm.py`)

**Status:** ✅ Implemented
**Provider:** vLLM server (self-hosted or remote)
**Model:** `deepseek-ai/deepseek-vl2`

Backend for DeepSeek VL2 model served via vLLM.

#### Configuration

```python
OcrBackendConfig(
    name="deepseek-vllm",
    model="deepseek-ai/deepseek-vl2",
    base_url="http://localhost:8000/v1/chat/completions",
    api_key="",  # Not required for local vLLM
    temperature=0.0,
    max_tokens=8192,
)
```

#### Features

- **vLLM compatibility:** Uses vLLM's OpenAI-compatible API
- **Local deployment:** Can run on your own hardware
- **High throughput:** vLLM provides optimized inference
- **DeepSeek VL2 model:** State-of-the-art vision-language model

### 3. DeepSeek MLX (`deepseek_mlx_stub.py`)

**Status:** ○ Stub - Future implementation
**Provider:** MLX (Apple Silicon)
**Model:** `deepseek-ai/deepseek-vl2`

Planned backend for running DeepSeek on Apple Silicon using MLX framework.

#### Planned Features

- Native Apple Silicon support
- On-device inference
- No external API dependencies
- Lower latency for M1/M2/M3 Macs

### 4. Fallback Backend (`fallback.py`)

**Status:** ✅ Implemented
**Purpose:** Try multiple backends in sequence

A meta-backend that tries multiple backends in order until one succeeds.

#### Configuration

```python
from docling_hybrid.backends.fallback import FallbackBackend
from docling_hybrid.backends import make_backend

# Create individual backends
backends = [
    make_backend(config1),  # Primary
    make_backend(config2),  # Fallback 1
    make_backend(config3),  # Fallback 2
]

# Create fallback chain
fallback = FallbackBackend(backends)

# Use normally - will try backends in order
markdown = await fallback.page_to_markdown(image_bytes, page_num, doc_id)
```

#### Behavior

1. Try first backend
2. If it fails with retryable error (timeout, connection), try next
3. If it fails with non-retryable error (auth, invalid input), fail immediately
4. Return first successful result
5. If all fail, raise last error

## Backend Factory

The factory provides a centralized registry for backend creation.

### Factory Functions

```python
def make_backend(config: OcrBackendConfig) -> OcrVlmBackend:
    """Create backend instance from config.

    Args:
        config: Backend configuration

    Returns:
        Backend instance

    Raises:
        ConfigurationError: If backend name not recognized
    """

def list_backends() -> list[str]:
    """List all registered backend names.

    Returns:
        ["nemotron-openrouter", "deepseek-vllm", "deepseek-mlx"]
    """

def register_backend(name: str, backend_class: type[OcrVlmBackend]) -> None:
    """Register a new backend implementation.

    Args:
        name: Backend identifier
        backend_class: Backend class (must inherit from OcrVlmBackend)
    """
```

### Usage

```python
from docling_hybrid.backends import make_backend, list_backends
from docling_hybrid.common.models import OcrBackendConfig

# List available backends
backends = list_backends()
print(backends)  # ["nemotron-openrouter", "deepseek-vllm", "deepseek-mlx"]

# Create from config
config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
backend = make_backend(config)

# Use backend
async with backend:
    markdown = await backend.page_to_markdown(image_bytes, 1, "doc-123")
```

### Registry

The factory maintains a registry mapping names to classes:

```python
BACKEND_REGISTRY: dict[str, type[OcrVlmBackend]] = {
    "nemotron-openrouter": OpenRouterNemotronBackend,
    "deepseek-vllm": DeepSeekVLLMBackend,
    "deepseek-mlx": DeepseekOcrMlxBackend,  # Stub
}
```

### Adding Custom Backends

```python
from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.backends.factory import register_backend

class MyCustomBackend(OcrVlmBackend):
    async def page_to_markdown(self, image_bytes, page_num, doc_id):
        # Your implementation
        return "# Markdown content"

# Register it
register_backend("my-backend", MyCustomBackend)

# Now it's available via factory
config = OcrBackendConfig(name="my-backend", ...)
backend = make_backend(config)
```

## Health Checking

The `health.py` module provides backend health monitoring.

```python
from docling_hybrid.backends.health import check_backend_health

# Check if backend is reachable
health = await check_backend_health(backend)

print(health)
# {
#     "name": "nemotron-openrouter",
#     "status": "healthy",
#     "response_time_ms": 245,
#     "last_check": "2024-01-15T10:30:45Z",
#     "error": None
# }
```

## Common Patterns

### Pattern 1: Basic Usage

```python
from docling_hybrid.backends import make_backend
from docling_hybrid.common.config import get_config

# Get config
config = get_config()
backend_config = config.backends.get_backend_config()

# Create backend
backend = make_backend(backend_config)

# Use as context manager
async with backend:
    markdown = await backend.page_to_markdown(
        image_bytes=png_bytes,
        page_num=1,
        doc_id="doc-abc123"
    )
    print(markdown)
```

### Pattern 2: Error Handling

```python
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendTimeoutError,
    BackendResponseError,
)

try:
    async with backend:
        markdown = await backend.page_to_markdown(image_bytes, 1, doc_id)
except BackendConnectionError as e:
    logger.error("cannot_connect", backend=e.backend_name, error=str(e))
    # Try alternative backend or fail
except BackendTimeoutError as e:
    logger.warning("timeout", backend=e.backend_name, page=1)
    # Retry or skip page
except BackendResponseError as e:
    logger.error("bad_response", status=e.status_code, backend=e.backend_name)
    # Handle specific error codes
    if e.status_code == 401:
        # Invalid API key
        pass
    elif e.status_code == 429:
        # Rate limited
        pass
```

### Pattern 3: Fallback Chain

```python
from docling_hybrid.backends import make_backend
from docling_hybrid.backends.fallback import FallbackBackend

# Create multiple backends
primary = make_backend(primary_config)
secondary = make_backend(secondary_config)
tertiary = make_backend(tertiary_config)

# Create fallback chain
backend = FallbackBackend([primary, secondary, tertiary])

# Use normally - automatically tries fallbacks
async with backend:
    markdown = await backend.page_to_markdown(image_bytes, 1, doc_id)
    # Will try primary first, then secondary if it fails, then tertiary
```

### Pattern 4: Retry with Rate Limits

```python
from docling_hybrid.backends.openrouter_nemotron import RateLimitError
import asyncio

async def process_with_retry(backend, image_bytes, page_num, doc_id):
    """Process with automatic rate limit retry."""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return await backend.page_to_markdown(image_bytes, page_num, doc_id)
        except RateLimitError as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = e.retry_after or (2 ** attempt)  # Exponential backoff
            logger.info("rate_limited", wait_s=wait_time, attempt=attempt+1)
            await asyncio.sleep(wait_time)
```

## Testing

### Unit Tests

```bash
# Test all backends
pytest tests/unit/backends -v

# Test specific backend
pytest tests/unit/test_backends.py::test_openrouter_backend -v

# Test factory
pytest tests/unit/backends/test_factory.py -v

# Test fallback logic
pytest tests/unit/backends/test_fallback.py -v
```

### Integration Tests

```bash
# Test with real API (requires API key)
OPENROUTER_API_KEY=sk-... pytest tests/integration/test_openrouter_integration.py -v

# Test HTTP interactions (mocked)
pytest tests/integration/test_backend_http.py -v
```

### Testing Custom Backends

```python
import pytest
from docling_hybrid.backends.base import OcrVlmBackend

@pytest.mark.asyncio
async def test_my_custom_backend():
    """Test custom backend implementation."""
    backend = MyCustomBackend(config)

    async with backend:
        result = await backend.page_to_markdown(
            image_bytes=b"fake png data",
            page_num=1,
            doc_id="test-doc"
        )

        assert isinstance(result, str)
        assert len(result) > 0
        assert result.startswith("#")  # Markdown heading
```

## Configuration Examples

### Production Configuration

```toml
# configs/default.toml
[backends]
default = "nemotron-openrouter"

[[backends.candidates]]
name = "nemotron-openrouter"
model = "nvidia/nemotron-nano-12b-v2-vl:free"
base_url = "https://openrouter.ai/api/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
timeout_s = 120
retry_attempts = 3

[backends.candidates.extra_headers]
HTTP-Referer = "https://github.com/your-org/docling-hybrid-ocr"
```

### Local Development Configuration

```toml
# configs/local.toml
[backends]
default = "deepseek-vllm"

[[backends.candidates]]
name = "deepseek-vllm"
model = "deepseek-ai/deepseek-vl2"
base_url = "http://localhost:8000/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
timeout_s = 60
```

### Multi-Backend Fallback

```toml
# Multiple backends configured
[[backends.candidates]]
name = "deepseek-vllm"
model = "deepseek-ai/deepseek-vl2"
base_url = "http://localhost:8000/v1/chat/completions"

[[backends.candidates]]
name = "nemotron-openrouter"
model = "nvidia/nemotron-nano-12b-v2-vl:free"
base_url = "https://openrouter.ai/api/v1/chat/completions"

# Then in code:
# backends = [make_backend(cfg) for cfg in config.backends.configs.values()]
# fallback = FallbackBackend(backends)
```

## Performance Considerations

### Latency

- **OpenRouter Nemotron:** 2-5s per page (depends on network + model)
- **DeepSeek vLLM (local):** 1-3s per page (depends on hardware)
- **DeepSeek MLX (planned):** Expected 0.5-2s per page on Apple Silicon

### Throughput

- **Concurrent requests:** Backends support async processing
- **Rate limits:** OpenRouter free tier: ~20 req/min
- **Batch size:** Limit concurrent requests to avoid overwhelming backend

### Memory

- **Image encoding:** ~20-30% overhead from base64 encoding
- **Response size:** ~5-50 KB per page depending on content
- **Session pooling:** aiohttp sessions reused for efficiency

## Troubleshooting

### "Missing API key"

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

Or set in config:
```python
config = OcrBackendConfig(
    name="nemotron-openrouter",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    ...
)
```

### "Backend timeout"

Increase timeout in config:
```toml
timeout_s = 300  # 5 minutes
```

Or reduce image DPI to send smaller images:
```bash
docling-hybrid-ocr convert doc.pdf --dpi 100
```

### "Rate limited (429)"

The backend automatically retries with exponential backoff. If you hit rate limits frequently:

1. Reduce concurrency: `--max-workers 1`
2. Add delays between requests
3. Upgrade to paid tier for higher rate limits

### "Invalid response format"

Check the response structure. Some providers return:
- String content: `content: "markdown"`
- List content: `content: [{"text": "markdown"}]`

The OpenRouter backend handles both formats automatically.

## See Also

- [../README.md](../README.md) - Package overview
- [../common/README.md](../common/README.md) - Common utilities
- [../orchestrator/README.md](../orchestrator/README.md) - Pipeline orchestration
- [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) - System architecture
- [../../CLAUDE.md](../../CLAUDE.md) - Master development context
