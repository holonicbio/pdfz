# Development Continuation Guide - Mac M2 Air (24GB RAM) with MLX

## Environment Overview

**Target Machine:** Mac M2 Air with 24GB RAM
**Primary Focus:** DeepSeek-OCR MLX Backend Implementation
**Framework:** Apple MLX + mlx-vlm
**Date:** November 2024
**Version:** 0.1.0

This machine is now the **primary development environment** for:
1. DeepSeek MLX backend implementation
2. Real PDF testing and optimization
3. Production-ready local inference

---

## Quick Start - Mac Setup

### 1. Clone and Setup

```bash
# Clone repository
git clone <repo>
cd docling-hybrid-ocr

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install with MLX dependencies
pip install -e ".[dev,mlx]"
```

### 2. Install MLX and mlx-vlm

```bash
# Install MLX (Apple Silicon optimized)
pip install mlx>=0.10.0

# Install mlx-vlm for vision-language models
pip install mlx-vlm>=0.1.0

# Verify installation
python -c "import mlx; print(f'MLX version: {mlx.__version__}')"
python -c "import mlx_vlm; print('mlx-vlm installed')"
```

### 3. Download DeepSeek-OCR Model

```bash
# Option A: Use mlx-vlm to download (recommended)
python -c "from mlx_vlm import load; load('deepseek-ai/DeepSeek-OCR')"

# Option B: Manual download from HuggingFace
# Model will be cached in ~/.cache/huggingface/hub/
```

### 4. Environment Variables

```bash
# Create .env.local
cat > .env.local << 'EOF'
# For fallback to cloud API (optional but recommended)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Config for Mac development
DOCLING_HYBRID_CONFIG=configs/mac.toml

# Logging
DOCLING_HYBRID_LOG_LEVEL=DEBUG
EOF

source .env.local
```

---

## Current Project State

### What's Complete (100%)

| Component | Location | Status |
|-----------|----------|--------|
| Configuration system | `common/config.py` | Fully tested |
| Data models | `common/models.py` | Fully tested |
| Error handling | `common/errors.py` | Fully tested |
| ID generation | `common/ids.py` | Fully tested |
| Structured logging | `common/logging.py` | Fully tested |
| Backend abstraction | `backends/base.py` | Interface defined |
| Backend factory | `backends/factory.py` | Fully tested |
| OpenRouter/Nemotron | `backends/openrouter_nemotron.py` | Production ready |
| Page renderer | `renderer/core.py` | Fully tested |
| Pipeline orchestrator | `orchestrator/pipeline.py` | Fully tested |
| CLI | `cli/main.py` | Fully tested |

### What Needs Implementation

| Component | Location | Priority | Status |
|-----------|----------|----------|--------|
| **DeepSeek MLX Backend** | `backends/deepseek_mlx_stub.py` | **HIGH** | Stub only |
| DeepSeek vLLM Backend | `backends/deepseek_vllm_stub.py` | Medium | Stub only |
| Integration tests | `tests/integration/` | HIGH | Partial |
| E2E PDF tests | `tests/e2e/` | HIGH | Needed |
| Block processing | `blocks/` | Low | Stub |
| Exporters | `exporters/` | Low | Stub |

---

## Outstanding Work - Priority Order

### Priority 1: DeepSeek MLX Backend Implementation (MAIN TASK)

**Location:** `src/docling_hybrid/backends/deepseek_mlx_stub.py`
**Effort:** 2-3 days
**Dependencies:** MLX, mlx-vlm installed

#### Implementation Options

**Option A: Direct Python API (Recommended for Mac)**
```python
from mlx_vlm import load, generate
from mlx_vlm.utils import load_image

# Load model once at initialization
model, processor = load("deepseek-ai/DeepSeek-OCR")

# For each page
output = generate(
    model=model,
    processor=processor,
    prompt=PAGE_TO_MARKDOWN_PROMPT,
    images=[image],
    max_tokens=8192,
    temperature=0.0,
)
```

**Option B: HTTP Sidecar Server**
- Run mlx-vlm HTTP server as background process
- Use same HTTP logic as OpenRouter backend
- Better for batch processing

#### Implementation Tasks

1. **Implement `DeepseekOcrMlxBackend` class:**
   - [ ] `__init__`: Load MLX model, handle memory
   - [ ] `page_to_markdown`: Convert page image to Markdown
   - [ ] `table_to_markdown`: Table-specific extraction
   - [ ] `formula_to_latex`: Math formula extraction
   - [ ] `close`: Cleanup resources

