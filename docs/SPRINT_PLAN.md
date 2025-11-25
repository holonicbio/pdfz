# Docling Hybrid OCR - Development Sprint Plan

## Overview

**Project Duration:** 16 weeks (8 sprints × 2 weeks)  
**Team Size:** 10 developers  
**Sprint Length:** 2 weeks  
**Integration Period:** 2-3 days between sprints

### Two-Stage Development

| Stage | Sprints | Goal | Duration |
|-------|---------|------|----------|
| **Stage 1** | Sprints 1-4 | Minimal Functioning System (OpenRouter) | 8 weeks |
| **Stage 2** | Sprints 5-8 | Full Local System (DeepSeek + Extensions) | 8 weeks |

### Team Structure

| Role | Developer | Primary Focus |
|------|-----------|---------------|
| Tech Lead | Dev-01 | Architecture, integration, code review |
| Backend Lead | Dev-02 | OCR backends, API integration |
| Pipeline Lead | Dev-03 | Orchestrator, data flow |
| Infrastructure | Dev-04 | Config, logging, CI/CD |
| Renderer Specialist | Dev-05 | PDF rendering, image processing |
| CLI/UX Lead | Dev-06 | CLI, user experience |
| Testing Lead | Dev-07 | Test infrastructure, quality |
| Documentation | Dev-08 | Docs, examples, tutorials |
| Block Processing | Dev-09 | Block segmentation, routing |
| Evaluation | Dev-10 | Metrics, evaluation framework |

---

# STAGE 1: Minimal Functioning System
## Goal: PDF → Markdown via OpenRouter/Nemotron

---

## Sprint 1: Foundation & Interfaces
**Duration:** Weeks 1-2  
**Theme:** "Build the skeleton, define the contracts"

### Sprint Goals
1. Establish project structure and tooling
2. Define ALL interfaces upfront (critical for parallel work)
3. Implement foundation layer (no external dependencies)
4. Set up CI/CD pipeline

### Ownership Map (No Overlapping Files)

```
Dev-01 (Tech Lead):
├── pyproject.toml
├── README.md
├── docs/ARCHITECTURE.md
└── Interface definitions (reviews all)

Dev-02 (Backend Lead):
├── src/docling_hybrid/backends/
│   ├── __init__.py
│   ├── base.py              # OcrVlmBackend ABC
│   └── interfaces.py        # Type definitions
└── docs/components/BACKENDS.md

Dev-03 (Pipeline Lead):
├── src/docling_hybrid/orchestrator/
│   ├── __init__.py
│   ├── interfaces.py        # Pipeline interfaces
│   └── models.py            # ConversionOptions, ConversionResult
└── docs/components/ORCHESTRATOR.md

Dev-04 (Infrastructure):
├── src/docling_hybrid/common/
│   ├── __init__.py
│   ├── config.py
│   └── errors.py
├── configs/
│   ├── default.toml
│   ├── local.toml
│   └── test.toml
└── .github/workflows/

Dev-05 (Renderer):
├── src/docling_hybrid/renderer/
│   ├── __init__.py
│   └── interfaces.py        # Renderer interface
└── docs/components/RENDERER.md

Dev-06 (CLI Lead):
├── src/docling_hybrid/cli/
│   ├── __init__.py
│   └── interfaces.py        # CLI argument models
└── docs/CLI.md

Dev-07 (Testing Lead):
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   └── unit/__init__.py
├── pytest.ini (if needed)
└── docs/TESTING.md

Dev-08 (Documentation):
├── CLAUDE.md
├── CONTINUATION.md
├── LOCAL_DEV.md
├── docs/GETTING_STARTED.md
└── docs/interfaces/           # Interface documentation

Dev-09 (Block Processing):
├── src/docling_hybrid/blocks/
│   ├── __init__.py
│   └── interfaces.py        # Block processing interfaces
└── docs/components/BLOCKS.md

Dev-10 (Evaluation):
├── src/docling_hybrid/eval/
│   ├── __init__.py
│   └── interfaces.py        # Evaluation interfaces
└── docs/components/EVALUATION.md
```

### Interface Contract: Sprint 1 Deliverable

All developers MUST define their interfaces by Day 3 and get approval from Tech Lead.

```python
# Example: Backend Interface (Dev-02 delivers, all reference)
class OcrVlmBackend(ABC):
    @abstractmethod
    async def page_to_markdown(self, image_bytes: bytes, page_num: int, doc_id: str) -> str: ...
    @abstractmethod
    async def table_to_markdown(self, image_bytes: bytes, meta: dict) -> str: ...
    @abstractmethod
    async def formula_to_latex(self, image_bytes: bytes, meta: dict) -> str: ...
```

