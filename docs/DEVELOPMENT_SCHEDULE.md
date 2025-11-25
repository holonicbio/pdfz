# Docling Hybrid OCR - Complete Development Schedule

## Executive Summary

| Attribute | Value |
|-----------|-------|
| **Total Duration** | 16 weeks (8 sprints) |
| **Team Size** | 10 developers |
| **Sprint Length** | 2 weeks |
| **Integration Period** | 2-3 days between sprints |
| **Stage 1 Goal** | Minimal system with OpenRouter (Sprints 1-4) |
| **Stage 2 Goal** | Full local system with DeepSeek + Extensions (Sprints 5-8) |

---

## Architecture Philosophy: Modularity First

### Core Principles

1. **Interface-Driven Development**: Define ALL interfaces in Sprint 1 before implementation
2. **Dependency Injection**: Components receive dependencies, never create them
3. **Plugin Architecture**: New backends/exporters can be added without core changes
4. **Layered Configuration**: Environment → User Config → Defaults
5. **Isolated Testing**: Each component testable in complete isolation

### Module Dependency Graph

```
Layer 0 (Foundation - No Dependencies):
├── common.config
├── common.errors
├── common.ids
├── common.logging
└── common.models

Layer 1 (Core Abstractions - Depends on Layer 0):
├── backends.base (ABC)
├── renderer.base (ABC)
├── blocks.base (ABC)
└── eval.base (ABC)

Layer 2 (Implementations - Depends on Layers 0-1):
├── backends.openrouter_nemotron
├── backends.deepseek_vllm
├── backends.deepseek_mlx
├── renderer.pypdfium
├── blocks.segmenter
└── eval.metrics

Layer 3 (Orchestration - Depends on Layers 0-2):
├── orchestrator.pipeline
├── orchestrator.routing
└── orchestrator.merging

Layer 4 (User Interface - Depends on All):
├── cli.main
├── exporters.markdown
└── exporters.json
```

---

## Team Structure & Responsibilities

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

# STAGE 1: MINIMAL FUNCTIONING SYSTEM
## Sprints 1-4 | Weeks 1-8 | OpenRouter/Nemotron Backend

---

## Sprint 1: Foundation & Interface Contracts
**Weeks 1-2 | Theme: "Define the contracts, build the foundation"**

### Sprint 1 Objectives
1. ✅ Establish complete project structure
2. ✅ Define ALL public interfaces (frozen after this sprint)
3. ✅ Implement foundation layer (common utilities)
4. ✅ Set up CI/CD pipeline
5. ✅ Create comprehensive documentation framework

### Sprint 1 File Ownership Matrix

**CRITICAL: Each file has ONE owner. No exceptions.**

```
D01 - Tech Lead:
├── pyproject.toml
├── README.md
├── .gitignore
├── LICENSE
└── docs/ARCHITECTURE.md

D02 - Backend Lead:
├── src/docling_hybrid/backends/__init__.py
├── src/docling_hybrid/backends/base.py
├── src/docling_hybrid/backends/types.py
└── docs/interfaces/BACKEND_INTERFACE.md

D03 - Pipeline Lead:
├── src/docling_hybrid/orchestrator/__init__.py
├── src/docling_hybrid/orchestrator/types.py
├── src/docling_hybrid/orchestrator/interfaces.py
└── docs/interfaces/PIPELINE_INTERFACE.md

D04 - Infrastructure:
├── src/docling_hybrid/__init__.py
├── src/docling_hybrid/common/__init__.py
├── src/docling_hybrid/common/config.py
├── src/docling_hybrid/common/errors.py
├── src/docling_hybrid/common/ids.py
├── src/docling_hybrid/common/logging.py
├── configs/default.toml
├── configs/local.toml
├── configs/test.toml
├── .env.example
├── .github/workflows/test.yml
└── .github/workflows/lint.yml

D05 - Renderer:
├── src/docling_hybrid/renderer/__init__.py
├── src/docling_hybrid/renderer/base.py
├── src/docling_hybrid/renderer/types.py
└── docs/interfaces/RENDERER_INTERFACE.md

D06 - CLI Lead:
├── src/docling_hybrid/cli/__init__.py
├── src/docling_hybrid/cli/types.py
└── docs/interfaces/CLI_INTERFACE.md

D07 - Testing Lead:
├── tests/__init__.py
├── tests/conftest.py
├── tests/fixtures/__init__.py
├── tests/fixtures/sample_1page.pdf
├── tests/fixtures/sample_3page.pdf
├── tests/unit/__init__.py
├── tests/integration/__init__.py
├── tests/mocks/__init__.py
└── docs/TESTING_GUIDE.md

D08 - Documentation:
├── CLAUDE.md
├── CONTINUATION.md
├── LOCAL_DEV.md
├── docs/GETTING_STARTED.md
├── docs/CONTRIBUTING.md
└── docs/guides/

D09 - Block Processing:
├── src/docling_hybrid/blocks/__init__.py
├── src/docling_hybrid/blocks/base.py
├── src/docling_hybrid/blocks/types.py
└── docs/interfaces/BLOCKS_INTERFACE.md

D10 - Evaluation:
├── src/docling_hybrid/eval/__init__.py
├── src/docling_hybrid/eval/base.py
├── src/docling_hybrid/eval/types.py
└── docs/interfaces/EVAL_INTERFACE.md
```

### Sprint 1 Task Cards

---

#### S1-D01-01: Project Initialization
```yaml
Owner: D01 (Tech Lead)
Priority: P0-BLOCKING
Duration: 2 days
Dependencies: None
Branch: feat/s1-project-init

Description: |
  Initialize the complete project structure with all directories,
  package configuration, and development tooling.

Tasks:
  - Create pyproject.toml with all dependencies
  - Create directory structure (all __init__.py files)
  - Configure ruff, mypy, pytest in pyproject.toml
  - Create .gitignore with Python patterns
  - Create LICENSE (MIT)
  - Write initial README.md

Files:
  - pyproject.toml
  - README.md
  - .gitignore
  - LICENSE

Acceptance Criteria:
  - `pip install -e ".[dev]"` succeeds
  - `ruff check .` runs (may have errors)
  - `mypy .` runs (may have errors)
  - `pytest` runs (no tests yet)
  - All imports work: `from docling_hybrid import __version__`

Definition of Done:
  - PR approved by D04
  - Merged to develop branch
  - Other developers can clone and install
```

---

#### S1-D02-01: Backend Interface Definition
```yaml
Owner: D02 (Backend Lead)
Priority: P0-BLOCKING
Duration: 3 days
Dependencies: S1-D01-01
Branch: feat/s1-backend-interface

Description: |
  Define the complete backend abstraction layer including:
  - Abstract base class for all OCR/VLM backends
  - Configuration models
  - Response models
  - Factory interface

Tasks:
  - Define OcrVlmBackend ABC with all methods
  - Define OcrBackendConfig Pydantic model
  - Define BackendResponse model
  - Define BackendCandidate model
  - Define BackendError hierarchy
  - Write comprehensive docstrings
  - Create interface documentation

Files:
  - src/docling_hybrid/backends/__init__.py
  - src/docling_hybrid/backends/base.py
  - src/docling_hybrid/backends/types.py
  - docs/interfaces/BACKEND_INTERFACE.md

Interface Specification:
  ```python
  class OcrVlmBackend(ABC):
      """Abstract base class for OCR/VLM backends."""
      
      @abstractmethod
      async def __aenter__(self) -> "OcrVlmBackend": ...
      
      @abstractmethod
      async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
      
      @abstractmethod
      async def page_to_markdown(
          self,
          image_bytes: bytes,
          page_num: int,
          doc_id: str,
          options: Optional[PageOcrOptions] = None
      ) -> PageOcrResult: ...
      
      @abstractmethod
      async def table_to_markdown(
          self,
          image_bytes: bytes,
          meta: TableMeta
      ) -> TableOcrResult: ...
      
      @abstractmethod
      async def formula_to_latex(
          self,
          image_bytes: bytes,
          meta: FormulaMeta
      ) -> FormulaOcrResult: ...
      
      @property
      @abstractmethod
      def name(self) -> str: ...
      
      @property
      @abstractmethod
      def capabilities(self) -> BackendCapabilities: ...
  ```

Acceptance Criteria:
  - Interface is complete and type-hinted
  - All models validate correctly
  - Documentation explains each method
  - Tech Lead (D01) approves interface

Definition of Done:
  - Interface frozen for Sprint 2
  - PR approved by D01 and D03
  - Documentation complete
```

