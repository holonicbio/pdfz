# Sprint 2 Plan: Backend Expansion & Production Readiness

**Sprint:** Sprint 2
**Duration:** 2 Weeks (Weeks 5-6)
**Start Date:** After Sprint 1 Completion
**Status:** APPROVED
**Team Size:** 6 Developers (100% allocation)

---

## Executive Summary

Sprint 2 focuses on expanding backend capabilities and hardening for production. With 6 developers working in parallel, we use **strict file ownership** and **interface-first design** to enable smooth integration at sprint end.

### Sprint Goals
1. Implement DeepSeek vLLM Backend (local GPU inference)
2. Add backend fallback chain for resilience
3. Implement pipeline progress hooks with real-time updates
4. Docker containerization for deployment
5. Performance benchmarking and profiling
6. CLI batch processing and enhanced UX

---

## Team Structure & File Ownership

### CRITICAL: One Owner Per File

Each file/module has exactly ONE owner. No exceptions. This prevents merge conflicts.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SPRINT 2: FILE OWNERSHIP MATRIX                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Developer │ Owned Files                                                    │
├────────────┼────────────────────────────────────────────────────────────────┤
│  Dev-02    │ backends/deepseek_vllm.py (NEW)                               │
│  (Backend) │ backends/fallback.py (NEW)                                    │
│            │ backends/health.py (NEW)                                       │
│            │ tests/unit/backends/test_deepseek_vllm.py (NEW)               │
│            │ tests/unit/backends/test_fallback.py (NEW)                    │
├────────────┼────────────────────────────────────────────────────────────────┤
│  Dev-03    │ orchestrator/progress.py (NEW)                                │
│  (Pipeline)│ orchestrator/callbacks.py (NEW)                               │
│            │ tests/unit/orchestrator/test_progress.py (NEW)                │
│            │ tests/unit/orchestrator/test_callbacks.py (NEW)               │
├────────────┼────────────────────────────────────────────────────────────────┤
│  Dev-04    │ Dockerfile (NEW)                                              │
│  (DevOps)  │ docker-compose.yml (NEW)                                      │
│            │ .dockerignore (NEW)                                           │
│            │ common/health.py (NEW)                                        │
│            │ scripts/docker-build.sh (NEW)                                 │
│            │ docs/DOCKER.md (NEW)                                          │
├────────────┼────────────────────────────────────────────────────────────────┤
│  Dev-06    │ cli/batch.py (NEW)                                            │
│  (CLI)     │ cli/progress_display.py (NEW)                                 │
│            │ tests/unit/cli/test_batch.py (NEW)                            │
│            │ docs/CLI_GUIDE.md (NEW)                                       │
├────────────┼────────────────────────────────────────────────────────────────┤
│  Dev-07    │ tests/benchmarks/__init__.py (NEW)                            │
│  (QA/Test) │ tests/benchmarks/test_performance.py (NEW)                    │
│            │ tests/benchmarks/test_memory.py (NEW)                         │
│            │ tests/benchmarks/conftest.py (NEW)                            │
│            │ tests/integration/test_pipeline_e2e.py (NEW)                  │
│            │ docs/BENCHMARKS.md (NEW)                                      │
├────────────┼────────────────────────────────────────────────────────────────┤
│  Dev-08    │ docs/DEPLOYMENT.md (NEW)                                      │
│  (Docs)    │ docs/API_REFERENCE.md (NEW)                                   │
│            │ docs/QUICK_START.md (NEW)                                     │
│            │ examples/basic_conversion.py (NEW)                            │
│            │ examples/batch_conversion.py (NEW)                            │
│            │ examples/custom_backend.py (NEW)                              │
└────────────┴────────────────────────────────────────────────────────────────┘
```

### Shared Files Protocol

When a developer needs to modify a shared file (e.g., `pyproject.toml`, `__init__.py`):

1. **Request via Slack/Teams** to Tech Lead
2. **Wait for approval** before editing
3. **Small, atomic changes only**
4. **Coordinate merge timing** during integration phase

---

## Developer Workstreams (Week 1-2)

### Dev-02: Backend Lead (100%)

#### S2-D02-01: DeepSeek vLLM Backend
**Priority:** P0-CRITICAL
**Duration:** 5 days
**Branch:** `feat/s2-deepseek-vllm`

**Description:**
Implement full DeepSeek vLLM backend for local GPU inference via vLLM server.

**Tasks:**
- [ ] Create `backends/deepseek_vllm.py` with full implementation
- [ ] Support DeepSeek-VL-7B model
- [ ] Async HTTP client to vLLM OpenAI-compatible endpoint
- [ ] Handle vLLM-specific response format
- [ ] Implement connection validation
- [ ] Add comprehensive unit tests
- [ ] Add integration tests (mocked)

**File Structure:**
```python
# backends/deepseek_vllm.py
class DeepSeekVLLMBackend(OcrVlmBackend):
    """OCR backend using DeepSeek-VL via local vLLM server."""

    def __init__(self, config: OcrBackendConfig) -> None: ...
    async def page_to_markdown(self, image_bytes, page_num, doc_id) -> str: ...
    async def table_to_markdown(self, image_bytes, meta) -> str: ...
    async def formula_to_latex(self, image_bytes, meta) -> str: ...
    async def health_check(self) -> bool: ...
