# Sprint 4 Plan: DeepSeek OCR MLX Implementation

## Overview

**Sprint Duration:** 7 working days
**Developer:** Single developer with Claude Code
**Target Platform:** Mac M2 Air with 24GB RAM
**Primary Goal:** Implement fully functional DeepSeek OCR using Apple MLX

---

## Sprint Goals

### Primary Objectives

1. **DeepSeek MLX Backend** - Complete, production-ready implementation
2. **Comprehensive Testing** - Test with all 325 PDFs in collection
3. **Performance Optimization** - Optimize for M2 Air hardware
4. **Documentation** - MLX-specific setup and usage guides

### Success Criteria

- [ ] DeepSeek MLX backend passes all unit tests
- [ ] Backend integrates with existing pipeline
- [ ] Successfully processes 90%+ of test PDFs
- [ ] Performance meets targets (3+ pages/minute)
- [ ] Memory usage stays under 16GB peak
- [ ] Documentation complete for Mac setup

---

## Timeline

### Day 1: Environment Setup & Backend Skeleton

**Morning:**
- [ ] Set up Mac development environment
- [ ] Install Python 3.11, create venv
- [ ] Install MLX, mlx-lm, mlx-vlm packages
- [ ] Verify MLX installation with simple test

**Afternoon:**
- [ ] Download DeepSeek-OCR model
- [ ] Test model loading with mlx-vlm
- [ ] Create `deepseek_mlx.py` from stub
- [ ] Implement basic `__init__` and model loading

### Day 2: Core Implementation

**Morning:**
- [ ] Implement `_ensure_model_loaded()` with lazy loading
- [ ] Implement `_generate()` method for inference
- [ ] Implement `page_to_markdown()` method
- [ ] Test with simple image

**Afternoon:**
- [ ] Implement `table_to_markdown()` method
- [ ] Implement `formula_to_latex()` method
- [ ] Add proper error handling
- [ ] Add logging throughout

### Day 3: Unit Tests & Factory Integration

**Morning:**
- [ ] Create `tests/unit/backends/test_deepseek_mlx.py`
- [ ] Test backend initialization
- [ ] Test model loading (with mocks)
- [ ] Test image conversion

**Afternoon:**
- [ ] Update `factory.py` to support MLX backend
- [ ] Update `backends/__init__.py` exports
- [ ] Create `configs/mac-m2-air.toml`
- [ ] Run unit tests and fix issues

### Day 4: Integration Testing

**Morning:**
- [ ] Create `tests/integration/test_mlx_integration.py`
- [ ] Test full pipeline with MLX backend
- [ ] Test with 10 small PDFs from collection
- [ ] Debug any integration issues

**Afternoon:**
- [ ] Test fallback to OpenRouter
- [ ] Test progress callbacks with MLX
- [ ] Test error recovery scenarios
- [ ] Run all integration tests

### Day 5: PDF Collection Testing (Phase 1)

**Morning:**
- [ ] Process 50 small PDFs (<500KB)
- [ ] Log results and timing
- [ ] Identify any failures
- [ ] Check memory usage patterns

**Afternoon:**
- [ ] Process 50 medium PDFs (500KB-2MB)
- [ ] Compare output quality samples
- [ ] Fix any issues discovered
- [ ] Document problematic PDFs

### Day 6: PDF Collection Testing (Phase 2)

**Morning:**
- [ ] Process 20 large PDFs (>5MB)
- [ ] Monitor memory under load
- [ ] Test batch processing limits
- [ ] Optimize where needed

**Afternoon:**
- [ ] Process remaining PDFs
- [ ] Generate summary report
- [ ] Calculate success rate
- [ ] Identify patterns in failures

### Day 7: Optimization & Documentation

**Morning:**
- [ ] Performance profiling
- [ ] Memory optimization
- [ ] Benchmark final implementation
- [ ] Compare with OpenRouter results

