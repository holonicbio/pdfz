# Quick Start Guide

Get started with Docling Hybrid OCR in 5 minutes.

---

## What is Docling Hybrid OCR?

Docling Hybrid OCR converts PDF documents to Markdown using Vision-Language Models (VLMs). It can extract:
- Plain text
- Tables (preserving structure)
- Mathematical formulas
- Document layout and hierarchy

**Perfect for:**
- Converting scanned documents to editable text
- Extracting data from PDFs with complex layouts
- Creating Markdown documentation from PDFs
- Building searchable document databases

---

## Installation

### Prerequisites

- Python 3.11 or higher
- 12GB RAM minimum
- Internet connection (for API access)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr
```

### Step 2: Run Setup Script

```bash
./scripts/setup.sh
```

This creates a virtual environment and installs all dependencies.

### Step 3: Activate Virtual Environment

```bash
source .venv/bin/activate
```

On Windows:
```cmd
.venv\Scripts\activate
```

### Step 4: Get an OpenRouter API Key

**OpenRouter** is the recommended backend for Docling Hybrid OCR. It provides:
- ✅ Free tier available (with rate limits)
- ✅ No GPU required (cloud-based)
- ✅ Multiple VLM models to choose from
- ✅ Works on any platform (Windows, Mac, Linux)

**To get your API key:**

1. Visit [OpenRouter](https://openrouter.ai)
2. Click "Sign Up" and create a free account
3. Navigate to "API Keys" in your dashboard
4. Click "Create Key" and give it a name (e.g., "docling-hybrid")
5. Copy the key - it starts with `sk-or-v1-...`
6. **Important:** Save the key securely - you won't be able to see it again!

**Free Tier Limits:**
- The free tier includes models like Nemotron Nano (our default)
- Sufficient for testing and small-scale use
- For production use, consider upgrading to a paid tier

### Step 5: Configure Your API Key

**Method 1: Using openrouter_key file (Recommended)**

This is the simplest method for local development:

```bash
# Create the key file
echo 'sk-or-v1-your-actual-key-here' > openrouter_key

# Source the environment setup script
source ./scripts/setup_env.sh
```

The setup script will automatically read your key and export it.

**Method 2: Using .env.local file**

For more configuration options:

```bash
# Create environment file from example
cp .env.example .env.local

# Edit the file
nano .env.local  # or use your preferred editor
```

Add your API key:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=INFO
```

Load the environment:
```bash
source .env.local
```

**Method 3: Direct export (Quick testing)**

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

**Verify your API key is set:**

```bash
echo $OPENROUTER_API_KEY
# Should display: sk-or-v1-...
```

### Step 6: Verify Installation

**Check CLI version:**
```bash
docling-hybrid-ocr --version
```

Expected output:
```
docling-hybrid-ocr version 0.1.0
```

**Check available backends:**
```bash
docling-hybrid-ocr backends
```

Expected output:
```
Available backends:
  ✓ nemotron-openrouter (default) - OpenRouter with Nemotron Nano VLM
  ○ deepseek-vllm - DeepSeek OCR via vLLM (not configured)
  ○ deepseek-mlx - DeepSeek OCR via MLX (not configured)
```

**Verify your API key is configured:**
```bash
docling-hybrid-ocr info
```

This will show your configuration including whether the API key is set.

---

## Your First Conversion

### Command Line Usage

Convert a PDF to Markdown using OpenRouter:

```bash
docling-hybrid-ocr convert document.pdf
```

This will:
1. Read `document.pdf`
2. Render each page as an image (PNG format, 200 DPI)
3. Send images to OpenRouter's Nemotron Nano VLM
4. Receive Markdown output for each page
5. Combine pages and save as `document.md` in the same directory

**What you'll see:**

```
Converting document.pdf...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 10/10 100% 0:00:42
✓ Conversion complete!
  Processed: 10/10 pages
  Time: 42.3s (0.24 pages/s)
  Output: document.md
```

**With custom output:**
```bash
docling-hybrid-ocr convert document.pdf --output result.md
```

**Process only first 5 pages (recommended for testing):**
```bash
docling-hybrid-ocr convert document.pdf --max-pages 5
```

**Lower DPI for faster processing (uses less API credits):**
```bash
docling-hybrid-ocr convert document.pdf --dpi 150
```

**Verbose output (shows each page):**
```bash
docling-hybrid-ocr convert document.pdf --verbose
```

