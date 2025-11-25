# Pipeline Orchestrator

This module coordinates the full PDF-to-Markdown conversion pipeline.

## Overview

**Status:** ✅ Complete
**Purpose:** Coordinate PDF rendering, VLM processing, and result aggregation

The orchestrator is the main entry point for document conversion. It manages the entire workflow from PDF input to Markdown output.

## Module Contents

```
orchestrator/
├── __init__.py         # Package exports
├── pipeline.py         # Main HybridPipeline class
├── models.py           # ConversionOptions, ConversionResult
├── callbacks.py        # Progress callback implementations
├── events.py           # Event type definitions
└── progress.py         # Progress tracking interface
```

## Quick Start

```python
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

# Initialize
config = init_config(Path("configs/local.toml"))
pipeline = HybridPipeline(config)

# Convert PDF
result = await pipeline.convert_pdf(Path("document.pdf"))

# Access results
print(result.markdown)              # Full markdown
print(f"Pages: {result.total_pages}")
print(f"Backend: {result.backend_name}")

# Save to file
result = await pipeline.convert_pdf(
    pdf_path=Path("input.pdf"),
    output_path=Path("output.md")
)
```

## Core Components

### HybridPipeline

Main pipeline class for PDF conversion.

**Initialization:**
```python
pipeline = HybridPipeline(config)
```

**Main Method:**
```python
async def convert_pdf(
    pdf_path: Path,
    output_path: Path | None = None,
    options: ConversionOptions | None = None,
    progress_callback: ProgressCallback | None = None,
) -> ConversionResult:
    """Convert PDF to Markdown.

    Args:
        pdf_path: Path to source PDF
        output_path: Optional output file path
        options: Conversion options (DPI, backend, etc.)
        progress_callback: Optional progress reporting callback

    Returns:
        ConversionResult with markdown and metadata
    """
```

**Pipeline Steps:**
1. Generate document ID
2. Get PDF page count
3. Initialize backend
4. For each page:
   - Render to PNG
   - Send to backend for OCR
   - Collect result
5. Concatenate pages
6. Write output file (if specified)
7. Return ConversionResult

### ConversionOptions

Configuration for a single conversion run.

```python
class ConversionOptions(BaseModel):
    backend_name: str | None = None         # Backend to use (None = default)
    dpi: int | None = None                  # Rendering DPI (None = from config)
    add_page_separators: bool = True        # Add <!-- PAGE N --> comments
    page_separator_format: str = "<!-- PAGE {page_num} -->\n\n"
    max_pages: int | None = None            # Limit pages processed
    start_page: int = 1                     # First page (1-indexed)
```

**Usage:**
```python
from docling_hybrid.orchestrator import ConversionOptions

options = ConversionOptions(
    backend_name="nemotron-openrouter",
    dpi=150,
    max_pages=10,
    add_page_separators=True
)

result = await pipeline.convert_pdf(pdf_path, options=options)
```

### ConversionResult

Output from a conversion run.

```python
class ConversionResult(BaseModel):
    doc_id: str                          # Document identifier
    source_path: Path                    # Source PDF path
    output_path: Path | None             # Output file (if written)
    markdown: str                        # Full markdown content
    page_results: list[PageResult]       # Per-page results
    total_pages: int                     # Total pages in PDF
    processed_pages: int                 # Pages successfully processed
    backend_name: str                    # Backend used
    metadata: dict[str, Any]             # Additional metadata
```

**Metadata includes:**
- `total_time_s`: Total conversion time
- `avg_time_per_page_s`: Average time per page
- `render_time_s`: Total rendering time
- `ocr_time_s`: Total OCR time
- `options_used`: ConversionOptions that were applied

### Progress Callbacks

Track conversion progress in real-time.

**Console Progress:**
```python
from docling_hybrid.orchestrator import ConsoleProgressCallback

callback = ConsoleProgressCallback()
result = await pipeline.convert_pdf(
    pdf_path,
    progress_callback=callback
)
```

**File Progress (JSON logging):**
```python
from docling_hybrid.orchestrator import FileProgressCallback

callback = FileProgressCallback(Path("progress.jsonl"))
result = await pipeline.convert_pdf(
    pdf_path,
    progress_callback=callback
)
```