---

#### S1-D03-01: Pipeline Interface Definition
```yaml
Owner: D03 (Pipeline Lead)
Priority: P0-BLOCKING
Duration: 3 days
Dependencies: S1-D01-01, S1-D02-01
Branch: feat/s1-pipeline-interface

Description: |
  Define the orchestration layer interfaces including:
  - Pipeline interface for document conversion
  - Conversion options and results
  - Page-level result models
  - Error handling contracts

Tasks:
  - Define HybridPipeline interface
  - Define ConversionOptions model
  - Define ConversionResult model
  - Define PageResult model
  - Define pipeline error hierarchy
  - Write comprehensive docstrings

Files:
  - src/docling_hybrid/orchestrator/__init__.py
  - src/docling_hybrid/orchestrator/types.py
  - src/docling_hybrid/orchestrator/interfaces.py
  - docs/interfaces/PIPELINE_INTERFACE.md

Interface Specification:
  ```python
  class PipelineProtocol(Protocol):
      """Protocol for document conversion pipelines."""
      
      async def convert_pdf(
          self,
          pdf_path: Path,
          output_path: Optional[Path] = None,
          options: Optional[ConversionOptions] = None
      ) -> ConversionResult: ...
      
      async def convert_pages(
          self,
          pdf_path: Path,
          page_indices: List[int],
          options: Optional[ConversionOptions] = None
      ) -> List[PageResult]: ...
  
  @dataclass
  class ConversionOptions:
      max_pages: Optional[int] = None
      start_page: int = 0
      dpi: int = 200
      backend_name: Optional[str] = None
      include_page_separators: bool = True
      on_page_error: Literal["skip", "raise", "placeholder"] = "skip"
  ```

Acceptance Criteria:
  - Interface supports all conversion scenarios
  - Options cover all configurable aspects
  - Error handling strategy is clear
  - Tech Lead approves interface

Definition of Done:
  - Interface frozen for Sprint 2
  - PR approved by D01 and D02
```

---

#### S1-D04-01: Configuration System
```yaml
Owner: D04 (Infrastructure)
Priority: P0-BLOCKING
Duration: 4 days
Dependencies: S1-D01-01
Branch: feat/s1-config-system

Description: |
  Implement the complete configuration system with:
  - Layered configuration loading
  - Pydantic validation
  - Environment variable overrides
  - Configuration access patterns

Tasks:
  - Implement all Config Pydantic models
  - Implement load_config() with layered loading
  - Implement init_config() / get_config() pattern
  - Create default.toml (production)
  - Create local.toml (12GB RAM development)
  - Create test.toml (minimal resources)
  - Create .env.example template
  - Write unit tests

Files:
  - src/docling_hybrid/common/config.py
  - configs/default.toml
  - configs/local.toml
  - configs/test.toml
  - .env.example
  - tests/unit/test_config.py

Configuration Schema:
  ```python
  class AppConfig(BaseModel):
      name: str = "docling-hybrid-ocr"
      version: str = "0.1.0"
      environment: Literal["development", "production", "test"]
  
  class BackendConfig(BaseModel):
      default_backend: str = "nemotron-openrouter"
      timeout_seconds: int = 120
      max_retries: int = 3
      retry_delay_seconds: float = 1.0
  
  class RenderingConfig(BaseModel):
      default_dpi: int = 200
      max_dpi: int = 600
      min_dpi: int = 72
  
  class ResourcesConfig(BaseModel):
      max_workers: int = 8
      max_memory_mb: int = 16384
      max_concurrent_pages: int = 4
  
  class LoggingConfig(BaseModel):
      level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
      format: Literal["json", "text"]
  
  class Config(BaseModel):
      app: AppConfig
      backend: BackendConfig
      rendering: RenderingConfig
      resources: ResourcesConfig
      logging: LoggingConfig
  ```

Acceptance Criteria:
  - Config loads from TOML files
  - Environment variables override file values
  - Missing required config raises clear error
  - Default values work for all optional fields
  - Tests achieve >95% coverage

Definition of Done:
  - All tests pass
  - Documentation includes examples
  - PR approved by D01
```

---

#### S1-D04-02: Common Utilities
```yaml
Owner: D04 (Infrastructure)
Priority: P0-BLOCKING
Duration: 2 days
Dependencies: S1-D04-01
Branch: feat/s1-common-utils

Description: |
  Implement shared utilities used by all components.

Tasks:
  - Implement ID generation utilities
  - Implement structured logging setup
  - Implement error class hierarchy
  - Write unit tests for all utilities

Files:
  - src/docling_hybrid/common/ids.py
  - src/docling_hybrid/common/logging.py
  - src/docling_hybrid/common/errors.py
  - tests/unit/test_ids.py
  - tests/unit/test_logging.py
  - tests/unit/test_errors.py

Acceptance Criteria:
  - IDs are unique across calls
  - Logging supports JSON and text formats
  - Error hierarchy is complete
  - >95% test coverage
```

---

#### S1-D04-03: CI/CD Pipeline
```yaml
Owner: D04 (Infrastructure)
Priority: P1
Duration: 2 days
Dependencies: S1-D04-01, S1-D07-01
Branch: feat/s1-cicd

Description: |
  Set up GitHub Actions for continuous integration.

Tasks:
  - Create test workflow (pytest)
  - Create lint workflow (ruff, mypy)
  - Configure branch protection rules
  - Set up code coverage reporting

Files:
  - .github/workflows/test.yml
  - .github/workflows/lint.yml
  - .github/PULL_REQUEST_TEMPLATE.md

Acceptance Criteria:
  - Tests run on every PR
  - Linting runs on every PR
  - Coverage report generated
  - PRs require passing CI
```

---

#### S1-D05-01: Renderer Interface Definition
```yaml
Owner: D05 (Renderer)
Priority: P0-BLOCKING
Duration: 2 days
Dependencies: S1-D01-01
Branch: feat/s1-renderer-interface

Description: |
  Define the PDF rendering interface.

Tasks:
  - Define PageRenderer protocol
  - Define rendering options model
  - Define rendering result model
  - Document interface

Files:
  - src/docling_hybrid/renderer/__init__.py
  - src/docling_hybrid/renderer/base.py
  - src/docling_hybrid/renderer/types.py
  - docs/interfaces/RENDERER_INTERFACE.md

Interface Specification:
  ```python
  class PageRendererProtocol(Protocol):
      """Protocol for PDF page rendering."""
      
      def render_page(
          self,
          pdf_path: Path,
          page_index: int,
          dpi: int = 200
      ) -> bytes: ...
      
      def render_region(
          self,
          pdf_path: Path,
          page_index: int,
          bbox: Tuple[float, float, float, float],
          dpi: int = 200
      ) -> bytes: ...
      
      def get_page_count(self, pdf_path: Path) -> int: ...
      
      def get_page_size(
          self,
          pdf_path: Path,
          page_index: int
      ) -> Tuple[float, float]: ...
  ```

Acceptance Criteria:
  - Interface covers all rendering needs
  - Types are complete
  - Documentation is clear
```

---