```

**Acceptance Criteria:**
- [ ] All OcrVlmBackend interface methods implemented
- [ ] Uses retry logic from `common/retry.py`
- [ ] Unit test coverage >90%
- [ ] Handles connection errors gracefully
- [ ] Logs all API calls with context

---

#### S2-D02-02: Backend Fallback Chain
**Priority:** P0-CRITICAL
**Duration:** 3 days
**Branch:** `feat/s2-backend-fallback`

**Description:**
Implement automatic fallback when primary backend fails.

**Tasks:**
- [ ] Create `backends/fallback.py` module
- [ ] Define FallbackChain class
- [ ] Implement automatic backend switching
- [ ] Add health check integration
- [ ] Log all fallback events
- [ ] Unit tests

**File Structure:**
```python
# backends/fallback.py
class FallbackChain:
    """Manages backend fallback logic."""

    def __init__(
        self,
        primary: str,
        fallbacks: list[str],
        max_attempts: int = 2,
    ) -> None: ...

    async def execute_with_fallback(
        self,
        operation: Callable,
        *args, **kwargs,
    ) -> Any: ...

    async def get_healthy_backend(self) -> OcrVlmBackend: ...
```

**Configuration:**
```toml
[backends]
default = "deepseek-vllm"
fallback = ["nemotron-openrouter"]
fallback_on_errors = ["connection", "timeout", "server_error"]
max_fallback_attempts = 2
```

**Acceptance Criteria:**
- [ ] Falls back on connection/timeout errors
- [ ] Does NOT fall back on auth errors (4xx)
- [ ] Logs fallback events with context
- [ ] Unit tests for all fallback scenarios

---

#### S2-D02-03: Backend Health Checks
**Priority:** P1-IMPORTANT
**Duration:** 2 days
**Branch:** `feat/s2-backend-health`

**Tasks:**
- [ ] Create `backends/health.py` module
- [ ] Add health_check method to base interface
- [ ] Implement for OpenRouter and vLLM backends
- [ ] Create health check runner

---

### Dev-03: Pipeline Lead (100%)

#### S2-D03-01: Progress Callback System
**Priority:** P0-CRITICAL
**Duration:** 4 days
**Branch:** `feat/s2-progress-callbacks`

**Description:**
Implement progress callback system for real-time conversion updates.

**Tasks:**
- [ ] Create `orchestrator/progress.py` with protocols
- [ ] Create `orchestrator/callbacks.py` with implementations
- [ ] Define ProgressCallback protocol
- [ ] Implement ConsoleProgressCallback
- [ ] Implement FileProgressCallback (for logging)
- [ ] Unit tests

**File Structure:**
```python
# orchestrator/progress.py
from typing import Protocol

class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None: ...
    def on_page_start(self, page_num: int, total: int) -> None: ...
    def on_page_complete(self, page_num: int, total: int, result: PageResult) -> None: ...
    def on_page_error(self, page_num: int, error: Exception) -> None: ...
    def on_conversion_complete(self, result: ConversionResult) -> None: ...
    def on_conversion_error(self, error: Exception) -> None: ...

