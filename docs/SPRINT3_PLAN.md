# Sprint 3: Production Readiness and Stabilization

## Overview

**Duration:** 1 week
**Focus:** Complete integration testing with OpenRouter, stabilize test suite, production deployment readiness

Sprint 3 completes the initial product by testing with OpenRouter VLM models, addressing remaining test failures, and ensuring production-ready deployment. DeepSeek integration is planned but deferred to Sprint 4.

## Testing Strategy

**Primary Backend:** OpenRouter (nemotron-openrouter)
**API Key Required:** `OPENROUTER_API_KEY`

All integration and E2E tests will use OpenRouter VLM models. This provides:
- Real API testing without local GPU requirements
- Consistent test environment across all developers
- Validates the full pipeline with production-like conditions

## Sprint 3 Status from Sprint 2

### Completed in Sprint 2
- [x] DeepSeek vLLM Backend implementation (code complete, testing deferred)
- [x] Backend Fallback Chain
- [x] Progress Callback System
- [x] Docker Configuration
- [x] CLI Batch Processing
- [x] Performance Benchmarks
- [x] Core Documentation

### Current Test Status
- **Passing:** 242 tests
- **Failing:** 13 tests (including 3 DeepSeek tests - expected)
- **Skipped:** 28 tests

### Remaining Issues to Address
1. Complex async mock setup in backend retry tests
2. Pipeline callback test mock improvements
3. CLI test assertion refinements
4. OpenRouter integration testing

---

## Developer Assignments

### Dev-01: DeepSeek Integration Planning (NO IMPLEMENTATION)
**Separation of Concerns:** Planning, documentation, architecture review

**Deliverable:** Complete planning document for DeepSeek integration (Sprint 4)

**Tasks:**
1. Research vLLM server requirements and deployment options
2. Document hardware requirements (GPU, memory, storage)
3. Create architecture diagram for DeepSeek integration
4. Define test strategy for DeepSeek backend
5. Identify integration points and potential issues
6. Estimate effort for Sprint 4 implementation
7. Create `docs/DEEPSEEK_INTEGRATION_PLAN.md`

**Document Should Include:**
- vLLM server setup options (Docker, bare metal, cloud)
- Model variants and their requirements
- API compatibility with OpenRouter interface
- Testing approach (local vs cloud vLLM)
- Rollback strategy if DeepSeek underperforms
- Cost analysis (cloud GPU vs local)

**Files:**
- `docs/DEEPSEEK_INTEGRATION_PLAN.md` (new - planning only)

**Dependencies:** None (can start immediately)

**NOTE:** No code implementation. Planning document only.

---

### Dev-02: Test Infrastructure Stabilization
**Separation of Concerns:** Test fixtures, mock utilities, async test helpers

**Tasks:**
1. Create robust async mock utilities for aiohttp
2. Fix backend retry tests mock setup:
   - `tests/unit/backends/test_retry.py::TestBackendRetry`
3. Create reusable mock factories for common patterns
4. Add test utilities documentation
5. Skip DeepSeek tests with appropriate markers

**Files:**
- `tests/utils/mock_helpers.py` (new)
- `tests/utils/async_fixtures.py` (new)
- `tests/unit/backends/test_retry.py`
- `tests/unit/backends/test_deepseek_vllm.py` (add skip markers)
- `tests/conftest.py`

**Dependencies:** None (can start immediately)

---

### Dev-03: OpenRouter Integration Testing
**Separation of Concerns:** Live API testing, end-to-end validation

**Tasks:**
1. Create integration tests using real OpenRouter API
2. Test full pipeline with OpenRouter backend
3. Test concurrent page processing with rate limiting
4. Validate error handling with real API responses
5. Test fallback chain with OpenRouter as primary
6. Document API usage and rate limits

**Files:**
- `tests/integration/test_openrouter_live.py` (new)
- `tests/integration/test_pipeline_openrouter.py` (new)
- `tests/integration/conftest.py` (new - integration fixtures)
- `docs/OPENROUTER_TESTING.md` (new)