### Task Cards - Sprint 1

#### S1-T01: Project Setup (Dev-01)
```
Priority: P0 (Blocking)
Estimated: 2 days
Dependencies: None

Tasks:
- [ ] Initialize git repository with .gitignore
- [ ] Create pyproject.toml with all dependencies
- [ ] Create directory structure (all empty __init__.py)
- [ ] Write README.md with project overview
- [ ] Create initial ARCHITECTURE.md

Acceptance:
- [ ] `pip install -e .` works
- [ ] All directories exist with __init__.py
- [ ] README explains project purpose
```

#### S1-T02: Configuration System (Dev-04)
```
Priority: P0 (Blocking)
Estimated: 3 days
Dependencies: S1-T01

Tasks:
- [ ] Implement Config Pydantic models
- [ ] Implement load_config() with layered loading
- [ ] Implement get_config() / init_config()
- [ ] Create default.toml, local.toml, test.toml
- [ ] Write unit tests for config loading

Files:
- src/docling_hybrid/common/config.py
- src/docling_hybrid/common/errors.py
- configs/*.toml

Acceptance:
- [ ] Config loads from file
- [ ] Env vars override file values
- [ ] Missing config raises clear error
- [ ] Tests pass
```

#### S1-T03: Common Utilities (Dev-04)
```
Priority: P1
Estimated: 2 days
Dependencies: S1-T02

Tasks:
- [ ] Implement ID generation (generate_id, generate_timestamp_id)
- [ ] Implement structured logging setup
- [ ] Implement error hierarchy
- [ ] Write unit tests

Files:
- src/docling_hybrid/common/ids.py
- src/docling_hybrid/common/logging.py
- src/docling_hybrid/common/errors.py (extend)

Acceptance:
- [ ] IDs are unique
- [ ] Logging outputs JSON or text based on config
- [ ] All error types documented
```

#### S1-T04: Backend Interface Definition (Dev-02)
```
Priority: P0 (Blocking)
Estimated: 2 days
Dependencies: S1-T01

Tasks:
- [ ] Define OcrVlmBackend ABC
- [ ] Define OcrBackendConfig model
- [ ] Define BackendCandidate model
- [ ] Define factory interface
- [ ] Document interface contract

Files:
- src/docling_hybrid/backends/base.py
- src/docling_hybrid/common/models.py (backend models only)

Acceptance:
- [ ] Interface reviewed by Tech Lead
- [ ] All methods have docstrings
- [ ] Type hints complete
```

#### S1-T05: Pipeline Interface Definition (Dev-03)
```
Priority: P0 (Blocking)
Estimated: 2 days
Dependencies: S1-T01

Tasks:
- [ ] Define ConversionOptions model
- [ ] Define ConversionResult model
- [ ] Define PageResult model
- [ ] Define HybridPipeline interface
- [ ] Document interface contract

Files:
- src/docling_hybrid/orchestrator/models.py
- src/docling_hybrid/orchestrator/interfaces.py

Acceptance:
- [ ] Interface reviewed by Tech Lead
- [ ] Models validate correctly
```

#### S1-T06: Renderer Interface Definition (Dev-05)
```
Priority: P0 (Blocking)
Estimated: 1 day
Dependencies: S1-T01

Tasks:
- [ ] Define render_page_to_png_bytes signature
- [ ] Define render_region_to_png_bytes signature
- [ ] Define get_page_count signature
- [ ] Document expected behavior

Files:
- src/docling_hybrid/renderer/interfaces.py

Acceptance:
- [ ] Interface approved by Tech Lead
```

#### S1-T07: CLI Interface Definition (Dev-06)
```
Priority: P1
Estimated: 1 day
Dependencies: S1-T01

Tasks:
- [ ] Design CLI command structure
- [ ] Define argument models
- [ ] Document expected behavior

Files:
- src/docling_hybrid/cli/interfaces.py
- docs/CLI.md

Acceptance:
- [ ] CLI design approved
```

#### S1-T08: Test Infrastructure (Dev-07)
```
Priority: P0 (Blocking)
Estimated: 3 days
Dependencies: S1-T02, S1-T03

Tasks:
- [ ] Set up pytest configuration
- [ ] Create conftest.py with fixtures
- [ ] Create mock fixtures for backends
- [ ] Create sample test data
- [ ] Set up coverage reporting

Files:
- tests/conftest.py
- tests/fixtures/
- tests/unit/__init__.py

Acceptance:
- [ ] pytest runs with no errors
- [ ] Coverage reporting works
- [ ] Mock fixtures usable
```