**OpenRouter Tips:**
- Start with `--max-pages 5` to test before converting large documents
- Use `--dpi 150` if you're on the free tier to process more pages
- Monitor your usage at https://openrouter.ai/activity

### Python API Usage

Create a file `convert.py`:

```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.orchestrator.callbacks import ConsoleProgressCallback

async def main():
    # Initialize configuration (loads OpenRouter API key from env)
    config = init_config(Path("configs/local.toml"))

    # Create pipeline (uses nemotron-openrouter backend by default)
    pipeline = HybridPipeline(config)

    # Create progress callback for live updates
    progress = ConsoleProgressCallback(verbose=True)

    # Convert PDF with OpenRouter
    result = await pipeline.convert_pdf(
        pdf_path=Path("document.pdf"),
        output_path=Path("output.md"),
        progress_callback=progress
    )

    # Print result summary
    print(f"\n✓ Converted {result.processed_pages}/{result.total_pages} pages")
    print(f"✓ Backend: {result.backend_name}")
    print(f"✓ Saved to {result.output_path}")

    # Access individual page results
    for page_result in result.page_results:
        print(f"  Page {page_result.page_num}: {len(page_result.content)} chars")

# Run
if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python convert.py
```

**Expected output:**
```
Starting conversion - 10 pages
  Processing page 1/10...
    ✓ Page 1 complete (1234 chars)
  Processing page 2/10...
    ✓ Page 2 complete (2345 chars)
...
✓ Conversion complete!
  Processed: 10/10 pages
  Time: 42.3s (0.24 pages/s)
  Output: output.md

✓ Converted 10/10 pages
✓ Backend: nemotron-openrouter
✓ Saved to output.md
  Page 1: 1234 chars
  Page 2: 2345 chars
  ...
```

---

## Common Use Cases

### Use Case 1: Convert a Single PDF

**CLI:**
```bash
docling-hybrid-ocr convert document.pdf
```

**Python:**
```python
result = await pipeline.convert_pdf(Path("document.pdf"))
markdown = result.markdown
```

---

### Use Case 2: Convert Multiple PDFs

**CLI (one at a time):**
```bash
for file in pdfs/*.pdf; do
    docling-hybrid-ocr convert "$file"
done
```

**Python (batch):**
```python
import asyncio
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

async def batch_convert(pdf_files):
    config = init_config()
    pipeline = HybridPipeline(config)

    for pdf_path in pdf_files:
        try:
            result = await pipeline.convert_pdf(pdf_path)
            print(f"✓ {pdf_path.name}: {result.processed_pages} pages")
        except Exception as e:
            print(f"✗ {pdf_path.name}: {e}")

# Convert all PDFs in a directory
pdf_files = list(Path("pdfs").glob("*.pdf"))
asyncio.run(batch_convert(pdf_files))
```

---

### Use Case 3: Convert Large PDFs (Memory-Efficient)

For PDFs with 100+ pages, process in chunks:

**CLI:**
```bash
# Process first 20 pages
docling-hybrid-ocr convert large.pdf --max-pages 20

# Process next 20 pages
docling-hybrid-ocr convert large.pdf --start-page 20 --max-pages 20
```

**Python:**
```python
from docling_hybrid.orchestrator import ConversionOptions

# Process in chunks of 20 pages
async def convert_large_pdf(pdf_path, chunk_size=20):
    config = init_config()
    pipeline = HybridPipeline(config)

    # Get total pages
    from docling_hybrid.renderer import get_page_count
    total_pages = get_page_count(pdf_path)

    all_markdown = []

    for start in range(0, total_pages, chunk_size):
        options = ConversionOptions(
            start_page=start,
            max_pages=chunk_size,
            dpi=150  # Lower DPI to save memory
        )

        result = await pipeline.convert_pdf(pdf_path, options=options)
        all_markdown.append(result.markdown)
        print(f"Processed pages {start+1}-{start+result.processed_pages}")

    # Combine all chunks
    full_markdown = "\n\n".join(all_markdown)

    # Save to file
    output_path = pdf_path.with_suffix(".md")
    output_path.write_text(full_markdown)
    print(f"✓ Saved complete document to {output_path}")

asyncio.run(convert_large_pdf(Path("large.pdf")))
```

---

### Use Case 4: Extract Text Only (No Tables/Formulas)

The markdown output includes everything. To extract just plain text:

