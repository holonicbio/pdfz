# Docling Hybrid OCR

Convert PDFs to Markdown using Vision-Language Models (VLMs).

## Overview

Docling Hybrid OCR is a PDF-to-Markdown conversion system that combines:
- **pypdfium2** for fast PDF page rendering
- **Vision-Language Models** for intelligent text extraction
- **Pluggable backend architecture** for multiple VLM providers

The system extracts text, tables, formulas, and structure from PDF documents, producing clean Markdown output.

## Features

- 📄 **Page-level OCR** using state-of-the-art VLMs
- 🔌 **Pluggable backends** - OpenRouter/Nemotron (working), DeepSeek (coming soon)
- ⚡ **Async processing** for better performance
- 🛠️ **Resource-aware** - works on 12GB RAM machines
- 📝 **Structured logging** for debugging and training data

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr

# Run setup script
./scripts/setup.sh

# Activate environment
source .venv/bin/activate

# Set your API key
export OPENROUTER_API_KEY=your-key-here
# Or add to .env.local
```

### Basic Usage

```bash
# Convert a PDF to Markdown
docling-hybrid-ocr convert document.pdf

# With options
docling-hybrid-ocr convert document.pdf --output output.md --dpi 150

# List available backends
docling-hybrid-ocr backends
```

### Python API

```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

async def main():
    # Initialize configuration
    config = init_config(Path("configs/local.toml"))
    
    # Create pipeline and convert
    pipeline = HybridPipeline(config)
    result = await pipeline.convert_pdf(Path("document.pdf"))
    
    print(result.markdown)

asyncio.run(main())
```

## Configuration

### Environment Variables

```bash
OPENROUTER_API_KEY=sk-...           # Required: Your API key
DOCLING_HYBRID_CONFIG=configs/local.toml  # Optional: Config file path
DOCLING_HYBRID_LOG_LEVEL=DEBUG      # Optional: Logging level
```

### Config Files

- `configs/default.toml` - Production defaults
- `configs/local.toml` - Local development (12GB RAM)
- `configs/test.toml` - Testing

## Backends

| Backend | Status | Description |
|---------|--------|-------------|
| `nemotron-openrouter` | ✅ Working | OpenRouter API with Nemotron-nano-12b-v2-vl |
| `deepseek-vllm` | ○ Stub | DeepSeek-OCR via vLLM (CUDA Linux) |
| `deepseek-mlx` | ○ Stub | DeepSeek-OCR via MLX (macOS) |

## Development

### Setup

```bash
./scripts/setup.sh
source .venv/bin/activate
```

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=src/docling_hybrid
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/docling_hybrid
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Master development context
- **[CONTINUATION.md](CONTINUATION.md)** - Development handoff guide
- **[LOCAL_DEV.md](LOCAL_DEV.md)** - Local development guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture

## Project Structure

```
docling-hybrid-ocr/
├── src/docling_hybrid/    # Source code
│   ├── common/            # Shared utilities
│   ├── backends/          # OCR/VLM backends
│   ├── renderer/          # PDF rendering
│   ├── orchestrator/      # Pipeline coordination
│   └── cli/               # Command-line interface
├── tests/                 # Test suite
├── docs/                  # Documentation
├── configs/               # Configuration files
└── scripts/               # Utility scripts
```

## Requirements

- Python 3.11+
- 12GB RAM (minimum)
- Internet connection (for API backends)

## License

MIT License - see LICENSE file.

## Contributing

See CONTINUATION.md for development priorities and how to contribute.
