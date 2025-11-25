# Sprint 3: Production Readiness and Stabilization

## Overview

**Duration:** 1 week
**Focus:** Complete integration testing, stabilize test suite, production deployment readiness

Sprint 3 completes the initial product by addressing remaining test failures, finalizing DeepSeek integration, and ensuring production-ready deployment.

## Sprint 3 Status from Sprint 2

### Completed in Sprint 2
- [x] DeepSeek vLLM Backend implementation
- [x] Backend Fallback Chain
- [x] Progress Callback System
- [x] Docker Configuration
- [x] CLI Batch Processing
- [x] Performance Benchmarks
- [x] Core Documentation

### Current Test Status
- **Passing:** 242 tests
- **Failing:** 13 tests (including 3 DeepSeek tests expected to fail)
- **Skipped:** 28 tests

### Remaining Issues to Address
1. DeepSeek vLLM integration testing (requires live endpoint)
2. Complex async mock setup in backend retry tests
3. Pipeline callback test mock improvements
4. CLI test assertion refinements

---

## Developer Assignments

### Dev-01: DeepSeek Integration & Testing
**Separation of Concerns:** External API integration, vLLM server setup

**Tasks:**
1. Set up local vLLM server with DeepSeek model
2. Create integration test environment for DeepSeek
3. Fix `tests/unit/backends/test_deepseek_vllm.py` with proper mocks
4. Add end-to-end tests with real vLLM endpoint
5. Document DeepSeek setup requirements

**Files:**
- `src/docling_hybrid/backends/deepseek_vllm.py`
- `tests/integration/test_deepseek_vllm_live.py` (new)
- `docs/DEEPSEEK_SETUP.md` (new)
- `scripts/setup_vllm.sh` (new)

**Dependencies:** None (can start immediately)

---

### Dev-02: Test Infrastructure Stabilization
**Separation of Concerns:** Test fixtures, mock utilities, async test helpers

**Tasks:**
1. Create robust async mock utilities for aiohttp
2. Fix backend retry tests mock setup:
   - `tests/unit/backends/test_retry.py::TestBackendRetry`
3. Create reusable mock factories for common patterns
4. Add test utilities documentation

**Files:**
- `tests/utils/mock_helpers.py` (new)
- `tests/utils/async_fixtures.py` (new)
- `tests/unit/backends/test_retry.py`
- `tests/conftest.py`

**Dependencies:** None (can start immediately)

---

### Dev-03: Pipeline & Callback Tests
**Separation of Concerns:** Pipeline orchestration testing, callback mechanisms

**Tasks:**
1. Fix pipeline callback test failures:
   - `test_convert_without_progress_callback`
   - `test_callback_error_does_not_stop_conversion`
   - `test_conversion_error_callback_invoked`
2. Improve mock backend setup in pipeline tests
3. Add integration tests for full pipeline flow
4. Test concurrent page processing

**Files:**
- `tests/unit/test_pipeline.py`
- `tests/integration/test_pipeline_integration.py` (new)
- `src/docling_hybrid/orchestrator/pipeline.py` (if fixes needed)

**Dependencies:** Dev-02 (mock utilities)

---

### Dev-04: CLI Polish & E2E Testing
**Separation of Concerns:** Command-line interface, user experience

**Tasks:**
1. Fix remaining CLI test failures:
   - `test_convert_missing_pdf`
2. Add comprehensive E2E CLI tests
3. Improve error messages and user feedback
4. Add shell completion scripts
5. Test batch processing with real PDFs

**Files:**
- `tests/unit/test_cli.py`
- `tests/e2e/test_cli_e2e.py` (new)
- `src/docling_hybrid/cli/main.py`
- `scripts/completion.sh` (new)

**Dependencies:** Dev-03 (pipeline fixes)

---

### Dev-05: Performance & Benchmarking
**Separation of Concerns:** Performance optimization, metrics collection

