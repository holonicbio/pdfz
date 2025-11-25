# API Reference

Quick reference for Docling Hybrid OCR Python API.

> For comprehensive examples and detailed usage, see **[API.md](API.md)**

---

## Installation

```bash
pip install docling-hybrid-ocr
```

---

## Quick Reference

### Imports

```python
# Core imports
from docling_hybrid import (
    __version__,
    init_config,
    get_config,
    HybridPipeline,
    ConversionResult,
)

# Backend imports
from docling_hybrid.backends import (
    make_backend,
    list_backends,
    OcrVlmBackend,
)

# Model imports
from docling_hybrid.common.models import (
    OcrBackendConfig,
    PageResult,
)

# Orchestrator imports
from docling_hybrid.orchestrator import (
    ConversionOptions,
)

# Error imports
from docling_hybrid.common.errors import (
    DoclingHybridError,
    ConfigurationError,
    BackendError,
    RenderingError,
)
```

---

## Configuration

### init_config()

Initialize configuration from file or defaults.

**Signature:**
```python
def init_config(
    config_path: Path | None = None,
    env_prefix: str = "DOCLING_HYBRID_"
) -> Config
```

**Parameters:**
- `config_path` (Path | None): Path to TOML config file. If None, loads from default locations.
- `env_prefix` (str): Prefix for environment variable overrides. Default: "DOCLING_HYBRID_"

**Returns:**
- `Config`: Loaded configuration object

**Example:**
```python
from pathlib import Path
from docling_hybrid import init_config

# Load from specific file
config = init_config(Path("configs/local.toml"))

# Load from default location
config = init_config()

# Load with custom env prefix
config = init_config(env_prefix="MY_APP_")
```

**Environment Variables:**
- `DOCLING_HYBRID_CONFIG` - Config file path
- `DOCLING_HYBRID_LOG_LEVEL` - Log level (DEBUG, INFO, WARNING, ERROR)
- `DOCLING_HYBRID_MAX_WORKERS` - Concurrent workers
- `DOCLING_HYBRID_DEFAULT_BACKEND` - Default backend name
- `OPENROUTER_API_KEY` - OpenRouter API key

---

### get_config()

Get the globally initialized configuration.

**Signature:**
```python
def get_config() -> Config
```

**Returns:**
- `Config`: Previously initialized configuration

**Raises:**
- `ConfigurationError`: If init_config() hasn't been called

**Example:**
```python
from docling_hybrid import get_config

# Must call init_config() first
config = get_config()
print(config.backends.default)
```

---

## Pipeline

### HybridPipeline

Main conversion pipeline.

**Constructor:**
```python
class HybridPipeline:
    def __init__(
        self,
        config: Config,
        backend: OcrVlmBackend | None = None
    ) -> None
```

**Parameters:**
- `config` (Config): Configuration object from init_config()
- `backend` (OcrVlmBackend | None): Optional specific backend to use. If None, uses default from config.

**Example:**
```python
from docling_hybrid import init_config, HybridPipeline

config = init_config()
pipeline = HybridPipeline(config)
```

---

### convert_pdf()

Convert a PDF to Markdown.

**Signature:**
```python
async def convert_pdf(
    self,
    pdf_path: Path,
    output_path: Path | None = None,
    options: ConversionOptions | None = None,
    progress_callback: ProgressCallback | None = None,
) -> ConversionResult
```