#### S1-D06-01: CLI Interface Definition
```yaml
Owner: D06 (CLI Lead)
Priority: P1
Duration: 2 days
Dependencies: S1-D01-01, S1-D03-01
Branch: feat/s1-cli-interface

Description: |
  Design the CLI structure and argument models.

Tasks:
  - Design command structure
  - Define argument models
  - Define output format options
  - Document CLI design

Files:
  - src/docling_hybrid/cli/__init__.py
  - src/docling_hybrid/cli/types.py
  - docs/interfaces/CLI_INTERFACE.md

CLI Design:
  ```
  docling-hybrid-ocr [OPTIONS] COMMAND [ARGS]
  
  Commands:
    convert    Convert PDF to Markdown
    backends   List available backends
    info       Show system information
    validate   Validate configuration
  
  Global Options:
    --config PATH    Configuration file
    --verbose        Enable verbose output
    --quiet          Suppress output
    --version        Show version
  
  convert Options:
    INPUT            PDF file to convert
    --output PATH    Output file path
    --backend NAME   Backend to use
    --dpi INT        Rendering DPI
    --max-pages INT  Maximum pages to process
    --start-page INT Starting page (0-indexed)
    --format FORMAT  Output format (md, json)
  ```

Acceptance Criteria:
  - CLI design is intuitive
  - All options documented
  - Help text is clear
```

---

#### S1-D07-01: Test Infrastructure
```yaml
Owner: D07 (Testing Lead)
Priority: P0-BLOCKING
Duration: 4 days
Dependencies: S1-D01-01
Branch: feat/s1-test-infra

Description: |
  Set up comprehensive test infrastructure.

Tasks:
  - Configure pytest in pyproject.toml
  - Create conftest.py with shared fixtures
  - Create test fixture files (sample PDFs)
  - Create mock infrastructure
  - Set up coverage reporting
  - Document testing patterns

Files:
  - tests/conftest.py
  - tests/fixtures/__init__.py
  - tests/fixtures/sample_1page.pdf
  - tests/fixtures/sample_3page.pdf
  - tests/fixtures/sample_with_table.pdf
  - tests/mocks/__init__.py
  - tests/mocks/backends.py
  - tests/mocks/http.py
  - docs/TESTING_GUIDE.md

Fixtures to Create:
  ```python
  @pytest.fixture
  def test_config() -> Config:
      """Load test configuration."""
  
  @pytest.fixture
  def sample_pdf_path() -> Path:
      """Path to single-page test PDF."""
  
  @pytest.fixture
  def sample_image_bytes() -> bytes:
      """Sample PNG image bytes."""
  
  @pytest.fixture
  def mock_backend() -> MockBackend:
      """Mock OCR backend for testing."""
  
  @pytest.fixture
  def mock_http_response():
      """Factory for mock HTTP responses."""
  ```

Acceptance Criteria:
  - pytest runs successfully
  - All fixtures work
  - Coverage reporting works
  - Mocks are documented
```

---

#### S1-D08-01: Documentation Framework
```yaml
Owner: D08 (Documentation)
Priority: P1
Duration: 5 days
Dependencies: All interface definitions
Branch: feat/s1-documentation

Description: |
  Create comprehensive documentation framework.

Tasks:
  - Write CLAUDE.md master context
  - Write LOCAL_DEV.md for constrained development
  - Write GETTING_STARTED.md
  - Write CONTRIBUTING.md
  - Create documentation templates
  - Document all interfaces

Files:
  - CLAUDE.md
  - CONTINUATION.md
  - LOCAL_DEV.md
  - docs/GETTING_STARTED.md
  - docs/CONTRIBUTING.md
  - docs/guides/ADDING_BACKENDS.md
  - docs/guides/CONFIGURATION.md

Acceptance Criteria:
  - New developer can set up in <30 minutes
  - All interfaces documented
  - Examples provided
  - Contributing guidelines clear
```

---

#### S1-D09-01: Block Processing Interface
```yaml
Owner: D09 (Block Processing)
Priority: P1
Duration: 3 days
Dependencies: S1-D01-01, S1-D02-01
Branch: feat/s1-blocks-interface

Description: |
  Define interfaces for block-level processing (Stage 2 prep).

Tasks:
  - Define BlockType enumeration
  - Define Block data model
  - Define BlockSegmenter interface
  - Define RoutingRule model
  - Document interface

Files:
  - src/docling_hybrid/blocks/__init__.py
  - src/docling_hybrid/blocks/base.py
  - src/docling_hybrid/blocks/types.py
  - docs/interfaces/BLOCKS_INTERFACE.md

Interface Specification:
  ```python
  class BlockType(Enum):
      PARAGRAPH = "paragraph"
      HEADING = "heading"
      TABLE = "table"
      FIGURE = "figure"
      FORMULA = "formula"
      LIST = "list"
      CODE = "code"
      FOOTNOTE = "footnote"
      CAPTION = "caption"
      OTHER = "other"
  
  @dataclass
  class Block:
      id: str
      block_type: BlockType
      page_index: int
      bbox: Tuple[float, float, float, float]
      content: Optional[str] = None
      confidence: Optional[float] = None
      metadata: Dict[str, Any] = field(default_factory=dict)
  
  class BlockSegmenterProtocol(Protocol):
      def segment_page(
          self,
          pdf_path: Path,
          page_index: int
      ) -> List[Block]: ...
      
      def segment_document(
          self,
          pdf_path: Path
      ) -> Dict[int, List[Block]]: ...
  ```
```

---

#### S1-D10-01: Evaluation Interface
```yaml
Owner: D10 (Evaluation)
Priority: P1
Duration: 3 days
Dependencies: S1-D01-01
Branch: feat/s1-eval-interface

Description: |
  Define interfaces for evaluation framework (Stage 2 prep).

Tasks:
  - Define Metric base class
  - Define EvaluationResult model
  - Define GroundTruth model
  - Define EvaluationRunner interface
  - Document interface

Files:
  - src/docling_hybrid/eval/__init__.py
  - src/docling_hybrid/eval/base.py
  - src/docling_hybrid/eval/types.py
  - docs/interfaces/EVAL_INTERFACE.md

Interface Specification:
  ```python
  class MetricProtocol(Protocol):
      @property
      def name(self) -> str: ...
      
      def compute(
          self,
          predicted: str,
          ground_truth: str
      ) -> float: ...
  
  @dataclass
  class EvaluationResult:
      doc_id: str
      metrics: Dict[str, float]
      details: Dict[str, Any]
      timestamp: datetime
  
  class EvaluationRunnerProtocol(Protocol):
      def evaluate_document(
          self,
          predicted: ConversionResult,
          ground_truth: GroundTruth
      ) -> EvaluationResult: ...
      
      def evaluate_corpus(
          self,
          results: List[Tuple[ConversionResult, GroundTruth]]
      ) -> CorpusEvaluationResult: ...
  ```
```

---

### Sprint 1 Integration Procedure

**Integration Period: Days 9-10**

#### Day 9: Pre-Integration

| Time | Activity | Owner | Participants |
|------|----------|-------|--------------|
| 09:00 | PR Status Review | D01 | All |
| 10:00 | Interface Compatibility Check | D01 | D02, D03 |
| 11:00 | Begin PR Merges (Foundation) | D01 | D04 |
| 14:00 | Begin PR Merges (Interfaces) | D01 | D02, D03, D05, D06 |
| 16:00 | Integration Test Run | D07 | D01 |

#### Day 10: Post-Integration

| Time | Activity | Owner | Participants |
|------|----------|-------|--------------|
| 09:00 | Full Test Suite Run | D07 | All |
| 10:00 | Import Verification | D01 | All |
| 11:00 | Documentation Review | D08 | All |
| 14:00 | Interface Freeze Ceremony | D01 | All |
| 15:00 | Sprint Retrospective | D01 | All |
| 16:00 | Sprint 2 Planning | D01 | All |

#### Integration Checklist

```markdown
## Sprint 1 Integration Checklist

### Pre-Merge Verification
- [ ] All PRs have passing CI
- [ ] All PRs have 1+ approval
- [ ] No merge conflicts
- [ ] All interfaces documented

### Merge Order
1. [ ] S1-D01-01: Project Initialization
2. [ ] S1-D04-01: Configuration System
3. [ ] S1-D04-02: Common Utilities
4. [ ] S1-D02-01: Backend Interface
5. [ ] S1-D05-01: Renderer Interface
6. [ ] S1-D03-01: Pipeline Interface
7. [ ] S1-D06-01: CLI Interface
8. [ ] S1-D09-01: Block Processing Interface
9. [ ] S1-D10-01: Evaluation Interface
10. [ ] S1-D07-01: Test Infrastructure
11. [ ] S1-D04-03: CI/CD Pipeline
12. [ ] S1-D08-01: Documentation

### Post-Merge Verification
- [ ] `pip install -e ".[dev]"` works
- [ ] All imports work
- [ ] pytest passes
- [ ] ruff check passes
- [ ] mypy passes

### Interface Freeze
- [ ] Backend interface frozen
- [ ] Pipeline interface frozen
- [ ] Renderer interface frozen
- [ ] CLI interface frozen
- [ ] Block interface frozen
- [ ] Eval interface frozen

### Documentation
- [ ] CLAUDE.md updated
- [ ] CONTINUATION.md created
- [ ] All interfaces documented
```

