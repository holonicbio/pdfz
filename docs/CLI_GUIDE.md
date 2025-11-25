# CLI Guide

Complete guide to using the Docling Hybrid OCR command-line interface.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [convert](#convert)
  - [convert-batch](#convert-batch)
  - [backends](#backends)
  - [info](#info)
- [Common Options](#common-options)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Installation

Install docling-hybrid-ocr using pip:

```bash
pip install docling-hybrid-ocr
```

Or install from source:

```bash
git clone <repository-url>
cd docling-hybrid-ocr
pip install -e .
```

Verify installation:

```bash
docling-hybrid-ocr --version
```

---

## Quick Start

### 1. Set up API key

For OpenRouter backend (default):

```bash
export OPENROUTER_API_KEY=your-key-here
```

Or add to `.env.local`:

```bash
echo "OPENROUTER_API_KEY=your-key-here" >> .env.local
source .env.local
```

### 2. Convert a single PDF

```bash
docling-hybrid-ocr convert document.pdf
```

Output will be saved as `document.nemotron.md` in the same directory.

### 3. Convert multiple PDFs

```bash
docling-hybrid-ocr convert-batch ./pdfs/ --output-dir ./output/
```

All PDFs in the `./pdfs/` directory will be converted to Markdown in `./output/`.

---

## Commands

### convert

Convert a single PDF file to Markdown.

**Usage:**

```bash
docling-hybrid-ocr convert [OPTIONS] PDF_PATH
```

**Arguments:**

- `PDF_PATH`: Path to the PDF file to convert (required)

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output Markdown file path | `<input>.nemotron.md` |
| `--backend` | `-b` | Backend to use | From config |
| `--config` | `-c` | Configuration file path | `configs/default.toml` |
| `--dpi` | | Page rendering DPI (72-600) | From config (200) |
| `--max-pages` | `-n` | Maximum pages to process | All pages |
| `--start-page` | `-s` | First page to process (1-indexed) | 1 |
| `--no-separators` | | Don't add page separator comments | False |
| `--verbose` | `-V` | Enable verbose logging | False |
| `--help` | | Show help message | |

**Examples:**

```bash
# Basic conversion
docling-hybrid-ocr convert document.pdf

# Specify output file
docling-hybrid-ocr convert document.pdf -o output.md

# Use specific backend
docling-hybrid-ocr convert document.pdf --backend nemotron-openrouter

# Process only first 5 pages
docling-hybrid-ocr convert document.pdf --max-pages 5

# Start from page 10
docling-hybrid-ocr convert document.pdf --start-page 10

# Lower DPI for faster processing
docling-hybrid-ocr convert document.pdf --dpi 100

# Use custom config
docling-hybrid-ocr convert document.pdf --config configs/local.toml

# Verbose output for debugging
docling-hybrid-ocr convert document.pdf --verbose
```

**Output:**

The command displays:
- Progress bar with page processing status
- Time elapsed
- Final summary with:
  - Pages processed
  - Backend used
  - Output file path
  - Total time

**Exit codes:**
- `0`: Success
- `1`: Error occurred
- `130`: Cancelled by user (Ctrl+C)

---

### convert-batch

Convert multiple PDF files in batch mode.

**Usage:**

```bash
docling-hybrid-ocr convert-batch [OPTIONS] INPUT_DIR
```

**Arguments:**

- `INPUT_DIR`: Directory containing PDF files (required)

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output-dir` | `-o` | Output directory for converted files | `./output` |
| `--backend` | `-b` | Backend to use | From config |
| `--config` | `-c` | Configuration file path | `configs/default.toml` |
| `--parallel` | `-p` | Number of files to process in parallel (1-16) | 4 |
| `--recursive` | `-r` | Search subdirectories recursively | False |
| `--pattern` | | Glob pattern for matching files | `*.pdf` |
| `--dpi` | | Page rendering DPI (72-600) | From config (200) |
| `--max-pages` | `-n` | Maximum pages per file | All pages |
| `--verbose` | `-V` | Enable verbose logging | False |
| `--help` | | Show help message | |

**Examples:**

```bash
# Convert all PDFs in a directory
docling-hybrid-ocr convert-batch ./pdfs/

# Specify output directory
docling-hybrid-ocr convert-batch ./pdfs/ --output-dir ./markdown/

# Recursive search
docling-hybrid-ocr convert-batch ./documents/ -r

# Custom pattern
docling-hybrid-ocr convert-batch ./reports/ --pattern "report_*.pdf"

# Control parallelism
docling-hybrid-ocr convert-batch ./pdfs/ --parallel 8

# Limit pages per file (useful for testing)
docling-hybrid-ocr convert-batch ./pdfs/ --max-pages 3

# Combine options
docling-hybrid-ocr convert-batch ./docs/ \
    -r \
    --pattern "*.pdf" \
    --output-dir ./output/ \
    --parallel 6 \
    --dpi 150
```

**Output:**

The command displays:
- Files found
- Progress for each file
- Summary table with:
  - Total files
  - Successful conversions
  - Failed conversions
  - Success rate
  - Time elapsed
- List of failed files (if any)

**Exit codes:**
- `0`: All files converted successfully
- `1`: One or more files failed
- `130`: Cancelled by user (Ctrl+C)

---

### backends

List available OCR/VLM backends.

**Usage:**

```bash
docling-hybrid-ocr backends
```

**Output:**

Displays a table showing:
- Backend name
- Implementation status
- Description

**Example:**

```bash
$ docling-hybrid-ocr backends

                 Available Backends
┌─────────────────────┬─────────────────┬────────────────────────┐
│ Name                │ Status          │ Description            │
├─────────────────────┼─────────────────┼────────────────────────┤
│ nemotron-openrouter │ ✓ Implemented   │ OpenRouter API with... │
│ deepseek-vllm       │ ✓ Implemented   │ DeepSeek-OCR via vLLM  │
│ deepseek-mlx        │ ○ Stub          │ DeepSeek-OCR via MLX   │
└─────────────────────┴─────────────────┴────────────────────────┘

Use --backend <name> with the convert command to select a backend.
```

---

### info

Show system information and configuration.

**Usage:**

```bash
docling-hybrid-ocr info
```

**Output:**

Displays:
- Version
- API key status
- Configuration file path
- Setup instructions

**Example:**

```bash
$ docling-hybrid-ocr info

Docling Hybrid OCR
Version: 0.1.0

OPENROUTER_API_KEY: ✓ Set
Config file: Using defaults

Set OPENROUTER_API_KEY environment variable to use the Nemotron backend.
```

---

## Common Options

### Configuration File

Override default configuration:

```bash
docling-hybrid-ocr convert document.pdf --config configs/local.toml
```

Configuration files use TOML format. See [Configuration Guide](../CLAUDE.md#configuration) for details.

### Backend Selection

Choose a specific backend:

```bash
docling-hybrid-ocr convert document.pdf --backend nemotron-openrouter
```

Available backends:
- `nemotron-openrouter`: OpenRouter API with Nemotron model (default)
- `deepseek-vllm`: Local vLLM server with DeepSeek model
- `deepseek-mlx`: Local MLX server with DeepSeek model (macOS only)

### DPI Settings

Control image quality vs. speed:

```bash
# High quality (slower, more accurate)
docling-hybrid-ocr convert document.pdf --dpi 300

# Medium quality (balanced)
docling-hybrid-ocr convert document.pdf --dpi 150

# Low quality (faster, less accurate)
docling-hybrid-ocr convert document.pdf --dpi 100
```

**Recommendations:**
- **Production**: 200-300 DPI
- **Development/Testing**: 100-150 DPI
- **Low memory systems**: 72-100 DPI

### Verbose Mode

Enable detailed logging:

```bash
docling-hybrid-ocr convert document.pdf --verbose
```

Shows:
- Configuration loading
- PDF parsing details
- Page-by-page processing
- API calls and responses
- Timing information

Useful for:
- Debugging issues
- Understanding performance
- Verifying configuration

---

## Examples

### Example 1: Convert a research paper

```bash
docling-hybrid-ocr convert research_paper.pdf \
    --output research_paper.md \
    --dpi 200 \
    --verbose
```

### Example 2: Convert first 10 pages only

```bash
docling-hybrid-ocr convert large_document.pdf \
    --max-pages 10 \
    --output preview.md
```

### Example 3: Batch convert all reports

```bash
docling-hybrid-ocr convert-batch ./monthly_reports/ \
    --output-dir ./markdown_reports/ \
    --pattern "report_*.pdf" \
    --parallel 6
```

### Example 4: Convert with low resource settings

```bash
docling-hybrid-ocr convert document.pdf \
    --config configs/local.toml \
    --dpi 100 \
    --max-pages 5
```

### Example 5: Recursive batch conversion

```bash
docling-hybrid-ocr convert-batch ./documents/ \
    -r \
    --output-dir ./converted/ \
    --parallel 4 \
    --pattern "*.pdf"
```

### Example 6: Use local vLLM backend

```bash
# Start vLLM server first
# vllm serve deepseek-ai/deepseek-vl-7b-chat --port 8000

docling-hybrid-ocr convert document.pdf \
    --backend deepseek-vllm \
    --config configs/vllm.toml
```

---

## Troubleshooting

### Issue: "Missing OPENROUTER_API_KEY"

**Solution:**

```bash
export OPENROUTER_API_KEY=your-key-here
```

Or add to `.env.local` and source it.

Get a free API key at: https://openrouter.ai/keys

---

### Issue: "Out of memory"

**Symptoms:**
- Process crashes
- System becomes unresponsive
- "MemoryError" in logs

**Solutions:**

1. Use lower DPI:
   ```bash
   docling-hybrid-ocr convert document.pdf --dpi 100
   ```

2. Process fewer pages:
   ```bash
   docling-hybrid-ocr convert document.pdf --max-pages 5
   ```

3. Use local config (optimized for 12GB RAM):
   ```bash
   docling-hybrid-ocr convert document.pdf --config configs/local.toml
   ```

4. Reduce parallel workers in batch mode:
   ```bash
   docling-hybrid-ocr convert-batch ./pdfs/ --parallel 2
   ```

---

### Issue: "Backend timeout"

**Symptoms:**
- "Request timed out" error
- Long waits with no progress

**Solutions:**

1. Use lower DPI (smaller images = faster processing):
   ```bash
   docling-hybrid-ocr convert document.pdf --dpi 100
   ```

2. Check network connection

3. Try again later (API may be busy)

4. Use a different backend:
   ```bash
   docling-hybrid-ocr convert document.pdf --backend deepseek-vllm
   ```

---

### Issue: "Rate limit exceeded"

**Symptoms:**
- "429" error
- "Rate limit exceeded" message

**Solutions:**

1. Wait a few minutes and try again

2. Process fewer pages at once:
   ```bash
   docling-hybrid-ocr convert document.pdf --max-pages 5
   ```

3. Reduce parallelism in batch mode:
   ```bash
   docling-hybrid-ocr convert-batch ./pdfs/ --parallel 2
   ```

4. Check your API usage at OpenRouter dashboard

---

### Issue: "No PDF files found"

**Symptoms:**
- Batch command reports 0 files found

**Solutions:**

1. Check directory path is correct:
   ```bash
   ls ./pdfs/
   ```

2. Verify pattern matches files:
   ```bash
   docling-hybrid-ocr convert-batch ./pdfs/ --pattern "*.pdf"
   ```

3. Use recursive search if PDFs are in subdirectories:
   ```bash
   docling-hybrid-ocr convert-batch ./pdfs/ -r
   ```

---

### Issue: "Permission denied"

**Symptoms:**
- Cannot read input file
- Cannot write output file

**Solutions:**

1. Check file permissions:
   ```bash
   ls -l document.pdf
   ```

2. Ensure output directory is writable:
   ```bash
   mkdir -p ./output
   chmod u+w ./output
   ```

3. Run with appropriate permissions

---

## Advanced Usage

### Custom Configuration

Create a custom configuration file:

```toml
# my-config.toml
[resources]
max_workers = 4
page_render_dpi = 150

[backends]
default = "nemotron-openrouter"

[backends.nemotron-openrouter]
temperature = 0.0
max_tokens = 8192
```

Use it:

```bash
docling-hybrid-ocr convert document.pdf --config my-config.toml
```

### Environment Variables

Override settings via environment variables:

```bash
# Set API key
export OPENROUTER_API_KEY=your-key

# Set config path
export DOCLING_HYBRID_CONFIG=configs/local.toml

# Set log level
export DOCLING_HYBRID_LOG_LEVEL=DEBUG

# Set max workers
export DOCLING_HYBRID_MAX_WORKERS=2
```

### Scripting

Use in shell scripts:

```bash
#!/bin/bash
# convert_all_pdfs.sh

INPUT_DIR="$1"
OUTPUT_DIR="$2"

if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <input_dir> <output_dir>"
    exit 1
fi

docling-hybrid-ocr convert-batch "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --parallel 4 \
    --recursive \
    --verbose

echo "Conversion complete!"
```

Run it:

```bash
chmod +x convert_all_pdfs.sh
./convert_all_pdfs.sh ./pdfs/ ./output/
```

---

## Getting Help

### Command help

```bash
# Main help
docling-hybrid-ocr --help

# Command-specific help
docling-hybrid-ocr convert --help
docling-hybrid-ocr convert-batch --help
```

### Version information

```bash
docling-hybrid-ocr --version
```

### System information

```bash
docling-hybrid-ocr info
```

### Further resources

- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [GitHub Issues](https://github.com/yourusername/docling-hybrid-ocr/issues)

---

*Last updated: 2024-11-25*
