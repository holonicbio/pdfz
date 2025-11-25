# Architecture Overview

## System Purpose

The Docling Hybrid OCR system provides a unified framework for converting PDF documents to structured Markdown using a hybrid approach that combines:

1. **Docling's native PDF parsing** - Extracts structure, text, and layout from PDFs
2. **VLM-based OCR** - Uses vision-language models to extract text from page images
3. **Pluggable backends** - Supports multiple OCR/VLM providers (OpenRouter/Nemotron, DeepSeek, etc.)

The system is designed to run on resource-constrained development machines (12GB RAM, CPU-only) while supporting production deployment with GPU acceleration.

## Design Principles

1. **Backend Agnostic**: Core pipeline is independent of specific OCR/VLM providers
2. **Fail Fast**: Invalid configurations or API errors surface immediately with actionable messages
3. **Extensible**: New backends require only implementing a simple interface
4. **Resource Aware**: Default configuration works on 12GB RAM machines
5. **Observable**: All operations are logged for debugging and training data generation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI / Python API                            │
│                    (docling-hybrid-ocr command)                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Orchestrator                                │
│              (Pipeline coordination, page iteration)                │
└─────────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────────┐     ┌────────────────────────────────────┐
│      Page Renderer            │     │       Backend Factory              │
│   (pypdfium2 → PNG)           │     │   (Backend selection & creation)   │
└───────────────────────────────┘     └────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
        ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
        │ OpenRouter        │   │ DeepSeek vLLM     │   │ DeepSeek MLX      │
        │ Nemotron Backend  │   │ Backend (stub)    │   │ Backend (stub)    │
        └───────────────────┘   └───────────────────┘   └───────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │   OpenRouter API  │
        │   (External)      │
        └───────────────────┘
```

## Components

### 1. Common (Foundation Layer)

**Purpose:** Shared utilities, configuration, and data models  
**Location:** `src/docling_hybrid/common/`  
**Status:** ✅ Complete  
**Dependencies:** None (leaf module)

**Files:**
- `config.py` - Configuration loading with layered overrides
- `models.py` - Pydantic data models (OcrBackendConfig, PageResult, etc.)
- `errors.py` - Exception hierarchy
- `ids.py` - ID generation utilities
- `logging.py` - Structured logging setup

### 2. Backends (OCR/VLM Interface Layer)

**Purpose:** Abstract interface for OCR/VLM operations  
**Location:** `src/docling_hybrid/backends/`  
**Status:** ✅ Nemotron complete, DeepSeek stubs  
**Dependencies:** Common

**Files:**
- `base.py` - Abstract `OcrVlmBackend` interface
- `factory.py` - Backend factory and registry
- `openrouter_nemotron.py` - ✅ Full implementation
- `deepseek_vllm_stub.py` - ○ Stub (Phase 2)
- `deepseek_mlx_stub.py` - ○ Stub (Phase 2)

### 3. Renderer (PDF → Image Layer)

**Purpose:** Convert PDF pages to images for VLM processing  
**Location:** `src/docling_hybrid/renderer/`  
**Status:** ✅ Complete  
**Dependencies:** Common, pypdfium2

**Files:**
- `core.py` - Page rendering functions

### 4. Orchestrator (Pipeline Layer)

**Purpose:** Coordinate the full PDF→Markdown pipeline  
**Location:** `src/docling_hybrid/orchestrator/`  
**Status:** ✅ Complete  
**Dependencies:** Common, Backends, Renderer

**Files:**
- `pipeline.py` - HybridPipeline class
- `models.py` - ConversionOptions, ConversionResult

### 5. CLI (User Interface Layer)

**Purpose:** Command-line interface for users  
**Location:** `src/docling_hybrid/cli/`  
**Status:** ✅ Complete  
**Dependencies:** Orchestrator, Common

**Files:**
- `main.py` - Typer CLI application

### 6. Extended Scope (Future Phases)

**Exporters** (`src/docling_hybrid/exporters/`)
- Status: ○ Stub
- Purpose: Multi-format export (HTML, JSON, RAG)

**Blocks** (`src/docling_hybrid/blocks/`)
- Status: ○ Stub
- Purpose: Block-level OCR with routing and merging

**Eval** (`src/docling_hybrid/eval/`)
- Status: ○ Stub
- Purpose: Evaluation framework with metrics

## Data Flow

### Minimal Core Flow (Page-Level)

```
PDF File Path
      │
      ▼
