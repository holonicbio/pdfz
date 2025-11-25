# Docling Hybrid OCR - Master Development Context

## Table of Contents
- [Project Overview](#project-overview)
- [Architecture Summary](#architecture-summary)
- [Repository Structure](#repository-structure)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Data Models](#data-models)
- [Common Patterns](#common-patterns)
- [Implementation Notes](#implementation-notes)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

### What This Is
Docling Hybrid OCR is a PDF-to-Markdown conversion system that combines:
- **pypdfium2** for PDF page rendering
- **Vision-Language Models (VLMs)** for OCR via pluggable backends
- **Async processing** for concurrent page handling

The system is designed to be extensible, supporting multiple VLM backends (OpenRouter/Nemotron, DeepSeek via vLLM, DeepSeek via MLX) with a unified interface.

### Why It Exists
Traditional OCR often fails on complex documents with tables, formulas, and mixed layouts. Modern VLMs can handle these cases better, but require:
- Image rendering of PDF pages
- API integration with model providers
- Structured output parsing

This project provides a clean abstraction layer to make VLM-based OCR practical and extensible.

### Key Features
- **Page-level OCR** using VLM backends
- **Pluggable backend architecture** for different model providers
- **Async HTTP** for concurrent processing
- **Resource-aware configuration** for constrained environments
- **Structured logging** for debugging and training data

### Current Status
**Version:** 0.1.0  
**Status:** Minimal Core Complete

**What's Complete:**
- ✅ Configuration system (layered: env → file → defaults)
- ✅ Common utilities (IDs, logging, errors, models)
- ✅ Backend abstraction and factory
- ✅ OpenRouter/Nemotron backend (fully implemented)
- ✅ Page renderer (pypdfium2)
- ✅ Orchestrator pipeline
- ✅ CLI (convert, backends, info commands)
- ✅ Unit tests for core components

**What's Stubbed (Phase 2+):**
- ○ DeepSeek vLLM backend
- ○ DeepSeek MLX backend
- ○ Block-level processing
- ○ Multi-format exporters
- ○ Evaluation framework

---

## Architecture Summary

### High-Level Diagram
```
┌────────────────────────────────────────────────────────┐
│                    CLI / Python API                    │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                     Orchestrator                       │
│            (HybridPipeline.convert_pdf)               │
└────────────────────────────────────────────────────────┘
              │                        │
              ▼                        ▼
┌───────────────────────┐   ┌────────────────────────────┐
│     Renderer          │   │    Backend Factory         │
│  (render_page_to_png) │   │     (make_backend)         │
└───────────────────────┘   └────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  Nemotron   │   │  DeepSeek   │   │  DeepSeek   │
            │  (working)  │   │  vLLM(stub) │   │  MLX(stub)  │
            └─────────────┘   └─────────────┘   └─────────────┘
```

### Components Overview

| Component | Location | Status | Purpose |
|-----------|----------|--------|---------|
| Common | `src/docling_hybrid/common/` | ✅ | Config, models, errors, IDs, logging |
| Backends | `src/docling_hybrid/backends/` | ✅/○ | OCR/VLM backend implementations |
| Renderer | `src/docling_hybrid/renderer/` | ✅ | PDF page to PNG rendering |
| Orchestrator | `src/docling_hybrid/orchestrator/` | ✅ | Pipeline coordination |
| CLI | `src/docling_hybrid/cli/` | ✅ | Command-line interface |
| Exporters | `src/docling_hybrid/exporters/` | ○ Stub | Multi-format export |
| Blocks | `src/docling_hybrid/blocks/` | ○ Stub | Block-level processing |
| Eval | `src/docling_hybrid/eval/` | ○ Stub | Evaluation framework |

### Data Flow

```
PDF File → get_page_count() → Loop:
    render_page_to_png_bytes(page_index)
    → PNG bytes
    → backend.page_to_markdown(image, page_num, doc_id)
    → Markdown string
→ Concatenate pages → Write output file
```

---

## Repository Structure

```
docling-hybrid-ocr/
├── src/docling_hybrid/          # Source code
│   ├── __init__.py              # Package exports, version
│   ├── common/                  # Shared utilities
│   │   ├── config.py            # Configuration loading
│   │   ├── models.py            # Pydantic data models
│   │   ├── errors.py            # Exception hierarchy
│   │   ├── ids.py               # ID generation
│   │   └── logging.py           # Structured logging
│   ├── backends/                # OCR/VLM backends
│   │   ├── base.py              # Abstract interface
│   │   ├── factory.py           # Backend factory
│   │   ├── openrouter_nemotron.py  # ✅ Implemented
│   │   ├── deepseek_vllm_stub.py   # ○ Stub
│   │   └── deepseek_mlx_stub.py    # ○ Stub
│   ├── renderer/                # PDF rendering
│   │   └── core.py              # Rendering functions
│   ├── orchestrator/            # Pipeline
│   │   ├── pipeline.py          # HybridPipeline
│   │   └── models.py            # ConversionOptions/Result
│   ├── cli/                     # Command line
│   │   └── main.py              # Typer CLI
│   ├── exporters/               # ○ Extended scope
│   ├── blocks/                  # ○ Extended scope
│   └── eval/                    # ○ Extended scope
├── tests/                       # Test suite
│   ├── conftest.py              # Fixtures
│   └── unit/                    # Unit tests
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # System architecture
│   └── components/              # Component specs
├── configs/                     # Configuration files
│   ├── default.toml             # Production defaults
│   ├── local.toml               # Local dev (12GB RAM)
│   └── test.toml                # Test configuration
├── scripts/                     # Utility scripts
│   ├── setup.sh                 # Installation
│   └── cleanup.sh               # Disk cleanup
├── pyproject.toml               # Package configuration
├── .env.example                 # Environment template
├── CLAUDE.md                    # This file
├── CONTINUATION.md              # Handoff guide
└── LOCAL_DEV.md                 # Local dev guide
```

---

## Configuration

### Configuration Files
- `configs/default.toml` - Production defaults
- `configs/local.toml` - Local development (12GB RAM constraints)
- `.env.local` - Secrets and overrides (create from .env.example)

### Key Settings

```toml
# configs/local.toml (for 12GB RAM)
[resources]
max_workers = 2        # Concurrent pages (reduced from 8)
max_memory_mb = 4096   # Memory limit
page_render_dpi = 150  # Lower DPI (reduced from 200)

[backends]
default = "nemotron-openrouter"
```

### Environment Variables
```bash
# Required
OPENROUTER_API_KEY=sk-...        # Your OpenRouter API key

# Optional overrides
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=DEBUG
DOCLING_HYBRID_MAX_WORKERS=2
```

### Quick Setup: OpenRouter API Key

The easiest way to set up your API key:

```bash
# Create the key file (add to .gitignore, never commit!)
echo 'sk-or-v1-your-key-here' > openrouter_key

# Source the environment setup
source ./scripts/setup_env.sh
```

This reads the key from `openrouter_key` file and exports `OPENROUTER_API_KEY`.

**Optional:** Install git hooks to remind you about environment setup:
```bash
./scripts/install-hooks.sh
```

---

## Development Workflow

### Setup (First Time)
```bash
# Clone and setup
git clone <repo>
cd docling-hybrid-ocr
./scripts/setup.sh

# Activate virtual environment
source .venv/bin/activate

# Set up API key (choose one method):

# Method 1: Using openrouter_key file (recommended)
echo 'sk-or-v1-your-key-here' > openrouter_key
source ./scripts/setup_env.sh

# Method 2: Using .env.local
cp .env.example .env.local
# Edit .env.local with your OPENROUTER_API_KEY
source .env.local
```

### Daily Workflow
```bash
# Activate environment
source .venv/bin/activate
source .env.local

# Run tests
pytest tests/unit -v

# Run CLI
docling-hybrid-ocr convert document.pdf

# Check code quality
ruff check src/
mypy src/docling_hybrid
```

### Testing Strategy

**Level 1: Unit Tests (Fast, No External Deps)**
```bash
pytest tests/unit -v
```

**Level 2: Integration Tests (Mocked HTTP)**
```bash
pytest tests/integration -v
```

**Level 3: Manual Testing (Real API)**
```bash
docling-hybrid-ocr convert sample.pdf --verbose
```

---

## Data Models

### OcrBackendConfig
```python
class OcrBackendConfig(BaseModel):
    name: str              # "nemotron-openrouter"
    model: str             # "nvidia/nemotron-nano-12b-v2-vl:free"
    base_url: str          # "https://openrouter.ai/api/v1/chat/completions"
    api_key: str | None    # From env var usually
    temperature: float     # 0.0 for deterministic
    max_tokens: int        # 8192 default
```

### PageResult
```python
class PageResult(BaseModel):
    page_num: int          # 1-indexed
    doc_id: str            # "doc-a1b2c3d4"
    content: str           # Markdown content
    backend_name: str      # Backend used
    metadata: dict         # Image size, timing, etc.
```

### ConversionResult
```python
class ConversionResult(BaseModel):
    doc_id: str
    source_path: Path
    output_path: Path | None
    markdown: str          # Full document
    page_results: list[PageResult]
    total_pages: int
    processed_pages: int
    backend_name: str
    metadata: dict         # Timing, options used
```

---

## Common Patterns

### Pattern 1: Configuration Loading
```python
from docling_hybrid.common.config import init_config, get_config

# At startup
config = init_config(Path("configs/local.toml"))

# Anywhere else
config = get_config()
value = config.resources.max_workers
```

### Pattern 2: Logging
```python
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)
logger.info("event_name", key1="value1", key2=42)
logger.error("error_event", error=str(e), doc_id=doc_id)
```

### Pattern 3: Backend Usage
```python
from docling_hybrid.backends import make_backend

config = get_config()
backend_config = config.backends.get_backend_config()
backend = make_backend(backend_config)

# Use as context manager
async with backend:
    md = await backend.page_to_markdown(image_bytes, page_num, doc_id)
```

### Pattern 4: Pipeline Usage
```python
from docling_hybrid.orchestrator import HybridPipeline, ConversionOptions

config = get_config()
pipeline = HybridPipeline(config)

options = ConversionOptions(max_pages=5, dpi=150)
result = await pipeline.convert_pdf(pdf_path, options=options)

print(result.markdown)
```

### Pattern 5: Error Handling
```python
from docling_hybrid.common.errors import (
    DoclingHybridError,
    BackendError,
    ConfigurationError,
)

try:
    result = await pipeline.convert_pdf(pdf_path)
except ConfigurationError as e:
    logger.error("config_error", error=str(e))
except BackendError as e:
    logger.error("backend_error", backend=e.backend_name, error=str(e))
except DoclingHybridError as e:
    logger.error("general_error", error=str(e))
```

---

## Implementation Notes

### For Backends
- All methods must be async
- Use `aiohttp` for HTTP calls
- Implement proper timeout handling
- Log all API calls with context
- Handle both string and list content responses

### For Renderer
- Use pypdfium2 for fast rendering
- Default DPI: 200 (150 for local dev)
- Output PNG format (lossless)
- Handle page index validation

### For Orchestrator
- Generate doc_id for each conversion
- Bind logging context (doc_id, pdf path)
- Clear context after processing
- Handle per-page errors gracefully

### For CLI
- Use Typer for argument parsing
- Use Rich for pretty output
- Always show progress/status
- Exit with appropriate codes

---

## Troubleshooting

**Note:** For comprehensive troubleshooting, see **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** which covers installation issues, configuration problems, API errors, memory issues, and more.

### Quick Reference: Common Issues

### Issue: "Missing OPENROUTER_API_KEY"
**Cause:** API key not set  
**Solution:**
```bash
# Add to .env.local
OPENROUTER_API_KEY=your-key-here

# Then load it
source .env.local
```

### Issue: "Out of memory"
**Cause:** Processing too many pages or high DPI  
**Solution:**
```bash
# Use local config
export DOCLING_HYBRID_CONFIG=configs/local.toml

# Or reduce settings
docling-hybrid-ocr convert doc.pdf --dpi 100 --max-pages 5
```

### Issue: "Backend timeout"
**Cause:** VLM API taking too long  
**Solution:**
- Check network connection
- Check OpenRouter status
- Try smaller document or lower DPI

### Issue: "PDF cannot be opened"
**Cause:** Invalid or corrupted PDF  
**Solution:**
- Verify PDF opens in viewer
- Check file permissions
- Try re-downloading/creating PDF

---

## Next Steps

For current development priorities, see:
- **CONTINUATION.md** - What to work on next
- **LOCAL_DEV.md** - Local development constraints

For specific components:
- **docs/ARCHITECTURE.md** - Detailed architecture
- **docs/components/** - Component specifications

For API and usage:
- **docs/API.md** - Complete Python API documentation
- **docs/TROUBLESHOOTING.md** - Comprehensive troubleshooting guide