#### S1-T09: CI/CD Pipeline (Dev-04)
```
Priority: P1
Estimated: 2 days
Dependencies: S1-T08

Tasks:
- [ ] Create GitHub Actions test workflow
- [ ] Create linting workflow
- [ ] Set up branch protection rules

Files:
- .github/workflows/test.yml
- .github/workflows/lint.yml

Acceptance:
- [ ] Tests run on PR
- [ ] Linting runs on PR
```

#### S1-T10: Documentation Framework (Dev-08)
```
Priority: P1
Estimated: 4 days
Dependencies: All interface definitions

Tasks:
- [ ] Write CLAUDE.md master context
- [ ] Write LOCAL_DEV.md
- [ ] Create docs/GETTING_STARTED.md
- [ ] Document all interfaces in docs/interfaces/
- [ ] Create component doc templates

Acceptance:
- [ ] New developer can understand project from docs
- [ ] All interfaces documented
```

### Sprint 1 Integration (Days 9-10)

**Integration Owner:** Dev-01 (Tech Lead)

**Checklist:**
- [ ] All interfaces defined and approved
- [ ] All PRs merged to develop branch
- [ ] CI/CD pipeline green
- [ ] All tests pass
- [ ] Documentation reviewed
- [ ] Interface contracts frozen for Sprint 2

**Integration Meeting Agenda:**
1. Demo each component's interface
2. Verify no import cycles
3. Confirm interface contracts
4. Plan Sprint 2 dependencies

---

## Sprint 2: Core Implementation
**Duration:** Weeks 3-4  
**Theme:** "Implement the core, test in isolation"

### Sprint Goals
1. Implement PDF renderer with pypdfium2
2. Implement OpenRouter/Nemotron backend
3. Implement backend factory
4. Unit tests for all components

### Ownership Map (No Overlapping Files)

```
Dev-01 (Tech Lead):
└── Integration tests design, code review

Dev-02 (Backend Lead):
├── src/docling_hybrid/backends/
│   ├── factory.py
│   └── openrouter_nemotron.py
└── tests/unit/test_backends.py

Dev-03 (Pipeline Lead):
└── (Preparing pipeline implementation for Sprint 3)
└── Design review, test planning

Dev-04 (Infrastructure):
├── src/docling_hybrid/common/models.py (shared models)
└── Configuration refinement based on needs

Dev-05 (Renderer):
├── src/docling_hybrid/renderer/core.py
└── tests/unit/test_renderer.py

Dev-06 (CLI Lead):
└── (Preparing CLI implementation for Sprint 3)
└── Design review, test planning

Dev-07 (Testing Lead):
├── tests/unit/test_common.py
├── tests/mocks/
│   ├── __init__.py
│   ├── mock_backends.py
│   └── mock_http.py
└── Test documentation

Dev-08 (Documentation):
├── docs/components/BACKENDS.md (implementation details)
├── docs/components/RENDERER.md (implementation details)
└── Code documentation review

Dev-09 (Block Processing):
└── (Preparing block interfaces for Stage 2)
└── Research Docling block extraction

Dev-10 (Evaluation):
└── (Preparing evaluation design for Stage 2)
└── Research evaluation metrics
```

### Task Cards - Sprint 2

#### S2-T01: Renderer Implementation (Dev-05)
```
Priority: P0 (Blocking)
Estimated: 4 days
Dependencies: Sprint 1 complete

Tasks:
- [ ] Implement render_page_to_png_bytes with pypdfium2
- [ ] Implement render_region_to_png_bytes
- [ ] Implement get_page_count
- [ ] Handle edge cases (invalid PDF, out of range page)
- [ ] Write comprehensive unit tests

Files:
- src/docling_hybrid/renderer/core.py
- tests/unit/test_renderer.py

Test Cases:
- [ ] Valid PDF renders correctly
- [ ] Invalid PDF raises RenderingError
- [ ] Page index out of range raises ValidationError
- [ ] Different DPI values work
- [ ] Region cropping works

Acceptance:
- [ ] All public functions implemented
- [ ] >90% test coverage
- [ ] No memory leaks on repeated calls
```

#### S2-T02: Backend Factory (Dev-02)
```
Priority: P0 (Blocking)
Estimated: 2 days
Dependencies: S1-T04

Tasks:
- [ ] Implement make_backend() factory function
- [ ] Implement list_backends()
- [ ] Implement register_backend()
- [ ] Write unit tests

Files:
- src/docling_hybrid/backends/factory.py
- tests/unit/test_backend_factory.py

Acceptance:
- [ ] Factory creates correct backend types
- [ ] Unknown backend raises ConfigurationError
- [ ] Registration works for custom backends
```