# orchestrator/callbacks.py
class ConsoleProgressCallback:
    """Rich console progress display."""
    ...

class FileProgressCallback:
    """Write progress to file for external monitoring."""
    ...

class CompositeProgressCallback:
    """Combine multiple callbacks."""
    ...
```

**Acceptance Criteria:**
- [ ] Protocol is well-defined and documented
- [ ] ConsoleProgressCallback shows real progress
- [ ] Callbacks are optional (None = no callbacks)
- [ ] Unit tests >90% coverage

---

#### S2-D03-02: Pipeline Progress Integration
**Priority:** P1-IMPORTANT
**Duration:** 3 days
**Branch:** `feat/s2-pipeline-progress-integration`

**Description:**
Integrate progress callbacks into HybridPipeline.

**NOTE:** This task modifies shared file `orchestrator/pipeline.py`.
Coordinate with Tech Lead for integration timing.

**Tasks:**
- [ ] Add progress_callback parameter to convert_pdf
- [ ] Call callbacks at appropriate points
- [ ] Ensure callbacks don't break existing API
- [ ] Update pipeline tests

**Integration Point (pipeline.py changes):**
```python
async def convert_pdf(
    self,
    pdf_path: Path,
    output_path: Path | None = None,
    options: ConversionOptions | None = None,
    progress_callback: ProgressCallback | None = None,  # NEW
) -> ConversionResult:
    ...