**Afternoon:**
- [ ] Write MLX setup documentation
- [ ] Update CLAUDE.md with Mac instructions
- [ ] Create performance tuning guide
- [ ] Final commit and cleanup

---

## Implementation Details

### Backend Structure

```
src/docling_hybrid/backends/
├── __init__.py           # Add DeepseekOcrMlxBackend export
├── base.py               # No changes
├── factory.py            # Add MLX backend support
├── deepseek_mlx.py       # NEW: Full implementation
├── deepseek_vllm.py      # Reference implementation
└── openrouter_nemotron.py # Reference implementation
```

### Key Implementation Decisions

#### 1. Model Loading Strategy: Lazy Loading

```python
async def _ensure_model_loaded(self) -> None:
    """Load model on first use, not initialization."""
    if not self._model_loaded:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
```

**Rationale:**
- Faster startup time
- Model only loaded when needed
- Memory freed when backend closed

#### 2. Inference Strategy: Thread Pool Executor

```python
async def page_to_markdown(self, image_bytes, page_num, doc_id) -> str:
    await self._ensure_model_loaded()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, self._generate, prompt, image
    )
    return result
```

**Rationale:**
- MLX operations are CPU-bound
- Keeps async interface compatible
- Allows concurrent I/O during inference

#### 3. Memory Management: Sequential Processing

```python
# In pipeline, don't use concurrent workers for MLX
if backend_name == "deepseek-mlx":
    max_workers = 1  # Force sequential
```

**Rationale:**
- MLX model uses significant memory
- Concurrent calls may exceed 24GB RAM
- Sequential is safer for M2 Air

### Configuration Changes

#### New Backend Config

```toml
# configs/mac-m2-air.toml
[[backends.candidates]]
name = "deepseek-mlx"
model = "deepseek-ai/DeepSeek-OCR"
temperature = 0.0
max_tokens = 8192
timeout_s = 180
```

#### Factory Update

```python
# factory.py
def make_backend(config: OcrBackendConfig) -> OcrVlmBackend:
    if config.name == "deepseek-mlx":
        from docling_hybrid.backends.deepseek_mlx import DeepseekOcrMlxBackend
        return DeepseekOcrMlxBackend(config)
    # ... existing backends
```

---

## Testing Strategy

### Test Levels

#### 1. Unit Tests (50%)

```python
# tests/unit/backends/test_deepseek_mlx.py

class TestDeepseekMlxBackend:
    def test_init(self):
        """Test backend initialization."""

    def test_model_not_loaded_on_init(self):
        """Verify lazy loading."""

    @pytest.mark.asyncio
    async def test_page_to_markdown_calls_generate(self):
        """Test page conversion with mocked model."""

    def test_image_to_pil_conversion(self):
        """Test bytes to PIL Image conversion."""
```

#### 2. Integration Tests (30%)

```python
# tests/integration/test_mlx_integration.py

@pytest.mark.mlx
@pytest.mark.skipif(sys.platform != "darwin", reason="MLX requires macOS")
class TestMlxIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test PDF to Markdown with MLX backend."""

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Test fallback to OpenRouter."""
```

#### 3. E2E Tests (20%)

```python
# tests/e2e/test_pdf_collection.py

@pytest.mark.slow
@pytest.mark.mlx
class TestPdfCollection:
    @pytest.mark.asyncio
    async def test_small_pdfs(self):
        """Test PDFs under 100KB."""

    @pytest.mark.asyncio
    async def test_large_pdfs(self):
        """Test PDFs over 5MB."""
```

### Test Commands

```bash
# Unit tests only (fast)
pytest tests/unit -v

# MLX-specific tests
pytest tests/ -v -m mlx

# Skip MLX tests (for non-Mac CI)
pytest tests/ -v -m "not mlx"

# Full suite with coverage
pytest tests/ -v --cov=src/docling_hybrid --cov-report=html
```

---