#### S2-T03: OpenRouter Nemotron Backend (Dev-02)
```
Priority: P0 (Blocking)
Estimated: 5 days
Dependencies: S2-T02

Tasks:
- [ ] Implement OpenRouterNemotronBackend class
- [ ] Implement _encode_image (base64)
- [ ] Implement _build_messages (OpenAI format)
- [ ] Implement _post_chat with aiohttp
- [ ] Implement _extract_content (string/list)
- [ ] Define PAGE_TO_MARKDOWN_PROMPT
- [ ] Define TABLE_TO_MARKDOWN_PROMPT
- [ ] Define FORMULA_TO_LATEX_PROMPT
- [ ] Handle all error cases
- [ ] Write unit tests with mocked HTTP

Files:
- src/docling_hybrid/backends/openrouter_nemotron.py
- tests/unit/test_openrouter_backend.py

Test Cases:
- [ ] Successful API response
- [ ] API error response (4xx, 5xx)
- [ ] Timeout handling
- [ ] Connection error handling
- [ ] Content extraction (string format)
- [ ] Content extraction (list format)
- [ ] Missing API key error

Acceptance:
- [ ] All three methods implemented
- [ ] All error cases handled
- [ ] >85% test coverage
```

#### S2-T04: Shared Models (Dev-04)
```
Priority: P0 (Blocking)
Estimated: 2 days
Dependencies: S1-T04, S1-T05

Tasks:
- [ ] Finalize OcrBackendConfig model
- [ ] Finalize BackendCandidate model
- [ ] Finalize PageResult model
- [ ] Add validation rules
- [ ] Write unit tests

Files:
- src/docling_hybrid/common/models.py
- tests/unit/test_models.py

Acceptance:
- [ ] All models validate correctly
- [ ] Invalid data rejected with clear errors
```

#### S2-T05: Mock Infrastructure (Dev-07)
```
Priority: P1
Estimated: 3 days
Dependencies: S2-T02

Tasks:
- [ ] Create MockBackend implementation
- [ ] Create HTTP response mocking utilities
- [ ] Create test PDF fixtures
- [ ] Document mock usage

Files:
- tests/mocks/mock_backends.py
- tests/mocks/mock_http.py
- tests/fixtures/sample.pdf (1-page)
- tests/fixtures/multi_page.pdf (3-page)

Acceptance:
- [ ] MockBackend passes interface tests
- [ ] HTTP mocking works for async code
```

#### S2-T06: Common Module Tests (Dev-07)
```
Priority: P1
Estimated: 3 days
Dependencies: Sprint 1

Tasks:
- [ ] Write tests for config.py
- [ ] Write tests for ids.py
- [ ] Write tests for logging.py
- [ ] Write tests for errors.py
- [ ] Achieve >90% coverage on common module

Files:
- tests/unit/test_common.py
- tests/unit/test_config.py

Acceptance:
- [ ] All tests pass
- [ ] >90% coverage on common/
```

#### S2-T07: Backend Documentation (Dev-08)
```
Priority: P2
Estimated: 3 days
Dependencies: S2-T03

Tasks:
- [ ] Document OpenRouter backend usage
- [ ] Document prompt engineering decisions
- [ ] Create backend extension guide
- [ ] Add code examples

Files:
- docs/components/BACKENDS.md
- docs/guides/ADDING_BACKENDS.md

Acceptance:
- [ ] New developer can understand backend implementation
- [ ] Extension guide enables custom backends
```

#### S2-T08: Block Processing Research (Dev-09)
```
Priority: P2
Estimated: 5 days
Dependencies: None

Tasks:
- [ ] Research Docling block extraction API
- [ ] Document block types and attributes
- [ ] Design routing strategy
- [ ] Create proof-of-concept
- [ ] Write design document

Deliverables:
- docs/design/BLOCK_PROCESSING.md
- Proof-of-concept code (not production)

Acceptance:
- [ ] Design document approved by Tech Lead
- [ ] PoC demonstrates block extraction
```

#### S2-T09: Evaluation Research (Dev-10)
```
Priority: P2
Estimated: 5 days
Dependencies: None

Tasks:
- [ ] Research OCR evaluation metrics (edit distance, TEDS)
- [ ] Research ground truth formats
- [ ] Design evaluation framework
- [ ] Create proof-of-concept
- [ ] Write design document

Deliverables:
- docs/design/EVALUATION.md
- Proof-of-concept code (not production)

Acceptance:
- [ ] Design document approved by Tech Lead
- [ ] Metrics clearly defined
```

### Sprint 2 Integration (Days 9-10)

**Integration Owner:** Dev-01 (Tech Lead)

