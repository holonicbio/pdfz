# Docling Hybrid OCR - Source Code

This is the main source code directory for the Docling Hybrid OCR system, a PDF-to-Markdown conversion tool that combines PDF rendering with Vision-Language Model (VLM) backends for intelligent OCR.

## Package Overview

**Version:** 0.1.0
**Python Package:** `docling_hybrid`
**Entry Point:** `docling-hybrid-ocr` CLI command

## Architecture

The package is organized into specialized modules, each handling a specific aspect of the PDF-to-Markdown conversion pipeline:

```
src/docling_hybrid/
├── __init__.py              # Package exports, version info
├── common/                  # ✅ Shared utilities and configuration
├── backends/                # ✅ OCR/VLM backend implementations
├── renderer/                # ✅ PDF page rendering
├── orchestrator/            # ✅ Conversion pipeline coordination
├── cli/                     # ✅ Command-line interface
├── blocks/                  # ○ Block-level processing (future)
├── exporters/               # ○ Multi-format export (future)
└── eval/                    # ○ Evaluation framework (future)
```

**Legend:**
✅ = Implemented
○ = Stub/Planned for future phases

## Quick Start

### Python API

```python
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

# Initialize with config
config = init_config(Path("configs/local.toml"))

# Create pipeline
pipeline = HybridPipeline(config)

# Convert PDF
result = await pipeline.convert_pdf(Path("document.pdf"))

# Access results
print(result.markdown)              # Full document markdown
print(f"Pages: {result.total_pages}")
print(f"Backend: {result.backend_name}")

# Per-page results
for page_result in result.page_results:
    print(f"Page {page_result.page_num}: {len(page_result.content)} chars")
```

### CLI Usage

```bash
# Convert a PDF
docling-hybrid-ocr convert document.pdf

# Specify output file
docling-hybrid-ocr convert input.pdf -o output.md

# Use specific backend
docling-hybrid-ocr convert doc.pdf --backend nemotron-openrouter

# Limit pages and DPI
docling-hybrid-ocr convert doc.pdf --max-pages 5 --dpi 150

# List available backends
docling-hybrid-ocr backends

# Show system info
docling-hybrid-ocr info
```

## Module Descriptions

### [common/](./common/README.md)
**Purpose:** Shared utilities used across all components
**Status:** ✅ Complete

Core functionality:
- **Configuration:** Layered config system (env → file → defaults)
- **Models:** Pydantic data models for type safety
- **Logging:** Structured logging with context binding
- **IDs:** Unique identifier generation
- **Errors:** Custom exception hierarchy
- **Health:** System health monitoring
- **Retry:** Exponential backoff retry logic

### [backends/](./backends/README.md)
**Purpose:** OCR/VLM backend implementations
**Status:** ✅ Core complete, stubs for future backends

Implements pluggable backend architecture:
- **base.py:** Abstract `OcrVlmBackend` interface
- **factory.py:** Backend registration and creation
- **openrouter_nemotron.py:** ✅ Full OpenRouter/Nemotron implementation
- **deepseek_vllm.py:** ✅ DeepSeek vLLM implementation
- **deepseek_vllm_stub.py:** ○ Stub for local vLLM deployment
- **deepseek_mlx_stub.py:** ○ Stub for MLX (Apple Silicon) deployment
- **fallback.py:** ✅ Multi-backend fallback chain
- **health.py:** ✅ Backend health checking

### [renderer/](./renderer/README.md)
**Purpose:** PDF page rendering to images
**Status:** ✅ Complete

Core functions:
- `render_page_to_png_bytes()` - Render single page to PNG
- `get_page_count()` - Get total page count from PDF
- Uses pypdfium2 for fast, reliable rendering

### [orchestrator/](./orchestrator/README.md)
**Purpose:** Conversion pipeline coordination
**Status:** ✅ Complete

Components:
- **pipeline.py:** Main `HybridPipeline` class
- **models.py:** `ConversionOptions`, `ConversionResult`
- **callbacks.py:** Event callback system
- **events.py:** Event type definitions
- **progress.py:** Progress tracking

Handles:
- Document ID generation
- Page rendering orchestration
- Backend coordination
- Error handling and recovery
- Progress reporting

### [cli/](./cli/README.md)
**Purpose:** Command-line interface
**Status:** ✅ Complete

Commands:
- `convert` - Convert PDF to Markdown
- `backends` - List available backends
- `info` - Show system information
- `batch` - Batch process multiple PDFs

Features:
- Rich console output
- Progress bars
- Error reporting
- Configuration override via flags

### [blocks/](./blocks/README.md)
**Purpose:** Block-level document processing
**Status:** ○ Stub - Future phase

Planned features:
- Extract document blocks (text, tables, images)
- Block classification
- Structure preservation

### [exporters/](./exporters/README.md)
**Purpose:** Multi-format export
**Status:** ○ Stub - Future phase

Planned formats:
- Markdown (baseline)
- Docling JSON
- HTML
- LaTeX

### [eval/](./eval/README.md)
**Purpose:** Evaluation and benchmarking
**Status:** ○ Stub - Future phase

Planned features:
- Accuracy metrics
- Performance benchmarks
- Quality evaluation