---

## Sprint 2: Core Implementation
**Weeks 3-4 | Theme: "Build the engine"**

### Sprint 2 Objectives
1. ✅ Implement PDF renderer with pypdfium2
2. ✅ Implement OpenRouter/Nemotron backend
3. ✅ Implement backend factory
4. ✅ Comprehensive unit tests
5. ✅ Mocked integration tests

### Sprint 2 File Ownership Matrix

```
D01 - Tech Lead:
└── Code review, integration planning
    (No file ownership - focuses on coordination)

D02 - Backend Lead:
├── src/docling_hybrid/backends/factory.py
├── src/docling_hybrid/backends/openrouter_nemotron.py
├── src/docling_hybrid/backends/prompts.py
└── tests/unit/backends/test_factory.py
└── tests/unit/backends/test_openrouter.py

D03 - Pipeline Lead:
└── Pipeline design refinement (no implementation yet)
└── Integration test design

D04 - Infrastructure:
├── src/docling_hybrid/common/http.py (async HTTP utilities)
├── src/docling_hybrid/common/retry.py (retry logic)
└── tests/unit/common/test_http.py

D05 - Renderer:
├── src/docling_hybrid/renderer/pypdfium.py
└── tests/unit/renderer/test_pypdfium.py

D06 - CLI Lead:
└── CLI design refinement (no implementation yet)
└── User documentation planning

D07 - Testing Lead:
├── tests/mocks/http_responses.py
├── tests/mocks/pdf_fixtures.py
├── tests/integration/test_renderer_backend.py
└── Coverage analysis

D08 - Documentation:
├── docs/components/BACKENDS.md
├── docs/components/RENDERER.md
└── Code documentation review

D09 - Block Processing:
└── Research Docling API
└── docs/design/BLOCK_EXTRACTION.md

D10 - Evaluation:
└── Research evaluation metrics
└── docs/design/EVALUATION_METRICS.md
```

### Sprint 2 Task Cards

---

#### S2-D02-01: Backend Factory
```yaml
Owner: D02 (Backend Lead)
Priority: P0-BLOCKING
Duration: 2 days
Dependencies: S1-D02-01
Branch: feat/s2-backend-factory

Description: |
  Implement the backend factory with registration system.

Tasks:
  - Implement make_backend() factory function
  - Implement list_backends() function
  - Implement register_backend() for custom backends
  - Support configuration-based backend selection
  - Write comprehensive unit tests

Files:
  - src/docling_hybrid/backends/factory.py
  - tests/unit/backends/test_factory.py

Implementation:
  ```python
  # Registry for backend classes
  _BACKEND_REGISTRY: Dict[str, Type[OcrVlmBackend]] = {}
  
  def register_backend(name: str, backend_class: Type[OcrVlmBackend]) -> None:
      """Register a backend class."""
      _BACKEND_REGISTRY[name] = backend_class
  
  def make_backend(config: OcrBackendConfig) -> OcrVlmBackend:
      """Create a backend instance from configuration."""
      name = config.name.lower()
      if name not in _BACKEND_REGISTRY:
          available = ", ".join(_BACKEND_REGISTRY.keys())
          raise ConfigurationError(
              f"Unknown backend: {name}. Available: {available}"
          )
      return _BACKEND_REGISTRY[name](config)
  
  def list_backends() -> List[str]:
      """List all registered backends."""
      return list(_BACKEND_REGISTRY.keys())
  ```

Test Cases:
  - Factory creates correct backend type
  - Unknown backend raises ConfigurationError
  - Custom backend registration works
  - list_backends returns all registered

Acceptance Criteria:
  - All tests pass
  - >95% coverage
  - Documentation complete
```

---

#### S2-D02-02: OpenRouter Nemotron Backend
```yaml
Owner: D02 (Backend Lead)
Priority: P0-BLOCKING
Duration: 5 days
Dependencies: S2-D02-01, S2-D04-01
Branch: feat/s2-openrouter-backend

Description: |
  Implement the complete OpenRouter/Nemotron backend.

Tasks:
  - Implement OpenRouterNemotronBackend class
  - Implement async context manager
  - Implement _encode_image (base64)
  - Implement _build_messages (OpenAI format)
  - Implement _post_chat with aiohttp
  - Implement _extract_content (string/list)
  - Define prompt templates
  - Handle all error cases
  - Write unit tests with mocked HTTP

Files:
  - src/docling_hybrid/backends/openrouter_nemotron.py
  - src/docling_hybrid/backends/prompts.py
  - tests/unit/backends/test_openrouter.py

Prompt Templates:
  ```python
  PAGE_TO_MARKDOWN_PROMPT = """
  You are a document OCR assistant. Convert the provided image 
  to GitHub-flavored Markdown.
  
  Rules:
  1. Preserve all text exactly as shown
  2. Use appropriate heading levels (# ## ###)
  3. Format tables using Markdown table syntax
  4. Format mathematical formulas using LaTeX ($..$ or $$..$$)
  5. Use <FIGURE> placeholder for non-text images
  6. Do NOT invent or describe content not visible
  7. Maintain original reading order
  
  Output only the Markdown content, no explanations.
  """
  
  TABLE_TO_MARKDOWN_PROMPT = """
  The image contains a single table. Convert it to Markdown format.
  
  Rules:
  1. Use standard Markdown table syntax
  2. Preserve all cell content exactly
  3. Maintain column alignment
  4. Handle merged cells by repeating content
  5. Output only the table, no other text
  """
  
  FORMULA_TO_LATEX_PROMPT = """
  The image contains a mathematical formula. Convert it to LaTeX.
  
  Rules:
  1. Output only the LaTeX expression
  2. Do NOT include $ delimiters
  3. Use standard LaTeX commands
  4. Be precise with subscripts and superscripts
  """
  ```

HTTP Implementation:
  ```python
  async def _post_chat(self, messages: List[Dict]) -> str:
      """Send chat completion request."""
      headers = {
          "Authorization": f"Bearer {self._config.api_key}",
          "Content-Type": "application/json",
          "HTTP-Referer": self._config.http_referer,
          "X-Title": self._config.x_title,
      }
      
      payload = {
          "model": self._config.model,
          "messages": messages,
          "temperature": self._config.temperature,
          "max_tokens": self._config.max_tokens,
      }
      
      async with self._session.post(
          self._config.base_url,
          headers=headers,
          json=payload,
          timeout=aiohttp.ClientTimeout(total=self._config.timeout),
      ) as response:
          if response.status != 200:
              body = await response.text()
              raise BackendResponseError(
                  f"API error {response.status}: {body}"
              )
          data = await response.json()
          return self._extract_content(data)
  ```

Test Cases:
  - Successful page conversion
  - Successful table conversion
  - Successful formula conversion
  - API error (4xx) handling
  - API error (5xx) handling
  - Timeout handling
  - Connection error handling
  - Missing API key error
  - String content extraction
  - List content extraction

Acceptance Criteria:
  - All three methods implemented
  - All error cases handled
  - >90% test coverage
  - Works with mock HTTP
```

---