**Integration Tests:**
```python
# tests/integration/test_sprint2.py

async def test_renderer_produces_valid_png():
    """Renderer output can be used by backend."""
    image_bytes = render_page_to_png_bytes(pdf_path, 0, dpi=150)
    assert len(image_bytes) > 0
    # Verify PNG header
    assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'

async def test_backend_factory_creates_nemotron():
    """Factory creates working Nemotron backend."""
    config = OcrBackendConfig(name="nemotron-openrouter", ...)
    backend = make_backend(config)
    assert isinstance(backend, OpenRouterNemotronBackend)

async def test_backend_with_rendered_page(mock_http):
    """Backend can process rendered page."""
    image_bytes = render_page_to_png_bytes(pdf_path, 0)
    mock_http.post(..., json={"choices": [{"message": {"content": "# Test"}}]})
    
    backend = make_backend(config)
    result = await backend.page_to_markdown(image_bytes, 1, "doc-123")
    assert result == "# Test"
```

**Checklist:**
- [ ] Renderer produces valid PNGs
- [ ] Backend processes images correctly
- [ ] Factory creates all backend types
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] No circular imports

---

## Sprint 3: Pipeline & CLI
**Duration:** Weeks 5-6  
**Theme:** "Connect the components, expose to users"

### Sprint Goals
1. Implement HybridPipeline orchestrator
2. Implement CLI with Typer
3. End-to-end flow working (with mocked backend)
4. Integration tests complete

### Ownership Map (No Overlapping Files)

```
Dev-01 (Tech Lead):
└── Integration orchestration, end-to-end testing

Dev-02 (Backend Lead):
├── Backend refinements based on pipeline needs
└── tests/integration/test_backend_integration.py

Dev-03 (Pipeline Lead):
├── src/docling_hybrid/orchestrator/pipeline.py
└── tests/unit/test_pipeline.py

Dev-04 (Infrastructure):
├── Environment configuration refinement
└── Deployment documentation

Dev-05 (Renderer):
├── Renderer optimizations if needed
└── tests/integration/test_renderer_integration.py

Dev-06 (CLI Lead):
├── src/docling_hybrid/cli/main.py
└── tests/unit/test_cli.py

Dev-07 (Testing Lead):
├── tests/integration/test_e2e.py
├── tests/smoke/
└── Test coverage reporting

Dev-08 (Documentation):
├── User documentation
├── docs/guides/QUICK_START.md
└── Example scripts

Dev-09 (Block Processing):
└── Continue design work, interface refinement

Dev-10 (Evaluation):
└── Continue design work, interface refinement
```

### Task Cards - Sprint 3

#### S3-T01: HybridPipeline Implementation (Dev-03)
```
Priority: P0 (Blocking)
Estimated: 5 days
Dependencies: Sprint 2 complete

Tasks:
- [ ] Implement HybridPipeline class
- [ ] Implement convert_pdf() method
- [ ] Implement page iteration logic
- [ ] Implement result concatenation
- [ ] Implement output file writing
- [ ] Handle per-page errors gracefully
- [ ] Add logging context binding
- [ ] Write comprehensive unit tests

Files:
- src/docling_hybrid/orchestrator/pipeline.py
- tests/unit/test_pipeline.py

Test Cases:
- [ ] Single page PDF
- [ ] Multi-page PDF
- [ ] Page rendering failure (continues with others)
- [ ] Backend failure (continues with others)
- [ ] Options (max_pages, start_page, dpi)
- [ ] Output file written correctly
- [ ] Page separators work

Acceptance:
- [ ] Full pipeline works with mock backend
- [ ] All options respected
- [ ] Errors handled gracefully
- [ ] >85% test coverage
```

#### S3-T02: CLI Implementation (Dev-06)
```
Priority: P0 (Blocking)
Estimated: 5 days
Dependencies: S3-T01

Tasks:
- [ ] Implement Typer app structure
- [ ] Implement `convert` command
- [ ] Implement `backends` command
- [ ] Implement `info` command
- [ ] Add --verbose, --config, --output options
- [ ] Add rich formatting for output
- [ ] Handle errors gracefully
- [ ] Write unit tests

Files:
- src/docling_hybrid/cli/main.py
- tests/unit/test_cli.py

Commands:
- docling-hybrid-ocr convert <pdf> [options]
- docling-hybrid-ocr backends
- docling-hybrid-ocr info
- docling-hybrid-ocr --version

Acceptance:
- [ ] All commands work
- [ ] --help shows useful information
- [ ] Errors show actionable messages
- [ ] Exit codes correct
```

#### S3-T03: Integration Tests (Dev-07)
```
Priority: P0 (Blocking)
Estimated: 5 days
Dependencies: S3-T01, S3-T02

Tasks:
- [ ] Write end-to-end test with mocked HTTP
- [ ] Write pipeline integration tests
- [ ] Write CLI integration tests
- [ ] Create smoke test suite

Files:
- tests/integration/test_e2e.py
- tests/integration/test_pipeline.py
- tests/integration/test_cli.py
- tests/smoke/test_smoke.py

Acceptance:
- [ ] E2E test converts PDF to Markdown
- [ ] All integration tests pass
- [ ] Smoke tests run in <30 seconds
```