## Data Flow

```
┌─────────────┐
│  PDF File   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│          HybridPipeline                 │
│  1. Generate doc_id                     │
│  2. Get page count                      │
│  3. Initialize backend                  │
└──────┬──────────────────────────────────┘
       │
       ▼ (for each page)
┌─────────────────────────────────────────┐
│     renderer.render_page_to_png_bytes() │
│          → PNG image bytes              │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  backend.page_to_markdown()             │
│    → Markdown string                    │
│    → PageResult metadata                │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Concatenate all pages                  │
│    → Full markdown document             │
│    → ConversionResult                   │
└─────────────────────────────────────────┘
```

## Key Concepts

### Backend Abstraction
All backends implement the `OcrVlmBackend` abstract base class:

```python
class OcrVlmBackend(ABC):
    @abstractmethod
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str
    ) -> str:
        """Convert a page image to markdown."""
        pass
```

This allows seamless switching between backends without changing pipeline code.

### Configuration Layering
Configuration is loaded in priority order:
1. Environment variables (highest priority)
2. Config file specified by `DOCLING_HYBRID_CONFIG`
3. Default values from `configs/default.toml`

### Async Processing
The entire pipeline is async to support:
- Concurrent page processing
- Non-blocking HTTP calls
- Better resource utilization

### Structured Logging
All components use structured logging:

```python
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)
logger.info("page_rendered", page_num=1, doc_id="doc-123", size_kb=156)
```

## Development Patterns

### Adding a New Backend

1. Create backend class inheriting from `OcrVlmBackend`
2. Implement `page_to_markdown()` method
3. Register in factory:
   ```python
   from docling_hybrid.backends.factory import register_backend

   register_backend("my-backend", MyBackend)
   ```
4. Add configuration in TOML:
   ```toml
   [[backends.candidates]]
   name = "my-backend"
   model = "provider/model-name"
   base_url = "https://api.example.com"
   ```

### Error Handling

Use the custom exception hierarchy:

```python
from docling_hybrid.common.errors import (
    DoclingHybridError,      # Base exception
    ConfigurationError,      # Config issues
    BackendError,            # Backend failures
    RenderingError,          # Rendering failures
    ValidationError,         # Data validation
)
```

### Testing

Tests are organized by component:
- Unit tests: `tests/unit/<component>/`
- Integration tests: `tests/integration/`
- Benchmarks: `tests/benchmarks/`

Run tests:
```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit -v

# Specific component
pytest tests/unit/backends -v
```

## Dependencies

### Core Dependencies
- **pypdfium2** - Fast PDF rendering
- **aiohttp** - Async HTTP client
- **pydantic** - Data validation
- **typer** - CLI framework
- **rich** - Terminal formatting
- **structlog** - Structured logging
- **tomli** - TOML parsing

### Optional Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-mock** - Mocking utilities
- **ruff** - Linting
- **mypy** - Type checking

## Environment Variables

### Required
```bash
OPENROUTER_API_KEY=sk-...    # OpenRouter API key (for nemotron backend)
```

### Optional
```bash
DOCLING_HYBRID_CONFIG=configs/local.toml  # Config file path
DOCLING_HYBRID_LOG_LEVEL=DEBUG            # Log level
DOCLING_HYBRID_MAX_WORKERS=2              # Concurrent workers
DOCLING_HYBRID_DEFAULT_BACKEND=nemotron-openrouter
```

## Performance Considerations

### Memory Usage
- Each page rendering: ~5-20 MB (depends on DPI)
- Each backend request: ~1-5 MB
- For 12GB RAM systems: use `configs/local.toml` with max_workers=2

### Throughput
- Rendering: ~500ms per page (DPI 150)
- VLM inference: ~2-10s per page (depends on backend)
- Total: ~3-15s per page with async processing

### Optimization Tips
1. **Lower DPI** for faster rendering: `--dpi 100`
2. **Reduce workers** for lower memory: `--max-workers 1`
3. **Use local backends** for faster inference (future)
4. **Batch processing** for multiple documents

## Troubleshooting

### Import Issues
```python
# Correct import pattern
from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.common import get_config, generate_id
from docling_hybrid.backends import make_backend

# Incorrect - don't import internals directly
from docling_hybrid.orchestrator.pipeline import HybridPipeline  # Avoid
```

### Common Errors

**"Missing OPENROUTER_API_KEY"**
```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

**"Backend timeout"**
- Check network connection
- Try increasing timeout in config
- Use lower DPI for smaller images

**"Out of memory"**
```bash
# Use local config (reduced resources)
export DOCLING_HYBRID_CONFIG=configs/local.toml
```

## See Also

- [CLAUDE.md](../../CLAUDE.md) - Master development context
- [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) - Detailed architecture
- [docs/API.md](../../docs/API.md) - Complete API reference
- [docs/TROUBLESHOOTING.md](../../docs/TROUBLESHOOTING.md) - Comprehensive troubleshooting

## Contributing

When adding new features:
1. Follow existing patterns (async, structured logging, error handling)
2. Add comprehensive docstrings
3. Write unit tests
4. Update relevant README files
5. Update CLAUDE.md if architecture changes