2. **Handle Mac-specific concerns:**
   - [ ] Unified Memory management (24GB shared)
   - [ ] Metal GPU acceleration verification
   - [ ] Image preprocessing for MLX format
   - [ ] Batch size optimization

3. **Configuration:**
   - [ ] Create `configs/mac.toml` with MLX settings
   - [ ] Add model path configuration
   - [ ] Memory limits for 24GB system

4. **Testing:**
   - [ ] Unit tests with mocked MLX calls
   - [ ] Integration tests with real model
   - [ ] Performance benchmarks

#### Acceptance Criteria

- [ ] `make_backend("deepseek-mlx")` returns working backend
- [ ] `page_to_markdown()` produces correct Markdown output
- [ ] Memory usage stays under 16GB during inference
- [ ] Processes typical PDF page in <30 seconds
- [ ] All unit tests pass

#### Reference Files

- **Stub:** `src/docling_hybrid/backends/deepseek_mlx_stub.py`
- **Interface:** `src/docling_hybrid/backends/base.py`
- **Example:** `src/docling_hybrid/backends/openrouter_nemotron.py`
- **Prompts:** Same prompts as OpenRouter backend

### Priority 2: Mac Configuration File

Create `configs/mac.toml`:

```toml
[resources]
max_workers = 4          # Can use more with MLX efficiency
max_memory_mb = 16384    # 16GB for model + processing
page_render_dpi = 200    # Full quality
http_timeout_s = 120

[backends]
default = "deepseek-mlx"
fallback_chain = ["deepseek-mlx", "nemotron-openrouter"]

[backends.deepseek-mlx]
name = "deepseek-mlx"
model = "deepseek-ai/DeepSeek-OCR"
# No base_url - direct Python API
temperature = 0.0
max_tokens = 8192

[logging]
level = "INFO"
format = "text"
```

### Priority 3: Real PDF Testing

**Location:** `tests/e2e/` and `tests/fixtures/sample_pdfs/`

#### Test Categories Needed

1. **Simple Documents** (1-3 pages)
   - Plain text
   - Headers and paragraphs
   - Basic formatting

2. **Tables** (various complexity)
   - Simple 2-column tables
   - Complex multi-row/column tables
   - Nested tables

3. **Mathematical Content**
   - Inline equations
   - Display equations
   - Multi-line formulas

4. **Mixed Content**
   - Academic papers
   - Technical documentation
   - Reports with figures

5. **Edge Cases**
   - Scanned documents (low quality)
   - Multi-column layouts
   - Headers/footers
   - Watermarks

#### Test Script Template

```bash
#!/bin/bash
# scripts/test_real_pdfs.sh

# Test with sample PDFs
for pdf in tests/fixtures/sample_pdfs/*.pdf; do
    echo "Processing: $pdf"
    docling-hybrid-ocr convert "$pdf" --backend deepseek-mlx --verbose
    echo "---"
done
```

### Priority 4: Performance Benchmarking

Create benchmarks comparing:

1. **MLX vs OpenRouter:**
   - Latency per page
   - Quality of output
   - Cost (local vs API)

2. **Memory profiling:**
   - Peak memory during inference
   - Memory after model load
   - Memory per concurrent page

3. **Throughput testing:**
   - Pages per minute
   - Batch processing efficiency

### Priority 5: Integration Tests

**Location:** `tests/integration/`

#### Tests to Create

```python
# tests/integration/test_mlx_backend.py

@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="MLX only available on macOS"
)
class TestDeepseekMlxBackend:

    async def test_page_to_markdown_real_image(self):
        """Test with real page image."""
        pass

    async def test_table_extraction(self):
        """Test table extraction accuracy."""
        pass

    async def test_formula_extraction(self):
        """Test LaTeX formula output."""
        pass

    async def test_memory_usage(self):
        """Verify memory stays within limits."""
        pass

    async def test_concurrent_pages(self):
        """Test multiple pages concurrently."""
        pass
```

---

## Documentation Guide

### Core Documentation (Must Read)

| Document | Location | Purpose |
|----------|----------|---------|
| **CLAUDE.md** | `/CLAUDE.md` | Master context - START HERE |
| **ARCHITECTURE.md** | `/docs/ARCHITECTURE.md` | System design and components |
| **BACKENDS.md** | `/docs/components/BACKENDS.md` | Backend interface specification |
| **API.md** | `/docs/API.md` | Python API reference |

