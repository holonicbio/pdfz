# Common Utilities

This module provides shared utilities and foundational components used across all parts of the Docling Hybrid OCR system.

## Overview

**Status:** ✅ Complete
**Purpose:** Centralized configuration, logging, error handling, and data models

The `common` module is the foundation layer that all other modules depend on. It provides:
- **Configuration management** with layered overrides
- **Structured logging** with context binding
- **Data models** with validation
- **Error types** with detailed context
- **Utility functions** for IDs, retries, and health checks

## Module Contents

```
common/
├── __init__.py          # Exports for easy importing
├── config.py            # Configuration loading and management
├── models.py            # Pydantic data models
├── errors.py            # Exception hierarchy
├── ids.py               # ID generation utilities
├── logging.py           # Structured logging setup
├── health.py            # System health monitoring
└── retry.py             # Retry logic with exponential backoff
```

## Core Components

### 1. Configuration (`config.py`)

Provides a layered configuration system with environment variable overrides.

#### Configuration Hierarchy
1. **Environment variables** (highest priority)
2. **User config file** (via `--config` or `DOCLING_HYBRID_CONFIG`)
3. **Default config** (`configs/default.toml`)

#### Main Classes

**`Config`** - Root configuration object
```python
class Config:
    app: AppConfig              # Application metadata
    logging: LoggingConfig      # Logging settings
    resources: ResourcesConfig  # Resource limits
    backends: BackendsConfig    # Backend configurations
```

**`AppConfig`** - Application metadata
```python
class AppConfig:
    name: str = "docling-hybrid-ocr"
    version: str = "0.1.0"
    environment: str = "production"
```

**`LoggingConfig`** - Logging settings
```python
class LoggingConfig:
    level: str = "INFO"         # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = "json"        # "json" or "text"
```

**`ResourcesConfig`** - Resource limits
```python
class ResourcesConfig:
    max_workers: int = 8              # Concurrent page processing
    max_memory_mb: int = 16384        # Memory limit
    page_render_dpi: int = 200        # PDF rendering DPI
    http_timeout_s: int = 120         # HTTP request timeout
    http_retry_attempts: int = 3      # Number of retries
```

**`BackendsConfig`** - Backend configuration
```python
class BackendsConfig:
    default: str = "nemotron-openrouter"
    configs: dict[str, OcrBackendConfig]  # name -> config mapping

    def get_backend_config(self, name: str | None = None) -> OcrBackendConfig:
        """Get config for a backend (or default if name is None)"""
```

#### Usage

```python
from docling_hybrid.common.config import init_config, get_config

# At application startup (call once)
config = init_config(Path("configs/local.toml"))

# Anywhere else in the codebase
config = get_config()
max_workers = config.resources.max_workers
backend_config = config.backends.get_backend_config()
```

#### Environment Variable Overrides

```bash
# Override any config value
DOCLING_HYBRID_LOG_LEVEL=DEBUG
DOCLING_HYBRID_MAX_WORKERS=2
DOCLING_HYBRID_PAGE_RENDER_DPI=150
DOCLING_HYBRID_DEFAULT_BACKEND=nemotron-openrouter

# Specify config file
DOCLING_HYBRID_CONFIG=configs/local.toml
```

### 2. Data Models (`models.py`)

Pydantic models for type-safe data structures throughout the system.

#### Main Models

**`OcrBackendConfig`** - Backend configuration
```python
class OcrBackendConfig(BaseModel):
    name: str                        # e.g., "nemotron-openrouter"
    model: str                       # e.g., "nvidia/nemotron-nano-12b-v2-vl:free"
    base_url: str                    # HTTP endpoint
    api_key: str | None = None       # Auth token (usually from env)
    extra_headers: dict | None       # Additional HTTP headers
    temperature: float = 0.0         # Generation temperature (0-2)
    max_tokens: int = 8192           # Max response tokens
    timeout_s: int = 120             # Request timeout
    retry_attempts: int = 3          # Number of retries
```

**`PageResult`** - OCR result for a single page
```python
class PageResult(BaseModel):
    page_num: int                    # 1-indexed page number
    doc_id: str                      # Document ID
    content: str                     # Markdown content
    backend_name: str                # Backend used
    metadata: dict[str, Any]         # Additional info (timing, image size, etc.)
```

**`BackendCandidate`** - Output from a backend
```python
class BackendCandidate(BaseModel):
    backend_name: str                # Backend that produced this
    content: str                     # Markdown content
    confidence: float = 1.0          # Confidence score (0-1)
    metadata: dict[str, Any]         # Backend-specific metadata
```

#### Enums

**`ContentType`** - Output format types
```python
class ContentType(str, Enum):
    MARKDOWN = "markdown"
    LATEX = "latex"
    TEXT = "text"
    HTML = "html"
```

**`BlockType`** - Document block types (for future block-level processing)
```python
class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    CODE = "code"
    FOOTNOTE = "footnote"
    CAPTION = "caption"
    OTHER = "other"
```

#### Usage