#### S2-D04-01: HTTP Utilities
```yaml
Owner: D04 (Infrastructure)
Priority: P0-BLOCKING
Duration: 2 days
Dependencies: S1-D04-01
Branch: feat/s2-http-utils

Description: |
  Implement shared async HTTP utilities.

Tasks:
  - Implement async HTTP client wrapper
  - Implement retry logic with exponential backoff
  - Implement timeout handling
  - Write unit tests

Files:
  - src/docling_hybrid/common/http.py
  - src/docling_hybrid/common/retry.py
  - tests/unit/common/test_http.py
  - tests/unit/common/test_retry.py

Implementation:
  ```python
  async def retry_async(
      func: Callable[..., Awaitable[T]],
      max_retries: int = 3,
      initial_delay: float = 1.0,
      max_delay: float = 60.0,
      exponential_base: float = 2.0,
      retryable_exceptions: Tuple[Type[Exception], ...] = (
          aiohttp.ClientError,
          asyncio.TimeoutError,
      ),
  ) -> T:
      """Retry an async function with exponential backoff."""
      delay = initial_delay
      last_exception = None
      
      for attempt in range(max_retries + 1):
          try:
              return await func()
          except retryable_exceptions as e:
              last_exception = e
              if attempt < max_retries:
                  await asyncio.sleep(delay)
                  delay = min(delay * exponential_base, max_delay)
      
      raise last_exception
  ```

Acceptance Criteria:
  - Retry logic works correctly
  - Exponential backoff is correct
  - Non-retryable errors propagate immediately
```

---

#### S2-D05-01: PyPDFium Renderer
```yaml
Owner: D05 (Renderer)
Priority: P0-BLOCKING
Duration: 4 days
Dependencies: S1-D05-01
Branch: feat/s2-pypdfium-renderer

Description: |
  Implement PDF rendering using pypdfium2.

Tasks:
  - Implement PypdfiumRenderer class
  - Implement render_page method
  - Implement render_region method
  - Implement get_page_count method
  - Implement get_page_size method
  - Handle edge cases
  - Write comprehensive unit tests

Files:
  - src/docling_hybrid/renderer/pypdfium.py
  - tests/unit/renderer/test_pypdfium.py

Implementation:
  ```python
  class PypdfiumRenderer:
      """PDF renderer using pypdfium2."""
      
      def render_page(
          self,
          pdf_path: Path,
          page_index: int,
          dpi: int = 200
      ) -> bytes:
          """Render a PDF page to PNG bytes."""
          pdf = pdfium.PdfDocument(str(pdf_path))
          
          if page_index < 0 or page_index >= len(pdf):
              raise ValidationError(
                  f"Page index {page_index} out of range [0, {len(pdf)})"
              )
          
          page = pdf[page_index]
          scale = dpi / 72.0
          
          bitmap = page.render(scale=scale)
          pil_image = bitmap.to_pil()
          
          buffer = io.BytesIO()
          pil_image.save(buffer, format="PNG")
          return buffer.getvalue()
      
      def render_region(
          self,
          pdf_path: Path,
          page_index: int,
          bbox: Tuple[float, float, float, float],
          dpi: int = 200
      ) -> bytes:
          """Render a region of a PDF page."""
          # Render full page then crop
          full_page = self.render_page(pdf_path, page_index, dpi)
          image = Image.open(io.BytesIO(full_page))
          
          # Convert PDF coordinates to pixel coordinates
          scale = dpi / 72.0
          x1, y1, x2, y2 = bbox
          crop_box = (
              int(x1 * scale),
              int(y1 * scale),
              int(x2 * scale),
              int(y2 * scale),
          )
          
          cropped = image.crop(crop_box)
          buffer = io.BytesIO()
          cropped.save(buffer, format="PNG")
          return buffer.getvalue()
  ```

Test Cases:
  - Valid PDF renders correctly
  - Different DPI values work
  - Invalid PDF raises error
  - Page out of range raises error
  - Region cropping works
  - Empty page renders
  - Page count is correct
  - Page size is correct

Acceptance Criteria:
  - All methods implemented
  - All edge cases handled
  - >90% test coverage
  - Memory usage reasonable
```

---

#### S2-D07-01: HTTP Mocking Infrastructure
```yaml
Owner: D07 (Testing Lead)
Priority: P1
Duration: 3 days
Dependencies: S2-D02-02
Branch: feat/s2-http-mocks

Description: |
  Create comprehensive HTTP mocking for backend tests.

Tasks:
  - Create mock HTTP response factory
  - Create fixtures for common API responses
  - Create error response fixtures
  - Document mock usage patterns

Files:
  - tests/mocks/http_responses.py
  - tests/mocks/fixtures/api_responses.json

Implementation:
  ```python
  def mock_openrouter_success(content: str = "# Test"):
      """Create successful OpenRouter response."""
      return {
          "choices": [
              {
                  "message": {
                      "content": content
                  }
              }
          ]
      }
  
  def mock_openrouter_error(status: int, message: str):
      """Create error OpenRouter response."""
      return aioresponses.CallbackResult(
          status=status,
          payload={"error": {"message": message}}
      )
  ```

Acceptance Criteria:
  - Mocks are easy to use
  - Cover all response types
  - Documentation is clear
```

---

#### S2-D07-02: Renderer-Backend Integration Tests
```yaml
Owner: D07 (Testing Lead)
Priority: P1
Duration: 2 days
Dependencies: S2-D02-02, S2-D05-01
Branch: feat/s2-integration-tests

Description: |
  Create integration tests that verify renderer and backend work together.

Tasks:
  - Test renderer output can be processed by backend
  - Test various PDF types
  - Test error scenarios
  - Verify output quality

Files:
  - tests/integration/test_renderer_backend.py

Test Cases:
  ```python
  async def test_rendered_page_processed_by_backend(
      mock_http,
      sample_pdf_path,
      test_config
  ):
      """Rendered page can be processed by backend."""
      renderer = PypdfiumRenderer()
      image_bytes = renderer.render_page(sample_pdf_path, 0)
      
      mock_http.post(
          OPENROUTER_URL,
          payload=mock_openrouter_success("# Test Content")
      )
      
      backend = make_backend(test_config.backend)
      async with backend:
          result = await backend.page_to_markdown(image_bytes, 1, "doc-1")
      
      assert result.content == "# Test Content"
      assert result.status == "success"
  ```

Acceptance Criteria:
  - Integration tests pass with mocked HTTP
  - Cover main use cases
  - Tests are reliable (no flakiness)
```

---

### Sprint 2 Integration Procedure

**Integration Period: Days 9-10**

#### Integration Order
1. S2-D04-01: HTTP Utilities (foundation)
2. S2-D05-01: PyPDFium Renderer
3. S2-D02-01: Backend Factory
4. S2-D02-02: OpenRouter Backend
5. S2-D07-01: HTTP Mocking
6. S2-D07-02: Integration Tests

#### Integration Verification Tests
```python
# tests/integration/test_sprint2_integration.py

def test_renderer_produces_valid_png(sample_pdf_path):
    """Renderer produces valid PNG that PIL can read."""
    renderer = PypdfiumRenderer()
    image_bytes = renderer.render_page(sample_pdf_path, 0, dpi=150)
    
    # Verify PNG header
    assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'
    
    # Verify PIL can read it
    image = Image.open(io.BytesIO(image_bytes))
    assert image.format == "PNG"
    assert image.size[0] > 0
    assert image.size[1] > 0

async def test_backend_factory_creates_nemotron(test_config):
    """Factory creates Nemotron backend."""
    backend = make_backend(test_config.backend)
    assert isinstance(backend, OpenRouterNemotronBackend)
    assert backend.name == "nemotron-openrouter"

async def test_full_page_ocr_flow(mock_http, sample_pdf_path, test_config):
    """Complete flow: PDF -> Render -> Backend -> Markdown."""
    # Render
    renderer = PypdfiumRenderer()
    image_bytes = renderer.render_page(sample_pdf_path, 0)
    
    # Mock API
    mock_http.post(OPENROUTER_URL, payload=mock_openrouter_success("# Title\n\nContent"))
    
    # OCR
    backend = make_backend(test_config.backend)
    async with backend:
        result = await backend.page_to_markdown(image_bytes, 1, "test-doc")
    
    assert "# Title" in result.content
    assert "Content" in result.content
```