**Python:**
```python
import re

result = await pipeline.convert_pdf(Path("document.pdf"))
markdown = result.markdown

# Remove markdown tables
markdown = re.sub(r'\|.*\|', '', markdown)
markdown = re.sub(r'\|[-:]+\|', '', markdown)

# Remove LaTeX formulas
markdown = re.sub(r'\$.*?\$', '', markdown)
markdown = re.sub(r'\$\$.*?\$\$', '', markdown, flags=re.DOTALL)

# Clean up extra whitespace
text = re.sub(r'\n{3,}', '\n\n', markdown)

print(text)
```

---

### Use Case 5: Convert with Custom Backend

If you have a local vLLM server running:

**CLI:**
```bash
docling-hybrid-ocr convert document.pdf --backend deepseek-vllm
```

**Python:**
```python
from docling_hybrid.backends import make_backend
from docling_hybrid.common.models import OcrBackendConfig

# Create custom backend config
backend_config = OcrBackendConfig(
    name="deepseek-vllm",
    model="deepseek-ai/DeepSeek-OCR",
    base_url="http://localhost:8000/v1/chat/completions",
    api_key=None,  # Local server, no key needed
    temperature=0.0,
    max_tokens=8192,
)

backend = make_backend(backend_config)
pipeline = HybridPipeline(config, backend=backend)

result = await pipeline.convert_pdf(Path("document.pdf"))
```

---

### Use Case 6: Monitor Progress

Show progress while converting:

**Python:**
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

async def convert_with_progress(pdf_path):
    config = init_config()
    pipeline = HybridPipeline(config)

    # Get page count
    from docling_hybrid.renderer import get_page_count
    total_pages = get_page_count(pdf_path)

    # Create progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task(
            f"Converting {pdf_path.name}...",
            total=total_pages
        )

        # Convert
        result = await pipeline.convert_pdf(pdf_path)

        # Update to completion
        progress.update(task, completed=total_pages)

    print(f"✓ Done! Saved to {pdf_path.with_suffix('.md')}")

asyncio.run(convert_with_progress(Path("document.pdf")))
```

---

## Frequently Asked Questions (FAQ)

### General Questions

**Q: What PDF types are supported?**

A: All PDF types:
- Native PDFs (created digitally)
- Scanned PDFs (images)
- Mixed PDFs (text + images)
- Password-protected PDFs (if password is removed first)

**Q: How accurate is the OCR?**

A: Very accurate for most documents. VLMs are particularly good at:
- Complex table structures
- Mathematical formulas
- Mixed layouts
- Handwriting (varies by model)

**Q: Is it free?**

A: The software is free (MIT license). You need an API key:
- OpenRouter free tier: Limited daily requests
- OpenRouter paid: Pay per token
- Self-hosted vLLM: Free if you have GPU hardware

**Q: Does it work offline?**

A: Not with OpenRouter backend (requires internet). For offline:
- Use DeepSeek vLLM backend with local GPU
- Use DeepSeek MLX backend on macOS with Apple Silicon

**Q: How long does conversion take?**

A: Typical times (with OpenRouter):
- 1 page: 2-5 seconds
- 10 pages: 20-50 seconds
- 100 pages: 5-10 minutes (with 8 concurrent workers)

Times vary based on:
- Document complexity
- API response time
- Number of concurrent workers
- System resources

---

### Configuration Questions

**Q: Where should I put my API key?**

A: Three options:
1. **Environment file** (recommended): `.env.local`
2. **Environment variable**: `export OPENROUTER_API_KEY=...`
3. **Config file**: Add to `configs/local.toml` (not recommended for security)

**Q: How do I change the configuration?**

A: Edit `configs/local.toml` for development or `configs/default.toml` for production.

Common settings:
```toml
[resources]
max_workers = 2      # Concurrent pages (reduce if low memory)
page_render_dpi = 150  # Lower = faster, higher = better quality

[backends]
default = "nemotron-openrouter"  # or "deepseek-vllm"
```

**Q: My machine only has 8GB RAM. Will it work?**

A: It might work with adjustments:
```toml
[resources]
max_workers = 1      # Process one page at a time
page_render_dpi = 100  # Low DPI
max_memory_mb = 3072   # 3GB limit
```

Also use `--max-pages` to process in small batches.

---

### Troubleshooting Questions

**Q: Error: "Missing OPENROUTER_API_KEY"**

A:
```bash
# Check if set
echo $OPENROUTER_API_KEY

# If empty, load environment
source .env.local

# Or set directly
export OPENROUTER_API_KEY=sk-your-key-here
```

**Q: Error: "Out of memory"**

A: Reduce memory usage:
```bash
# Lower DPI
docling-hybrid-ocr convert doc.pdf --dpi 100

