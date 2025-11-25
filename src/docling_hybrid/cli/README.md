# Command-Line Interface

This module provides the `docling-hybrid-ocr` CLI tool for PDF conversion.

## Overview

**Status:** ✅ Complete
**Purpose:** User-friendly command-line interface using Typer and Rich

The CLI provides an easy way to convert PDFs without writing Python code.

## Module Contents

```
cli/
├── __init__.py            # Package exports
├── main.py                # Main CLI app with Typer
├── batch.py               # Batch processing commands
└── progress_display.py    # Rich progress bars and UI
```

## Commands

### `convert` - Convert PDF to Markdown

```bash
# Basic usage
docling-hybrid-ocr convert document.pdf

# Specify output file
docling-hybrid-ocr convert input.pdf -o output.md

# Use specific backend
docling-hybrid-ocr convert doc.pdf --backend nemotron-openrouter

# Lower DPI for speed
docling-hybrid-ocr convert doc.pdf --dpi 150

# Limit pages
docling-hybrid-ocr convert doc.pdf --max-pages 5

# Start from specific page
docling-hybrid-ocr convert doc.pdf --start-page 10 --max-pages 5

# Reduce concurrency
docling-hybrid-ocr convert doc.pdf --max-workers 2

# Verbose output
docling-hybrid-ocr convert doc.pdf --verbose
```

### `batch` - Batch process multiple PDFs

```bash
# Convert all PDFs in directory
docling-hybrid-ocr batch --input-dir ./pdfs --output-dir ./markdown

# With glob pattern
docling-hybrid-ocr batch --input-dir ./pdfs --pattern "*.pdf"

# Parallel processing
docling-hybrid-ocr batch --input-dir ./pdfs --max-workers 4
```

### `backends` - List available backends

```bash
docling-hybrid-ocr backends
```

Output:
```
Available OCR Backends:
  ✓ nemotron-openrouter  (default)
  ✓ deepseek-vllm
  ○ deepseek-mlx
```

### `info` - Show system information

```bash
docling-hybrid-ocr info
```

Output shows:
- Version
- Configuration file location
- Default backend
- Resource settings (DPI, workers, etc.)
- System resources

### `--help` - Get help

```bash
docling-hybrid-ocr --help
docling-hybrid-ocr convert --help
```

## Options

### Global Options
- `--config PATH`: Config file path
- `--log-level LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `--version`: Show version

### Convert Options
- `-o, --output PATH`: Output file path
- `--backend NAME`: Backend to use
- `--dpi INT`: Rendering DPI (72-600)
- `--max-pages INT`: Maximum pages to process
- `--start-page INT`: First page to process (1-indexed)
- `--max-workers INT`: Concurrent workers
- `--no-page-separators`: Disable page separator comments
- `--verbose`: Enable verbose output

## Examples

**Convert single PDF:**
```bash
docling-hybrid-ocr convert report.pdf -o report.md
```

**Quick preview (first 3 pages):**
```bash
docling-hybrid-ocr convert long-document.pdf --max-pages 3
```

**Low memory mode:**
```bash
docling-hybrid-ocr convert huge.pdf --dpi 100 --max-workers 1
```

**Batch convert:**
```bash
docling-hybrid-ocr batch --input-dir ./input --output-dir ./output
```

## Output

The CLI uses Rich for formatted output:
- **Progress bars** for conversion
- **Colored status** messages
- **Tables** for listings
- **Panels** for results

## Environment Variables

```bash
# Config file
export DOCLING_HYBRID_CONFIG=configs/local.toml

# Log level
export DOCLING_HYBRID_LOG_LEVEL=DEBUG

# API keys
export OPENROUTER_API_KEY=sk-...
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Validation error
- `4`: Backend error
- `5`: Rendering error

## See Also

- [../README.md](../README.md) - Package overview
- [../../CLAUDE.md](../../CLAUDE.md) - Master context
