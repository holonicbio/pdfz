# Local Development Guide
## For Resource-Constrained Environments (12GB RAM, CPU-only)

This guide covers development on machines with limited resources.
All instructions assume 12GB RAM and no GPU.

---

## Hardware Constraints

### Target Environment
- **RAM:** 12GB total
- **CPU:** Multi-core (no GPU)
- **Disk:** 50GB+ available
- **Network:** Required for API calls

### Resource Allocation
| Process | RAM Budget |
|---------|------------|
| OS + System | 2GB |
| IDE/Editor | 1-2GB |
| Python + venv | 500MB |
| Application | 2-4GB |
| Browser/Docs | 2GB |
| **Buffer** | 2-4GB |

---

## Configuration for Local Dev

### Use Local Config

Always use `configs/local.toml` during development:

```bash
export DOCLING_HYBRID_CONFIG=configs/local.toml
```

Or add to `.env.local`:
```bash
DOCLING_HYBRID_CONFIG=configs/local.toml
```

### Key Settings (configs/local.toml)

```toml
[resources]
max_workers = 2          # Reduced from 8
max_memory_mb = 4096     # 4GB limit
page_render_dpi = 150    # Reduced from 200
http_timeout_s = 180     # More generous timeout

[logging]
level = "DEBUG"
format = "text"          # Human-readable
```

### Environment Variables

```bash
# .env.local
OPENROUTER_API_KEY=your-key-here
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=DEBUG
DOCLING_HYBRID_MAX_WORKERS=2
```

---

## Memory Management

### Before Starting Development

Check available memory:
```bash
free -h
```

If less than 4GB free, close other applications.

### Processing Large PDFs

For PDFs > 20 pages, use limits:
```bash
# Process only first 5 pages
docling-hybrid-ocr convert large.pdf --max-pages 5

# Lower DPI for testing
docling-hybrid-ocr convert large.pdf --dpi 100
```

### Memory per Page (Approximate)

| DPI | Image Size | Memory During Render |
|-----|------------|---------------------|
| 72 | ~100KB | ~50MB |
| 150 | ~300KB | ~100MB |
| 200 | ~500KB | ~150MB |
| 300 | ~1MB | ~300MB |

**Recommendation:** Use DPI 150 for local development.

### Cleanup Between Runs

If memory seems high:
```bash
# Clear Python cache
./scripts/cleanup.sh

# Or manually
find . -name "__pycache__" -exec rm -rf {} +
```

---

## Disk Space Management

### Project Size
| Component | Size |
|-----------|------|
| Repository | ~5MB |
| Virtual environment | ~500MB |
| Test fixtures | ~10MB |
| Output files | Variable |

### Cleanup Commands

```bash
# Full cleanup
./scripts/cleanup.sh

# Remove output files only
rm -f *.nemotron.md *.deepseek.md

# Remove virtual environment (if needed)
rm -rf .venv
```

### Avoid Committing Large Files
- Don't commit PDFs to git
- Don't commit output .md files
- Don't commit .env.local

---

## Testing Locally

### Fast Feedback Loop

```bash
# Unit tests only (~10 seconds)
pytest tests/unit -v

# Specific test file
pytest tests/unit/test_backends.py -v

# With minimal output
pytest tests/unit -q
```

### Skip Slow Tests

```bash
# Skip integration tests
pytest tests/unit -v

# Skip marked slow tests (if any)
pytest -m "not slow" -v
```

### Coverage (Optional)

Coverage analysis uses more memory:
```bash
# Only run if you have memory headroom
pytest tests/unit --cov=src/docling_hybrid --cov-report=term-missing
```

---

## API Usage

### Free Tier Limitations

OpenRouter's Nemotron model is free but has rate limits:
- Requests per minute: Limited
- May have queue delays during peak times

### Minimize API Calls

During development:
1. Test with small PDFs (1-3 pages)
2. Cache results when possible
3. Use mocked tests when API not needed

### Mock Testing

For testing without API calls:
```python
# tests/conftest.py provides mock_backend fixture
def test_with_mock(mock_backend):
    mock_backend.page_to_markdown.return_value = "# Mock"
    # Test logic without API calls
```

---

## IDE Configuration

### VS Code Settings

`.vscode/settings.json`:
```json
{
    "python.pythonPath": ".venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/unit"],
    "editor.formatOnSave": true,
    "python.formatting.provider": "none",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

### PyCharm Settings

- Set Python interpreter to `.venv/bin/python`
- Set pytest as test runner
- Disable unnecessary inspections

### Reduce IDE Memory

- Disable unused plugins
- Limit indexed directories
- Close unused projects

---

## Debugging

### Enable Debug Logging

```bash
export DOCLING_HYBRID_LOG_LEVEL=DEBUG
docling-hybrid-ocr convert test.pdf --verbose
```

### Common Issues

#### "Cannot connect to OpenRouter"
```bash
# Check network
curl -I https://openrouter.ai/api/v1/

# Check API key
echo $OPENROUTER_API_KEY
```

#### "Out of memory"
```bash
# Use lower settings
docling-hybrid-ocr convert doc.pdf --dpi 100 --max-pages 3

# Check memory usage
free -h
```

#### "Request timed out"
```bash
# Increase timeout in config or wait for API
# OpenRouter may be busy during peak hours
```

---

## What NOT to Do Locally

### Don't Run Production Config
```bash
# Don't do this locally
export DOCLING_HYBRID_CONFIG=configs/default.toml  # Uses 8 workers!
```

### Don't Process Huge PDFs
```bash
# Don't do this without limits
docling-hybrid-ocr convert 500-page-book.pdf  # Will run out of memory
```

### Don't Run Full Test Suite with Coverage
```bash
# This uses a lot of memory
pytest tests/ --cov=src --cov-report=html  # ~2GB extra
```

### Don't Keep Many Output Files
```bash
# Clean up after testing
rm -f *.nemotron.md
```

---

## Quick Reference

### Start Development Session
```bash
cd docling-hybrid-ocr
source .venv/bin/activate
source .env.local
```

### Run Tests
```bash
pytest tests/unit -v
```

### Convert a PDF
```bash
docling-hybrid-ocr convert doc.pdf --dpi 150
```

### Check Memory
```bash
free -h
```

### Clean Up
```bash
./scripts/cleanup.sh
```

### End Session
```bash
deactivate
```

---

## Troubleshooting Checklist

When things aren't working:

1. ✅ Is virtual environment activated? (`which python`)
2. ✅ Is `.env.local` sourced? (`echo $OPENROUTER_API_KEY`)
3. ✅ Is local config being used? (`echo $DOCLING_HYBRID_CONFIG`)
4. ✅ Is there enough free memory? (`free -h`)
5. ✅ Is the PDF file valid and readable?
6. ✅ Is the network working? (`ping openrouter.ai`)

If still stuck:
- Check logs with `--verbose` flag
- Review error messages carefully
- Check CONTINUATION.md for known issues