**Test Requirements:**
```bash
# Required environment variable
export OPENROUTER_API_KEY="your-key-here"

# Run integration tests
pytest tests/integration -v --run-live
```

**Dependencies:** None (can start immediately)

---

### Dev-04: Pipeline & Callback Tests
**Separation of Concerns:** Pipeline orchestration testing, callback mechanisms

**Tasks:**
1. Fix pipeline callback test failures:
   - `test_convert_without_progress_callback`
   - `test_callback_error_does_not_stop_conversion`
   - `test_conversion_error_callback_invoked`
2. Improve mock backend setup in pipeline tests
3. Add pipeline tests using OpenRouter fixtures
4. Test concurrent page processing

**Files:**
- `tests/unit/test_pipeline.py`
- `tests/integration/test_pipeline_integration.py` (new)
- `src/docling_hybrid/orchestrator/pipeline.py` (if fixes needed)

**Dependencies:** Dev-02 (mock utilities)

---

### Dev-05: CLI & E2E Testing with OpenRouter
**Separation of Concerns:** Command-line interface, user experience, E2E workflows

**Tasks:**
1. Fix remaining CLI test failures:
   - `test_convert_missing_pdf`
2. Add comprehensive E2E CLI tests using OpenRouter
3. Test batch processing with real PDFs
4. Improve error messages and user feedback
5. Add shell completion scripts
6. Create sample test PDFs

**Files:**
- `tests/unit/test_cli.py`
- `tests/e2e/test_cli_e2e.py` (new)
- `tests/fixtures/sample_pdfs/` (new - test documents)
- `src/docling_hybrid/cli/main.py`
- `scripts/completion.sh` (new)

**E2E Test Example:**
```bash
# Test with real PDF and OpenRouter
docling-hybrid-ocr convert tests/fixtures/sample_pdfs/simple.pdf -o output.md
```

**Dependencies:** Dev-03 (OpenRouter testing), Dev-04 (pipeline fixes)

---

### Dev-06: Documentation & Release Prep
**Separation of Concerns:** Documentation, packaging, release

**Tasks:**
1. Finalize API documentation
2. Update QUICK_START.md with OpenRouter examples
3. Create CHANGELOG.md
4. Prepare PyPI packaging
5. Create release checklist
6. Document OpenRouter setup for users

**Files:**
- `docs/API_REFERENCE.md` (update)
- `docs/QUICK_START.md` (update with OpenRouter focus)
- `CHANGELOG.md` (new)
- `docs/RELEASE_CHECKLIST.md` (new)
- `pyproject.toml` (release prep)

**Dependencies:** All other tasks (final step)

---

## Parallel Development Strategy

```
Week 1:
┌────────────────────────────────────────────────────────────────┐
│ Day 1-2                                                        │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│ │   Dev-01    │ │   Dev-02    │ │   Dev-03    │               │
│ │  DeepSeek   │ │ Test Infra  │ │ OpenRouter  │               │
│ │  PLANNING   │ │   Mocks     │ │ Integration │               │
│ └─────────────┘ └─────────────┘ └─────────────┘               │
├────────────────────────────────────────────────────────────────┤
│ Day 3-4                                                        │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│ │   Dev-01    │ │   Dev-04    │ │   Dev-05    │               │
│ │  Planning   │ │  Pipeline   │ │  CLI E2E    │               │
│ │   Doc Done  │ │   Tests     │ │   Tests     │               │
│ └─────────────┘ └─────────────┘ └─────────────┘               │
├────────────────────────────────────────────────────────────────┤
│ Day 5                                                          │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │                      Dev-06                                 ││
│ │              Documentation & Release Prep                   ││
│ └─────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

---

## OpenRouter Testing Setup

### Environment Configuration

```bash
# Required for integration tests
export OPENROUTER_API_KEY="sk-or-v1-..."