# Process fewer pages
docling-hybrid-ocr convert doc.pdf --max-pages 5

# Or edit config
export DOCLING_HYBRID_MAX_WORKERS=1
```

**Q: Error: "Connection timeout"**

A: Network or API issue:
```bash
# Check internet
ping openrouter.ai

# Increase timeout
export DOCLING_HYBRID_HTTP_TIMEOUT_S=300

# Check backend health
docling-hybrid-ocr health
```

**Q: Conversion is slow**

A: Speed up:
1. **Lower DPI**: `--dpi 150` instead of 200
2. **More workers**: `export DOCLING_HYBRID_MAX_WORKERS=8` (if you have RAM)
3. **Use local backend**: Set up vLLM for local inference

**Q: Output is incomplete or incorrect**

A: Try:
1. **Check PDF**: Open in viewer to ensure it's not corrupted
2. **Higher DPI**: `--dpi 250` for better quality
3. **Check logs**: `export DOCLING_HYBRID_LOG_LEVEL=DEBUG`
4. **Report issue**: Share PDF and output with maintainers

**Q: How do I see detailed logs?**

A:
```bash
export DOCLING_HYBRID_LOG_LEVEL=DEBUG
docling-hybrid-ocr convert document.pdf --verbose
```

---

### Advanced Questions

**Q: Can I customize the output format?**

A: Yes, in config:
```toml
[output]
format = "markdown"
add_page_separators = true
page_separator = "<!-- PAGE {page_num} -->\n\n"
```

Or post-process the markdown in Python.

**Q: Can I use a different VLM model?**

A: Yes, edit backend config:
```toml
[backends.nemotron-openrouter]
model = "your-preferred-model"
```

Or create a custom backend (see [API_REFERENCE.md](API_REFERENCE.md)).

**Q: How do I process only specific pages?**

A:
```bash
# Pages 5-10
docling-hybrid-ocr convert doc.pdf --start-page 4 --max-pages 6
```

Or in Python:
```python
options = ConversionOptions(start_page=4, max_pages=6)
result = await pipeline.convert_pdf(pdf_path, options=options)
```

**Q: Can I run this in a Docker container?**

A: Yes! See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker instructions.

**Q: How do I contribute or report bugs?**

A:
- **Bugs**: https://github.com/your-org/docling-hybrid-ocr/issues
- **Questions**: Create a discussion on GitHub
- **Pull requests**: See [CONTINUATION.md](../CONTINUATION.md)

---

## Next Steps

Now that you've completed your first conversion:

1. **Try different documents** - Test with various PDF types
2. **Explore the Python API** - See [API_REFERENCE.md](API_REFERENCE.md)
3. **Read about deployment** - See [DEPLOYMENT.md](DEPLOYMENT.md)
4. **Learn about backends** - Try local inference with vLLM
5. **Join the community** - Star the repo and share feedback

### Additional Resources

- **[README.md](../README.md)** - Project overview
- **[API.md](API.md)** - Comprehensive API documentation
- **[API_REFERENCE.md](API_REFERENCE.md)** - Quick API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Detailed troubleshooting
- **[CLAUDE.md](../CLAUDE.md)** - Development context
- **[examples/](../examples/)** - Example scripts

### Getting Help

- **GitHub Issues**: https://github.com/your-org/docling-hybrid-ocr/issues
- **Discussions**: https://github.com/your-org/docling-hybrid-ocr/discussions
- **Email**: support@your-org.com (if available)

---

## Example: Complete Workflow

Here's a complete example from installation to conversion:

```bash
# 1. Clone and setup
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr
./scripts/setup.sh

# 2. Activate environment
source .venv/bin/activate

# 3. Configure API key
cp .env.example .env.local
echo "OPENROUTER_API_KEY=sk-your-key-here" >> .env.local
source .env.local

# 4. Verify installation
docling-hybrid-ocr --version
docling-hybrid-ocr backends

# 5. Convert a PDF
docling-hybrid-ocr convert document.pdf

# 6. Check output
cat document.md

# 7. Convert with options
docling-hybrid-ocr convert document.pdf \
  --output result.md \
  --max-pages 10 \
  --dpi 150 \
  --verbose
```

That's it! You're now ready to convert PDFs to Markdown. 🎉

---

*Last Updated: 2025-11-25*
*Version: Sprint 3 - Production Readiness with OpenRouter*