#### S3-T04: User Documentation (Dev-08)
```
Priority: P1
Estimated: 4 days
Dependencies: S3-T02

Tasks:
- [ ] Write QUICK_START.md
- [ ] Write CLI usage guide
- [ ] Create example scripts
- [ ] Update README with examples
- [ ] Add troubleshooting guide

Files:
- docs/guides/QUICK_START.md
- docs/guides/CLI_USAGE.md
- examples/basic_conversion.py
- examples/custom_options.py

Acceptance:
- [ ] New user can convert PDF in <5 minutes
- [ ] All examples work
```

### Sprint 3 Integration (Days 9-10)

**Integration Owner:** Dev-01 (Tech Lead)

**End-to-End Test:**
```bash
# With mocked HTTP (CI)
pytest tests/integration -v

# Manual smoke test (requires API key)
export OPENROUTER_API_KEY=...
docling-hybrid-ocr convert tests/fixtures/sample.pdf --verbose
```

**Checklist:**
- [ ] CLI commands all work
- [ ] Pipeline converts PDFs correctly
- [ ] Output Markdown is valid
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Ready for real API testing

---

## Sprint 4: Polish & Stage 1 Complete
**Duration:** Weeks 7-8  
**Theme:** "Production-ready minimal system"

### Sprint Goals
1. Real API testing and refinement
2. Error handling hardening
3. Performance optimization
4. Complete documentation
5. Stage 1 release

### Ownership Map

```
Dev-01: Release management, final integration
Dev-02: Backend hardening, retry logic
Dev-03: Pipeline optimization, concurrent processing
Dev-04: Deployment docs, Docker setup
Dev-05: Renderer optimization
Dev-06: CLI polish, UX improvements
Dev-07: Final test coverage, release testing
Dev-08: Final documentation review
Dev-09: Block processing interface finalization
Dev-10: Evaluation interface finalization
```

### Task Cards - Sprint 4

#### S4-T01: Real API Testing (Dev-02)
```
Priority: P0
Estimated: 3 days

Tasks:
- [ ] Test with real OpenRouter API
- [ ] Test various PDF types (text, tables, formulas)
- [ ] Identify and fix edge cases
- [ ] Document API behavior
```

#### S4-T02: Retry Logic (Dev-02)
```
Priority: P1
Estimated: 2 days

Tasks:
- [ ] Implement exponential backoff
- [ ] Add configurable retry count
- [ ] Handle rate limiting
```

#### S4-T03: Concurrent Page Processing (Dev-03)
```
Priority: P1
Estimated: 3 days

Tasks:
- [ ] Implement asyncio.gather for pages
- [ ] Add concurrency limit (max_workers)
- [ ] Maintain page order in output
```

#### S4-T04: Docker Setup (Dev-04)
```
Priority: P2
Estimated: 2 days

Tasks:
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Document container usage
```

#### S4-T05: Stage 1 Release (Dev-01)
```
Priority: P0
Estimated: 2 days

Tasks:
- [ ] Create release branch
- [ ] Version bump to 0.1.0
- [ ] Create GitHub release
- [ ] Publish documentation
```

### Stage 1 Completion Criteria

- [ ] CLI converts PDFs using OpenRouter API
- [ ] All tests pass (unit, integration, smoke)
- [ ] Documentation complete
- [ ] Docker image available
- [ ] No critical bugs
- [ ] Performance acceptable (<30s for 10-page PDF)

---

# STAGE 2: Full Local System
## Goal: DeepSeek OCR + Block Processing + Evaluation

---

## Sprint 5: DeepSeek Backends
**Duration:** Weeks 9-10  
**Theme:** "Local inference capability"

### Sprint Goals
1. Implement DeepSeek vLLM backend
2. Implement DeepSeek MLX backend
3. Backend selection via config
4. Testing with local models

### Ownership Map

```
Dev-01: Integration, multi-backend testing
Dev-02: DeepSeek vLLM backend
Dev-03: Pipeline updates for local backends
Dev-04: vLLM deployment documentation
Dev-05: Image preprocessing optimizations
Dev-06: Backend selection in CLI
Dev-07: Backend integration tests
Dev-08: Backend comparison documentation
Dev-09: Begin block segmentation
Dev-10: Begin evaluation implementation
```

### Task Cards - Sprint 5