#### Sprint 2 Checklist
```markdown
## Sprint 2 Integration Checklist

### Component Verification
- [ ] PypdfiumRenderer renders all test PDFs
- [ ] Backend factory creates all registered backends
- [ ] OpenRouter backend handles all response types
- [ ] Retry logic works correctly

### Integration Verification
- [ ] Renderer output works with backend
- [ ] Error handling flows correctly
- [ ] Logging is consistent

### Test Coverage
- [ ] Unit test coverage >85%
- [ ] Integration tests pass
- [ ] No test flakiness

### Documentation
- [ ] Backend documentation complete
- [ ] Renderer documentation complete
- [ ] Code comments adequate
```

---

## Sprint 3: Pipeline & CLI
**Weeks 5-6 | Theme: "User-facing functionality"**

### Sprint 3 Objectives
1. ✅ Implement HybridPipeline orchestrator
2. ✅ Implement CLI with Typer
3. ✅ End-to-end flow working
4. ✅ User documentation complete

### Sprint 3 File Ownership Matrix

```
D01 - Tech Lead:
└── End-to-end testing coordination

D02 - Backend Lead:
├── Backend refinements based on pipeline feedback
└── tests/integration/test_backend_e2e.py

D03 - Pipeline Lead:
├── src/docling_hybrid/orchestrator/pipeline.py
├── src/docling_hybrid/orchestrator/page_processor.py
└── tests/unit/orchestrator/test_pipeline.py

D04 - Infrastructure:
├── src/docling_hybrid/common/progress.py (progress reporting)
└── Deployment configuration

D05 - Renderer:
└── Renderer optimizations based on pipeline feedback

D06 - CLI Lead:
├── src/docling_hybrid/cli/main.py
├── src/docling_hybrid/cli/commands/convert.py
├── src/docling_hybrid/cli/commands/backends.py
├── src/docling_hybrid/cli/commands/info.py
└── tests/unit/cli/test_main.py

D07 - Testing Lead:
├── tests/integration/test_e2e.py
├── tests/smoke/test_smoke.py
└── Test documentation

D08 - Documentation:
├── docs/guides/QUICK_START.md
├── docs/guides/CLI_USAGE.md
├── examples/basic_conversion.py
└── examples/custom_options.py

D09 - Block Processing:
└── Continue design work
└── Prototype block extraction

D10 - Evaluation:
└── Continue design work
└── Prototype metric computation
```

### Sprint 3 Key Task Cards

#### S3-D03-01: HybridPipeline Implementation
```yaml
Owner: D03 (Pipeline Lead)
Priority: P0-BLOCKING
Duration: 5 days
Dependencies: Sprint 2 complete
Branch: feat/s3-pipeline

Files:
  - src/docling_hybrid/orchestrator/pipeline.py
  - src/docling_hybrid/orchestrator/page_processor.py
  - tests/unit/orchestrator/test_pipeline.py

Implementation:
  ```python
  class HybridPipeline:
      """Main document conversion pipeline."""
      
      def __init__(
          self,
          config: Config,
          backend: Optional[OcrVlmBackend] = None,
          renderer: Optional[PageRendererProtocol] = None,
      ):
          self._config = config
          self._backend = backend
          self._renderer = renderer or PypdfiumRenderer()
          self._logger = get_logger(__name__)
      
      async def convert_pdf(
          self,
          pdf_path: Path,
          output_path: Optional[Path] = None,
          options: Optional[ConversionOptions] = None,
      ) -> ConversionResult:
          """Convert a PDF to Markdown."""
          options = options or ConversionOptions()
          doc_id = generate_id("doc")
          
          self._logger.info(
              "conversion_started",
              doc_id=doc_id,
              pdf_path=str(pdf_path),
          )
          
          # Get page count
          total_pages = self._renderer.get_page_count(pdf_path)
          pages_to_process = self._get_pages_to_process(
              total_pages, options
          )
          
          # Process pages
          page_results = []
          for page_index in pages_to_process:
              result = await self._process_page(
                  pdf_path, page_index, doc_id, options
              )
              page_results.append(result)
          
          # Combine results
          markdown = self._combine_pages(page_results, options)
          
          # Write output
          if output_path:
              output_path.write_text(markdown)
          
          return ConversionResult(
              doc_id=doc_id,
              input_path=pdf_path,
              output_path=output_path,
              total_pages=total_pages,
              processed_pages=len(page_results),
              page_results=page_results,
              markdown=markdown,
              status="success",
          )
      
      async def _process_page(
          self,
          pdf_path: Path,
          page_index: int,
          doc_id: str,
          options: ConversionOptions,
      ) -> PageResult:
          """Process a single page."""
          page_num = page_index + 1
          
          try:
              # Render page
              image_bytes = self._renderer.render_page(
                  pdf_path, page_index, dpi=options.dpi
              )
              
              # OCR page
              ocr_result = await self._backend.page_to_markdown(
                  image_bytes, page_num, doc_id
              )
              
              return PageResult(
                  page_index=page_index,
                  page_num=page_num,
                  content=ocr_result.content,
                  status="success",
              )
              
          except Exception as e:
              self._logger.error(
                  "page_processing_failed",
                  page_index=page_index,
                  error=str(e),
              )
              
              if options.on_page_error == "raise":
                  raise
              elif options.on_page_error == "placeholder":
                  return PageResult(
                      page_index=page_index,
                      page_num=page_num,
                      content=f"<!-- Page {page_num} failed: {e} -->",
                      status="error",
                      error=str(e),
                  )
              else:  # skip
                  return PageResult(
                      page_index=page_index,
                      page_num=page_num,
                      content="",
                      status="skipped",
                      error=str(e),
                  )
  ```
```

#### S3-D06-01: CLI Implementation
```yaml
Owner: D06 (CLI Lead)
Priority: P0-BLOCKING
Duration: 5 days
Dependencies: S3-D03-01
Branch: feat/s3-cli

Files:
  - src/docling_hybrid/cli/main.py
  - src/docling_hybrid/cli/commands/convert.py
  - src/docling_hybrid/cli/commands/backends.py
  - src/docling_hybrid/cli/commands/info.py
  - tests/unit/cli/test_main.py

Implementation:
  ```python
  import typer
  from rich.console import Console
  from rich.progress import Progress, SpinnerColumn, TextColumn
  
  app = typer.Typer(
      name="docling-hybrid-ocr",
      help="Convert PDFs to Markdown using Vision-Language Models",
      add_completion=False,
  )
  console = Console()
  
  @app.command()
  def convert(
      input_path: Path = typer.Argument(..., help="PDF file to convert"),
      output: Optional[Path] = typer.Option(None, "--output", "-o"),
      backend: Optional[str] = typer.Option(None, "--backend", "-b"),
      dpi: int = typer.Option(200, "--dpi"),
      max_pages: Optional[int] = typer.Option(None, "--max-pages"),
      start_page: int = typer.Option(0, "--start-page"),
      verbose: bool = typer.Option(False, "--verbose", "-v"),
      config_path: Optional[Path] = typer.Option(None, "--config"),
  ):
      """Convert a PDF file to Markdown."""
      # Load config
      config = init_config(config_path)
      
      # Override with CLI options
      if backend:
          config.backend.default_backend = backend
      
      # Create pipeline
      with Progress(
          SpinnerColumn(),
          TextColumn("[progress.description]{task.description}"),
          console=console,
      ) as progress:
          task = progress.add_task("Converting...", total=None)
          
          pipeline = HybridPipeline(config)
          options = ConversionOptions(
              dpi=dpi,
              max_pages=max_pages,
              start_page=start_page,
          )
          
          result = asyncio.run(
              pipeline.convert_pdf(input_path, output, options)
          )
      
      console.print(f"[green]✓[/green] Converted {result.processed_pages} pages")
      if output:
          console.print(f"[blue]Output:[/blue] {output}")
  
  @app.command()
  def backends():
      """List available OCR backends."""
      from docling_hybrid.backends import list_backends
      
      backends = list_backends()
      console.print("[bold]Available Backends:[/bold]")
      for name in backends:
          console.print(f"  • {name}")
  
  @app.command()
  def info():
      """Show system information."""
      console.print(f"[bold]Version:[/bold] {__version__}")
      console.print(f"[bold]Python:[/bold] {sys.version}")
      # ... more info
  ```
```

