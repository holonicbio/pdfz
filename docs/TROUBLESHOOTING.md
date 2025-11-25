# Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues when using Docling Hybrid OCR.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [API Connection Issues](#api-connection-issues)
- [PDF Rendering Issues](#pdf-rendering-issues)
- [Memory Issues](#memory-issues)
- [Performance Issues](#performance-issues)
- [Output Quality Issues](#output-quality-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Debug Mode](#debug-mode)
- [Getting Help](#getting-help)

---

## Installation Issues

### Issue: `pip install` fails with dependency errors

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement pypdfium2
```

**Causes:**
- Outdated pip version
- Python version incompatibility
- Platform not supported

**Solutions:**

1. **Update pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

3. **Install with explicit Python version:**
   ```bash
   python3.11 -m pip install docling-hybrid-ocr
   ```

4. **Install from source:**
   ```bash
   git clone https://github.com/your-org/docling-hybrid-ocr.git
   cd docling-hybrid-ocr
   pip install -e ".[dev]"
   ```

---

### Issue: Import errors after installation

**Symptoms:**
```python
ModuleNotFoundError: No module named 'docling_hybrid'
```

**Causes:**
- Multiple Python environments
- Package not installed in active environment

**Solutions:**

1. **Verify installation:**
   ```bash
   pip list | grep docling
   ```

2. **Check which Python:**
   ```bash
   which python
   pip show docling-hybrid-ocr
   ```

3. **Use virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install docling-hybrid-ocr
   ```

---

## Configuration Issues

### Issue: "Missing OPENROUTER_API_KEY"

**Symptoms:**
```
ConfigurationError: Missing OpenRouter API key
```

**Causes:**
- Environment variable not set
- API key not in config file

**Solutions:**

1. **Set environment variable:**
   ```bash
   export OPENROUTER_API_KEY=your-key-here
   ```

2. **Or create .env.local file:**
   ```bash
   echo "OPENROUTER_API_KEY=your-key-here" > .env.local
   source .env.local
   ```

3. **Verify it's set:**
   ```bash
   echo $OPENROUTER_API_KEY
   ```

4. **In Python:**
   ```python
   import os
   os.environ["OPENROUTER_API_KEY"] = "your-key-here"
   ```

**Prevention:**
- Create `.env.local` from `.env.example`
- Add to shell profile (`~/.bashrc`, `~/.zshrc`)

---

### Issue: "Configuration file not found"

**Symptoms:**
```
ConfigurationError: Config file not found: configs/custom.toml
```

**Causes:**
- Wrong path to config file
- Config file doesn't exist
- Working directory is wrong

**Solutions:**

1. **Use absolute path:**
   ```python
   from pathlib import Path
   config_path = Path.cwd() / "configs" / "local.toml"
   config = init_config(config_path)
   ```

2. **Check file exists:**
   ```bash
   ls -la configs/
   ```

3. **Use default config:**
   ```python
   # Don't specify path - uses built-in defaults
   config = init_config()
   ```

4. **Copy example config:**
   ```bash
   cp configs/default.toml configs/local.toml
   ```

---

### Issue: Invalid configuration values

**Symptoms:**
```
ValidationError: max_workers must be >= 1
```

**Causes:**
- Invalid values in config file
- Type mismatch

**Solutions:**

1. **Check config syntax:**
   ```bash
   # Configs should be valid TOML
   cat configs/local.toml
   ```

2. **Verify value types:**
   ```toml
   [resources]
   max_workers = 2         # Integer, not string
   max_memory_mb = 4096    # Integer

   [logging]
   level = "INFO"          # String in quotes
   ```

3. **Use default config as template:**
   ```bash
   cp configs/default.toml configs/local.toml
   # Edit local.toml carefully
   ```

---

## API Connection Issues

### Issue: "Connection timeout" or "Cannot connect to OpenRouter"

**Symptoms:**
```
BackendConnectionError: Failed to connect to https://openrouter.ai
```

**Causes:**
- No internet connection
- Firewall blocking requests
- API service down
- Invalid API endpoint

**Solutions:**

1. **Test network connectivity:**
   ```bash
   curl -I https://openrouter.ai/api/v1/
   ping openrouter.ai
   ```

2. **Check firewall:**
   ```bash
   # Allow HTTPS connections
   # Check corporate firewall/proxy settings
   ```

3. **Increase timeout:**
   ```toml
   # In config file
   [backends]
   timeout_seconds = 180  # Default is 120
   ```

4. **Check API status:**
   - Visit https://openrouter.ai/status
   - Check Twitter/Discord for service updates

5. **Use proxy if needed:**
   ```python
   import os
   os.environ["HTTP_PROXY"] = "http://proxy.company.com:8080"
   os.environ["HTTPS_PROXY"] = "http://proxy.company.com:8080"
   ```

---

### Issue: "API rate limit exceeded"

**Symptoms:**
```
BackendResponseError: API error 429: Rate limit exceeded
```

**Causes:**
- Too many requests in short time
- Free tier limits reached
- Shared API key

**Solutions:**

1. **Wait before retrying:**
   - The system will automatically retry with backoff
   - Wait 60 seconds before manual retry

2. **Reduce concurrency:**
   ```toml
   [resources]
   max_workers = 1  # Process one page at a time
   ```

3. **Upgrade API plan:**
   - Check OpenRouter pricing
   - Get higher rate limits

4. **Use local backend:**
   ```bash
   # Switch to DeepSeek vLLM (local)
   export DOCLING_HYBRID_DEFAULT_BACKEND=deepseek-vllm
   ```

---

### Issue: Invalid API key

**Symptoms:**
```
BackendResponseError: API error 401: Unauthorized
```

**Causes:**
- Wrong API key
- Expired API key
- API key not activated

**Solutions:**

1. **Verify API key:**
   ```bash
   # Check it's set correctly
   echo $OPENROUTER_API_KEY
   ```

2. **Test API key manually:**
   ```bash
   curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        https://openrouter.ai/api/v1/models
   ```

3. **Get new API key:**
   - Visit https://openrouter.ai/keys
   - Generate new key
   - Update environment variable

---

## PDF Rendering Issues

### Issue: "PDF cannot be opened" or "Invalid PDF"

**Symptoms:**
```
RenderingError: Could not open PDF: /path/to/file.pdf
```

**Causes:**
- Corrupted PDF file
- Encrypted/password-protected PDF
- Invalid file format
- File permissions issue

**Solutions:**

1. **Verify PDF is valid:**
   ```bash
   # Try opening with another viewer
   # On Linux:
   xdg-open document.pdf

   # On macOS:
   open document.pdf

   # On Windows:
   start document.pdf
   ```

2. **Check file permissions:**
   ```bash
   ls -la document.pdf
   chmod 644 document.pdf  # Make readable
   ```

3. **Remove password protection:**
   ```bash
   # Use qpdf or similar tool
   qpdf --decrypt --password=PASSWORD input.pdf output.pdf
   ```

4. **Repair corrupted PDF:**
   ```bash
   # Use ghostscript to repair
   gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress input.pdf
   ```

5. **Verify it's actually a PDF:**
   ```bash
   file document.pdf  # Should say "PDF document"
   ```

---

### Issue: "Page index out of range"

**Symptoms:**
```
ValidationError: Page index 10 out of range [0, 5)
```

**Causes:**
- Requesting page that doesn't exist
- Off-by-one error (0-indexed vs 1-indexed)

**Solutions:**

1. **Check page count first:**
   ```python
   from docling_hybrid.renderer import get_page_count

   total_pages = get_page_count(pdf_path)
   print(f"PDF has {total_pages} pages")

   # Use 0-indexed: valid range is 0 to total_pages-1
   for page_index in range(total_pages):
       render_page_to_png_bytes(pdf_path, page_index)
   ```

2. **Use pipeline (handles this automatically):**
   ```python
   # Pipeline handles page iteration
   result = await pipeline.convert_pdf(pdf_path)
   ```

---

### Issue: Rendered images are too large/small

**Symptoms:**
- Output images are huge (several MB each)
- Text is blurry or unreadable

**Causes:**
- DPI setting too high or too low

**Solutions:**

1. **Adjust DPI:**
   ```python
   # Low DPI (fast, small files, lower quality)
   render_page_to_png_bytes(pdf_path, 0, dpi=72)

   # Medium DPI (balanced - recommended for dev)
   render_page_to_png_bytes(pdf_path, 0, dpi=150)

   # High DPI (slower, large files, better quality)
   render_page_to_png_bytes(pdf_path, 0, dpi=200)

   # Very high DPI (for detailed documents)
   render_page_to_png_bytes(pdf_path, 0, dpi=300)
   ```

2. **For production:**
   ```toml
   # In config file
   [rendering]
   default_dpi = 200
   ```

---

## Memory Issues

### Issue: "Out of memory" or process killed

**Symptoms:**
```
Killed
MemoryError
```

**Causes:**
- Processing too many pages concurrently
- DPI too high
- Large PDF files
- Insufficient system RAM

**Solutions:**

1. **Use local config (for 12GB RAM):**
   ```bash
   export DOCLING_HYBRID_CONFIG=configs/local.toml
   ```

2. **Reduce max workers:**
   ```toml
   [resources]
   max_workers = 1  # Process one page at a time
   ```

3. **Lower DPI:**
   ```python
   options = ConversionOptions(dpi=100)
   result = await pipeline.convert_pdf(pdf_path, options=options)
   ```

4. **Process in batches:**
   ```python
   # Process 5 pages at a time
   total_pages = get_page_count(pdf_path)

   for start in range(0, total_pages, 5):
       options = ConversionOptions(
           start_page=start,
           max_pages=5
       )
       result = await pipeline.convert_pdf(pdf_path, options=options)
       # Save/process result
   ```

5. **Monitor memory usage:**
   ```bash
   # While running
   watch -n 1 free -h

   # Or
   htop
   ```

6. **Close other applications:**
   - Free up RAM before processing
   - Close browser tabs, IDEs, etc.

---

### Issue: Memory usage grows over time

**Symptoms:**
- First pages process fine
- Later pages slow down or crash
- Memory not released after processing

**Causes:**
- Memory leak in processing loop
- Large intermediate data not cleared

**Solutions:**

1. **Process pages separately:**
   ```python
   import gc

   for page_idx in range(total_pages):
       options = ConversionOptions(
           start_page=page_idx,
           max_pages=1
       )
       result = await pipeline.convert_pdf(pdf_path, options=options)

       # Process result
       save_result(result)

       # Clear memory
       del result
       gc.collect()
   ```

2. **Use async context managers:**
   ```python
   async with make_backend(config) as backend:
       result = await backend.page_to_markdown(image_bytes, 1, "doc")
   # Backend properly cleaned up here
   ```

---

## Performance Issues

### Issue: Conversion is very slow

**Symptoms:**
- Taking >10 seconds per page
- CLI hangs for long time

**Causes:**
- API latency (VLM inference is slow)
- Network latency
- High DPI rendering
- Sequential processing

**Solutions:**

1. **Enable concurrent processing:**
   ```toml
   [resources]
   max_workers = 4  # Process 4 pages simultaneously
   ```

2. **Use local backend (if available):**
   ```bash
   # DeepSeek vLLM is faster than API
   export DOCLING_HYBRID_DEFAULT_BACKEND=deepseek-vllm
   ```

3. **Lower DPI for testing:**
   ```python
   options = ConversionOptions(dpi=150)  # Instead of 200
   ```

4. **Test with fewer pages:**
   ```python
   options = ConversionOptions(max_pages=3)
   ```

5. **Check network latency:**
   ```bash
   ping openrouter.ai
   ```

**Expected Performance:**
- API latency: 2-10 seconds per page
- Rendering: <1 second per page
- Total: 3-11 seconds per page (with API)
- Local backend: 1-3 seconds per page

---

### Issue: Timeout errors

**Symptoms:**
```
BackendTimeoutError: Request timed out after 120 seconds
```

**Causes:**
- API is slow or overloaded
- Large images taking long to process
- Network issues

**Solutions:**

1. **Increase timeout:**
   ```toml
   [backends]
   timeout_seconds = 300  # 5 minutes
   ```

2. **Or via environment:**
   ```bash
   export DOCLING_HYBRID_TIMEOUT=300
   ```

3. **Use smaller images:**
   ```python
   options = ConversionOptions(dpi=150)  # Smaller image = faster
   ```

---

## Output Quality Issues

### Issue: Poor OCR quality / many errors in output

**Symptoms:**
- Text is garbled or incorrect
- Tables not recognized
- Formulas missing

**Causes:**
- Low DPI rendering
- Poor quality input PDF
- Wrong backend for content type

**Solutions:**

1. **Increase DPI:**
   ```python
   options = ConversionOptions(dpi=200)  # Or 300 for detailed docs
   ```

2. **Check input PDF quality:**
   - Open PDF in viewer
   - If scanned, text may already be poor quality
   - Consider re-scanning at higher resolution

3. **Try different backend:**
   ```bash
   # DeepSeek may work better for some content
   export DOCLING_HYBRID_DEFAULT_BACKEND=deepseek-vllm
   ```

4. **Use specialized methods:**
   ```python
   # For table-heavy documents, future versions will support
   # block-level routing with specialized prompts
   ```

---

### Issue: Tables not formatted correctly

**Symptoms:**
- Table structure lost
- Cells merged incorrectly
- Alignment issues

**Causes:**
- Complex table layout
- VLM limitations
- Low resolution

**Current Solutions:**

1. **Increase DPI:**
   ```python
   options = ConversionOptions(dpi=300)
   ```

2. **Manual post-processing may be needed:**
   - Tables are a known limitation
   - Future versions will have better table handling

**Future Solutions:**
- Block-level processing (Sprint 6)
- Table-specific backends
- Result validation/repair

---

### Issue: Missing content or "Figure" placeholders

**Symptoms:**
- `<FIGURE>` instead of actual content
- Some text missing

**Causes:**
- Content not recognized as text
- Diagram/image in PDF
- VLM can't read handwriting

**Solutions:**

1. **This is expected behavior:**
   - Non-text content is replaced with `<FIGURE>`
   - Handwritten text may not be recognized

2. **For scanned documents:**
   - Ensure scan quality is high (300 DPI+)
   - Use OCR-optimized scan settings

3. **Check input:**
   - If PDF has images embedded, they won't be converted
   - This tool is for text/table/formula OCR

---

## Platform-Specific Issues

### macOS Issues

**Issue: "Unable to load dynamic library 'libpdfium'"**

**Solutions:**
```bash
# Install via Homebrew
brew install pdfium

# Or
pip install --upgrade pypdfium2
```

---

### Windows Issues

**Issue: DLL loading errors**

**Solutions:**
```bash
# Install Visual C++ Redistributable
# Download from Microsoft

# Reinstall pypdfium2
pip uninstall pypdfium2
pip install pypdfium2
```

**Issue: Path issues with backslashes**

**Solutions:**
```python
from pathlib import Path

# Use Path objects (handles Windows paths correctly)
pdf_path = Path(r"C:\Users\Name\Documents\file.pdf")

# Or use forward slashes
pdf_path = Path("C:/Users/Name/Documents/file.pdf")
```

---

### Linux Issues

**Issue: "Permission denied" errors**

**Solutions:**
```bash
# Check file permissions
ls -la document.pdf
chmod 644 document.pdf

# Check directory permissions
chmod 755 output_directory/
```

---

## Debug Mode

### Enable detailed logging

1. **Via environment variable:**
   ```bash
   export DOCLING_HYBRID_LOG_LEVEL=DEBUG
   ```

2. **Via config file:**
   ```toml
   [logging]
   level = "DEBUG"
   format = "text"  # Human-readable
   ```

3. **In Python:**
   ```python
   import os
   os.environ["DOCLING_HYBRID_LOG_LEVEL"] = "DEBUG"

   from docling_hybrid import init_config
   config = init_config()  # Will use DEBUG level
   ```

4. **Use verbose CLI flag:**
   ```bash
   docling-hybrid-ocr convert document.pdf --verbose
   ```

### Interpreting debug output

**Configuration loading:**
```
DEBUG config_loading path=/path/to/config.toml
DEBUG config_loaded environment=development
```

**Backend operations:**
```
DEBUG backend_request backend=nemotron-openrouter page_num=1
DEBUG backend_response status=200 content_length=1234
```

**Errors:**
```
ERROR page_processing_failed page_index=5 error="Connection timeout"
```

---

## Getting Help

### Before asking for help

1. **Check this guide** for your specific issue
2. **Enable debug mode** and review logs
3. **Try with a simple test case:**
   ```bash
   # Test with 1-page PDF
   docling-hybrid-ocr convert test.pdf --max-pages 1 --verbose
   ```

4. **Gather information:**
   - Python version: `python --version`
   - Package version: `pip show docling-hybrid-ocr`
   - OS and version: `uname -a` (Linux/Mac) or `ver` (Windows)
   - Error messages (full stack trace)
   - Config file (without API keys)

### Reporting issues

Create a GitHub issue with:

```markdown
## Environment
- OS: Ubuntu 22.04
- Python: 3.11.5
- Package version: 0.1.0

## Steps to reproduce
1. Run `docling-hybrid-ocr convert test.pdf`
2. See error...

## Expected behavior
Should convert PDF to Markdown

## Actual behavior
Error: ConfigurationError: Missing API key

## Logs
(Paste debug logs here)

## Additional context
- First time using the tool
- Following Quick Start guide
```

### Community resources

- **Documentation:** https://github.com/your-org/docling-hybrid-ocr/docs
- **Issues:** https://github.com/your-org/docling-hybrid-ocr/issues
- **Discussions:** https://github.com/your-org/docling-hybrid-ocr/discussions

---

## Common Error Messages Reference

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `ConfigurationError: Missing OpenRouter API key` | API key not set | `export OPENROUTER_API_KEY=...` |
| `BackendConnectionError` | No internet / API down | Check network connection |
| `BackendTimeoutError` | Request took too long | Increase timeout in config |
| `RenderingError: Could not open PDF` | Invalid/corrupted PDF | Verify PDF opens in viewer |
| `ValidationError: Page index out of range` | Invalid page number | Check page count first |
| `MemoryError` | Out of RAM | Reduce max_workers, lower DPI |
| `ModuleNotFoundError` | Package not installed | `pip install docling-hybrid-ocr` |
| `429 Rate limit exceeded` | Too many API requests | Wait 60s, reduce concurrency |
| `401 Unauthorized` | Invalid API key | Check API key is correct |

---

## Quick Diagnostic Script

Run this to check your setup:

```python
import sys
import os
from pathlib import Path

print("=== Docling Hybrid OCR Diagnostics ===\n")

# Python version
print(f"Python: {sys.version}")

# Package version
try:
    import docling_hybrid
    print(f"Package version: {docling_hybrid.__version__}")
except ImportError as e:
    print(f"ERROR: Package not installed: {e}")
    sys.exit(1)

# API key
api_key = os.getenv("OPENROUTER_API_KEY")
if api_key:
    print(f"API key: {'*' * 8}{api_key[-4:]}")
else:
    print("WARNING: No API key set")

# Config
try:
    from docling_hybrid import init_config
    config = init_config()
    print(f"Config loaded: {config.backends.default}")
except Exception as e:
    print(f"ERROR: Config failed: {e}")

# Dependencies
deps = ["pypdfium2", "aiohttp", "pydantic", "typer", "rich"]
for dep in deps:
    try:
        __import__(dep)
        print(f"✓ {dep}")
    except ImportError:
        print(f"✗ {dep} (missing)")

print("\n=== End Diagnostics ===")
```

Save as `diagnose.py` and run:
```bash
python diagnose.py
```

---

## Still Stuck?

If this guide doesn't solve your problem:

1. Check [API.md](API.md) for API usage details
2. Check [CLAUDE.md](../CLAUDE.md) for development context
3. Check [examples/](../examples/) for code examples
4. Create an issue with full details

Remember: Include your environment details, error messages, and what you've tried!