**Tasks:**
1. Run comprehensive benchmarks with Sprint 2 framework
2. Optimize memory usage for large PDFs
3. Tune concurrency settings
4. Document performance characteristics
5. Add performance regression tests

**Files:**
- `tests/benchmark/` (existing)
- `docs/BENCHMARKS.md` (update)
- `configs/performance.toml` (new)
- `src/docling_hybrid/common/config.py` (optimizations)

**Dependencies:** Dev-01, Dev-03 (need working integrations)

---

### Dev-06: Documentation & Release Prep
**Separation of Concerns:** Documentation, packaging, release

**Tasks:**
1. Finalize API documentation
2. Update QUICK_START.md with tested examples
3. Create CHANGELOG.md
4. Prepare PyPI packaging
5. Create release checklist

**Files:**
- `docs/API_REFERENCE.md` (update)
- `docs/QUICK_START.md` (update)
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
│ │   Dev-01    │ │   Dev-02    │ │   Dev-05    │               │
│ │  DeepSeek   │ │ Test Infra  │ │ Benchmarks  │               │
│ │   Setup     │ │   Mocks     │ │  (Parallel) │               │
│ └─────────────┘ └─────────────┘ └─────────────┘               │
├────────────────────────────────────────────────────────────────┤
│ Day 3-4                                                        │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│ │   Dev-01    │ │   Dev-03    │ │   Dev-04    │               │
│ │  DeepSeek   │ │  Pipeline   │ │    CLI      │               │
│ │   Tests     │ │   Tests     │ │   Tests     │               │
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

## Definition of Done

### Sprint 3 Completion Criteria:

1. **Test Coverage:**
   - All unit tests passing (>95% pass rate)
   - Integration tests for each backend
   - E2E tests for CLI workflows

2. **DeepSeek Integration:**
   - Working with local vLLM server
   - Documented setup process
   - Integration tests passing

3. **Documentation:**
   - All APIs documented
   - Quick start guide tested
   - Deployment guide complete

4. **Release Ready:**
   - PyPI package buildable
   - Docker image tested
   - Release checklist complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| vLLM server setup complexity | Document step-by-step, provide Docker option |
| Async mock complexity | Create dedicated mock utility module |
| Pipeline test flakiness | Add timeouts, use deterministic mocks |
| Integration test flakiness | Use test containers, mock external calls |

---

## Success Metrics

- [ ] 0 failing unit tests (excluding skipped DeepSeek if no server)
- [ ] 100% documented public API
- [ ] <5% test flake rate
- [ ] Successful PyPI test upload
- [ ] Docker image builds without errors
- [ ] All CLI commands tested E2E

---

## Handoff Notes

### For Dev-01 (DeepSeek):
- Review `src/docling_hybrid/backends/deepseek_vllm.py`
- Check existing tests at `tests/unit/backends/test_deepseek_vllm.py`
- Connection tests fail due to no live endpoint
- Consider using `testcontainers` for vLLM

### For Dev-02 (Test Infrastructure):
- Main issue: `session.post()` returns coroutine, needs async context manager mock
- See pattern in `tests/unit/backends/test_retry.py`
- Create helper: `AsyncContextManagerMock` class

### For Dev-03 (Pipeline):
- Pipeline tests at `tests/unit/test_pipeline.py`
- Callback tests need proper mock backend setup
- Review `conftest.py` for existing fixtures

### For Dev-04 (CLI):
- CLI at `src/docling_hybrid/cli/main.py`
- Tests at `tests/unit/test_cli.py`
- `test_convert_missing_pdf` has assertion issue
- Check Typer testing patterns

### For Dev-05 (Performance):
- Benchmark framework at `tests/benchmark/`
- Review `docs/BENCHMARKS.md` for baseline
- Focus on memory and concurrency tuning

### For Dev-06 (Documentation):
- API docs at `docs/API_REFERENCE.md`
- Quick start at `docs/QUICK_START.md`
- Ensure examples actually work
