# Development Continuation Guide

## Current State

**Version:** 0.1.0  
**Date:** November 2024  
**Status:** Minimal Core Complete - Ready for Extension

### What's Complete

#### Foundation (100%)
- ✅ Configuration system (layered: env → file → defaults)
- ✅ Common utilities (IDs, logging, errors)
- ✅ Pydantic data models
- ✅ Test infrastructure (pytest, fixtures)

#### Core Components (100%)
- ✅ Backend abstraction (`OcrVlmBackend` ABC)
- ✅ Backend factory (`make_backend`)
- ✅ OpenRouter/Nemotron backend (fully implemented)
- ✅ Page renderer (pypdfium2)
- ✅ Orchestrator pipeline (`HybridPipeline`)
- ✅ CLI (`docling-hybrid-ocr` command)

#### Testing (70%)
- ✅ Unit tests for common module
- ✅ Unit tests for backends
- ○ Integration tests (need mocked HTTP)
- ○ End-to-end tests (need real API)

### Implementation Status by File

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `common/config.py` | ~200 | ✅ Complete | Tested |
| `common/models.py` | ~180 | ✅ Complete | Tested |
| `common/errors.py` | ~120 | ✅ Complete | Tested |
| `common/ids.py` | ~80 | ✅ Complete | Tested |
| `common/logging.py` | ~80 | ✅ Complete | Tested |
| `backends/base.py` | ~100 | ✅ Complete | Interface |
| `backends/factory.py` | ~80 | ✅ Complete | Tested |
| `backends/openrouter_nemotron.py` | ~250 | ✅ Complete | Tested |
| `backends/deepseek_vllm_stub.py` | ~80 | ○ Stub | Phase 2 |
| `backends/deepseek_mlx_stub.py` | ~80 | ○ Stub | Phase 2 |
| `renderer/core.py` | ~150 | ✅ Complete | Tested |
| `orchestrator/pipeline.py` | ~180 | ✅ Complete | Needs integration test |
| `orchestrator/models.py` | ~60 | ✅ Complete | Tested |
| `cli/main.py` | ~200 | ✅ Complete | Manual tested |

---

## Immediate Next Steps

### Priority 1: DeepSeek vLLM Backend (Sprint 2)
**Status:** Stub exists  
**Blocking:** Production deployment on GPU servers  
**Estimated effort:** 1-2 days

**Tasks:**
1. Copy HTTP logic from `openrouter_nemotron.py`
2. Adapt for vLLM's OpenAI-compatible API
3. Test with local vLLM server
4. Add integration tests

**Files to modify:**
- `src/docling_hybrid/backends/deepseek_vllm_stub.py` → full implementation

**Acceptance criteria:**
- [ ] Can connect to local vLLM server
- [ ] Uses same prompts as Nemotron backend
- [ ] Passes same interface tests
- [ ] Works with `make_backend("deepseek-vllm")`

### Priority 2: Integration Tests (Sprint 2)
**Status:** Not started  
**Blocking:** CI/CD confidence  
**Estimated effort:** 1 day

**Tasks:**
1. Create HTTP mocking fixtures (aioresponses)
2. Test Nemotron backend with mocked responses
3. Test full pipeline with mocked backend
4. Add to CI workflow

**Files to create:**
- `tests/integration/test_nemotron_backend.py`
- `tests/integration/test_pipeline.py`

### Priority 3: DeepSeek MLX Backend (Sprint 3)
**Status:** Stub exists  
**Blocking:** macOS deployment  
**Estimated effort:** 2-3 days

**Tasks:**
1. Research mlx-vlm API
2. Decide: direct API or HTTP sidecar
3. Implement chosen approach
4. Test on Apple Silicon Mac

### Priority 4: Block-Level Processing (Sprint 3-4)
**Status:** Stub module exists  
**Blocking:** Better table/formula handling  
**Estimated effort:** 5-7 days

**Tasks:**
1. Design block segmentation from Docling output
2. Implement backend routing per block type
3. Implement candidate merging
4. Add configuration for routing rules

---

## Architecture Decisions

### Decision 1: Why Async Everywhere
**Rationale:** VLM API calls take 2-10 seconds. Async enables concurrent page processing.
**Trade-off:** More complex code, but 5-10x throughput improvement.
**Alternative considered:** Threads - rejected due to GIL and complexity.

### Decision 2: Backend Interface Design
**Chosen:** Abstract base class with factory pattern
**Rationale:**
- Clear contract via abstract methods
- Type hints work well
- Easy to test with mocks
- Factory enables runtime selection