**Parameters:**
- `pdf_path` (Path): Path to input PDF file
- `output_path` (Path | None): Optional output file path. If None, no file is written.
- `options` (ConversionOptions | None): Conversion options. If None, uses defaults.
- `progress_callback` (ProgressCallback | None): Optional callback for progress updates. See [Progress Callbacks](#progress-callbacks).

**Returns:**
- `ConversionResult`: Conversion result with markdown content and metadata

**Raises:**
- `RenderingError`: If PDF cannot be rendered
- `BackendError`: If VLM backend fails
- `ValidationError`: If inputs are invalid

**Example:**
```python
from pathlib import Path

# Basic conversion with OpenRouter
result = await pipeline.convert_pdf(Path("document.pdf"))
print(result.markdown)

# With output file
result = await pipeline.convert_pdf(
    Path("document.pdf"),
    output_path=Path("output.md")
)

# With options
from docling_hybrid.orchestrator import ConversionOptions
options = ConversionOptions(max_pages=5, dpi=150)
result = await pipeline.convert_pdf(
    Path("document.pdf"),
    options=options
)

# With progress callback
from docling_hybrid.orchestrator.callbacks import ConsoleProgressCallback
callback = ConsoleProgressCallback(verbose=True)
result = await pipeline.convert_pdf(
    Path("document.pdf"),
    progress_callback=callback
)
```

---

## Conversion Options

### ConversionOptions

Configuration for a single conversion.

**Class:**
```python
class ConversionOptions(BaseModel):
    backend_name: str | None = None
    max_pages: int | None = None
    start_page: int = 1
    dpi: int | None = None
    add_page_separators: bool = True
    page_separator_format: str = "<!-- PAGE {page_num} -->\n\n"
```

**Fields:**
- `backend_name` (str | None): Backend to use. None = use default from config.
- `max_pages` (int | None): Maximum pages to process. None = all pages.
- `start_page` (int): Starting page number (1-indexed). Default: 1
- `dpi` (int | None): Rendering DPI. None = use config value. Higher = better quality, more memory. Range: 72-600
- `add_page_separators` (bool): Add `<!-- PAGE N -->` comments. Default: True
- `page_separator_format` (str): Format string for page separators. Default: `"<!-- PAGE {page_num} -->\n\n"`

**Example:**
```python
from docling_hybrid.orchestrator import ConversionOptions

# Process first 10 pages at lower DPI
options = ConversionOptions(
    max_pages=10,
    start_page=1,
    dpi=150,
    add_page_separators=True
)

# Process pages 5-10 with custom backend
options = ConversionOptions(
    backend_name="nemotron-openrouter",
    start_page=5,
    max_pages=6,
    dpi=200
)
```

---

## Results

### ConversionResult

Result of a PDF conversion.

**Class:**
```python
class ConversionResult(BaseModel):
    doc_id: str
    source_path: Path
    output_path: Path | None
    markdown: str
    page_results: list[PageResult]
    total_pages: int
    processed_pages: int
    backend_name: str
    metadata: dict
```

**Fields:**
- `doc_id` (str): Unique document ID (e.g., "doc-abc123")
- `source_path` (Path): Path to input PDF
- `output_path` (Path | None): Path to output file (if written)
- `markdown` (str): Full Markdown content
- `page_results` (list[PageResult]): Results for each page
- `total_pages` (int): Total pages in PDF
- `processed_pages` (int): Number of pages successfully processed
- `backend_name` (str): Backend used for conversion
- `metadata` (dict): Additional metadata (timing, etc.)

**Example:**
```python
result = await pipeline.convert_pdf(pdf_path)

# Access result data
print(f"Document ID: {result.doc_id}")
print(f"Processed: {result.processed_pages}/{result.total_pages} pages")
print(f"Backend: {result.backend_name}")

# Get markdown
markdown = result.markdown

# Iterate pages
for page_result in result.page_results:
    print(f"Page {page_result.page_num}: {len(page_result.content)} chars")
```

---

### PageResult

Result for a single page.

**Class:**
```python
class PageResult(BaseModel):
    page_num: int
    doc_id: str
    content: str
    backend_name: str
    metadata: dict
```

**Fields:**
- `page_num` (int): Page number (1-indexed)
- `doc_id` (str): Document ID this page belongs to
- `content` (str): Markdown content for this page
- `backend_name` (str): Backend used
- `metadata` (dict): Page-specific metadata (image size, processing time, etc.)

**Example:**
```python
page_result = result.page_results[0]

print(f"Page: {page_result.page_num}")
print(f"Content length: {len(page_result.content)}")
print(f"Processing time: {page_result.metadata.get('processing_time_s')}s")
```

---

## Backends

### make_backend()

Create a backend instance.

**Signature:**
```python
def make_backend(config: OcrBackendConfig) -> OcrVlmBackend
```

**Parameters:**
- `config` (OcrBackendConfig): Backend configuration

**Returns:**
- `OcrVlmBackend`: Backend instance

**Raises:**
- `ConfigurationError`: If backend configuration is invalid
- `ValueError`: If backend name is unknown

**Example:**
```python
from docling_hybrid.backends import make_backend
from docling_hybrid.common.models import OcrBackendConfig

# Create from config
backend_config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.0,
    max_tokens=8192,
)
backend = make_backend(backend_config)

# Use with context manager
async with backend:
    result = await backend.page_to_markdown(image_bytes, 1, "doc-123")
```

---

### list_backends()

List available backend names.

**Signature:**
```python
def list_backends() -> list[str]
```

**Returns:**
- `list[str]`: List of backend names

**Example:**
```python
from docling_hybrid.backends import list_backends

backends = list_backends()
print(backends)  # ['nemotron-openrouter', 'deepseek-vllm', 'deepseek-mlx']
```

---

### OcrVlmBackend (Abstract Interface)

Base interface for all backends.

**Abstract Methods:**
```python
class OcrVlmBackend(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self:
        """Enter async context manager."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""

    @abstractmethod
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str
    ) -> str:
        """Convert full page image to Markdown."""

    @abstractmethod
    async def table_to_markdown(
        self,
        image_bytes: bytes,
        meta: dict
    ) -> str:
        """Convert table region to Markdown."""

    @abstractmethod
    async def formula_to_latex(
        self,
        image_bytes: bytes,
        meta: dict
    ) -> str:
        """Convert formula region to LaTeX."""
```

**Example:**
```python
from docling_hybrid.backends import make_backend

config = get_config()
backend_config = config.backends.get_backend_config()
backend = make_backend(backend_config)

async with backend:
    # Convert page
    markdown = await backend.page_to_markdown(image_bytes, 1, "doc-123")

    # Convert table
    table_md = await backend.table_to_markdown(
        image_bytes,
        {"page": 1, "bbox": (10, 20, 200, 300)}
    )

    # Convert formula
    latex = await backend.formula_to_latex(
        image_bytes,
        {"page": 1, "type": "inline"}
    )
```

---

## Renderer

### render_page_to_png_bytes()

Render a PDF page to PNG image bytes.

**Signature:**
```python
def render_page_to_png_bytes(
    pdf_path: Path,
    page_index: int,
    dpi: int = 200
) -> bytes
```

**Parameters:**
- `pdf_path` (Path): Path to PDF file
- `page_index` (int): Page index (0-indexed)
- `dpi` (int): Rendering DPI. Default: 200

**Returns:**
- `bytes`: PNG image bytes

**Raises:**
- `RenderingError`: If rendering fails
- `ValueError`: If page_index is out of range

**Example:**
```python
from pathlib import Path
from docling_hybrid.renderer import render_page_to_png_bytes

# Render first page
image_bytes = render_page_to_png_bytes(
    Path("document.pdf"),
    page_index=0,
    dpi=200
)

# Save to file
with open("page_0.png", "wb") as f:
    f.write(image_bytes)
```

---

### get_page_count()

Get total number of pages in a PDF.

**Signature:**
```python
def get_page_count(pdf_path: Path) -> int
```

**Parameters:**
- `pdf_path` (Path): Path to PDF file

**Returns:**
- `int`: Number of pages

**Raises:**
- `RenderingError`: If PDF cannot be opened

**Example:**
```python
from pathlib import Path
from docling_hybrid.renderer import get_page_count

total_pages = get_page_count(Path("document.pdf"))
print(f"Total pages: {total_pages}")
```

---

### render_region_to_png_bytes()

Render a specific region of a PDF page.

**Signature:**
```python
def render_region_to_png_bytes(
    pdf_path: Path,
    page_index: int,
    bbox: tuple[int, int, int, int],
    dpi: int = 200
) -> bytes
```

**Parameters:**
- `pdf_path` (Path): Path to PDF file
- `page_index` (int): Page index (0-indexed)
- `bbox` (tuple[int, int, int, int]): Bounding box (x1, y1, x2, y2) in PDF coordinates
- `dpi` (int): Rendering DPI. Default: 200

**Returns:**
- `bytes`: PNG image bytes for the region

**Example:**
```python
from docling_hybrid.renderer import render_region_to_png_bytes

# Render specific region
region_bytes = render_region_to_png_bytes(
    Path("document.pdf"),
    page_index=0,
    bbox=(100, 100, 400, 300),
    dpi=200
)
```

---

## Error Handling

### Exception Hierarchy

```
DoclingHybridError (base)
├── ConfigurationError
├── BackendError
│   ├── BackendConnectionError
│   ├── BackendTimeoutError
│   └── BackendResponseError
├── RenderingError
└── ValidationError
```

### DoclingHybridError

Base exception for all errors.

**Attributes:**
- `message` (str): Error message

---

### ConfigurationError

Configuration-related errors.

**Example:**
```python
from docling_hybrid.common.errors import ConfigurationError

try:
    config = init_config(Path("invalid.toml"))
except ConfigurationError as e:
    print(f"Config error: {e}")
```

---

### BackendError

Backend-related errors.

**Attributes:**
- `message` (str): Error message
- `backend_name` (str): Name of backend that failed

**Subclasses:**
- `BackendConnectionError` - Connection/network failures
- `BackendTimeoutError` - Request timeout
- `BackendResponseError` - Invalid API response

**Example:**
```python
from docling_hybrid.common.errors import BackendError, BackendTimeoutError

try:
    result = await pipeline.convert_pdf(pdf_path)
except BackendTimeoutError as e:
    print(f"Backend {e.backend_name} timed out: {e}")
except BackendError as e:
    print(f"Backend {e.backend_name} failed: {e}")
```

---

### RenderingError

PDF rendering errors.

**Example:**
```python
from docling_hybrid.common.errors import RenderingError

try:
    image_bytes = render_page_to_png_bytes(pdf_path, 0)
except RenderingError as e:
    print(f"Cannot render PDF: {e}")
```

---

## Models

### OcrBackendConfig

Backend configuration.

**Class:**
```python
class OcrBackendConfig(BaseModel):
    name: str
    model: str
    base_url: str
    api_key: str | None = None
    temperature: float = 0.0
    max_tokens: int = 8192
```

**Fields:**
- `name` (str): Backend identifier (e.g., "nemotron-openrouter")
- `model` (str): Model identifier
- `base_url` (str): API endpoint URL
- `api_key` (str | None): API key (if required)
- `temperature` (float): Sampling temperature (0.0 = deterministic)
- `max_tokens` (int): Maximum response tokens

**Example:**
```python
from docling_hybrid.common.models import OcrBackendConfig

config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.0,
    max_tokens=8192,
)
```

---

### Config

Main configuration object.

**Structure:**
```python
class Config(BaseModel):
    app: AppConfig
    logging: LoggingConfig
    resources: ResourceConfig
    backends: BackendManagerConfig
    output: OutputConfig
    docling: DoclingConfig
```

**Access via:**
```python
config = get_config()

# App settings
print(config.app.name)
print(config.app.version)

# Logging
print(config.logging.level)

# Resources
print(config.resources.max_workers)
print(config.resources.max_memory_mb)

# Backends
backend_config = config.backends.get_backend_config()
print(config.backends.default)
```

---

## Progress Callbacks

### ProgressCallback Protocol

Protocol for receiving progress updates during conversion.

**Methods:**
```python
class ProgressCallback(Protocol):
    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        """Called when conversion starts."""

    def on_page_start(self, page_num: int, total: int) -> None:
        """Called when a page starts processing."""

    def on_page_complete(self, page_num: int, total: int, result: PageResult) -> None:
        """Called when a page completes successfully."""

    def on_page_error(self, page_num: int, error: Exception) -> None:
        """Called when a page fails."""

    def on_conversion_complete(self, result: ConversionResult) -> None:
        """Called when conversion completes successfully."""

    def on_conversion_error(self, error: Exception) -> None:
        """Called when conversion fails."""
```

---

### ConsoleProgressCallback

Rich console progress display with progress bar.

**Constructor:**
```python
class ConsoleProgressCallback:
    def __init__(
        self,
        console: Console | None = None,
        verbose: bool = False
    ) -> None
```

**Parameters:**
- `console` (Console | None): Rich Console instance (creates new if None)
- `verbose` (bool): Show detailed per-page information

**Example:**
```python
from docling_hybrid.orchestrator.callbacks import ConsoleProgressCallback

# Basic console progress
callback = ConsoleProgressCallback()
result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)

# Verbose mode (shows each page)
callback = ConsoleProgressCallback(verbose=True)
result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)
```

---

### FileProgressCallback

Write JSON progress events to a file for monitoring.

**Constructor:**
```python
class FileProgressCallback:
    def __init__(
        self,
        file_path: Path,
        append: bool = True
    ) -> None
```

**Parameters:**
- `file_path` (Path): Path to write progress events
- `append` (bool): If True, append to existing file; if False, overwrite

**Example:**
```python
from pathlib import Path
from docling_hybrid.orchestrator.callbacks import FileProgressCallback

# Log progress to file
callback = FileProgressCallback(Path("progress.log"))
result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)

# File contents (JSON lines):
# {"timestamp": 1234567890.0, "event": "conversion_start", "doc_id": "doc-abc", ...}
# {"timestamp": 1234567892.0, "event": "page_complete", "page_num": 1, ...}
```

---

### CompositeProgressCallback

Combine multiple callbacks (e.g., console + file logging).

**Constructor:**
```python
class CompositeProgressCallback:
    def __init__(self, callbacks: list[Any]) -> None
```

**Parameters:**
- `callbacks` (list): List of callback instances

**Example:**
```python
from docling_hybrid.orchestrator.callbacks import (
    ConsoleProgressCallback,
    FileProgressCallback,
    CompositeProgressCallback,
)

# Combine console and file logging
console = ConsoleProgressCallback(verbose=True)
file = FileProgressCallback(Path("progress.log"))
composite = CompositeProgressCallback([console, file])

result = await pipeline.convert_pdf(pdf_path, progress_callback=composite)
```

---

## Logging

### get_logger()

Get a structured logger.

**Signature:**
```python
def get_logger(name: str) -> BoundLogger
```

**Parameters:**
- `name` (str): Logger name (typically `__name__`)

**Returns:**
- `BoundLogger`: Structured logger instance

**Example:**
```python
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info(
    "conversion_started",
    doc_id="doc-123",
    pdf_path="/path/to/doc.pdf",
    total_pages=10
)

logger.error(
    "backend_failed",
    backend="nemotron",
    error="Connection timeout"
)
```

---

## Complete Example

```python
import asyncio
import os
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.orchestrator import ConversionOptions
from docling_hybrid.common.errors import DoclingHybridError

async def main():
    try:
        # 1. Initialize configuration
        config = init_config(Path("configs/local.toml"))

        # 2. Create pipeline
        pipeline = HybridPipeline(config)

        # 3. Set conversion options
        options = ConversionOptions(
            max_pages=10,
            dpi=150,
            include_page_separators=True
        )

        # 4. Convert PDF
        result = await pipeline.convert_pdf(
            pdf_path=Path("document.pdf"),
            output_path=Path("output.md"),
            options=options
        )

        # 5. Process result
        print(f"✓ Converted {result.processed_pages} pages")
        print(f"  Backend: {result.backend_name}")
        print(f"  Output: {result.output_path}")

        # 6. Access page-level results
        for page_result in result.page_results:
            print(f"  Page {page_result.page_num}: {len(page_result.content)} chars")

        return result

    except DoclingHybridError as e:
        print(f"✗ Conversion failed: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(main())
```

---

## See Also

- **[API.md](API.md)** - Comprehensive API documentation with detailed examples
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide for beginners
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Troubleshooting guide
- **[CLAUDE.md](../CLAUDE.md)** - Development context

---

*Last Updated: 2025-11-25*
*Version: Sprint 3 - Production Readiness*