```

---

#### S2-D03-03: Progress Event Types
**Priority:** P2-NICE
**Duration:** 1 day
**Branch:** `feat/s2-progress-events`

**Tasks:**
- [ ] Define typed event classes
- [ ] Add event serialization (for external consumers)

---

### Dev-04: DevOps Engineer (100%)

#### S2-D04-01: Docker Setup
**Priority:** P0-CRITICAL
**Duration:** 3 days
**Branch:** `feat/s2-docker`

**Description:**
Create Docker configuration for production deployment.

**Tasks:**
- [ ] Create multi-stage Dockerfile
- [ ] Create docker-compose.yml for development
- [ ] Create .dockerignore
- [ ] Create docker-build.sh script
- [ ] Write Docker documentation

**File: Dockerfile**
```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install build && pip wheel . -w /wheels

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install /wheels/*.whl && rm -rf /wheels
COPY configs/ /app/configs/

# Runtime configuration
ENV DOCLING_HYBRID_CONFIG=/app/configs/default.toml
EXPOSE 8080
ENTRYPOINT ["docling-hybrid-ocr"]
```

**File: docker-compose.yml**
```yaml
version: "3.8"
services:
  docling-hybrid:
    build: .
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DOCLING_HYBRID_CONFIG=/app/configs/local.toml
    volumes:
      - ./input:/app/input
      - ./output:/app/output
      - ./configs:/app/configs:ro
    command: ["convert", "/app/input/document.pdf", "-o", "/app/output/result.md"]
```

**Acceptance Criteria:**
- [ ] Image builds successfully
- [ ] Image size <500MB
- [ ] docker-compose works
- [ ] Environment variables work
- [ ] Volume mounts work
- [ ] Documentation complete

---

#### S2-D04-02: Health Check CLI Command
**Priority:** P1-IMPORTANT
**Duration:** 2 days
**Branch:** `feat/s2-health-check`

**Tasks:**
- [ ] Create `common/health.py` module
- [ ] Add `health` CLI command
- [ ] Check backend connectivity
- [ ] Check configuration validity
- [ ] Output structured health report

**CLI Usage:**
```bash
docling-hybrid-ocr health
# Output:
# ✓ Configuration: Valid
# ✓ OpenRouter Backend: Connected (latency: 120ms)
# ✗ DeepSeek vLLM Backend: Connection refused
# Overall: DEGRADED (1/2 backends healthy)
```

---

#### S2-D04-03: Configuration Validation Tool
**Priority:** P1-IMPORTANT
**Duration:** 2 days
**Branch:** `feat/s2-config-validation`

**Tasks:**
- [ ] Add `validate-config` CLI command
- [ ] Schema validation
- [ ] Connection testing (optional)
- [ ] Clear error messages

---

#### S2-D04-04: Telemetry Hooks (Optional)
**Priority:** P2-NICE
**Duration:** 2 days
**Branch:** `feat/s2-telemetry`

**Tasks:**
- [ ] Add optional metrics collection
- [ ] Prometheus format output
- [ ] Opt-in configuration

---

### Dev-06: CLI Developer (100%)

#### S2-D06-01: Batch Processing Command
**Priority:** P0-CRITICAL
**Duration:** 4 days
**Branch:** `feat/s2-cli-batch`

**Description:**
Add batch conversion for multiple PDFs.

**Tasks:**
- [ ] Create `cli/batch.py` module
- [ ] Add `convert-batch` command to CLI
- [ ] Directory scanning with glob patterns
- [ ] Parallel file processing
- [ ] Summary report generation
- [ ] Unit tests

**File: cli/batch.py**
```python
"""Batch processing command implementation."""

import asyncio
from pathlib import Path
from typing import List

import typer
from rich.progress import Progress

from docling_hybrid.orchestrator import HybridPipeline


async def convert_batch(
    input_paths: List[Path],
    output_dir: Path,
    parallel: int = 4,
    progress_callback = None,
) -> BatchResult:
    """Convert multiple PDFs in parallel."""
    ...


def batch_command(
    input_dir: Path = typer.Argument(..., help="Directory or glob pattern"),
    output_dir: Path = typer.Option("./output", "--output-dir", "-o"),
    parallel: int = typer.Option(4, "--parallel", "-p", min=1, max=16),
    recursive: bool = typer.Option(False, "--recursive", "-r"),
    pattern: str = typer.Option("*.pdf", "--pattern"),
) -> None:
    """Convert multiple PDFs in batch mode."""
    ...
```

**CLI Usage:**
```bash
# Convert all PDFs in directory
docling-hybrid-ocr convert-batch ./pdfs/ --output-dir ./output/

# Recursive with pattern
docling-hybrid-ocr convert-batch ./docs/ -r --pattern "*.pdf"

# Control parallelism
docling-hybrid-ocr convert-batch ./pdfs/ --parallel 8
```

**Acceptance Criteria:**
- [ ] Glob patterns work
- [ ] Parallel processing works
- [ ] Progress shows for all files
- [ ] Summary report at end
- [ ] Handles individual file failures gracefully

---

#### S2-D06-02: Progress Display Integration
**Priority:** P1-IMPORTANT
**Duration:** 3 days
**Branch:** `feat/s2-cli-progress`

**Description:**
Integrate real progress callbacks into CLI.

**Tasks:**
- [ ] Create `cli/progress_display.py` module
- [ ] Implement RichProgressCallback
- [ ] Show per-page progress
- [ ] Show per-file progress (batch mode)
- [ ] Show ETA estimates

**File: cli/progress_display.py**
```python
"""Rich progress display for CLI."""

from rich.progress import Progress, TaskID
from docling_hybrid.orchestrator.progress import ProgressCallback


class RichProgressCallback(ProgressCallback):
    """Rich console progress display."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.progress = Progress(...)

    def on_page_complete(self, page_num: int, total: int, result) -> None:
        self.progress.update(self.task, completed=page_num)
```

---

#### S2-D06-03: CLI UX Polish
**Priority:** P2-NICE
**Duration:** 1 day
**Branch:** `feat/s2-cli-polish`

**Tasks:**
- [ ] Improve help messages
- [ ] Add examples to help
- [ ] Shell completion setup

---

### Dev-07: QA/Test Engineer (100%)

#### S2-D07-01: Performance Benchmarking Suite
**Priority:** P0-CRITICAL
**Duration:** 5 days
**Branch:** `feat/s2-benchmarks`

**Description:**
Create comprehensive performance benchmarks.

**Tasks:**
- [ ] Create `tests/benchmarks/` directory structure
- [ ] Implement memory profiling tests
- [ ] Implement throughput benchmarks
- [ ] Implement API latency measurements
- [ ] Create benchmark fixtures (sample PDFs)
- [ ] Document benchmark results

**File Structure:**
```
tests/benchmarks/
├── __init__.py
├── conftest.py          # Benchmark fixtures
├── test_performance.py  # Throughput tests
├── test_memory.py       # Memory profiling
├── test_latency.py      # API latency
└── README.md            # How to run benchmarks
```

**File: tests/benchmarks/test_performance.py**
```python
"""Performance benchmark tests."""

import pytest
import time
from pathlib import Path

from docling_hybrid.orchestrator import HybridPipeline


@pytest.fixture
def sample_pdf_10_pages(tmp_path) -> Path:
    """Generate a 10-page test PDF."""
    ...


class TestThroughput:
    """Throughput benchmarks."""

    @pytest.mark.benchmark
    async def test_pages_per_minute_sequential(self, pipeline, sample_pdf_10_pages):
        """Measure pages/minute in sequential mode."""
        start = time.time()
        result = await pipeline.convert_pdf(sample_pdf_10_pages)
        elapsed = time.time() - start

        pages_per_minute = (result.processed_pages / elapsed) * 60
        assert pages_per_minute > 5, f"Too slow: {pages_per_minute:.1f} pages/min"

    @pytest.mark.benchmark
    async def test_pages_per_minute_concurrent(self, pipeline, sample_pdf_10_pages):
        """Measure pages/minute in concurrent mode."""
        ...


class TestMemory:
    """Memory usage benchmarks."""

    @pytest.mark.benchmark
    async def test_peak_memory_100_pages(self, pipeline, sample_pdf_100_pages):
        """Measure peak memory for 100-page PDF."""
        import tracemalloc

        tracemalloc.start()
        await pipeline.convert_pdf(sample_pdf_100_pages)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        assert peak_mb < 500, f"Memory too high: {peak_mb:.1f}MB"
```

**Metrics to Track:**
- Pages per minute (sequential)
- Pages per minute (concurrent, various worker counts)
- Memory usage (peak, average)
- API latency (p50, p95, p99)
- Image encoding time
- Total conversion time

**Acceptance Criteria:**
- [ ] Benchmarks run in CI (optional flag)
- [ ] Results documented in BENCHMARKS.md
- [ ] Baseline established for regressions
- [ ] Memory profiling works

---

#### S2-D07-02: End-to-End Integration Tests
**Priority:** P1-IMPORTANT
**Duration:** 3 days
**Branch:** `feat/s2-e2e-tests`

**Tasks:**
- [ ] Create `tests/integration/test_pipeline_e2e.py`
- [ ] Test full conversion flow (mocked HTTP)
- [ ] Test batch processing
- [ ] Test progress callbacks
- [ ] Test fallback scenarios

---

#### S2-D07-03: Test Fixtures Enhancement
**Priority:** P1-IMPORTANT
**Duration:** 2 days
**Branch:** `feat/s2-test-fixtures`

**Tasks:**
- [ ] Create sample PDFs of various sizes
- [ ] Create PDFs with specific content (tables, formulas)
- [ ] Add fixtures to conftest.py

---

### Dev-08: Documentation Lead (100%)

#### S2-D08-01: Deployment Guide
**Priority:** P0-CRITICAL
**Duration:** 3 days
**Branch:** `feat/s2-deployment-docs`

**Tasks:**
- [ ] Create `docs/DEPLOYMENT.md`
- [ ] Document Docker deployment
- [ ] Document local deployment
- [ ] Document cloud deployment options
- [ ] Include troubleshooting

**File: docs/DEPLOYMENT.md**
```markdown
# Deployment Guide

## Quick Start with Docker

1. Build the image:
   ```bash
   docker build -t docling-hybrid-ocr .
   ```

2. Run a conversion:
   ```bash
   docker run -v $(pwd)/input:/app/input \
              -v $(pwd)/output:/app/output \
              -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
              docling-hybrid-ocr convert /app/input/doc.pdf
   ```

## Local Installation
...

## Cloud Deployment
...

## Troubleshooting
...
```

---

#### S2-D08-02: API Reference Documentation
**Priority:** P1-IMPORTANT
**Duration:** 3 days
**Branch:** `feat/s2-api-docs`

**Tasks:**
- [ ] Create `docs/API_REFERENCE.md`
- [ ] Document all public APIs
- [ ] Include code examples
- [ ] Document configuration options

---

#### S2-D08-03: Quick Start Guide
**Priority:** P1-IMPORTANT
**Duration:** 2 days
**Branch:** `feat/s2-quick-start`

**Tasks:**
- [ ] Create `docs/QUICK_START.md`
- [ ] Step-by-step first conversion
- [ ] Common use cases
- [ ] FAQ section

---

#### S2-D08-04: Example Scripts
**Priority:** P1-IMPORTANT
**Duration:** 2 days
**Branch:** `feat/s2-examples`

**Tasks:**
- [ ] Create `examples/` directory
- [ ] `basic_conversion.py` - Simple conversion
- [ ] `batch_conversion.py` - Multiple files
- [ ] `custom_backend.py` - Custom backend config
- [ ] `progress_tracking.py` - Progress callbacks

---

## Sprint 2 Timeline

```
Week 5 (Days 1-5):
┌─────────────────────────────────────────────────────────────────────────────┐
│          Day 1       Day 2       Day 3       Day 4       Day 5             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-02 │ vLLM       vLLM       vLLM       vLLM       vLLM                  │
│        │ Backend    Backend    Backend    Backend    Backend               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-03 │ Progress   Progress   Progress   Progress   Pipeline              │
│        │ Protocol   Callbacks  Callbacks  Callbacks  Integration           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-04 │ Dockerfile Docker     Docker     Health     Health                │
│        │            Compose    Docs       Check      Check                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-06 │ Batch      Batch      Batch      Batch      Progress              │
│        │ Command    Command    Command    Command    Display               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-07 │ Benchmark  Benchmark  Benchmark  Benchmark  Benchmark             │
│        │ Setup      Throughput Memory     Latency    Fixtures              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-08 │ Deploy     Deploy     Deploy     API        API                   │
│        │ Guide      Guide      Guide      Reference  Reference             │
└─────────────────────────────────────────────────────────────────────────────┘

Week 6 (Days 6-10):
┌─────────────────────────────────────────────────────────────────────────────┐
│          Day 6       Day 7       Day 8       Day 9       Day 10            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-02 │ Fallback   Fallback   Fallback   INTEGRATION INTEGRATION          │
│        │ Chain      Chain      Tests      Support     Support              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-03 │ Pipeline   Pipeline   Event      INTEGRATION INTEGRATION          │
│        │ Integ.     Tests      Types      Support     Support              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-04 │ Config     Config     Telemetry  INTEGRATION INTEGRATION          │
│        │ Validation Validation (Optional) Support     Support              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-06 │ Progress   Progress   CLI        INTEGRATION INTEGRATION          │
│        │ Display    Display    Polish     Support     Support              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-07 │ E2E        E2E        Fixtures   INTEGRATION INTEGRATION          │
│        │ Tests      Tests      Tests      TESTING     TESTING              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dev-08 │ Quick      Examples   Examples   INTEGRATION INTEGRATION          │
│        │ Start      Scripts    Scripts    DOCS        DOCS                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Strategy (Days 9-10)

### Pre-Integration Requirements (Day 8 EOD)

Each developer must complete:
- [ ] All code committed to feature branch
- [ ] All unit tests passing locally
- [ ] PR created with description
- [ ] CI pipeline green
- [ ] Self-review completed

### Integration Order (Day 9)

Merge in this specific order to minimize conflicts:

```
Phase 1: Foundation (No Dependencies)
├── 1. Dev-04: Docker files (Dockerfile, docker-compose.yml)
├── 2. Dev-08: Documentation (docs/*.md, examples/)
└── 3. Dev-07: Test infrastructure (tests/benchmarks/)

Phase 2: New Modules (Isolated)
├── 4. Dev-03: Progress system (orchestrator/progress.py, callbacks.py)
├── 5. Dev-02: vLLM backend (backends/deepseek_vllm.py)
└── 6. Dev-02: Fallback chain (backends/fallback.py)

Phase 3: CLI Integration
├── 7. Dev-06: Batch processing (cli/batch.py)
└── 8. Dev-06: Progress display (cli/progress_display.py)

Phase 4: Cross-Module Integration
├── 9. Dev-03: Pipeline integration (orchestrator/pipeline.py changes)
└── 10. Dev-04: Health check (common/health.py, CLI integration)

Phase 5: Final
└── 11. Dev-07: E2E tests (depends on all above)
```

### Integration Day Schedule

**Day 9 (Integration Day 1):**
```
09:00-10:00  Sprint Demo Meeting (All)
             - Each dev shows their work (7 min each)
             - Q&A and dependency review

10:00-12:00  Phase 1 & 2 Merges (Dev-01 leads)
             - Merge Docker, Docs, Tests, Progress, Backends
             - Run tests after each merge

12:00-13:00  Lunch Break

13:00-15:00  Phase 3 & 4 Merges
             - Merge CLI, Pipeline integration
             - Run full test suite

15:00-17:00  Issue Resolution
             - Fix any integration issues
             - Dev-07 starts E2E testing
```

**Day 10 (Integration Day 2):**
```
09:00-12:00  Full Verification (Dev-07 leads)
             - Complete test suite
             - Performance benchmarks
             - Manual testing

12:00-13:00  Lunch Break

13:00-14:00  Documentation Final Review (Dev-08)
             - Verify all docs accurate
             - Update CHANGELOG

14:00-15:30  Sprint Retrospective (All)
             - What went well
             - What needs improvement
             - Action items

15:30-17:00  Sprint 3 Planning (All)
             - Review Sprint 3 backlog
             - Assign tasks
             - Identify risks
```

### Conflict Resolution Protocol

If merge conflicts occur:

1. **File owner resolves** their own files
2. **Tech Lead arbitrates** shared file conflicts
3. **Rerun full tests** after resolution
4. **Document resolution** in PR comments

---

## Success Criteria

### Sprint 2 Definition of Done

**Dev-02 (Backend):**
- [ ] DeepSeek vLLM backend fully functional
- [ ] Fallback chain working
- [ ] Unit test coverage >90%
- [ ] Integration tests passing

**Dev-03 (Pipeline):**
- [ ] Progress callback protocol defined
- [ ] ConsoleProgressCallback implemented
- [ ] Pipeline integration complete
- [ ] Unit tests passing

**Dev-04 (DevOps):**
- [ ] Docker image builds (<500MB)
- [ ] docker-compose works
- [ ] Health check CLI command works
- [ ] Config validation works

**Dev-06 (CLI):**
- [ ] Batch command works
- [ ] Progress display shows real progress
- [ ] Glob patterns work
- [ ] Parallel processing works

**Dev-07 (QA):**
- [ ] Benchmark suite complete
- [ ] E2E tests passing
- [ ] Performance baseline documented
- [ ] Memory usage acceptable

**Dev-08 (Docs):**
- [ ] Deployment guide complete
- [ ] API reference complete
- [ ] Quick start tested
- [ ] Examples working

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| vLLM API incompatibility | Medium | High | Early testing, mock fallback |
| Merge conflicts | Low | Medium | Strict file ownership |
| Docker image size | Low | Low | Multi-stage builds |
| Progress integration complexity | Medium | Medium | Clear protocol first |
| Benchmark flakiness | Medium | Low | Multiple runs, thresholds |
| Documentation lag | Low | Medium | Start early, review often |

---

## Communication Protocol

**Daily Standups (Async):**
- Post in team channel by 10:00 AM
- Format: "Yesterday | Today | Blockers"

**Sync Meetings:**
- Monday 10:00: Sprint sync (30 min)
- Wednesday 14:00: Mid-sprint check (30 min)
- Friday 15:00: Demo prep (30 min)

**Integration Period:**
- Day 9: Heavy Slack presence
- Day 10: All hands for testing

**Escalation:**
1. DM file owner
2. Post in team channel @owner
3. Escalate to Tech Lead
4. Emergency sync meeting

---

*Document Version: 2.0*
*Updated: 2024-11-25*
*Approved By: Tech Lead*