---

## Sprint 4: Polish & Stage 1 Release
**Weeks 7-8 | Theme: "Production-ready"**

### Sprint 4 Objectives
1. ✅ Real API testing and hardening
2. ✅ Concurrent page processing
3. ✅ Error handling improvements
4. ✅ Performance optimization
5. ✅ Stage 1 release (v0.1.0)

### Sprint 4 File Ownership

```
D01: Release management, final integration
D02: Retry logic, rate limiting, API hardening
D03: Concurrent processing, progress reporting
D04: Docker setup, deployment docs
D05: Memory optimization, DPI tuning
D06: CLI polish, error messages
D07: Release testing, regression suite
D08: User guides, API documentation
D09: Block processing finalization (for Stage 2)
D10: Evaluation finalization (for Stage 2)
```

### Stage 1 Release Criteria

```markdown
## Stage 1 Release Checklist (v0.1.0)

### Functionality
- [ ] CLI converts PDFs using OpenRouter API
- [ ] All three backend methods work (page, table, formula)
- [ ] Multiple DPI options work
- [ ] Max pages option works
- [ ] Output file writing works
- [ ] Error handling is graceful

### Quality
- [ ] Unit test coverage >85%
- [ ] Integration tests pass
- [ ] Smoke tests pass with real API
- [ ] No critical bugs
- [ ] No memory leaks

### Performance
- [ ] <5s per page (excluding API time)
- [ ] <500MB memory for 100-page PDF
- [ ] Concurrent page processing works

### Documentation
- [ ] README complete
- [ ] CLAUDE.md current
- [ ] CLI help is helpful
- [ ] Quick start guide works
- [ ] Configuration documented

### DevOps
- [ ] Docker image builds
- [ ] CI/CD passes
- [ ] Version is 0.1.0
- [ ] CHANGELOG written
```

---

# STAGE 2: FULL LOCAL SYSTEM
## Sprints 5-8 | Weeks 9-16 | DeepSeek + Extensions

---

## Sprint 5: DeepSeek Backends
**Weeks 9-10 | Theme: "Local inference capability"**

### Sprint 5 Objectives
1. ✅ DeepSeek vLLM backend
2. ✅ DeepSeek MLX backend
3. ✅ Backend comparison tooling
4. ✅ Local deployment guide

### Sprint 5 File Ownership

```
D01 - Tech Lead:
└── Multi-backend architecture review

D02 - Backend Lead:
├── src/docling_hybrid/backends/deepseek_vllm.py
├── src/docling_hybrid/backends/deepseek_mlx.py
└── tests/unit/backends/test_deepseek.py

D03 - Pipeline Lead:
├── Backend selection logic improvements
└── tests/integration/test_multi_backend.py

D04 - Infrastructure:
├── docs/deployment/VLLM_SETUP.md
├── docs/deployment/MLX_SETUP.md
└── Docker configs for vLLM

D05 - Renderer:
└── Image preprocessing optimizations

D06 - CLI Lead:
├── --backend selection improvements
└── Backend comparison command

D07 - Testing Lead:
├── tests/integration/test_deepseek.py
└── Backend benchmark tests

D08 - Documentation:
├── docs/backends/DEEPSEEK.md
└── Backend comparison guide

D09 - Block Processing:
├── src/docling_hybrid/blocks/segmenter.py (START)
└── Docling integration

D10 - Evaluation:
├── src/docling_hybrid/eval/metrics.py (START)
└── Ground truth format
```

### Key Task: DeepSeek vLLM Backend

```yaml
Owner: D02
Priority: P0-BLOCKING
Duration: 5 days

Files:
  - src/docling_hybrid/backends/deepseek_vllm.py
  - tests/unit/backends/test_deepseek_vllm.py

Implementation Notes:
  - Reuse prompt templates from Nemotron backend
  - vLLM uses OpenAI-compatible API
  - Base URL: http://localhost:8000/v1/chat/completions
  - No API key required for local deployment
  - Same message format as OpenRouter

Key Differences from Nemotron:
  - No HTTP-Referer or X-Title headers
  - Different model name format
  - Local endpoint (configurable)
  - May need different timeout (local is faster)
```

---

## Sprint 6: Block-Level Processing
**Weeks 11-12 | Theme: "Intelligent segmentation"**

### Sprint 6 Objectives
1. ✅ Block segmentation using Docling
2. ✅ Block type detection
3. ✅ Block-to-backend routing
4. ✅ Region rendering for blocks

### Sprint 6 File Ownership

```
D01: Block processing architecture
D02: Table-specific backend wrapper
D03: Block-aware pipeline mode
D04: Block processing configuration
D05: Region rendering for blocks
D06: Block-level CLI options
D07: Block processing tests
D08: Block processing documentation
D09: Block segmentation (PRIMARY)
D10: Block-level evaluation
```

### Key Architecture: Block Routing

```python
# src/docling_hybrid/orchestrator/routing.py

@dataclass
class RoutingRule:
    """Rule for routing blocks to backends."""
    block_type: BlockType
    backends: List[str]  # Priority order
    use_specialized_prompt: bool = True
    fallback_to_page: bool = True

class BlockRouter:
    """Routes blocks to appropriate backends."""
    
    def __init__(self, rules: List[RoutingRule]):
        self._rules = {r.block_type: r for r in rules}
    
    def get_backend_for_block(
        self,
        block: Block,
        available_backends: List[str]
    ) -> Tuple[str, str]:
        """Get backend and method for a block.
        
        Returns:
            (backend_name, method_name)
        """
        rule = self._rules.get(block.block_type)
        
        if rule:
            for backend in rule.backends:
                if backend in available_backends:
                    method = self._get_method(block.block_type, rule)
                    return (backend, method)
        
        # Default: page-level OCR
        return (available_backends[0], "page_to_markdown")
    
    def _get_method(self, block_type: BlockType, rule: RoutingRule) -> str:
        if not rule.use_specialized_prompt:
            return "page_to_markdown"
        
        if block_type == BlockType.TABLE:
            return "table_to_markdown"
        elif block_type == BlockType.FORMULA:
            return "formula_to_latex"
        else:
            return "page_to_markdown"
```

---

## Sprint 7: Multi-Backend & Merging
**Weeks 13-14 | Theme: "Best of all worlds"**

### Sprint 7 Objectives
1. ✅ Run multiple backends per block
2. ✅ Candidate collection
3. ✅ Merge strategies
4. ✅ Optional LLM arbitration

### Merge Strategy Implementation

```python
# src/docling_hybrid/orchestrator/merging.py

class MergeStrategy(ABC):
    """Base class for merge strategies."""
    
    @abstractmethod
    def merge(
        self,
        candidates: List[BackendCandidate],
        block: Block
    ) -> str: ...

class PreferFirstStrategy(MergeStrategy):
    """Use first successful result."""
    
    def merge(self, candidates, block):
        for c in candidates:
            if c.status == "success":
                return c.content
        raise MergeError("No successful candidates")

class PreferBackendStrategy(MergeStrategy):
    """Prefer specific backend."""
    
    def __init__(self, preferred: str):
        self._preferred = preferred
    
    def merge(self, candidates, block):
        for c in candidates:
            if c.backend_name == self._preferred and c.status == "success":
                return c.content
        # Fallback to first success
        return PreferFirstStrategy().merge(candidates, block)

class VotingStrategy(MergeStrategy):
    """Use majority voting for similar results."""
    
    def merge(self, candidates, block):
        # Group by similarity
        # Return most common result
        pass

class LLMArbitrationStrategy(MergeStrategy):
    """Use LLM to choose/merge results."""
    
    def __init__(self, arbitrator_backend: OcrVlmBackend):
        self._arbitrator = arbitrator_backend
    
    async def merge(self, candidates, block):
        prompt = self._build_arbitration_prompt(candidates, block)
        result = await self._arbitrator.page_to_markdown(
            prompt, 0, "arbitration"
        )
        return result.content
```