#### S5-T01: DeepSeek vLLM Backend (Dev-02)
```
Priority: P0
Estimated: 5 days
Dependencies: vLLM server available for testing

Tasks:
- [ ] Implement DeepseekOcrVllmBackend
- [ ] Reuse prompt templates from Nemotron
- [ ] Adapt HTTP calls for vLLM API
- [ ] Handle vLLM-specific response format
- [ ] Write unit tests with mocked HTTP
- [ ] Integration test with real vLLM

Files:
- src/docling_hybrid/backends/deepseek_vllm.py
- tests/unit/test_deepseek_vllm.py

Acceptance:
- [ ] Same interface as Nemotron backend
- [ ] Works with local vLLM server
- [ ] All prompts produce similar results
```

#### S5-T02: DeepSeek MLX Backend (Dev-02 + Dev-05)
```
Priority: P1
Estimated: 5 days
Dependencies: macOS with Apple Silicon

Tasks:
- [ ] Implement DeepseekOcrMlxBackend
- [ ] Choose: direct API or HTTP sidecar
- [ ] Implement chosen approach
- [ ] Write unit tests
- [ ] Test on Apple Silicon Mac

Files:
- src/docling_hybrid/backends/deepseek_mlx.py
- tests/unit/test_deepseek_mlx.py

Acceptance:
- [ ] Same interface as other backends
- [ ] Works on macOS with M1/M2/M3
```

#### S5-T03: CLI Backend Selection (Dev-06)
```
Priority: P1
Estimated: 2 days

Tasks:
- [ ] Add --backend option to convert command
- [ ] Add backend validation
- [ ] Update help text
```

#### S5-T04: Block Segmentation Start (Dev-09)
```
Priority: P2
Estimated: 5 days

Tasks:
- [ ] Implement Docling document parsing
- [ ] Extract blocks with geometry
- [ ] Map block types to BlockType enum
- [ ] Create BlockGraph structure
```

#### S5-T05: Evaluation Infrastructure Start (Dev-10)
```
Priority: P2
Estimated: 5 days

Tasks:
- [ ] Implement ground truth loading
- [ ] Implement text edit distance metric
- [ ] Create evaluation runner skeleton
```

---

## Sprint 6: Block-Level Processing
**Duration:** Weeks 11-12  
**Theme:** "Intelligent block routing"

### Sprint Goals
1. Block segmentation from Docling
2. Backend routing per block type
3. Block-level OCR integration
4. Merge block results to document

### Ownership Map

```
Dev-01: Block processing architecture review
Dev-02: Table backend wrapper
Dev-03: Block-to-document pipeline
Dev-04: Block processing configuration
Dev-05: Region rendering for blocks
Dev-06: Block-level CLI options
Dev-07: Block processing tests
Dev-08: Block processing documentation
Dev-09: Block segmentation (primary)
Dev-10: Continue evaluation
```

### Key Components

```python
# Block types to handle
class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    LIST = "list"
    CODE = "code"

# Routing configuration
routing_rules:
  - block_type: TABLE
    backends: [deepseek-vllm, nemotron-openrouter]
    use_specialized: true
  - block_type: FORMULA
    backends: [deepseek-vllm]
    use_specialized: true
  - block_type: PARAGRAPH
    backends: [docling-native, deepseek-vllm]
```

---

## Sprint 7: Multi-Backend & Merging
**Duration:** Weeks 13-14  
**Theme:** "Best of all worlds"

### Sprint Goals
1. Run multiple backends per block
2. Implement candidate merging strategies
3. Optional LLM arbitration
4. Quality scoring

### Ownership Map

```
Dev-01: Merge strategy design
Dev-02: Multi-backend orchestration
Dev-03: Candidate collection pipeline
Dev-04: Merge policy configuration
Dev-05: Quality scoring heuristics
Dev-06: Multi-backend CLI options
Dev-07: Merge strategy tests
Dev-08: Merge documentation
Dev-09: Block result merging
Dev-10: Evaluation framework completion
```

### Merge Strategies

```python
class MergePolicy(Enum):
    PREFER_FIRST = "prefer_first"           # Use first successful
    PREFER_BACKEND = "prefer_backend"       # Prefer specific backend
    VOTE = "vote"                           # Majority voting
    LLM_ARBITRATE = "llm_arbitrate"         # Use LLM to choose/merge
    ENSEMBLE = "ensemble"                   # Weighted combination
```

---

## Sprint 8: Evaluation & Release
**Duration:** Weeks 15-16  
**Theme:** "Measure, optimize, release"

### Sprint Goals
1. Complete evaluation framework
2. Run benchmarks on test corpus
3. Optimize based on results
4. Stage 2 release

### Ownership Map

