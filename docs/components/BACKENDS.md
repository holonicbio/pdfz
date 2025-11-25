# Component: Backends

## Overview

The Backends component provides the abstraction layer for OCR/VLM operations. It defines a unified interface (`OcrVlmBackend`) that all backend implementations must follow, enabling the system to work with multiple VLM providers interchangeably.

The component uses a factory pattern (`make_backend`) to instantiate backends by name, making it easy to switch between providers via configuration.

## Responsibilities

This component is responsible for:
1. Defining the abstract interface for OCR operations
2. Implementing concrete backends for specific providers
3. Managing backend lifecycle (initialization, cleanup)
4. Handling HTTP communication with VLM APIs
5. Parsing and normalizing API responses

This component is NOT responsible for:
- PDF rendering (handled by Renderer)
- Pipeline orchestration (handled by Orchestrator)
- Configuration loading (handled by Common)

## Dependencies

### Required
- **Common**: Configuration models, error types, logging
- **aiohttp**: Async HTTP client for API calls

### Optional
- **openai**: For vLLM-compatible backends (not used in current implementation)

## Interface

### OcrVlmBackend (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from docling_hybrid.common.models import OcrBackendConfig

class OcrVlmBackend(ABC):
    def __init__(self, config: OcrBackendConfig) -> None:
        self.config = config
        self.name = config.name
    
    @abstractmethod
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert full page image to Markdown."""
        pass
    
    @abstractmethod
    async def table_to_markdown(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert table image to Markdown table."""
        pass
    
    @abstractmethod
    async def formula_to_latex(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert formula image to LaTeX."""
        pass
    
    async def close(self) -> None:
        """Close resources (optional override)."""
        pass
```

### Factory Function

```python
from docling_hybrid.backends import make_backend

# Create backend from config
backend = make_backend(config)

# Available backends
backends = list_backends()
# ['deepseek-mlx', 'deepseek-vllm', 'nemotron-openrouter']
```

## Implementation Details

### OpenRouterNemotronBackend

The primary implemented backend using OpenRouter's API.

**Key Features:**
- Base64 image encoding for API requests
- OpenAI-style chat completion format
- Handles both string and list content responses
- Automatic retry headers for identification

**Prompts:**
- `PAGE_TO_MARKDOWN_PROMPT`: Full page OCR to Markdown
- `TABLE_TO_MARKDOWN_PROMPT`: Table-only extraction
- `FORMULA_TO_LATEX_PROMPT`: Formula-only extraction

**HTTP Flow:**
1. Encode image as base64 data URL
2. Build messages array with text prompt + image
3. POST to OpenRouter `/v1/chat/completions`
4. Parse JSON response
5. Extract content (string or list format)

### DeepSeek Stubs

Both `DeepseekOcrVllmBackend` and `DeepseekOcrMlxBackend` are stubs that:
- Implement the interface
- Raise `NotImplementedError` on method calls
- Log warnings on initialization
- Document intended implementation approach

## Configuration

```toml
[backends.nemotron-openrouter]
name = "nemotron-openrouter"
model = "nvidia/nemotron-nano-12b-v2-vl:free"
base_url = "https://openrouter.ai/api/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
```

**Required Environment Variables:**
- `OPENROUTER_API_KEY`: API authentication

**Optional Environment Variables:**
- `DOCLING_HYBRID_HTTP_REFERER`: HTTP-Referer header
- `DOCLING_HYBRID_X_TITLE`: X-Title header

## Error Handling

**Error Cases:**
1. Missing API key → `ConfigurationError`
2. Network failure → `BackendConnectionError`
3. Request timeout → `BackendTimeoutError`
4. Invalid response → `BackendResponseError`
5. Unknown backend → `ConfigurationError`

**Recovery Strategy:**
- API errors surface immediately with actionable messages
- HTTP errors include status code and response body
- Configuration errors include hints for resolution

## Testing

### Unit Tests

```python
# Test factory
def test_make_backend_nemotron():
    backend = make_backend(config)
    assert isinstance(backend, OpenRouterNemotronBackend)

# Test unknown backend
def test_make_backend_unknown():
    with pytest.raises(ConfigurationError):
        make_backend(bad_config)

# Test content extraction
def test_extract_content_string():
    content = backend._extract_content(response)
    assert content == "expected"
```

### Integration Tests (TODO)

```python
@pytest.mark.integration
async def test_real_api_call():
    """Test with mocked HTTP response."""
    # Uses aioresponses to mock HTTP
    pass
```

## Examples

### Example 1: Basic Usage

```python
from docling_hybrid.backends import make_backend
from docling_hybrid.common.models import OcrBackendConfig

config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key="sk-...",
)

async with make_backend(config) as backend:
    markdown = await backend.page_to_markdown(
        image_bytes=png_bytes,
        page_num=1,
        doc_id="doc-123",
    )
    print(markdown)
```

### Example 2: Using from Config File

```python
from docling_hybrid.common.config import get_config
from docling_hybrid.backends import make_backend

config = get_config()
backend_config = config.backends.get_backend_config()  # Uses default

backend = make_backend(backend_config)
```

### Example 3: Registering Custom Backend

```python
from docling_hybrid.backends import register_backend, OcrVlmBackend

class MyBackend(OcrVlmBackend):
    async def page_to_markdown(self, image_bytes, page_num, doc_id):
        # Custom implementation
        return "# Custom"
    
    # ... other methods

register_backend("my-backend", MyBackend)
backend = make_backend(my_config)
```

## Future Extensions

### Phase 2: DeepSeek Implementations
- Implement `DeepseekOcrVllmBackend` for CUDA Linux
- Implement `DeepseekOcrMlxBackend` for macOS

### Phase 3: Specialized Backends
- `TableBackend` interface for table-specific models
- `FormulaBackend` interface for math-specific models
- MinerU integration for tables
- Mathpix integration for formulas

### Phase 4: Multi-Backend Ensemble
- Run multiple backends concurrently
- Implement voting/arbitration logic
- Add confidence scoring