```python
from docling_hybrid.common.models import OcrBackendConfig, PageResult

# Create backend config
config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.0,
)

# Validate and serialize
config_dict = config.model_dump()        # Convert to dict
config_json = config.model_dump_json()   # Convert to JSON

# Parse from dict/JSON
config = OcrBackendConfig.model_validate(data)
config = OcrBackendConfig.model_validate_json(json_str)
```

### 3. Error Handling (`errors.py`)

Custom exception hierarchy for structured error handling.

#### Exception Hierarchy

```
DoclingHybridError (base)
├── ConfigurationError          # Config issues
├── ValidationError             # Invalid input
├── BackendError                # Backend failures
│   ├── BackendConnectionError  # Cannot connect
│   ├── BackendTimeoutError     # Request timeout
│   └── BackendResponseError    # Invalid response
└── RenderingError              # PDF rendering errors
```

#### Exception Details

All exceptions support:
- **message**: Human-readable error description
- **details**: Dictionary with additional context

**`DoclingHybridError`** - Base exception
```python
class DoclingHybridError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
```

**`ConfigurationError`** - Configuration problems
```python
# Raised when:
# - Config file not found
# - Invalid config syntax
# - Missing required values
# - Invalid config values

raise ConfigurationError(
    "Missing OPENROUTER_API_KEY environment variable",
    details={"env_var": "OPENROUTER_API_KEY"}
)
```

**`ValidationError`** - Input validation failures
```python
# Raised when:
# - PDF path doesn't exist
# - Invalid PDF file
# - Parameters out of range

raise ValidationError(
    f"PDF file not found: {pdf_path}",
    details={"path": str(pdf_path)}
)
```

**`BackendError`** - Backend failures (with subclasses)
```python
# Base class for backend errors
# Additional attribute: backend_name

raise BackendError(
    "Failed to process page",
    backend_name="nemotron-openrouter",
    details={"page": 1, "error": str(e)}
)

# Specific subclasses:
BackendConnectionError  # Network/connection issues
BackendTimeoutError     # Request timeouts
BackendResponseError    # Invalid/error responses (has status_code, response_body)
```

**`RenderingError`** - PDF rendering failures
```python
# Raised when:
# - PDF cannot be opened
# - Page cannot be rendered
# - Image conversion fails

raise RenderingError(
    f"Failed to render page {page_num}",
    details={"page": page_num, "pdf": str(pdf_path)}
)
```

#### Usage

```python
from docling_hybrid.common.errors import (
    DoclingHybridError,
    BackendError,
    BackendTimeoutError,
    ConfigurationError,
)

# Specific error handling
try:
    result = await backend.page_to_markdown(image_bytes)
except BackendTimeoutError as e:
    logger.error("backend_timeout", backend=e.backend_name, details=e.details)
    # Retry or fail gracefully
except BackendError as e:
    logger.error("backend_failed", backend=e.backend_name, error=str(e))
    raise

# Catch all project errors
try:
    result = await pipeline.convert_pdf(pdf_path)
except DoclingHybridError as e:
    logger.error("conversion_failed", error=str(e), details=e.details)
    sys.exit(1)
```

### 4. Logging (`logging.py`)

Structured logging with context binding using structlog.

#### Key Functions

```python
def setup_logging(level: str = "INFO", format_type: str = "json") -> None:
    """Initialize logging system"""

def get_logger(name: str | None = None) -> BoundLogger:
    """Get a logger instance"""

def bind_context(**kwargs) -> None:
    """Bind context to all subsequent logs"""

def unbind_context(*keys: str) -> None:
    """Remove context keys"""

def clear_context() -> None:
    """Clear all bound context"""
```

#### Usage

```python
from docling_hybrid.common.logging import get_logger, bind_context, clear_context

logger = get_logger(__name__)

# Simple logging
logger.info("server_started", port=8080)
logger.error("connection_failed", host="api.example.com", error=str(e))

# Context binding (useful for request tracking)
bind_context(doc_id="doc-abc123", user_id="user-456")
logger.info("processing_started")  # Automatically includes doc_id and user_id
logger.info("page_rendered", page=1)  # Also includes context
clear_context()

# In practice (from orchestrator)
doc_id = generate_id("doc")
bind_context(doc_id=doc_id, pdf_path=str(pdf_path))
try:
    # All logs in this scope include doc_id and pdf_path
    result = await process_pdf()
finally:
    clear_context()
```

#### Log Output

**JSON format** (default for production):
```json
{"event": "page_rendered", "page": 1, "doc_id": "doc-abc123", "level": "info", "timestamp": "2024-01-15T10:30:45Z"}
```

**Text format** (better for development):
```
2024-01-15 10:30:45 [info] page_rendered page=1 doc_id=doc-abc123
```

### 5. ID Generation (`ids.py`)

Utilities for generating unique identifiers.

#### Functions

