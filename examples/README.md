# Examples

This directory contains example scripts demonstrating various use cases of Docling Hybrid OCR.

## Prerequisites

Before running any example:

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Set your API key:**
   ```bash
   export OPENROUTER_API_KEY=your-key-here
   ```

3. **Have a sample PDF ready:**
   - Use your own PDF file
   - Or create a simple test PDF

## Available Examples

### 1. basic_conversion.py

**Purpose:** Simplest possible conversion example

**What it demonstrates:**
- Loading configuration
- Creating a pipeline
- Converting a PDF to Markdown
- Basic error handling

**Usage:**
```bash
python examples/basic_conversion.py document.pdf
```

**Output:**
- Creates `document.md` in the same directory
- Shows conversion progress and statistics
- Displays preview of converted content

**Best for:** Getting started with the API

---

### 2. batch_conversion.py

**Purpose:** Convert multiple PDF files efficiently

**What it demonstrates:**
- Batch processing
- Parallel conversion
- Directory scanning (with glob patterns)
- Error handling for individual files
- Summary reporting

**Usage:**
```bash
# Convert all PDFs in a directory
python examples/batch_conversion.py pdfs/

# Convert specific files
python examples/batch_conversion.py file1.pdf file2.pdf file3.pdf

# Recursive directory scan
python examples/batch_conversion.py pdfs/ --recursive

# Custom output directory
python examples/batch_conversion.py pdfs/ --output-dir output/

# Control parallelism (default: 4)
python examples/batch_conversion.py pdfs/ --parallel 8
```

**Features:**
- ✅ Parallel processing (configurable)
- ✅ Rich progress display
- ✅ Detailed summary table
- ✅ Graceful error handling per file
- ✅ Recursive directory scanning

**Best for:** Converting multiple documents

---

### 3. custom_backend.py

**Purpose:** Using different backends and custom configurations

**What it demonstrates:**
- Using pre-configured backends
- Creating custom backend configurations
- Switching between backends
- Using local vLLM servers
- Creating custom backend implementations

**Usage:**
```bash
# Use default backend
python examples/custom_backend.py document.pdf

# Use specific backend from config
python examples/custom_backend.py document.pdf --backend deepseek-vllm

# Use custom endpoint
python examples/custom_backend.py document.pdf --custom-endpoint http://localhost:8000

# Use OpenRouter with custom model
python examples/custom_backend.py document.pdf --model "nvidia/nemotron-nano-12b-v2-vl:free"

# Use local vLLM server
python examples/custom_backend.py document.pdf --vllm http://localhost:8000

# Use mock backend (for testing)
python examples/custom_backend.py document.pdf --mock
```

**Examples included:**
1. Using pre-configured backends
2. Custom backend configuration
3. OpenRouter with custom model
4. Local vLLM server
5. Custom backend implementation (MockBackend)

**Best for:** Advanced backend configuration and testing

---

### 4. progress_tracking.py

**Purpose:** Various ways to track conversion progress

**What it demonstrates:**
- Simple progress bars
- Detailed statistics display
- Writing progress to log files
- Live status updates
- Future progress callback API (Sprint 2)

**Usage:**
```bash
# Run all examples
python examples/progress_tracking.py document.pdf

# Run specific example (1-5)
python examples/progress_tracking.py document.pdf 1
python examples/progress_tracking.py document.pdf 2
python examples/progress_tracking.py document.pdf 3
python examples/progress_tracking.py document.pdf 4
python examples/progress_tracking.py document.pdf 5
```

**Examples included:**
1. Simple progress bar
2. Detailed progress with statistics
3. Progress to log file
4. Live status display
5. Future API documentation (Sprint 2)

**Best for:** Monitoring long conversions

---

## Quick Start

### Example 1: Simple Conversion

```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

async def main():
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)
    result = await pipeline.convert_pdf(Path("document.pdf"))
    print(result.markdown)

asyncio.run(main())
```

### Example 2: Batch Conversion

```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

async def batch_convert(pdf_files):
    config = init_config()
    pipeline = HybridPipeline(config)

    for pdf_path in pdf_files:
        result = await pipeline.convert_pdf(pdf_path)
        print(f"✓ {pdf_path.name}: {result.processed_pages} pages")

pdf_files = list(Path("pdfs").glob("*.pdf"))
asyncio.run(batch_convert(pdf_files))
```

### Example 3: Custom Backend

```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.backends import make_backend
from docling_hybrid.common.models import OcrBackendConfig

async def main():
    config = init_config()

    # Custom backend config
    backend_config = OcrBackendConfig(
        name="custom",
        model="your-model",
        base_url="http://localhost:8000/v1/chat/completions",
        api_key=None,
        temperature=0.0,
        max_tokens=8192,
    )

    backend = make_backend(backend_config)
    pipeline = HybridPipeline(config, backend=backend)

    result = await pipeline.convert_pdf(Path("document.pdf"))
    print(result.markdown)

asyncio.run(main())
```

## Common Issues

### Issue: "Missing OPENROUTER_API_KEY"

**Solution:**
```bash
export OPENROUTER_API_KEY=your-key-here
```

### Issue: "Out of memory"

**Solution:**
```bash
# Reduce workers and DPI
export DOCLING_HYBRID_MAX_WORKERS=1
export DOCLING_HYBRID_PAGE_RENDER_DPI=100
```

### Issue: "Backend connection timeout"

**Solution:**
```bash
# Increase timeout
export DOCLING_HYBRID_HTTP_TIMEOUT_S=300
```

## Additional Resources

- **[QUICK_START.md](../docs/QUICK_START.md)** - Beginner's guide
- **[API_REFERENCE.md](../docs/API_REFERENCE.md)** - Complete API reference
- **[API.md](../docs/API.md)** - Comprehensive API documentation
- **[DEPLOYMENT.md](../docs/DEPLOYMENT.md)** - Deployment guide
- **[TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)** - Troubleshooting guide

## Contributing

To contribute a new example:

1. Create a new Python file in this directory
2. Include clear docstring at the top
3. Add usage examples
4. Add entry to this README
5. Submit a pull request

## Support

- **GitHub Issues:** https://github.com/your-org/docling-hybrid-ocr/issues
- **Documentation:** https://github.com/your-org/docling-hybrid-ocr#readme

---

*Last Updated: 2024-11-25*
*Sprint: 2*