---

## Sprint 8: Evaluation & Final Release
**Weeks 15-16 | Theme: "Measure and ship"**

### Sprint 8 Objectives
1. ✅ Complete evaluation framework
2. ✅ Run benchmarks
3. ✅ Optimize based on results
4. ✅ Stage 2 release (v1.0.0)

### Evaluation Framework

```python
# src/docling_hybrid/eval/metrics.py

class TextEditDistanceMetric:
    """Normalized edit distance for text."""
    
    @property
    def name(self) -> str:
        return "text_edit_distance"
    
    def compute(self, predicted: str, ground_truth: str) -> float:
        distance = Levenshtein.distance(predicted, ground_truth)
        max_len = max(len(predicted), len(ground_truth))
        if max_len == 0:
            return 0.0
        return 1.0 - (distance / max_len)

class TEDSMetric:
    """Tree Edit Distance Similarity for tables."""
    
    @property
    def name(self) -> str:
        return "teds"
    
    def compute(self, predicted: str, ground_truth: str) -> float:
        # Convert Markdown tables to tree structure
        # Compute tree edit distance
        pass

class FormulaAccuracyMetric:
    """Exact match accuracy for formulas."""
    
    @property
    def name(self) -> str:
        return "formula_accuracy"
    
    def compute(self, predicted: str, ground_truth: str) -> float:
        # Normalize LaTeX
        pred_norm = self._normalize_latex(predicted)
        gt_norm = self._normalize_latex(ground_truth)
        return 1.0 if pred_norm == gt_norm else 0.0
```

### Stage 2 Release Criteria

```markdown
## Stage 2 Release Checklist (v1.0.0)

### Backends
- [ ] OpenRouter/Nemotron works
- [ ] DeepSeek vLLM works
- [ ] DeepSeek MLX works
- [ ] Backend comparison documented

### Block Processing
- [ ] Block segmentation works
- [ ] Block routing works
- [ ] Table extraction improved
- [ ] Formula extraction improved

### Multi-Backend
- [ ] Multiple backends per block works
- [ ] Merge strategies work
- [ ] LLM arbitration works (optional)

### Evaluation
- [ ] Text metrics work
- [ ] Table metrics work (TEDS)
- [ ] Formula metrics work
- [ ] Benchmark results documented

### Performance
- [ ] <3s per page (local backend)
- [ ] <30s for 10-page PDF
- [ ] Memory usage documented

### Documentation
- [ ] All backends documented
- [ ] Block processing documented
- [ ] Evaluation documented
- [ ] Performance benchmarks included
```

---

# Appendix A: Complete File Ownership Matrix

This matrix shows who owns each file throughout all sprints.

| File Path | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|-----------|----|----|----|----|----|----|----|----|
| `pyproject.toml` | D01 | D01 | D01 | D01 | D01 | D01 | D01 | D01 |
| `common/config.py` | D04 | D04 | D04 | D04 | D04 | D04 | D04 | D04 |
| `common/errors.py` | D04 | D04 | D04 | D04 | D04 | D04 | D04 | D04 |
| `common/ids.py` | D04 | D04 | - | - | - | - | - | - |
| `common/logging.py` | D04 | D04 | - | - | - | - | - | - |
| `common/http.py` | - | D04 | D04 | D04 | D04 | D04 | D04 | D04 |
| `backends/base.py` | D02 | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/factory.py` | - | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/openrouter_nemotron.py` | - | D02 | D02 | D02 | D02 | D02 | D02 | D02 |
| `backends/deepseek_vllm.py` | - | - | - | - | D02 | D02 | D02 | D02 |
| `backends/deepseek_mlx.py` | - | - | - | - | D02 | D02 | D02 | D02 |
| `renderer/base.py` | D05 | D05 | D05 | D05 | D05 | D05 | D05 | D05 |
| `renderer/pypdfium.py` | - | D05 | D05 | D05 | D05 | D05 | D05 | D05 |
| `orchestrator/interfaces.py` | D03 | D03 | D03 | D03 | D03 | D03 | D03 | D03 |
| `orchestrator/pipeline.py` | - | - | D03 | D03 | D03 | D03 | D03 | D03 |
| `orchestrator/routing.py` | - | - | - | - | - | D03 | D03 | D03 |
| `orchestrator/merging.py` | - | - | - | - | - | - | D03 | D03 |
| `cli/main.py` | - | - | D06 | D06 | D06 | D06 | D06 | D06 |
| `blocks/base.py` | D09 | D09 | D09 | D09 | D09 | D09 | D09 | D09 |
| `blocks/segmenter.py` | - | - | - | - | D09 | D09 | D09 | D09 |
| `eval/base.py` | D10 | D10 | D10 | D10 | D10 | D10 | D10 | D10 |
| `eval/metrics.py` | - | - | - | - | D10 | D10 | D10 | D10 |
| `tests/conftest.py` | D07 | D07 | D07 | D07 | D07 | D07 | D07 | D07 |
| `CLAUDE.md` | D08 | D08 | D08 | D08 | D08 | D08 | D08 | D08 |

---

# Appendix B: Integration Meeting Agendas

## Standard Integration Meeting Agenda (Days 9-10)

### Day 9 Morning (3 hours)
```
09:00 - Sprint Review
  - Each developer demos their work (5 min each)
  - Q&A for clarification

10:00 - PR Status Review
  - Check CI status for all PRs
  - Identify blockers
  - Assign reviewers for pending PRs

11:00 - Conflict Analysis
  - Check for potential merge conflicts
  - Plan resolution strategy
```

### Day 9 Afternoon (4 hours)
```
14:00 - Begin Merging
  - Merge in dependency order
  - Run tests after each merge
  - Fix any issues immediately

18:00 - Status Check
  - All PRs merged?
  - All tests passing?
  - Blockers for tomorrow?
```

### Day 10 Morning (3 hours)
```
09:00 - Full Test Suite
  - Run complete test suite
  - Run integration tests
  - Run smoke tests (if applicable)

10:30 - Documentation Review
  - Check all docs are current
  - Update CONTINUATION.md
  - Update CHANGELOG

11:30 - Release Preparation (if applicable)
  - Version bump
  - Release notes
  - Tag creation
```

### Day 10 Afternoon (3 hours)
```
14:00 - Sprint Retrospective
  - What went well?
  - What could improve?
  - Action items

15:00 - Next Sprint Planning
  - Review upcoming tasks
  - Assign ownership
  - Identify dependencies

16:00 - Wrap-up
  - Final documentation updates
  - Branch cleanup
  - Next sprint kickoff preparation
```

---

# Appendix C: Definition of Done

## For Task Cards
```markdown
A task is DONE when:
- [ ] Code is complete and compiles
- [ ] Unit tests written and passing
- [ ] Code reviewed by at least 1 peer
- [ ] Documentation updated
- [ ] PR approved
- [ ] Merged to develop branch
```

## For Sprints
```markdown
A sprint is DONE when:
- [ ] All P0 tasks complete
- [ ] All P1 tasks complete or rescheduled
- [ ] Integration tests passing
- [ ] Documentation current
- [ ] CONTINUATION.md updated
- [ ] Retrospective completed
```

## For Stages
```markdown
A stage is DONE when:
- [ ] All sprint objectives met
- [ ] Release criteria satisfied
- [ ] Version tagged
- [ ] Release notes written
- [ ] Deployment guide tested
```

---

# Appendix D: Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API rate limiting | Medium | High | Implement caching, use local backends for testing |
| Memory issues on large PDFs | High | Medium | Streaming processing, configurable limits |
| Block segmentation accuracy | Medium | Medium | Fallback to page-level OCR |
| MLX compatibility issues | Low | Low | Document supported hardware |
| Merge conflicts | Low | Low | Strict file ownership, small PRs |
| Scope creep | Medium | High | Strict sprint boundaries, defer to later sprints |
| Developer unavailable | Medium | Medium | Cross-training, documented ownership transfers |

---

This completes the comprehensive development schedule. Each sprint has clear ownership boundaries, detailed task cards, and integration procedures to ensure smooth parallel development.