```python
def generate_id(prefix: str = "") -> str:
    """Generate a short unique ID.

    Args:
        prefix: Optional prefix (e.g., "doc", "page")

    Returns:
        ID like "doc-a1b2c3d4" or just "a1b2c3d4" if no prefix
    """

def generate_timestamp_id(prefix: str = "") -> str:
    """Generate timestamp-based ID.

    Returns:
        ID like "doc-20240115-103045-a1b2"
    """
```

#### Usage

```python
from docling_hybrid.common.ids import generate_id, generate_timestamp_id

# Simple unique ID
doc_id = generate_id("doc")           # "doc-a1b2c3d4"
page_id = generate_id("page")         # "page-x7y8z9w0"
request_id = generate_id()            # "m3n4o5p6"

# Timestamp-based ID (useful for sorting)
batch_id = generate_timestamp_id("batch")  # "batch-20240115-103045-a1b2"
```

### 6. Health Monitoring (`health.py`)

System health check utilities.

#### Functions

```python
async def check_system_health() -> dict[str, Any]:
    """Check overall system health.

    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "memory_usage_mb": 2048,
            "cpu_percent": 45.2,
            "disk_usage_percent": 67.3,
            "timestamp": "2024-01-15T10:30:45Z"
        }
    """
```

#### Usage

```python
from docling_hybrid.common.health import check_system_health

health = await check_system_health()
if health["status"] != "healthy":
    logger.warning("system_degraded", **health)
```

### 7. Retry Logic (`retry.py`)

Exponential backoff retry decorator with configurable attempts.

#### Functions

```python
def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exceptions: Tuple of exceptions to catch
    """
```

#### Usage

```python
from docling_hybrid.common.retry import retry_with_backoff
from docling_hybrid.common.errors import BackendConnectionError, BackendTimeoutError

@retry_with_backoff(
    max_attempts=3,
    base_delay=2.0,
    exceptions=(BackendConnectionError, BackendTimeoutError)
)
async def fetch_from_backend(url: str) -> dict:
    """Fetch with automatic retry on connection/timeout errors."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Usage
try:
    data = await fetch_from_backend("https://api.example.com/data")
except BackendConnectionError:
    logger.error("all_retries_exhausted")
```

## Common Patterns

### Pattern 1: Configuration Loading
```python
# In main.py or __main__.py
from docling_hybrid.common.config import init_config
from pathlib import Path

config = init_config(Path("configs/local.toml"))

# Everywhere else
from docling_hybrid.common.config import get_config

config = get_config()
```

### Pattern 2: Structured Error Handling
```python
from docling_hybrid.common.errors import BackendError, ConfigurationError
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)

try:
    result = await process()
except ConfigurationError as e:
    logger.error("config_error", error=str(e), **e.details)
    sys.exit(1)
except BackendError as e:
    logger.error("backend_error", backend=e.backend_name, **e.details)
    raise
```

### Pattern 3: Context Logging
```python
from docling_hybrid.common.logging import get_logger, bind_context, clear_context
from docling_hybrid.common.ids import generate_id

logger = get_logger(__name__)
doc_id = generate_id("doc")

bind_context(doc_id=doc_id)
try:
    logger.info("processing_started")     # Includes doc_id
    # ... processing ...
    logger.info("processing_completed")   # Includes doc_id
finally:
    clear_context()
```

### Pattern 4: Model Validation
```python
from docling_hybrid.common.models import OcrBackendConfig
from docling_hybrid.common.errors import ValidationError

try:
    config = OcrBackendConfig.model_validate(data)
except pydantic.ValidationError as e:
    raise ValidationError("Invalid backend configuration", details={"errors": e.errors()})
```

## Testing

The common module has comprehensive unit tests:

```bash
# Run all common tests
pytest tests/unit/common -v

# Test specific component
pytest tests/unit/test_common.py::test_config_loading -v
pytest tests/unit/common/test_retry.py -v
```

## Dependencies

- **pydantic**: Data validation and serialization
- **structlog**: Structured logging
- **tomli/tomllib**: TOML parsing (tomli for Python <3.11)

## Best Practices

### Configuration
1. Always use `get_config()` instead of accessing global state directly
2. Initialize config once at application startup with `init_config()`
3. Use environment variables for secrets (API keys)
4. Use config files for structural settings

### Logging
1. Always use structured logging with key-value pairs
2. Use `bind_context()` for request-scoped context (doc_id, user_id, etc.)
3. Always `clear_context()` after processing to avoid leaking context
4. Use appropriate log levels (DEBUG for verbose, INFO for important events, ERROR for failures)

### Error Handling
1. Catch specific exceptions before generic ones
2. Always include context in `details` dict
3. Use appropriate exception types (don't use generic `Exception`)
4. Log errors before re-raising them

### Data Models
1. Use Pydantic models for all data structures
2. Add field descriptions for documentation
3. Use validators for complex validation logic
4. Prefer immutability where possible

## See Also

- [../README.md](../README.md) - Package overview
- [../backends/README.md](../backends/README.md) - Backend implementations
- [../orchestrator/README.md](../orchestrator/README.md) - Pipeline orchestration
- [../../CLAUDE.md](../../CLAUDE.md) - Master development context