### DeepSeek-Specific Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **DEEPSEEK_INTEGRATION_PLAN.md** | `/docs/DEEPSEEK_INTEGRATION_PLAN.md` | Comprehensive integration plan |

### Development Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **QUICK_START.md** | `/docs/QUICK_START.md` | Getting started guide |
| **TROUBLESHOOTING.md** | `/docs/TROUBLESHOOTING.md` | Common issues and fixes |
| **CLI_GUIDE.md** | `/docs/CLI_GUIDE.md` | CLI command reference |

### Sprint History

| Document | Location | Purpose |
|----------|----------|---------|
| **SPRINT1_COMPLETION_REPORT.md** | `/docs/SPRINT1_COMPLETION_REPORT.md` | Sprint 1 outcomes |
| **SPRINT2_PLAN.md** | `/docs/SPRINT2_PLAN.md` | Sprint 2 objectives |
| **SPRINT3_PLAN.md** | `/docs/SPRINT3_PLAN.md` | Sprint 3 objectives |

### Interface Specifications (Future Work)

| Document | Location | Purpose |
|----------|----------|---------|
| **BLOCKS_INTERFACE.md** | `/docs/interfaces/BLOCKS_INTERFACE.md` | Block processing spec |
| **EVAL_INTERFACE.md** | `/docs/interfaces/EVAL_INTERFACE.md` | Evaluation framework spec |

---

## Mac M2 Air Specific Considerations

### Unified Memory (24GB)

The M2 Air has unified memory shared between CPU and GPU:

```
Total: 24GB
├── System/OS: ~2-3GB
├── IDE/Apps: ~2-3GB
├── MLX Model: ~8-10GB (DeepSeek-OCR)
├── Processing: ~4-6GB
└── Buffer: ~4-6GB
```

**Memory Tips:**
- Close unused applications during testing
- Monitor with `Activity Monitor` or `htop`
- Use `memory_profiler` for Python code
- Consider quantization if needed (INT8)

### Metal GPU Performance

MLX automatically uses Metal for GPU acceleration:

```python
# Check Metal availability
import mlx.core as mx
print(f"Default device: {mx.default_device()}")
# Should show: Device(gpu, 0)
```

### Thermal Management

- M2 Air can throttle under sustained load
- Use external cooling for long processing sessions
- Consider batch processing with cooldown periods

### Battery vs Plugged In

- Performance is better when plugged in
- macOS Power Management may throttle on battery
- Recommend AC power for large PDFs

---

## Code Patterns for MLX Backend

### Pattern 1: Model Loading

```python
from mlx_vlm import load

class DeepseekOcrMlxBackend(OcrVlmBackend):
    def __init__(self, config: OcrBackendConfig) -> None:
        super().__init__(config)

        # Load model at initialization
        model_path = config.model or "deepseek-ai/DeepSeek-OCR"
        self._model, self._processor = load(model_path)

        logger.info("mlx_model_loaded", model=model_path)
```

### Pattern 2: Image Preprocessing

```python
from PIL import Image
import io

def _prepare_image(self, image_bytes: bytes) -> Image.Image:
    """Convert PNG bytes to PIL Image for MLX."""
    image = Image.open(io.BytesIO(image_bytes))

    # Ensure RGB format
    if image.mode != "RGB":
        image = image.convert("RGB")

    return image
```

### Pattern 3: Generation

```python
from mlx_vlm import generate

async def page_to_markdown(
    self,
    image_bytes: bytes,
    page_num: int,
    doc_id: str,
) -> str:
    """Convert page to Markdown using MLX."""

    image = self._prepare_image(image_bytes)

    # MLX generate is synchronous - run in executor for async
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: generate(
            model=self._model,
            processor=self._processor,
            prompt=PAGE_TO_MARKDOWN_PROMPT,
            images=[image],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
    )

    return result
```

### Pattern 4: Resource Cleanup

```python
async def close(self) -> None:
    """Release model resources."""
    if hasattr(self, '_model'):
        del self._model
        del self._processor

        # Force garbage collection
        import gc
        gc.collect()

        logger.info("mlx_model_unloaded")
```

---

## Testing Workflow

### 1. Run Unit Tests (No Model Required)

```bash
# Fast feedback - ~10 seconds
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=src/docling_hybrid --cov-report=term-missing
```

### 2. Run Integration Tests (Model Required)

```bash
# Requires MLX model downloaded
pytest tests/integration -v -m "not slow"

# Full integration suite
pytest tests/integration -v
```

### 3. Run E2E Tests (Real PDFs)

