# Docling Hybrid OCR - API Documentation

## Overview

This document provides comprehensive API documentation for using Docling Hybrid OCR programmatically in Python applications.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration API](#configuration-api)
- [Backend API](#backend-api)
- [Renderer API](#renderer-api)
- [Pipeline API](#pipeline-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)

---

## Installation

```bash
pip install docling-hybrid-ocr
```

Or for development:

```bash
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr
pip install -e ".[dev]"
```

---

## Quick Start

### Basic PDF Conversion

```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

async def convert_pdf():
    # Initialize configuration
    config = init_config(Path("configs/default.toml"))

    # Create pipeline
    pipeline = HybridPipeline(config)

    # Convert PDF
    result = await pipeline.convert_pdf(
        pdf_path=Path("document.pdf"),
        output_path=Path("output.md")
    )

    print(f"Converted {result.processed_pages} pages")
    print(result.markdown)

# Run the async function
asyncio.run(convert_pdf())
```

### Using Environment Variables

```python
import os
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

# Set API key
os.environ["OPENROUTER_API_KEY"] = "your-key-here"

# Use default config
config = init_config()

async def main():
    pipeline = HybridPipeline(config)
    result = await pipeline.convert_pdf(Path("document.pdf"))
    return result.markdown
```

---

## Configuration API

### Loading Configuration

```python
from pathlib import Path
from docling_hybrid.common.config import init_config, get_config

# Method 1: Load from file
config = init_config(Path("configs/local.toml"))

# Method 2: Load from default location
config = init_config()

# Method 3: Get global config (after init_config)
config = get_config()
```

### Configuration Structure

```python
from docling_hybrid.common.config import Config

config = get_config()

# Access configuration sections
print(config.resources.max_workers)      # 2
print(config.resources.max_memory_mb)    # 4096
print(config.backends.default)           # "nemotron-openrouter"
print(config.logging.level)              # "INFO"
```

### Environment Variable Overrides

Environment variables take precedence over config files:

```python
import os

# Override max workers
os.environ["DOCLING_HYBRID_MAX_WORKERS"] = "4"

# Override log level
os.environ["DOCLING_HYBRID_LOG_LEVEL"] = "DEBUG"

# Override backend
os.environ["DOCLING_HYBRID_DEFAULT_BACKEND"] = "deepseek-vllm"
```

---

## Backend API

### Creating Backends

```python
from docling_hybrid.backends import make_backend, list_backends
from docling_hybrid.common.models import OcrBackendConfig

# Method 1: Use configuration
config = get_config()
backend_config = config.backends.get_backend_config()
backend = make_backend(backend_config)

# Method 2: Create backend config manually
backend_config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.0,
    max_tokens=8192,
)
backend = make_backend(backend_config)

# List available backends
backends = list_backends()
print(backends)  # ['nemotron-openrouter', 'deepseek-vllm', 'deepseek-mlx']
```

### Using Backends Directly

```python
from docling_hybrid.backends import make_backend
from docling_hybrid.renderer import render_page_to_png_bytes

async def ocr_page(pdf_path, page_index):
    # Render page to image
    image_bytes = render_page_to_png_bytes(pdf_path, page_index, dpi=200)

    # Create backend
    backend_config = get_config().backends.get_backend_config()
    backend = make_backend(backend_config)

    # Use context manager for proper cleanup
    async with backend:
        result = await backend.page_to_markdown(
            image_bytes=image_bytes,
            page_num=page_index + 1,
            doc_id="my-doc-123"
        )

    return result
```

### Backend Methods

All backends implement the `OcrVlmBackend` interface:

```python
from docling_hybrid.backends.base import OcrVlmBackend

async def use_backend(backend: OcrVlmBackend, image_bytes: bytes):
    # Convert full page to Markdown
    page_result = await backend.page_to_markdown(
        image_bytes=image_bytes,
        page_num=1,
        doc_id="doc-123"
    )

    # Convert table to Markdown (with metadata)
    table_result = await backend.table_to_markdown(
        image_bytes=image_bytes,
        meta={"page": 1, "bbox": (10, 20, 200, 300)}
    )

    # Convert formula to LaTeX
    formula_result = await backend.formula_to_latex(
        image_bytes=image_bytes,
        meta={"page": 1, "type": "inline"}
    )

    return page_result, table_result, formula_result
```

---

## Renderer API

### Basic Rendering

```python
from pathlib import Path
from docling_hybrid.renderer import (
    render_page_to_png_bytes,
    render_region_to_png_bytes,
    get_page_count,
)

# Get total page count
pdf_path = Path("document.pdf")
total_pages = get_page_count(pdf_path)
print(f"Total pages: {total_pages}")

# Render specific page
image_bytes = render_page_to_png_bytes(
    pdf_path=pdf_path,
    page_index=0,  # 0-indexed
    dpi=200
)

# Save to file
with open("page_0.png", "wb") as f:
    f.write(image_bytes)
```

### Region Rendering

```python
# Render specific region (for block-level processing)
region_bytes = render_region_to_png_bytes(
    pdf_path=pdf_path,
    page_index=0,
    bbox=(100, 100, 400, 300),  # (x1, y1, x2, y2) in PDF coordinates
    dpi=200
)
```

### DPI Selection

```python
# Low DPI for quick preview (faster, smaller files)
preview = render_page_to_png_bytes(pdf_path, 0, dpi=72)

# Medium DPI for development (balanced)
dev = render_page_to_png_bytes(pdf_path, 0, dpi=150)

# High DPI for production (better quality)
prod = render_page_to_png_bytes(pdf_path, 0, dpi=200)

# Very high DPI for detailed documents
detail = render_page_to_png_bytes(pdf_path, 0, dpi=300)
```

---

## Pipeline API

### HybridPipeline

```python
from docling_hybrid.orchestrator import HybridPipeline, ConversionOptions

# Create pipeline
config = get_config()
pipeline = HybridPipeline(config)

# Basic conversion
result = await pipeline.convert_pdf(pdf_path=Path("doc.pdf"))

# With output file
result = await pipeline.convert_pdf(
    pdf_path=Path("doc.pdf"),
    output_path=Path("output.md")
)

# With options
options = ConversionOptions(
    max_pages=5,
    start_page=0,
    dpi=150,
    include_page_separators=True
)
result = await pipeline.convert_pdf(
    pdf_path=Path("doc.pdf"),
    options=options
)
```

### Conversion Options

```python
from docling_hybrid.orchestrator import ConversionOptions

# All available options
options = ConversionOptions(
    max_pages=10,           # Limit pages processed (None = all)
    start_page=0,           # Starting page index (0-indexed)
    dpi=200,                # Rendering DPI
    include_page_separators=True,  # Add <!-- PAGE N --> comments
)
```

### Conversion Result

```python
from docling_hybrid.orchestrator import ConversionResult

result = await pipeline.convert_pdf(pdf_path)

# Access result properties
print(result.doc_id)              # "doc-abc123"
print(result.source_path)         # Path("document.pdf")
print(result.output_path)         # Path("output.md") or None
print(result.markdown)            # Full Markdown content
print(result.total_pages)         # 10
print(result.processed_pages)     # 10
print(result.backend_name)        # "nemotron-openrouter"

# Access individual page results
for page_result in result.page_results:
    print(f"Page {page_result.page_num}: {len(page_result.content)} chars")
```

### Page Results

```python
from docling_hybrid.common.models import PageResult

page_result = result.page_results[0]

print(page_result.page_num)       # 1 (1-indexed)
print(page_result.doc_id)         # "doc-abc123"
print(page_result.content)        # Markdown content for page
print(page_result.backend_name)   # "nemotron-openrouter"
print(page_result.metadata)       # {"image_size": [1200, 1600], ...}
```

---

## Data Models

All data models use Pydantic for validation.

### OcrBackendConfig

```python
from docling_hybrid.common.models import OcrBackendConfig

config = OcrBackendConfig(
    name="nemotron-openrouter",
    model="nvidia/nemotron-nano-12b-v2-vl:free",
    base_url="https://openrouter.ai/api/v1/chat/completions",
    api_key="your-key",
    temperature=0.0,
    max_tokens=8192,
)
```

### PageResult

```python
from docling_hybrid.common.models import PageResult

result = PageResult(
    page_num=1,
    doc_id="doc-123",
    content="# Page Content\n\nText here...",
    backend_name="nemotron-openrouter",
    metadata={"processing_time_s": 2.5}
)
```

### ConversionResult

```python
from docling_hybrid.orchestrator.models import ConversionResult

result = ConversionResult(
    doc_id="doc-123",
    source_path=Path("input.pdf"),
    output_path=Path("output.md"),
    markdown="# Full Document\n\n...",
    page_results=[page_result1, page_result2],
    total_pages=10,
    processed_pages=10,
    backend_name="nemotron-openrouter",
    metadata={"total_time_s": 25.0}
)
```

---

## Error Handling

### Exception Hierarchy

```python
from docling_hybrid.common.errors import (
    DoclingHybridError,           # Base exception
    ConfigurationError,           # Configuration issues
    BackendError,                 # Backend issues
    BackendConnectionError,       # Network/connection issues
    BackendTimeoutError,          # Request timeout
    BackendResponseError,         # Invalid response
    RenderingError,               # PDF rendering issues
    ValidationError,              # Input validation issues
)
```

### Basic Error Handling

```python
from docling_hybrid.common.errors import (
    ConfigurationError,
    BackendError,
    RenderingError,
)

async def safe_conversion(pdf_path):
    try:
        config = init_config()
        pipeline = HybridPipeline(config)
        result = await pipeline.convert_pdf(pdf_path)
        return result

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("Check your .env file and config.toml")
        return None

    except RenderingError as e:
        print(f"PDF rendering error: {e}")
        print("The PDF may be corrupted or invalid")
        return None

    except BackendError as e:
        print(f"Backend error: {e}")
        print(f"Backend: {e.backend_name}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Per-Page Error Handling

```python
# Skip failed pages
options = ConversionOptions(on_page_error="skip")
result = await pipeline.convert_pdf(pdf_path, options=options)

# Show placeholder for failed pages
options = ConversionOptions(on_page_error="placeholder")
result = await pipeline.convert_pdf(pdf_path, options=options)

# Raise on first error (default)
options = ConversionOptions(on_page_error="raise")
result = await pipeline.convert_pdf(pdf_path, options=options)
```

---

## Advanced Usage

### Custom Backend Implementation

```python
from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.backends import register_backend

class MyCustomBackend(OcrVlmBackend):
    def __init__(self, config):
        super().__init__(config)
        self.name = "my-backend"

    async def __aenter__(self):
        # Initialize resources
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup resources
        pass

    async def page_to_markdown(self, image_bytes, page_num, doc_id):
        # Your implementation
        return "# Custom result"

    async def table_to_markdown(self, image_bytes, meta):
        return "| A | B |\n|---|---|\n| 1 | 2 |"

    async def formula_to_latex(self, image_bytes, meta):
        return "E = mc^2"

# Register custom backend
register_backend("my-backend", MyCustomBackend)

# Use it
config = OcrBackendConfig(name="my-backend")
backend = make_backend(config)
```

### Batch Processing

```python
from pathlib import Path
from typing import List

async def batch_convert(pdf_paths: List[Path], output_dir: Path):
    config = get_config()
    pipeline = HybridPipeline(config)

    results = []
    for pdf_path in pdf_paths:
        output_path = output_dir / f"{pdf_path.stem}.md"

        try:
            result = await pipeline.convert_pdf(
                pdf_path=pdf_path,
                output_path=output_path
            )
            results.append((pdf_path, result))
            print(f"✓ {pdf_path.name}: {result.processed_pages} pages")

        except Exception as e:
            print(f"✗ {pdf_path.name}: {e}")
            results.append((pdf_path, None))

    return results

# Usage
pdf_files = list(Path("pdfs").glob("*.pdf"))
results = await batch_convert(pdf_files, Path("output"))
```

### Progress Monitoring

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

async def convert_with_progress(pdf_path: Path):
    config = get_config()
    pipeline = HybridPipeline(config)

    # Get page count first
    from docling_hybrid.renderer import get_page_count
    total_pages = get_page_count(pdf_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task(
            f"Converting {total_pages} pages...",
            total=total_pages
        )

        result = await pipeline.convert_pdf(pdf_path)
        progress.update(task, completed=total_pages)

    return result
```

### Selective Backend Usage

```python
async def use_specific_backend(pdf_path: Path, backend_name: str):
    config = get_config()

    # Override backend in config
    backend_config = config.backends.get_backend_config(backend_name)
    backend = make_backend(backend_config)

    # Create pipeline with specific backend
    pipeline = HybridPipeline(config, backend=backend)

    result = await pipeline.convert_pdf(pdf_path)
    return result

# Use specific backend
result = await use_specific_backend(
    Path("document.pdf"),
    "deepseek-vllm"
)
```

### Logging Configuration

```python
from docling_hybrid.common.logging import get_logger
import logging

# Get module logger
logger = get_logger(__name__)

# Use structured logging
logger.info(
    "conversion_started",
    pdf_path="/path/to/doc.pdf",
    total_pages=10,
    backend="nemotron"
)

# Set log level programmatically
import os
os.environ["DOCLING_HYBRID_LOG_LEVEL"] = "DEBUG"

# Re-initialize config to apply new log level
config = init_config()
```

---

## Performance Tips

### Memory Optimization

```python
# Use lower DPI for large PDFs
options = ConversionOptions(dpi=150)

# Process in batches
options = ConversionOptions(max_pages=10)

# Clear intermediate data
import gc
for i in range(0, total_pages, 10):
    options = ConversionOptions(start_page=i, max_pages=10)
    result = await pipeline.convert_pdf(pdf_path, options=options)
    # Process result
    del result
    gc.collect()
```

### Concurrent Processing

The pipeline automatically processes pages concurrently based on `max_workers` configuration:

```python
# In config file (configs/local.toml)
# [resources]
# max_workers = 4

# Or via environment
os.environ["DOCLING_HYBRID_MAX_WORKERS"] = "4"
```

---

## API Reference Summary

### Main Exports

```python
from docling_hybrid import (
    __version__,
    init_config,
    get_config,
    HybridPipeline,
)

from docling_hybrid.backends import (
    make_backend,
    list_backends,
    register_backend,
)

from docling_hybrid.renderer import (
    render_page_to_png_bytes,
    render_region_to_png_bytes,
    get_page_count,
)

from docling_hybrid.orchestrator import (
    HybridPipeline,
    ConversionOptions,
    ConversionResult,
)

from docling_hybrid.common.models import (
    OcrBackendConfig,
    PageResult,
)

from docling_hybrid.common.errors import (
    DoclingHybridError,
    ConfigurationError,
    BackendError,
    RenderingError,
)
```

---

## Next Steps

- See [CLAUDE.md](../CLAUDE.md) for development context
- See [CLI_USAGE.md](guides/CLI_USAGE.md) for command-line usage
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [examples/](../examples/) for more code examples