## PDF Testing Plan

### Collection Summary

- **Total PDFs:** 325
- **Total Size:** 1.14 GB
- **Size Range:** 14 KB - 51 MB

### Testing Phases

#### Phase 1: Quick Validation (20 PDFs)

Select diverse samples:
- 5 small (<100KB)
- 5 medium (100KB-1MB)
- 5 large (1-5MB)
- 5 very large (>5MB)

**Command:**
```bash
python scripts/test_sample.py --sample-size 20 --output results/phase1.json
```

#### Phase 2: Category Testing (100 PDFs)

Test by document type:
- 40 ArXiv papers
- 20 BioRxiv papers
- 20 Journal articles
- 20 Books/chapters

**Command:**
```bash
python scripts/test_categories.py --output results/phase2.json
```

#### Phase 3: Full Collection (325 PDFs)

Process all PDFs with detailed logging:
```bash
docling-hybrid-ocr batch \
  --input-dir pdfs/ \
  --output-dir output/ \
  --backend deepseek-mlx \
  --log-file results/full_test.log \
  --max-pages 10  # Limit for time
```

### Quality Metrics

Track for each PDF:
- Processing time
- Memory peak
- Page count
- Output length
- Error (if any)

---

## Performance Targets

### Hardware Constraints

**Mac M2 Air 24GB:**
- 8 CPU cores (4 performance, 4 efficiency)
- 8 GPU cores (for MLX)
- 24 GB unified memory

### Target Metrics

| Metric | Target | Acceptable | Stretch |
|--------|--------|------------|---------|
| Pages/minute | 5 | 3 | 8 |
| Tokens/second | 25 | 15 | 40 |
| Memory peak | 14GB | 18GB | 12GB |
| Model load | 20s | 30s | 10s |
| First page | 15s | 25s | 8s |

### Optimization Priorities

1. **Memory:** Keep under 16GB to leave headroom
2. **Latency:** Minimize time to first result
3. **Throughput:** Maximize pages per hour

---

## Risks & Mitigations

### Risk 1: Model Too Large for 24GB

**Probability:** Medium
**Impact:** High
**Mitigation:**
- Use quantized model (Q4 or Q8)
- Reduce max_tokens
- Clear GPU cache between pages

### Risk 2: MLX Slower Than Expected

**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Accept lower throughput
- Use OpenRouter for batch jobs
- Implement async model swapping

### Risk 3: Model Quality Issues

**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Compare with OpenRouter baseline
- Document quality differences
- Allow per-document backend selection

### Risk 4: Installation Complexity

**Probability:** Low
**Impact:** Low
**Mitigation:**
- Document exact steps
- Create setup script
- Provide troubleshooting guide

---

## Deliverables Checklist

### Code

- [ ] `src/docling_hybrid/backends/deepseek_mlx.py`
- [ ] Updated `factory.py`
- [ ] Updated `backends/__init__.py`
- [ ] `configs/mac-m2-air.toml`
- [ ] `tests/unit/backends/test_deepseek_mlx.py`
- [ ] `tests/integration/test_mlx_integration.py`

### Documentation

- [ ] Updated CONTINUATION.md
- [ ] docs/MLX_SETUP.md
- [ ] docs/MAC_DEPLOYMENT.md
- [ ] docs/PERFORMANCE_TUNING.md
- [ ] Updated CLAUDE.md

### Test Results

- [ ] Unit test results
- [ ] Integration test results
- [ ] PDF collection test report
- [ ] Performance benchmark results
- [ ] Quality comparison report

---

## Sprint Retrospective Template

### What Went Well
-
-

### What Could Be Improved
-
-

### Action Items for Sprint 5
-
-

### Performance Summary
- Total PDFs processed: __/325
- Success rate: __%
- Average pages/minute: __
- Peak memory usage: __GB

---

**Document Version:** 1.0
**Created:** November 2024
**Sprint:** 4