**Multiple Callbacks:**
```python
from docling_hybrid.orchestrator import CompositeProgressCallback

callback = CompositeProgressCallback([
    ConsoleProgressCallback(),
    FileProgressCallback(Path("progress.jsonl"))
])

result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)
```

**Custom Callback:**
```python
from docling_hybrid.orchestrator import ProgressCallback, ProgressEvent

class MyCallback(ProgressCallback):
    async def on_event(self, event: ProgressEvent):
        if event.type == "page_complete":
            print(f"Page {event.page_num} done!")

result = await pipeline.convert_pdf(pdf_path, progress_callback=MyCallback())
```

## Event Types

The progress system emits events during conversion:

- `ConversionStartEvent`: Conversion started
- `PageStartEvent`: Page rendering/OCR started
- `PageCompleteEvent`: Page successfully processed
- `PageErrorEvent`: Page processing failed
- `ConversionCompleteEvent`: Conversion finished successfully
- `ConversionErrorEvent`: Conversion failed

Each event contains:
- `type`: Event type string
- `timestamp`: When event occurred
- `doc_id`: Document identifier
- Additional event-specific fields

## Common Patterns

### Basic Conversion

```python
from docling_hybrid import init_config, HybridPipeline
from pathlib import Path

config = init_config()
pipeline = HybridPipeline(config)

result = await pipeline.convert_pdf(
    Path("input.pdf"),
    output_path=Path("output.md")
)

print(f"Converted {result.processed_pages}/{result.total_pages} pages")
```

### Partial Document Processing

```python
from docling_hybrid.orchestrator import ConversionOptions

# First 5 pages only
options = ConversionOptions(max_pages=5)
result = await pipeline.convert_pdf(pdf_path, options=options)

# Pages 10-20
options = ConversionOptions(start_page=10, max_pages=11)
result = await pipeline.convert_pdf(pdf_path, options=options)
```

### Lower DPI for Speed

```python
options = ConversionOptions(dpi=100)  # Faster, lower quality
result = await pipeline.convert_pdf(pdf_path, options=options)
```

### With Progress Reporting

```python
from docling_hybrid.orchestrator import ConsoleProgressCallback

callback = ConsoleProgressCallback()
result = await pipeline.convert_pdf(
    pdf_path,
    progress_callback=callback
)
```

### Error Handling

```python
from docling_hybrid.common.errors import (
    ValidationError,
    BackendError,
    RenderingError,
)

try:
    result = await pipeline.convert_pdf(pdf_path)
except ValidationError as e:
    logger.error("invalid_input", **e.details)
except BackendError as e:
    logger.error("backend_failed", backend=e.backend_name)
except RenderingError as e:
    logger.error("rendering_failed", **e.details)
```

### Accessing Per-Page Results

```python
result = await pipeline.convert_pdf(pdf_path)

for page_result in result.page_results:
    print(f"Page {page_result.page_num}:")
    print(f"  Content length: {len(page_result.content)} chars")
    print(f"  Backend: {page_result.backend_name}")
    print(f"  Metadata: {page_result.metadata}")
```

## Configuration

Pipeline behavior is controlled by the Config object:

```toml
[resources]
max_workers = 8              # Concurrent page processing
page_render_dpi = 200        # Default DPI
http_timeout_s = 120         # Backend timeout
http_retry_attempts = 3      # Retry attempts

[backends]
default = "nemotron-openrouter"  # Default backend
```

## Performance

**Typical Performance (200 DPI, Nemotron backend):**
- Simple text page: 3-5s
- Complex diagrams: 5-10s
- Tables: 8-15s

**Optimization:**
- Lower DPI: Faster rendering, smaller images
- Reduce max_workers: Lower memory usage
- Use local backends: Lower latency

## Testing

```bash
# Unit tests
pytest tests/unit/test_pipeline.py -v
pytest tests/unit/orchestrator/ -v

# Integration tests
pytest tests/integration/test_pipeline_integration.py -v
pytest tests/integration/test_pipeline_e2e.py -v
```

## See Also

- [../README.md](../README.md) - Package overview
- [../backends/README.md](../backends/README.md) - OCR backends
- [../renderer/README.md](../renderer/README.md) - PDF rendering
- [../../CLAUDE.md](../../CLAUDE.md) - Master development context