# Optional: for testing specific models
export OPENROUTER_MODEL="nvidia/nemotron-nano-12b-v2-vl:free"
```

### Running Tests

```bash
# Unit tests (no API key needed)
pytest tests/unit -v

# Integration tests (requires OPENROUTER_API_KEY)
pytest tests/integration -v

# E2E tests (requires OPENROUTER_API_KEY)
pytest tests/e2e -v

# Full test suite
pytest tests/ -v
```

### Rate Limiting Considerations

- OpenRouter has rate limits per model
- Integration tests should include delays between requests
- Use `pytest-asyncio` with rate limiting fixtures
- Consider using free-tier models for testing

---

## Definition of Done

### Sprint 3 Completion Criteria:

1. **Test Coverage:**
   - All unit tests passing (>95% pass rate)
   - OpenRouter integration tests passing
   - E2E tests for CLI workflows passing

2. **OpenRouter Integration:**
   - Live API tests validated
   - Rate limiting handled properly
   - Error handling tested with real responses

3. **DeepSeek Planning:**
   - Complete planning document (`DEEPSEEK_INTEGRATION_PLAN.md`)
   - Ready for Sprint 4 implementation

4. **Documentation:**
   - All APIs documented
   - Quick start guide tested with OpenRouter
   - Deployment guide complete

5. **Release Ready:**
   - PyPI package buildable
   - Docker image tested
   - Release checklist complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OpenRouter rate limits | Add delays, use free-tier models |
| API key exposure | Use environment variables, .env files |
| Async mock complexity | Create dedicated mock utility module |
| Pipeline test flakiness | Add timeouts, use deterministic mocks |
| Integration test costs | Use free-tier models, limit test frequency |

---

## Success Metrics

- [ ] 0 failing unit tests (DeepSeek tests skipped with markers)
- [ ] OpenRouter integration tests passing
- [ ] 100% documented public API
- [ ] <5% test flake rate
- [ ] Successful PyPI test upload
- [ ] Docker image builds without errors
- [ ] All CLI commands tested E2E with OpenRouter
- [ ] DeepSeek planning document complete

---

## Handoff Notes

### For Dev-01 (DeepSeek Planning):
- **NO CODE IMPLEMENTATION** - planning document only
- Review `src/docling_hybrid/backends/deepseek_vllm.py` for understanding
- Research vLLM deployment options
- Document should enable Sprint 4 implementation

### For Dev-02 (Test Infrastructure):
- Main issue: `session.post()` returns coroutine, needs async context manager mock
- See pattern in `tests/unit/backends/test_retry.py`
- Create helper: `AsyncContextManagerMock` class
- Add `@pytest.mark.skip(reason="DeepSeek not integrated")` markers

### For Dev-03 (OpenRouter Integration):
- Focus on real API testing
- Use `OPENROUTER_API_KEY` environment variable
- Test rate limiting and error handling
- Create integration test fixtures

### For Dev-04 (Pipeline):
- Pipeline tests at `tests/unit/test_pipeline.py`
- Callback tests need proper mock backend setup
- Review `conftest.py` for existing fixtures

### For Dev-05 (CLI E2E):
- CLI at `src/docling_hybrid/cli/main.py`
- Tests at `tests/unit/test_cli.py`
- Create sample PDFs for testing
- Test with real OpenRouter backend

### For Dev-06 (Documentation):
- API docs at `docs/API_REFERENCE.md`
- Quick start at `docs/QUICK_START.md`
- Focus on OpenRouter setup for users
- Ensure examples work with real API

---

## Sprint 4 Preview (DeepSeek Implementation)

Based on Dev-01's planning document, Sprint 4 will:
1. Implement vLLM server deployment
2. Create DeepSeek integration tests
3. Add DeepSeek to fallback chain
4. Performance comparison: OpenRouter vs DeepSeek
5. Document local deployment options