```bash
# With sample PDFs
pytest tests/e2e -v

# Specific test
pytest tests/e2e/test_mlx_e2e.py -v
```

### 4. Manual CLI Testing

```bash
# Convert single PDF
docling-hybrid-ocr convert sample.pdf --backend deepseek-mlx

# With options
docling-hybrid-ocr convert sample.pdf \
    --backend deepseek-mlx \
    --output output.md \
    --dpi 200 \
    --verbose

# Batch processing
docling-hybrid-ocr batch docs/*.pdf --backend deepseek-mlx
```

### 5. Performance Benchmarks

```bash
# Run benchmarks
pytest tests/benchmarks -v --benchmark

# Memory profiling
python -m memory_profiler scripts/profile_mlx.py
```

---

## Known Issues

### Issue 1: MLX Model Loading Time
**Impact:** First inference takes 30-60 seconds for model load
**Workaround:** Keep model loaded for batch processing
**Fix:** Implement model caching/warm-up

### Issue 2: Large Image Memory Spike
**Impact:** High DPI pages can cause memory spikes
**Workaround:** Use DPI 150-200 instead of 300
**Fix:** Implement image chunking for very large pages

### Issue 3: mlx-vlm Version Compatibility
**Impact:** Breaking changes between versions
**Workaround:** Pin specific version in requirements
**Fix:** Test with each new release

### Issue 4: Table Markdown Formatting
**Impact:** Complex tables may have formatting issues
**Workaround:** Post-process table output
**Fix planned:** Add table validation/repair

---

## Sprint Plan - MLX Implementation

### Days 1-2: Core Implementation

**Goals:**
- [ ] Implement `DeepseekOcrMlxBackend` class
- [ ] Model loading and initialization
- [ ] `page_to_markdown()` implementation
- [ ] Basic unit tests

**Validation:**
```bash
pytest tests/unit/backends/test_deepseek_mlx.py -v
```

### Days 3-4: Integration and Testing

**Goals:**
- [ ] Create `configs/mac.toml`
- [ ] Integration tests with real model
- [ ] Test fallback chain (MLX → OpenRouter)
- [ ] Memory profiling

**Validation:**
```bash
pytest tests/integration -v
docling-hybrid-ocr convert sample.pdf --backend deepseek-mlx
```

### Days 5-6: Real PDF Testing

**Goals:**
- [ ] Test with various PDF types
- [ ] Performance benchmarking
- [ ] Quality comparison with OpenRouter
- [ ] Fix edge cases

**Validation:**
```bash
./scripts/test_real_pdfs.sh
pytest tests/benchmarks -v
```

### Day 7: Documentation and Polish

**Goals:**
- [ ] Update documentation
- [ ] Create usage examples
- [ ] Write troubleshooting guide
- [ ] Final review

---

## Success Criteria

### Functional

- [ ] `make_backend("deepseek-mlx")` works
- [ ] Full pipeline works with MLX backend
- [ ] CLI commands work with `--backend deepseek-mlx`
- [ ] Fallback chain works (MLX → OpenRouter)

### Performance

- [ ] Page processing < 30 seconds average
- [ ] Memory usage < 16GB peak
- [ ] No memory leaks over 50+ pages
- [ ] GPU utilization > 50%

### Quality

- [ ] Output comparable to OpenRouter (subjective)
- [ ] Tables render correctly
- [ ] Formulas convert to valid LaTeX
- [ ] No hallucinations

### Testing

- [ ] All unit tests pass
- [ ] Integration tests pass on Mac
- [ ] E2E tests with real PDFs pass
- [ ] Memory/performance benchmarks documented

---

## Resources

### MLX Documentation
- [MLX GitHub](https://github.com/ml-explore/mlx)
- [mlx-vlm GitHub](https://github.com/Blaizzy/mlx-vlm)
- [MLX Examples](https://github.com/ml-explore/mlx-examples)

### DeepSeek Documentation
- [DeepSeek-OCR HuggingFace](https://huggingface.co/deepseek-ai/DeepSeek-OCR)
- [DeepSeek-OCR Paper](https://arxiv.org/abs/2401.xxxxx)

### Project Documentation
- See [Documentation Guide](#documentation-guide) above

---

## Contact / Questions

For technical questions:
1. Check documentation files first
2. Search existing code for patterns
3. Review test files for usage examples
4. Check TROUBLESHOOTING.md

For this handoff:
- All core infrastructure is tested and working
- OpenRouter backend can be used as reference
- Focus is on MLX-specific implementation
- Real PDF testing is now possible on this machine
