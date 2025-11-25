# Docling Hybrid OCR - Comprehensive Parallel Development Plan

## Code Review Summary

### Current State Assessment

| Component | Status | Lines | Test Coverage | Notes |
|-----------|--------|-------|---------------|-------|
| **common/config.py** | ✅ Complete | ~320 | High | Layered config, Pydantic validation |
| **common/models.py** | ✅ Complete | ~335 | High | Well-structured data models |
| **common/errors.py** | ✅ Complete | ~242 | High | Clean exception hierarchy |
| **common/ids.py** | ✅ Complete | ~155 | High | ID generation utilities |
| **common/logging.py** | ✅ Complete | ~161 | High | Structlog integration |
| **backends/base.py** | ✅ Complete | ~227 | N/A | ABC well-defined |
| **backends/factory.py** | ✅ Complete | ~176 | High | Factory pattern, registration |
| **backends/openrouter_nemotron.py** | ✅ Complete | ~504 | Moderate | Fully functional |
| **backends/deepseek_vllm_stub.py** | ○ Stub | ~171 | N/A | Raises NotImplementedError |
| **backends/deepseek_mlx_stub.py** | ○ Stub | ~195 | N/A | Raises NotImplementedError |
| **renderer/core.py** | ✅ Complete | ~317 | Moderate | pypdfium2 integration |
| **orchestrator/pipeline.py** | ✅ Complete | ~296 | Low | Sequential processing only |
| **orchestrator/models.py** | ✅ Complete | ~105 | High | Pydantic models |
| **cli/main.py** | ✅ Complete | ~262 | Low | Typer + Rich |
| **blocks/** | ○ Stub | Minimal | None | Phase 2 |
| **eval/** | ○ Stub | Minimal | None | Phase 2 |
| **exporters/** | ○ Stub | Minimal | None | Phase 2 |

### Code Quality Findings

**Strengths:**
1. Clean architecture with well-defined abstractions
2. Comprehensive error handling with structured exceptions
3. Consistent use of Pydantic for validation
4. Good separation of concerns
5. Excellent documentation in docstrings and markdown

**Areas for Improvement:**
1. **Missing concurrent page processing** - Pipeline processes sequentially
2. **No retry logic** in backend HTTP calls
3. **No integration tests** with mocked HTTP
4. **Incomplete test coverage** for CLI and pipeline
5. **DeepSeek backends** are stubs
6. **No block-level processing** implemented
7. **No evaluation framework** implemented

---

## Team Structure (10 Developers)

| ID | Role | Primary Domain | Secondary Domain |
|----|------|----------------|------------------|
| **D01** | Tech Lead | Architecture, Integration | Code Review |
| **D02** | Backend Lead | OCR Backends | API Integration |
| **D03** | Pipeline Lead | Orchestrator | Data Flow |
| **D04** | Infrastructure | Config, CI/CD, Logging | DevOps |
| **D05** | Renderer Specialist | PDF Rendering | Image Processing |
| **D06** | CLI/UX Lead | CLI, User Experience | Documentation |
| **D07** | Testing Lead | Test Infrastructure | Quality Assurance |
| **D08** | Documentation Lead | Docs, Examples | Developer Experience |
| **D09** | Block Processing | Segmentation, Routing | Docling Integration |
| **D10** | Evaluation Lead | Metrics, Benchmarks | Quality Measurement |

---

## Development Stages Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              STAGE 1: PRODUCTION-READY MINIMAL SYSTEM (v0.1.0)              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Sprint 1          Sprint 2          Sprint 3          Sprint 4             │
│  Weeks 1-2         Weeks 3-4         Weeks 5-6         Weeks 7-8            │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │Hardening │     │Concurrency│    │Integration│    │ Polish & │           │
│  │& Testing │     │& Retry   │     │& CLI     │     │ Release  │  ★ v0.1.0│
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘           │
├─────────────────────────────────────────────────────────────────────────────┤
│               STAGE 2: FULL FEATURE SET (v1.0.0)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Sprint 5          Sprint 6          Sprint 7          Sprint 8             │
│  Weeks 9-10        Weeks 11-12       Weeks 13-14       Weeks 15-16          │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │ DeepSeek │     │  Block   │     │  Multi-  │     │  Eval &  │           │
│  │ Backends │     │Processing│     │ Backend  │     │ Release  │  ★ v1.0.0│
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# STAGE 1: PRODUCTION-READY MINIMAL SYSTEM

## Sprint 1: Hardening & Testing (Weeks 1-2)
**Theme: "Strengthen the foundation"**

### Sprint 1 Objectives
1. Achieve >85% test coverage on existing code
2. Add mocked integration tests
3. Implement HTTP retry logic
4. Fix known issues (concurrent processing, memory)
5. Improve error messages and logging

### Sprint 1 Work Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SPRINT 1: PARALLEL WORK STREAMS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  D01 (Tech Lead)                                                             │
│   └── Architecture review, code review, integration planning                 │
│   └── Define test coverage requirements                                      │
│   └── Design concurrent processing strategy                                  │
│                                                                              │
│  D02 (Backend Lead)                                                          │
│   └── S1-D02-01: Implement HTTP retry logic in backends                      │
│   └── S1-D02-02: Add rate limiting awareness                                 │
│   └── S1-D02-03: Improve backend error messages                              │
│   Files: backends/openrouter_nemotron.py, common/http.py (new)               │
│                                                                              │
│  D03 (Pipeline Lead)                                                         │
│   └── S1-D03-01: Design asyncio.gather for concurrent pages                  │
│   └── S1-D03-02: Add semaphore for concurrency limit                         │
│   └── S1-D03-03: Write pipeline unit tests                                   │
│   Files: orchestrator/pipeline.py, tests/unit/test_pipeline.py               │
│                                                                              │
│  D04 (Infrastructure)                                                        │
│   └── S1-D04-01: Create common/http.py with retry utilities                  │
│   └── S1-D04-02: Improve config validation                                   │
│   └── S1-D04-03: Add GitHub Actions CI improvements                          │
│   Files: common/http.py, common/retry.py, .github/workflows/                 │
│                                                                              │
│  D05 (Renderer)                                                              │
│   └── S1-D05-01: Add memory optimization for large PDFs                      │
│   └── S1-D05-02: Implement batch rendering option                            │
│   └── S1-D05-03: Write renderer integration tests                            │
│   Files: renderer/core.py, tests/unit/test_renderer.py                       │
│                                                                              │
│  D06 (CLI Lead)                                                              │
│   └── S1-D06-01: Improve CLI error messages                                  │
│   └── S1-D06-02: Add progress bar for multi-page conversion                  │
│   └── S1-D06-03: Write CLI unit tests                                        │
│   Files: cli/main.py, tests/unit/test_cli.py                                 │
│                                                                              │
│  D07 (Testing Lead)                                                          │
│   └── S1-D07-01: Create HTTP mocking infrastructure                          │
│   └── S1-D07-02: Write backend integration tests (mocked)                    │
│   └── S1-D07-03: Create test fixtures (sample PDFs)                          │
│   Files: tests/mocks/, tests/integration/, tests/fixtures/                   │
│                                                                              │
│  D08 (Documentation)                                                         │
│   └── S1-D08-01: Update CLAUDE.md with current state                         │
│   └── S1-D08-02: Write API documentation                                     │
│   └── S1-D08-03: Create troubleshooting guide                                │
│   Files: CLAUDE.md, docs/API.md, docs/TROUBLESHOOTING.md                     │
│                                                                              │
│  D09 (Block Processing)                                                      │
│   └── S1-D09-01: Research Docling block extraction API                       │
│   └── S1-D09-02: Write design document for block processing                  │
│   └── S1-D09-03: Prototype block extraction (non-production)                 │
│   Files: docs/design/BLOCK_PROCESSING.md, prototypes/                        │
│                                                                              │
│  D10 (Evaluation)                                                            │
│   └── S1-D10-01: Research OCR evaluation metrics (CER, WER, TEDS)            │
│   └── S1-D10-02: Design ground truth format                                  │
│   └── S1-D10-03: Write evaluation framework design doc                       │
│   Files: docs/design/EVALUATION.md, eval/types.py                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sprint 1 Task Cards

#### S1-D02-01: HTTP Retry Logic
```yaml
Owner: D02 (Backend Lead)
Priority: P0-BLOCKING
Duration: 3 days
Dependencies: S1-D04-01 (retry utilities)
Branch: feat/s1-backend-retry

Description: |
  Add exponential backoff retry logic to backend HTTP calls for resilience
  against transient failures.

Tasks:
  - Add retry wrapper to _post_chat method
  - Handle 429 rate limit responses with Retry-After header
  - Handle 5xx errors with exponential backoff
  - Log retry attempts with context
  - Make retry parameters configurable

Files:
  - src/docling_hybrid/backends/openrouter_nemotron.py
  - tests/unit/backends/test_retry.py

Acceptance Criteria:
  - Retries on 429, 500, 502, 503, 504 status codes
  - Exponential backoff: 1s, 2s, 4s, 8s (configurable)
  - Respects Retry-After header
  - Configurable max retries (default: 3)
  - All existing tests still pass
  - New tests for retry scenarios
```

#### S1-D03-01: Concurrent Page Processing
```yaml
Owner: D03 (Pipeline Lead)
Priority: P0-BLOCKING
Duration: 4 days
Dependencies: Sprint 1 foundation
Branch: feat/s1-concurrent-pages

Description: |
  Implement asyncio.gather for concurrent page processing with configurable
  concurrency limit via semaphore.

Tasks:
  - Add asyncio.Semaphore for concurrency control
  - Refactor convert_pdf to use asyncio.gather
  - Maintain page order in output
  - Handle per-page errors without failing others
  - Add progress callback support

Implementation Sketch:
  ```python
  async def convert_pdf(self, ...):
      semaphore = asyncio.Semaphore(self.config.resources.max_workers)

      async def process_with_limit(page_idx):
          async with semaphore:
              return await self._process_page(...)

      tasks = [process_with_limit(i) for i in range(start, end)]
      results = await asyncio.gather(*tasks, return_exceptions=True)

      # Sort by page index, handle exceptions
      ...
  ```

Files:
  - src/docling_hybrid/orchestrator/pipeline.py
  - tests/unit/orchestrator/test_concurrent.py

Acceptance Criteria:
  - Concurrent processing works with configurable limit
  - Page order is preserved in output
  - Individual page failures don't stop processing
  - Performance improvement measurable
```

#### S1-D04-01: Retry Utilities Module
```yaml
Owner: D04 (Infrastructure)
Priority: P0-BLOCKING
Duration: 2 days
Dependencies: None
Branch: feat/s1-retry-utils

Description: |
  Create reusable async retry utilities for HTTP operations.

Tasks:
  - Create common/retry.py with retry_async decorator
  - Support exponential backoff
  - Support max retries
  - Support exception filtering
  - Write comprehensive unit tests

Implementation:
  ```python
  async def retry_async(
      func: Callable[..., Awaitable[T]],
      max_retries: int = 3,
      initial_delay: float = 1.0,
      exponential_base: float = 2.0,
      max_delay: float = 60.0,
      retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
  ) -> T:
      """Retry an async function with exponential backoff."""
      ...
  ```

Files:
  - src/docling_hybrid/common/retry.py
  - tests/unit/common/test_retry.py

Acceptance Criteria:
  - Retry logic is correct
  - Backoff timing is correct
  - Non-retryable exceptions propagate immediately
  - >95% test coverage
```

#### S1-D07-01: HTTP Mocking Infrastructure
```yaml
Owner: D07 (Testing Lead)
Priority: P0-BLOCKING
Duration: 3 days
Dependencies: None
Branch: feat/s1-http-mocks

Description: |
  Create comprehensive HTTP mocking infrastructure using aioresponses
  for testing backend integrations without real API calls.

Tasks:
  - Set up aioresponses fixtures
  - Create mock response factories
  - Create error response fixtures
  - Document mock usage patterns

Files:
  - tests/mocks/__init__.py
  - tests/mocks/http.py
  - tests/mocks/responses.py
  - tests/integration/__init__.py
  - tests/integration/test_backend_http.py

Mock Factory Example:
  ```python
  def mock_openrouter_success(content: str = "# Test"):
      return {
          "choices": [{"message": {"content": content}}]
      }

  def mock_openrouter_rate_limit(retry_after: int = 60):
      return aioresponses.CallbackResult(
          status=429,
          headers={"Retry-After": str(retry_after)},
          payload={"error": "Rate limited"}
      )
  ```

Acceptance Criteria:
  - Mock fixtures work with aiohttp
  - Can simulate success, error, timeout scenarios
  - Documentation explains usage
```

### Sprint 1 Integration Checklist

**Days 9-10: Integration Period**

```markdown
## Sprint 1 Integration Checklist

### Pre-Integration (Day 8)
- [ ] All PRs have passing CI
- [ ] All PRs have code review approval
- [ ] No merge conflicts detected
- [ ] Test coverage >85% on modified files

### Merge Order (Day 9)
1. [ ] S1-D04-01: Retry utilities (foundation)
2. [ ] S1-D07-01: HTTP mocking infrastructure
3. [ ] S1-D02-01: Backend retry logic
4. [ ] S1-D03-01: Concurrent page processing
5. [ ] S1-D05-01: Renderer optimizations
6. [ ] S1-D06-01: CLI improvements
7. [ ] S1-D08-01: Documentation updates

### Post-Integration Verification (Day 10)
- [ ] All unit tests pass
- [ ] All integration tests pass (mocked)
- [ ] CLI manual testing passes
- [ ] No regressions detected
- [ ] Coverage report generated

### Documentation
- [ ] CONTINUATION.md updated
- [ ] CHANGELOG.md updated
- [ ] Known issues documented
```

---

## Sprint 2: Advanced Features (Weeks 3-4)
**Theme: "Build production features"**

### Sprint 2 Objectives
1. Implement streaming/chunked processing for large PDFs
2. Add real API testing with OpenRouter
3. Implement progress callbacks and reporting
4. Performance profiling and optimization
5. Start DeepSeek vLLM backend stub completion

### Sprint 2 Work Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SPRINT 2: PARALLEL WORK STREAMS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  D01 (Tech Lead): Integration, performance review, architecture guidance     │
│                                                                              │
│  D02 (Backend Lead)                                                          │
│   └── S2-D02-01: Begin DeepSeek vLLM backend implementation                  │
│   └── S2-D02-02: Add connection pooling                                      │
│   └── S2-D02-03: Implement backend health checks                             │
│   Files: backends/deepseek_vllm.py, backends/health.py (new)                 │
│                                                                              │
│  D03 (Pipeline Lead)                                                         │
│   └── S2-D03-01: Add streaming/chunked large PDF processing                  │
│   └── S2-D03-02: Implement progress callback system                          │
│   └── S2-D03-03: Add cancellation support                                    │
│   Files: orchestrator/pipeline.py, orchestrator/progress.py (new)            │
│                                                                              │
│  D04 (Infrastructure)                                                        │
│   └── S2-D04-01: Docker containerization                                     │
│   └── S2-D04-02: Add metrics/telemetry hooks                                 │
│   └── S2-D04-03: Environment validation tool                                 │
│   Files: Dockerfile, docker-compose.yml, common/metrics.py                   │
│                                                                              │
│  D05 (Renderer)                                                              │
│   └── S2-D05-01: Add PDF metadata extraction                                 │
│   └── S2-D05-02: Implement DPI auto-selection based on content               │
│   └── S2-D05-03: Add rendering quality validation                            │
│   Files: renderer/core.py, renderer/metadata.py (new)                        │
│                                                                              │
│  D06 (CLI Lead)                                                              │
│   └── S2-D06-01: Add batch processing command                                │
│   └── S2-D06-02: Implement watch mode for directories                        │
│   └── S2-D06-03: Add config validation command                               │
│   Files: cli/main.py, cli/commands/ (new directory)                          │
│                                                                              │
│  D07 (Testing Lead)                                                          │
│   └── S2-D07-01: Create real API test suite (optional, rate-limited)         │
│   └── S2-D07-02: Performance benchmark tests                                 │
│   └── S2-D07-03: Create smoke test suite                                     │
│   Files: tests/smoke/, tests/benchmarks/, tests/e2e/                         │
│                                                                              │
│  D08 (Documentation)                                                         │
│   └── S2-D08-01: Write deployment guide                                      │
│   └── S2-D08-02: Create example scripts                                      │
│   └── S2-D08-03: Performance tuning guide                                    │
│   Files: docs/DEPLOYMENT.md, examples/, docs/PERFORMANCE.md                  │
│                                                                              │
│  D09 (Block Processing)                                                      │
│   └── S2-D09-01: Implement Docling integration layer                         │
│   └── S2-D09-02: Create block type detection                                 │
│   └── S2-D09-03: Design routing rules system                                 │
│   Files: blocks/docling_adapter.py, blocks/detector.py                       │
│                                                                              │
│  D10 (Evaluation)                                                            │
│   └── S2-D10-01: Implement basic text metrics (CER, WER)                     │
│   └── S2-D10-02: Create ground truth loading                                 │
│   └── S2-D10-03: Build evaluation runner skeleton                            │
│   Files: eval/metrics.py, eval/ground_truth.py, eval/runner.py               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sprint 3: Integration & Polish (Weeks 5-6)
**Theme: "Connect and refine"**

### Sprint 3 Objectives
1. Complete DeepSeek vLLM backend
2. Full end-to-end integration testing
3. CLI polish and UX improvements
4. Documentation completion
5. Bug fixes from testing

### Sprint 3 Work Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SPRINT 3: PARALLEL WORK STREAMS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  D01: Release planning, final integration, bug triage                        │
│                                                                              │
│  D02: Complete DeepSeek vLLM, add backend comparison tooling                 │
│                                                                              │
│  D03: Pipeline hardening, edge case handling                                 │
│                                                                              │
│  D04: CI/CD finalization, release automation                                 │
│                                                                              │
│  D05: Renderer edge cases, corrupt PDF handling                              │
│                                                                              │
│  D06: CLI final polish, shell completion, man pages                          │
│                                                                              │
│  D07: Full regression testing, load testing                                  │
│                                                                              │
│  D08: Final documentation review, quick-start guide                          │
│                                                                              │
│  D09: Block processing foundation complete                                   │
│                                                                              │
│  D10: Evaluation metrics complete, basic benchmarks                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sprint 4: Stage 1 Release (Weeks 7-8)
**Theme: "Ship v0.1.0"**

### Sprint 4 Objectives
1. Release v0.1.0
2. All critical bugs fixed
3. Documentation complete
4. Docker image published
5. Stage 2 preparation

### Release Criteria (v0.1.0)

```markdown
## v0.1.0 Release Checklist

### Functionality
- [ ] CLI converts PDFs using OpenRouter API
- [ ] Concurrent page processing works
- [ ] Retry logic handles transient failures
- [ ] Progress reporting works
- [ ] Error messages are actionable
- [ ] Configuration system works

### Quality
- [ ] Unit test coverage >85%
- [ ] Integration tests pass (mocked)
- [ ] Smoke tests pass (real API)
- [ ] No P0/P1 bugs open
- [ ] Memory usage acceptable (<4GB for 100-page PDF)

### Performance
- [ ] <5s per page processing (excluding API)
- [ ] Concurrent processing shows improvement
- [ ] No memory leaks

### Documentation
- [ ] README complete with examples
- [ ] CLI help is comprehensive
- [ ] Quick-start guide tested
- [ ] API documentation complete
- [ ] CHANGELOG written

### Deployment
- [ ] Docker image builds and works
- [ ] pip install works
- [ ] GitHub release created
- [ ] Version tagged
```

---

# STAGE 2: FULL FEATURE SET

## Sprint 5: DeepSeek Backends (Weeks 9-10)

### Sprint 5 Focus Areas by Developer

| Developer | Primary Work | Deliverable |
|-----------|-------------|-------------|
| D01 | Multi-backend architecture | Design doc |
| D02 | DeepSeek vLLM completion, MLX start | Working backends |
| D03 | Backend selection logic | Auto-selection |
| D04 | vLLM deployment docs | Deployment guide |
| D05 | Image preprocessing for DeepSeek | Optimized images |
| D06 | Backend CLI commands | Compare command |
| D07 | Backend integration tests | Test suite |
| D08 | Backend comparison docs | User guide |
| D09 | Block segmentation implementation | Working segmenter |
| D10 | Backend-specific evaluation | Metrics per backend |

---

## Sprint 6: Block-Level Processing (Weeks 11-12)

### Sprint 6 Focus Areas by Developer

| Developer | Primary Work | Deliverable |
|-----------|-------------|-------------|
| D01 | Block processing architecture review | Approved design |
| D02 | Table-specific backend wrapper | Table OCR |
| D03 | Block-aware pipeline mode | New pipeline mode |
| D04 | Block processing config | Config schema |
| D05 | Region rendering for blocks | Crop function |
| D06 | Block-level CLI options | CLI flags |
| D07 | Block processing tests | Test coverage |
| D08 | Block processing docs | User guide |
| D09 | Block segmentation (primary) | Full implementation |
| D10 | Block-level evaluation | Per-block metrics |

---

## Sprint 7: Multi-Backend & Merging (Weeks 13-14)

### Sprint 7 Focus Areas by Developer

| Developer | Primary Work | Deliverable |
|-----------|-------------|-------------|
| D01 | Merge strategy design | Design doc |
| D02 | Multi-backend orchestration | Concurrent backends |
| D03 | Candidate collection pipeline | Collector |
| D04 | Merge policy configuration | Config schema |
| D05 | Quality scoring heuristics | Scoring module |
| D06 | Multi-backend CLI options | CLI flags |
| D07 | Merge strategy tests | Test coverage |
| D08 | Multi-backend docs | User guide |
| D09 | Block result merging | Merger |
| D10 | Ensemble evaluation | Comparison metrics |

---

## Sprint 8: Evaluation & v1.0.0 Release (Weeks 15-16)

### Sprint 8 Focus Areas by Developer

| Developer | Primary Work | Deliverable |
|-----------|-------------|-------------|
| D01 | Release management | v1.0.0 release |
| D02 | Backend optimization | Performance |
| D03 | Pipeline optimization | Performance |
| D04 | Deployment finalization | Docker/CI |
| D05 | Rendering optimization | Performance |
| D06 | CLI finalization | Polish |
| D07 | Release testing | Full regression |
| D08 | Final documentation | All docs |
| D09 | Block processing finalization | Polish |
| D10 | Evaluation completion (primary) | Benchmarks |

---

## File Ownership Matrix

**CRITICAL: Each file has ONE owner per sprint. No exceptions.**

| File/Directory | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|----------------|----|----|----|----|----|----|----|----|
| `common/config.py` | D04 | D04 | D04 | D04 | D04 | D04 | D04 | D04 |
| `common/retry.py` | D04 | D04 | - | - | - | - | - | - |
| `common/http.py` | D04 | D04 | D04 | D04 | D04 | D04 | D04 | D04 |
| `backends/base.py` | D02 | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/factory.py` | D02 | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/openrouter_nemotron.py` | D02 | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/deepseek_vllm.py` | - | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/deepseek_mlx.py` | - | - | - | - | D02 | D02 | D02 | D02 |
| `renderer/core.py` | D05 | D05 | D05 | D05 | D05 | D05 | D05 | D05 |
| `orchestrator/pipeline.py` | D03 | D03 | D03 | D03 | D03 | D03 | D03 | D03 |
| `orchestrator/progress.py` | - | D03 | D03 | D03 | D03 | D03 | D03 | D03 |
| `orchestrator/routing.py` | - | - | - | - | - | D03 | D03 | D03 |
| `orchestrator/merging.py` | - | - | - | - | - | - | D03 | D03 |
| `cli/main.py` | D06 | D06 | D06 | D06 | D06 | D06 | D06 | D06 |
| `blocks/*` | D09 | D09 | D09 | D09 | D09 | D09 | D09 | D09 |
| `eval/*` | D10 | D10 | D10 | D10 | D10 | D10 | D10 | D10 |
| `tests/conftest.py` | D07 | D07 | D07 | D07 | D07 | D07 | D07 | D07 |
| `tests/mocks/*` | D07 | D07 | D07 | D07 | D07 | D07 | D07 | D07 |
| `CLAUDE.md` | D08 | D08 | D08 | D08 | D08 | D08 | D08 | D08 |
| `docs/*` | D08 | D08 | D08 | D08 | D08 | D08 | D08 | D08 |

---

## Integration Protocol

### Sprint Integration Schedule (Days 9-10)

```
Day 9 (Integration Day 1):
├── 09:00 - Sprint Review Meeting (All)
│   ├── Each developer demos their work (5 min each)
│   └── Q&A and dependency review
├── 11:00 - PR Status Review (D01)
│   ├── Check CI status
│   └── Identify blockers
├── 14:00 - Begin Merging (D01 leads)
│   ├── Merge in dependency order
│   └── Run tests after each merge
└── 18:00 - Status Check

Day 10 (Integration Day 2):
├── 09:00 - Full Test Suite (D07)
│   ├── Unit tests
│   ├── Integration tests
│   └── Smoke tests
├── 11:00 - Documentation Review (D08)
├── 14:00 - Sprint Retrospective (All)
│   ├── What went well
│   ├── What needs improvement
│   └── Action items
└── 15:30 - Next Sprint Planning (All)
```

### PR Requirements

```yaml
PR Requirements:
  - CI must pass (all checks green)
  - At least 1 approval from:
    - File owner, OR
    - Tech Lead (D01)
  - No merge conflicts
  - Documentation updated (if applicable)
  - Tests included for new code
  - Coverage not decreased

Branch Naming: feat/sN-description
  Example: feat/s1-backend-retry

Merge Target: develop
```

### Communication Protocol

```
Daily:
- Async standup in team channel
- Format: "Yesterday | Today | Blockers"

Weekly:
- Monday 10:00: Sprint sync (30 min)
- Friday 15:00: Demo prep (30 min)

Integration Period:
- Day 9 09:00: Demo meeting (2 hours)
- Day 9 14:00: Merge session (4 hours)
- Day 10 09:00: Test & verify (3 hours)
- Day 10 14:00: Retro + planning (3 hours)

Escalation:
1. DM the file owner
2. Post in team channel with @owner
3. Escalate to D01 (Tech Lead)
4. Emergency meeting
```

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API rate limiting | Medium | High | Implement caching, mock testing |
| Memory issues on large PDFs | High | Medium | Streaming processing, limits |
| DeepSeek model availability | Medium | Medium | Fallback to OpenRouter |
| Merge conflicts | Low | Low | Strict file ownership |
| Scope creep | Medium | High | Strict sprint boundaries |
| Developer unavailable | Medium | Medium | Cross-training, documented ownership |

---

## Success Metrics

### Stage 1 (v0.1.0)
- Test coverage: >85%
- Pipeline performance: <5s per page (excluding API)
- Memory: <500MB per 100 pages
- Reliability: 99% success rate on valid PDFs
- Documentation: Complete for all features

### Stage 2 (v1.0.0)
- Multiple backends working
- Block-level OCR functional
- Evaluation framework complete
- Performance benchmarks documented
- Production deployment guide tested