```
Dev-01: Release management
Dev-02: Backend optimization
Dev-03: Pipeline optimization
Dev-04: Deployment finalization
Dev-05: Rendering optimization
Dev-06: CLI finalization
Dev-07: Release testing
Dev-08: Final documentation
Dev-09: Block processing finalization
Dev-10: Evaluation completion, benchmarks
```

### Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Text Edit Distance | <0.05 | Normalized edit distance vs ground truth |
| Table TEDS | >0.90 | Tree edit distance for tables |
| Formula Accuracy | >0.85 | LaTeX string match |
| Processing Speed | <3s/page | Average with local backend |

### Stage 2 Completion Criteria

- [ ] DeepSeek backends working (vLLM and MLX)
- [ ] Block-level processing functional
- [ ] Multi-backend merging available
- [ ] Evaluation framework complete
- [ ] Benchmarks documented
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Version 1.0.0 released

---

# Appendix A: File Ownership Matrix

This matrix prevents merge conflicts by assigning exclusive ownership.

| Directory/File | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5-8 |
|----------------|----------|----------|----------|----------|------------|
| `common/config.py` | Dev-04 | Dev-04 | Dev-04 | Dev-04 | Dev-04 |
| `common/models.py` | Dev-02,03 | Dev-04 | Dev-04 | Dev-04 | Dev-04 |
| `common/errors.py` | Dev-04 | Dev-04 | Dev-04 | Dev-04 | Dev-04 |
| `common/ids.py` | Dev-04 | Dev-04 | - | - | - |
| `common/logging.py` | Dev-04 | Dev-04 | - | - | - |
| `backends/base.py` | Dev-02 | Dev-02 | Dev-02 | Dev-02 | Dev-02 |
| `backends/factory.py` | - | Dev-02 | Dev-02 | Dev-02 | Dev-02 |
| `backends/openrouter_nemotron.py` | - | Dev-02 | Dev-02 | Dev-02 | Dev-02 |
| `backends/deepseek_vllm.py` | - | - | - | - | Dev-02 |
| `backends/deepseek_mlx.py` | - | - | - | - | Dev-02 |
| `renderer/core.py` | - | Dev-05 | Dev-05 | Dev-05 | Dev-05 |
| `orchestrator/pipeline.py` | - | - | Dev-03 | Dev-03 | Dev-03 |
| `orchestrator/models.py` | Dev-03 | Dev-03 | Dev-03 | Dev-03 | Dev-03 |
| `cli/main.py` | - | - | Dev-06 | Dev-06 | Dev-06 |
| `blocks/*` | Dev-09 | Dev-09 | Dev-09 | Dev-09 | Dev-09 |
| `eval/*` | Dev-10 | Dev-10 | Dev-10 | Dev-10 | Dev-10 |
| `tests/conftest.py` | Dev-07 | Dev-07 | Dev-07 | Dev-07 | Dev-07 |
| `tests/unit/*` | Various | Various | Various | Various | Various |
| `tests/integration/*` | - | - | Dev-07 | Dev-07 | Dev-07 |
| `docs/ARCHITECTURE.md` | Dev-01 | Dev-01 | Dev-01 | Dev-01 | Dev-01 |
| `docs/components/*` | Various | Various | Various | Various | Various |
| `CLAUDE.md` | Dev-08 | Dev-08 | Dev-08 | Dev-08 | Dev-08 |
| `README.md` | Dev-01 | Dev-01 | Dev-08 | Dev-08 | Dev-08 |

---

# Appendix B: Integration Checklist Template

Use this checklist at the end of each sprint.

```markdown
## Sprint N Integration Checklist

### Pre-Integration (Day 8)
- [ ] All PRs have passing CI
- [ ] All PRs have been code reviewed
- [ ] No merge conflicts in develop branch
- [ ] Documentation updated

### Integration (Day 9)
- [ ] Merge all PRs to develop
- [ ] Run full test suite
- [ ] Run integration tests
- [ ] Manual smoke test

### Post-Integration (Day 10)
- [ ] All tests pass
- [ ] No regressions
- [ ] Update CONTINUATION.md
- [ ] Sprint retrospective
- [ ] Plan next sprint kickoff
```

---

# Appendix C: Communication Protocol

### Daily Standups
- Time: 9:00 AM local
- Duration: 15 minutes
- Format: What I did, what I'm doing, blockers

### Sprint Planning
- When: Day 1 of sprint
- Duration: 2 hours
- Attendees: All developers

### Integration Reviews
- When: Days 9-10 of sprint
- Duration: 4 hours
- Owner: Tech Lead

### Code Reviews
- Required: 1 approval minimum
- Turnaround: 24 hours
- Focus: Interface adherence, test coverage

### Escalation Path
1. Pair with teammate
2. Ask in team channel
3. Escalate to Tech Lead
4. Architecture review meeting
