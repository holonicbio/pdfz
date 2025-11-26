# Development Continuation Guide - Mac M2 Air Edition

## Sprint 4: DeepSeek OCR MLX Implementation

**Target Environment:** Mac M2 Air with 24GB RAM
**Framework:** Apple MLX
**Developer:** Single developer with Claude Code
**Status:** Ready for Sprint 4 Implementation

---

## Table of Contents

1. [Current Project State](#current-project-state)
2. [Documentation Guide](#documentation-guide)
3. [Sprint 4 Overview](#sprint-4-overview)
4. [Environment Setup](#environment-setup)
5. [Implementation Tasks](#implementation-tasks)
6. [Testing Plan](#testing-plan)
7. [PDF Test Collection](#pdf-test-collection)
8. [Performance Targets](#performance-targets)
9. [Outstanding Work](#outstanding-work)
10. [Quick Reference](#quick-reference)

---

## Current Project State

### Version & Status
**Version:** 0.1.0
**Last Sprint:** Sprint 3 (Complete)
**Test Status:** 242 passing, 13 failing (DeepSeek tests expected to fail), 28 skipped

### What's Complete (Sprints 1-3)

#### Core Infrastructure (100%)
- ✅ Configuration system (layered: env → file → defaults)
- ✅ Common utilities (IDs, logging, errors, retry logic)
- ✅ Pydantic data models
- ✅ Test infrastructure (pytest, fixtures, mocks)

#### Backends (Partial)
- ✅ Backend abstraction (`OcrVlmBackend` ABC)
- ✅ Backend factory (`make_backend`)
- ✅ OpenRouter/Nemotron backend (fully implemented and tested)
- ✅ DeepSeek vLLM backend (implemented for CUDA/Linux)
- ✅ Fallback chain system
- ✅ Backend health checking
- ○ **DeepSeek MLX backend (STUB - Sprint 4 target)**

#### Pipeline & CLI (100%)
- ✅ Page renderer (pypdfium2)
- ✅ Orchestrator pipeline (`HybridPipeline`)
- ✅ Progress callbacks
- ✅ CLI (`docling-hybrid-ocr` command)
- ✅ Batch processing

#### Extended Scope (Stubs)
- ○ Block-level processing (stub)
- ○ Multi-format exporters (stub)
- ○ Evaluation framework (stub)

### Implementation Status by File

| File | Status | Notes |
|------|--------|-------|
| `common/config.py` | ✅ Complete | Tested |
| `common/models.py` | ✅ Complete | Tested |
| `common/errors.py` | ✅ Complete | Tested |
| `common/logging.py` | ✅ Complete | Tested |
| `common/retry.py` | ✅ Complete | Tested |
| `backends/base.py` | ✅ Complete | Interface |
| `backends/factory.py` | ✅ Complete | Tested |
| `backends/openrouter_nemotron.py` | ✅ Complete | Production ready |
| `backends/deepseek_vllm.py` | ✅ Complete | For CUDA/Linux |
| `backends/deepseek_mlx_stub.py` | ○ **STUB** | **Sprint 4 target** |
| `backends/fallback.py` | ✅ Complete | Tested |
| `backends/health.py` | ✅ Complete | Tested |
| `renderer/core.py` | ✅ Complete | Tested |
| `orchestrator/pipeline.py` | ✅ Complete | Tested |
| `cli/main.py` | ✅ Complete | Tested |

---

## Documentation Guide

### Master Documents

| Document | Purpose | Location |
|----------|---------|----------|
| **CLAUDE.md** | Master development context (start here) | `/CLAUDE.md` |
| **CONTINUATION.md** | This file - Sprint 4 handover | `/CONTINUATION.md` |
| **LOCAL_DEV.md** | Local development guide | `/LOCAL_DEV.md` |

### Architecture & Design

| Document | Purpose |
|----------|---------|
| `docs/ARCHITECTURE.md` | System architecture overview |
| `docs/components/BACKENDS.md` | Backend implementation details |
| `docs/design/BLOCK_PROCESSING.md` | Block processing design (future) |
| `docs/design/EVALUATION.md` | Evaluation framework design (future) |
| `docs/DEEPSEEK_INTEGRATION_PLAN.md` | DeepSeek vLLM plan (reference for MLX) |

### API & Usage

| Document | Purpose |
|----------|---------|
| `docs/API.md` | Python API guide |
| `docs/API_REFERENCE.md` | Detailed API reference |
| `docs/CLI_GUIDE.md` | Command-line usage |
| `docs/QUICK_START.md` | Getting started guide |
| `docs/TROUBLESHOOTING.md` | Common issues and solutions |

### Sprint Documents

| Document | Purpose |
|----------|---------|
| `docs/SPRINT_PLAN.md` | Overall sprint planning |
| `docs/SPRINT1_COMPLETION_REPORT.md` | Sprint 1 results |
| `docs/SPRINT2_PLAN.md` | Sprint 2 planning |
| `docs/SPRINT3_PLAN.md` | Sprint 3 planning |

### Component READMEs

Each source directory has a detailed README:

| Directory | README Location |
|-----------|-----------------|
| Source code root | `src/docling_hybrid/README.md` |
| Backends | `src/docling_hybrid/backends/README.md` |
| CLI | `src/docling_hybrid/cli/README.md` |
| Common utilities | `src/docling_hybrid/common/README.md` |
| Orchestrator | `src/docling_hybrid/orchestrator/README.md` |
| Renderer | `src/docling_hybrid/renderer/README.md` |
| Blocks (stub) | `src/docling_hybrid/blocks/README.md` |
| Eval (stub) | `src/docling_hybrid/eval/README.md` |
| Exporters (stub) | `src/docling_hybrid/exporters/README.md` |

### Test Documentation

| Directory | README Location |
|-----------|-----------------|
| Tests root | `tests/README.md` |
| Mock helpers | `tests/mocks/README.md` |
| Test utilities | `tests/utils/README.md` |
| Sample PDFs | `tests/fixtures/sample_pdfs/README.md` |

---

## Sprint 4 Overview

### Goal
Implement a fully functional DeepSeek OCR backend using Apple MLX framework, optimized for Mac M2 Air with 24GB RAM.

### Key Deliverables

1. **DeepSeek MLX Backend Implementation**
   - Full implementation of `DeepseekOcrMlxBackend` class
   - Support for `page_to_markdown()`, `table_to_markdown()`, `formula_to_latex()`
   - Compatible with existing backend interface

2. **Mac-Optimized Configuration**
   - Memory-efficient settings for 24GB RAM
   - MLX-specific configuration options
   - Local model caching strategy

3. **Comprehensive Testing**
   - Test with all 325 PDFs in `pdfs/` directory
   - Performance benchmarks on M2 Air
   - Quality comparison with OpenRouter backend

4. **Documentation**
   - MLX setup guide
   - Mac deployment documentation
   - Performance tuning guide

---

## Environment Setup

### Hardware Requirements
- Mac M2 Air with 24GB RAM
- ~10GB storage for model weights
- macOS 14.0+ (Sonoma recommended)

### Software Requirements

```bash
# Python 3.11+ (use pyenv or Homebrew)
brew install python@3.11

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install project dependencies
pip install -e ".[dev]"
```

### MLX Setup

```bash
# Install MLX and MLX-VLM
pip install mlx mlx-lm mlx-vlm

# Optional: Install additional dependencies
pip install pillow transformers huggingface_hub
```

### Model Download

```bash
# Download DeepSeek-OCR model for MLX
# Option 1: Using Hugging Face Hub
huggingface-cli download deepseek-ai/DeepSeek-OCR --local-dir ~/.cache/huggingface/deepseek-ocr

# Option 2: Using mlx-vlm
python -c "from mlx_vlm import load; load('deepseek-ai/DeepSeek-OCR')"
```

### Mac-Specific Configuration

Create `configs/mac-m2-air.toml`:

```toml
[app]
name = "docling-hybrid-ocr"
environment = "development"

[logging]
level = "INFO"
format = "text"

[resources]
max_workers = 2              # Conservative for 24GB RAM
max_memory_mb = 16384        # Leave 8GB for system + MLX
page_render_dpi = 150        # Balance quality vs memory

[backends]
default = "deepseek-mlx"

[[backends.candidates]]
name = "deepseek-mlx"
model = "deepseek-ai/DeepSeek-OCR"
temperature = 0.0
max_tokens = 8192
timeout_s = 180              # MLX can be slower than cloud APIs

[[backends.candidates]]
name = "nemotron-openrouter"
model = "nvidia/nemotron-nano-12b-v2-vl:free"
base_url = "https://openrouter.ai/api/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
```

---

## Implementation Tasks

### Phase 1: MLX Backend Core (Day 1-2)

#### Task 1.1: Implement DeepseekOcrMlxBackend

**File:** `src/docling_hybrid/backends/deepseek_mlx.py` (rename from stub)

**Implementation Strategy:** Direct Python API (recommended for single-developer workflow)

```python
"""DeepSeek-OCR backend using MLX on macOS.

This backend provides efficient local inference on Apple Silicon
using the MLX framework and mlx-vlm library.
"""

import asyncio
from pathlib import Path
from typing import Any

import mlx.core as mx
from mlx_vlm import load, generate
from PIL import Image
import io

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.logging import get_logger
from docling_hybrid.common.models import OcrBackendConfig
from docling_hybrid.common.errors import BackendError

logger = get_logger(__name__)

# Prompts (reuse from deepseek_vllm.py)
PAGE_TO_MARKDOWN_PROMPT = """..."""  # Same as vLLM backend

class DeepseekOcrMlxBackend(OcrVlmBackend):
    """DeepSeek-OCR backend using MLX on macOS."""

    def __init__(self, config: OcrBackendConfig) -> None:
        super().__init__(config)
        self._model = None
        self._processor = None
        self._model_loaded = False

    async def _ensure_model_loaded(self) -> None:
        """Lazy load model on first use."""
        if not self._model_loaded:
            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)

    def _load_model(self) -> None:
        """Load MLX model (runs in thread pool)."""
        self._model, self._processor = load(self.config.model)
        self._model_loaded = True
        logger.info("model_loaded", backend=self.name, model=self.config.model)

    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert page image to Markdown using MLX."""
        await self._ensure_model_loaded()

        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Run inference in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._generate,
            PAGE_TO_MARKDOWN_PROMPT,
            image,
        )

        return result

    def _generate(self, prompt: str, image: Image.Image) -> str:
        """Generate text from image (runs in thread pool)."""
        output = generate(
            self._model,
            self._processor,
            prompt=prompt,
            images=[image],
            max_tokens=self.config.max_tokens,
            temp=self.config.temperature,
        )
        return output
```

#### Task 1.2: Update Backend Factory

**File:** `src/docling_hybrid/backends/factory.py`

- Replace stub import with full implementation
- Ensure Mac detection for default backend selection

#### Task 1.3: Add MLX Dependencies

**File:** `pyproject.toml`

```toml
[project.optional-dependencies]
mlx = [
    "mlx>=0.17.0",
    "mlx-lm>=0.17.0",
    "mlx-vlm>=0.1.0",
]
```

### Phase 2: Testing & Optimization (Day 3-4)

#### Task 2.1: Unit Tests for MLX Backend

**File:** `tests/unit/backends/test_deepseek_mlx.py`

- Test backend initialization
- Test model loading (mocked)
- Test image encoding
- Test prompt construction
- Test error handling

#### Task 2.2: Integration Tests

**File:** `tests/integration/test_mlx_integration.py`

- Test full pipeline with MLX backend
- Test with sample PDFs
- Test memory usage under load
- Test concurrent processing limits

#### Task 2.3: Performance Benchmarks

**File:** `tests/benchmarks/test_mlx_performance.py`

- Measure tokens/second
- Measure pages/minute
- Track memory usage
- Compare with OpenRouter

### Phase 3: PDF Testing & Validation (Day 5-7)

#### Task 3.1: Test with Full PDF Collection

Run comprehensive tests with all 325 PDFs in `pdfs/` directory:

```bash
# Basic batch test
docling-hybrid-ocr batch --input-dir pdfs/ --output-dir output/

# With benchmarking
python scripts/benchmark_mlx.py --input-dir pdfs/ --output results.json
```

#### Task 3.2: Quality Validation

Compare MLX output with OpenRouter baseline:
- Character error rate
- Structure preservation
- Table extraction accuracy
- Formula recognition

#### Task 3.3: Edge Case Testing

Focus on challenging PDFs:
- Large files (>10MB)
- Complex layouts
- Tables and formulas
- Low-quality scans

---

## Testing Plan

### Test Pyramid for Sprint 4

```
         /\
        /E2E\         20% - Full PDF testing with MLX
       /------\
      / Integ \       30% - Pipeline integration
     /----------\
    /   Unit     \    50% - MLX backend logic
   /--------------\
```

### Test Commands

```bash
# Run unit tests (fast, no model needed)
pytest tests/unit -v

# Run unit tests for MLX backend
pytest tests/unit/backends/test_deepseek_mlx.py -v

# Run integration tests (requires MLX model)
pytest tests/integration -v -m mlx

# Run benchmarks
pytest tests/benchmarks -v --benchmark-enable

# Run full test suite
pytest tests/ -v
```

### CI Markers

```python
# Skip on non-Mac systems
@pytest.mark.skipif(sys.platform != "darwin", reason="MLX requires macOS")
@pytest.mark.mlx
async def test_mlx_backend():
    ...

# Skip if MLX not installed
@pytest.mark.skipif(not has_mlx(), reason="MLX not installed")
async def test_mlx_inference():
    ...
```

---

## PDF Test Collection

### Collection Statistics

| Metric | Value |
|--------|-------|
| Total PDFs | 325 |
| Total Size | 1.14 GB |
| Average Size | 3.6 MB |
| Smallest | 14 KB |
| Largest | 51 MB |

### PDF Categories

Based on file naming patterns, the collection includes:

| Category | Count (est.) | Examples |
|----------|--------------|----------|
| ArXiv papers | ~150 | `2511.*.pdf`, `2510.*.pdf` |
| BioRxiv papers | ~50 | `2025.*.full.pdf` |
| Scientific journals | ~40 | `s41467-*.pdf`, `s41586-*.pdf` |
| Books/chapters | ~30 | `978-3-*.pdf`, `PHMethods*.pdf` |
| Misc documents | ~55 | Various academic/technical PDFs |

### Testing Strategy

#### Phase 1: Quick Validation (Day 1)
- Test with 10 small PDFs (<100KB)
- Verify basic functionality
- Check memory usage

#### Phase 2: Standard Testing (Day 2-3)
- Test with 50 medium PDFs (100KB-1MB)
- Measure performance baselines
- Identify problematic documents

#### Phase 3: Stress Testing (Day 4-5)
- Test with 20 large PDFs (>5MB)
- Monitor memory under load
- Test batch processing limits

#### Phase 4: Full Suite (Day 6-7)
- Process all 325 PDFs
- Generate quality report
- Document any failures

### Sample Test Commands

```bash
# Quick validation with small PDFs
docling-hybrid-ocr convert pdfs/mmc2.pdf --verbose

# Batch process a subset
find pdfs/ -size -100k -name "*.pdf" | head -10 | \
  xargs -I {} docling-hybrid-ocr convert {} --dpi 150

# Full batch with logging
docling-hybrid-ocr batch \
  --input-dir pdfs/ \
  --output-dir output/ \
  --backend deepseek-mlx \
  --max-pages 5 \
  --log-file conversion.log
```

---

## Performance Targets

### Mac M2 Air with 24GB RAM

| Metric | Target | Stretch Goal |
|--------|--------|--------------|
| Pages/minute | 3-5 | 6-8 |
| Tokens/second | 15-25 | 30-40 |
| Memory usage | <16GB peak | <12GB peak |
| Model load time | <30s | <15s |
| First page latency | <20s | <10s |

### Optimization Strategies

1. **Memory Management**
   - Use lazy model loading
   - Process pages sequentially (avoid concurrent MLX calls)
   - Clear image buffers after processing

2. **Throughput Optimization**
   - Lower DPI for faster rendering (150 vs 200)
   - Batch preprocessing of images
   - Async I/O for file operations

3. **Quality vs Speed Tradeoffs**
   - Temperature 0.0 for deterministic output
   - Adjust max_tokens based on page complexity
   - Use fallback to OpenRouter for failed pages

---

## Outstanding Work

### High Priority (Sprint 4)

- [ ] **Implement DeepSeek MLX backend** - Full implementation
- [ ] **Create Mac-specific tests** - Unit and integration tests
- [ ] **Test with PDF collection** - All 325 PDFs
- [ ] **Performance benchmarks** - Measure and optimize
- [ ] **Documentation** - MLX setup and usage guides

### Medium Priority (Sprint 4 if time)

- [ ] **Quality comparison** - MLX vs OpenRouter output comparison
- [ ] **Error recovery** - Graceful handling of MLX failures
- [ ] **Progress callbacks** - Enhanced progress reporting for long jobs
- [ ] **Mac config optimization** - Fine-tune settings for M2 Air

### Lower Priority (Sprint 5+)

- [ ] **Block-level processing** - Extract tables/figures separately
- [ ] **Evaluation framework** - Automated quality metrics
- [ ] **Multi-format export** - HTML, LaTeX, DOCX output
- [ ] **HTTP server mode** - Run MLX as local server (optional)

### Known Issues to Address

1. **DeepSeek tests failing** - Expected until MLX backend implemented
2. **Large PDF memory usage** - May need streaming for 50MB+ files
3. **Concurrent processing** - MLX may not handle concurrent calls well

---

## Quick Reference

### Daily Development Commands

```bash
# Activate environment
source .venv/bin/activate

# Load API key (if using OpenRouter fallback)
source ./scripts/setup_env.sh

# Run tests
pytest tests/unit -v

# Run CLI
docling-hybrid-ocr convert document.pdf

# Check code quality
ruff check src/
mypy src/docling_hybrid
```

### Key Files to Modify

```
src/docling_hybrid/backends/
├── deepseek_mlx_stub.py  → deepseek_mlx.py (rename and implement)
├── factory.py            (update imports)
└── __init__.py           (update exports)

configs/
└── mac-m2-air.toml       (create new)

tests/
├── unit/backends/test_deepseek_mlx.py    (create new)
└── integration/test_mlx_integration.py   (create new)
```

### Environment Variables

```bash
# Config file
export DOCLING_HYBRID_CONFIG=configs/mac-m2-air.toml

# Log level
export DOCLING_HYBRID_LOG_LEVEL=DEBUG

# OpenRouter fallback (optional)
export OPENROUTER_API_KEY=sk-or-v1-...
```

### Useful Links

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [MLX-VLM GitHub](https://github.com/ml-explore/mlx-vlm)
- [DeepSeek-OCR Model](https://huggingface.co/deepseek-ai/DeepSeek-OCR)
- [Project GitHub](https://github.com/holonicbio/pdfz)

---

## Contact & Support

For questions during development:
1. Check documentation files first
2. Search existing code for patterns
3. Review test files for usage examples
4. Create GitHub issue for blockers

---

**Document Version:** 2.0
**Last Updated:** November 2024
**Sprint:** 4 (Mac M2 Air / MLX Implementation)
**Author:** Claude Code (handover from Linux environment)