### Decision 3: pypdfium2 for Rendering
**Chosen:** pypdfium2 instead of PyMuPDF or Docling's renderer
**Rationale:**
- Faster and lower memory
- No extra dependencies
- Good quality at all DPIs
- MIT licensed

### Decision 4: Page Separators in Output
**Chosen:** Optional HTML comments (`<!-- PAGE N -->`)
**Rationale:**
- Easy to find page boundaries
- Doesn't affect Markdown rendering
- Can be disabled via config

---

## Common Pitfalls

### Pitfall 1: Forgetting to Set API Key
**Problem:** `ConfigurationError: Missing OpenRouter API key`
**Solution:** 
```bash
export OPENROUTER_API_KEY=your-key
# or add to .env.local and source it
```

### Pitfall 2: Using Sync Code in Async Context
**Problem:** `RuntimeError: This event loop is already running`
**Solution:** Use `await` consistently, don't mix sync and async:
```python
# Bad
result = pipeline.convert_pdf(path)

# Good
result = await pipeline.convert_pdf(path)
```

### Pitfall 3: Not Closing Backend
**Problem:** Unclosed aiohttp session warnings
**Solution:** Use context manager:
```python
async with make_backend(config) as backend:
    result = await backend.page_to_markdown(...)
```

### Pitfall 4: High DPI on Low Memory
**Problem:** Out of memory when rendering at 300 DPI
**Solution:** Use 150 DPI for local development:
```bash
docling-hybrid-ocr convert doc.pdf --dpi 150
```

---

## Testing Strategy

### Test Pyramid
```
       /\
      /E2E\      5% - Manual testing with real API
     /------\
    / Integ \    25% - Mocked HTTP responses
   /----------\
  /   Unit     \ 70% - Pure logic, no I/O
 /--------------\
```

### Running Tests
```bash
# Unit tests only (fast, ~10 seconds)
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=src/docling_hybrid --cov-report=html

# Specific test file
pytest tests/unit/test_backends.py -v

# Specific test
pytest tests/unit/test_backends.py::TestBackendFactory::test_list_backends -v
```

### What to Test

**Always test (unit):**
- Data model validation
- ID generation
- Configuration loading
- Error types
- Backend factory logic

**Integration test (mocked):**
- Backend HTTP handling
- Pipeline page iteration
- Output concatenation

**Manual test (real API):**
- Full conversion flow
- Different PDF types
- Error recovery

---

## Known Issues

### Issue 1: Large PDF Memory Usage
**Impact:** Can run out of memory on 12GB machines with large PDFs
**Workaround:** Use `--max-pages` to limit processing
**Fix planned:** Sprint 4 - streaming processing

### Issue 2: No Concurrent Page Processing Yet
**Impact:** Pages processed sequentially, slower than optimal
**Workaround:** None currently
**Fix planned:** Sprint 3 - add asyncio.gather for pages

### Issue 3: Table Markdown Sometimes Malformed
**Impact:** VLM occasionally produces invalid table syntax
**Workaround:** Manual post-processing
**Fix planned:** Phase 2 - add table validation/repair

---

## Resources

### Internal Documentation
- **CLAUDE.md** - Master context (start here)
- **LOCAL_DEV.md** - Local development guide
- **docs/ARCHITECTURE.md** - System architecture

### External Documentation
- [OpenRouter API](https://openrouter.ai/docs)
- [pypdfium2](https://pypdfium2.readthedocs.io/)
- [Pydantic](https://docs.pydantic.dev/)
- [structlog](https://www.structlog.org/)
- [Typer](https://typer.tiangolo.com/)

### Example Commands
```bash
# Basic conversion
docling-hybrid-ocr convert document.pdf

# With options
docling-hybrid-ocr convert document.pdf -o output.md --dpi 150 --max-pages 5

# List backends
docling-hybrid-ocr backends

# Show system info
docling-hybrid-ocr info
```

---

## Sprint Plans

### Sprint 1 (Complete)
- ✅ Core infrastructure
- ✅ Nemotron backend
- ✅ Basic pipeline
- ✅ CLI

### Sprint 2 (Current)
- [ ] DeepSeek vLLM backend implementation
- [ ] Integration tests with mocked HTTP
- [ ] Documentation refinement

### Sprint 3
- [ ] DeepSeek MLX backend
- [ ] Concurrent page processing
- [ ] Block segmentation design

### Sprint 4
- [ ] Block-level processing
- [ ] Table/formula backends
- [ ] Merge policies

---

## Contact / Questions

For technical questions:
- Check documentation files first
- Search existing code for patterns
- Review test files for usage examples

For urgent issues:
- Create GitHub issue with reproduction steps
- Include error messages and config (without API keys!)