┌─────────────────────────────────────────┐
│  get_page_count() via pypdfium2         │
│  - Validate PDF exists                  │
│  - Get total page count                 │
└─────────────────────────────────────────┘
      │
      │ page_count
      ▼
┌─────────────────────────────────────────┐
│  Page Loop (for each page)              │
│                                         │
│  1. render_page_to_png_bytes()          │
│     └─► PNG bytes (200 DPI default)     │
│                                         │
│  2. backend.page_to_markdown()          │
│     └─► Markdown string for page        │
└─────────────────────────────────────────┘
      │
      │ List[str] (Markdown per page)
      ▼
┌─────────────────────────────────────────┐
│  Concatenate Pages                      │
│  - Join with "\n\n"                     │
│  - Add page separators (optional)       │
└─────────────────────────────────────────┘
      │
      ▼
Output: <input>.nemotron.md
```

## Technology Stack

### Core
- **Language:** Python 3.11+
- **PDF Rendering:** pypdfium2
- **HTTP Client:** aiohttp (async)
- **Configuration:** TOML (tomli) + Pydantic
- **CLI:** Typer + Rich
- **Logging:** structlog

### Testing
- **Framework:** pytest + pytest-asyncio
- **Mocking:** unittest.mock, aioresponses
- **Coverage:** pytest-cov

### External Services
- **OpenRouter API:** Remote VLM inference
- **Default Model:** nvidia/nemotron-nano-12b-v2-vl:free

## Design Decisions

### Decision 1: Async HTTP Client
**Context:** OCR/VLM API calls take 2-10 seconds per page  
**Choice:** aiohttp  
**Rationale:** Enables concurrent page processing, mature library

### Decision 2: Backend Interface Design
**Context:** Need to support multiple OCR/VLM providers  
**Choice:** Abstract base class with factory  
**Rationale:** Clear contract, easy testing, type safety

### Decision 3: Configuration Hierarchy
**Context:** Need production, local dev, and test configurations  
**Choice:** Layered (env → file → defaults)  
**Rationale:** Env vars for secrets, files for settings, code for defaults

### Decision 4: Page-Level First
**Context:** Full block-level processing is complex  
**Choice:** Implement page-level first, add block-level later  
**Rationale:** Simpler, provides immediate value, lower risk

### Decision 5: pypdfium2 for Rendering
**Context:** Need fast, memory-efficient PDF rendering  
**Choice:** pypdfium2 (PDFium wrapper)  
**Rationale:** Fast, low memory, good quality, active maintenance

## Component Dependency Graph

```
┌──────────────────────────────────────────────────────────┐
│                         CLI                              │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                     Orchestrator                         │
└──────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐
│  Renderer   │  │  Backends   │  │  Exporters (extended)   │
└─────────────┘  └─────────────┘  └─────────────────────────┘
           │              │              │
           └──────────────┼──────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                       Common                             │
│          (config, models, logging, errors)               │
└──────────────────────────────────────────────────────────┘
```

**Build Order:**
1. Common (no dependencies)
2. Renderer, Backends (depend on Common)
3. Orchestrator (depends on Renderer, Backends)
4. CLI (depends on Orchestrator)
5. Exporters, Blocks, Eval (extended, depend on above)

## Security Considerations

### API Keys
- Never commit to repository
- Load from environment variables (`OPENROUTER_API_KEY`)
- Document in `.env.example`

### Input Validation
- Validate PDF paths exist before processing
- Validate configuration values with Pydantic
- Sanitize file paths in output

## Performance Considerations

### Expected Bottlenecks
1. **VLM API latency** - 2-10 seconds per page
2. **Network bandwidth** - Large base64 images (~500KB per page)
3. **Memory for rendering** - ~100MB per page at high DPI

### Resource Limits (Local Dev)
```toml
[resources]
max_workers = 2          # Reduced from 8
max_memory_mb = 4096     # 4GB instead of 16GB
page_render_dpi = 150    # Reduced from 200
```

## Future Extensions

### Phase 2: Block-Level Processing
- Implement BlockProcessor component
- Add TableBackend, FormulaBackend interfaces
- Implement merge policies

### Phase 3: Multi-Backend Ensemble
- Run multiple backends in parallel
- Implement voting/arbitration
- Add confidence scoring

### Phase 4: Evaluation Suite
- Implement ground truth format
- Add metric computation (edit distance, TEDS)
- Create evaluation CLI

### Phase 5: Additional Backends
- DeepSeek-OCR via vLLM (CUDA Linux)
- DeepSeek-OCR via MLX (macOS)
- MinerU integration
- Mathpix integration
