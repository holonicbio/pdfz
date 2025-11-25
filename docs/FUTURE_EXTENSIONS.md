# Future Extensions Roadmap

This document outlines potential extensions beyond the initial product release (Sprint 3).

## Phase 2: Enhanced Features

### 2.1 DeepSeek MLX Backend (macOS)
**Priority:** High (for macOS users)
**Effort:** Medium

**Description:**
Implement the DeepSeek-OCR backend using MLX for native Apple Silicon performance.

**Tasks:**
- Complete `src/docling_hybrid/backends/deepseek_mlx_stub.py`
- Implement MLX model loading and inference
- Optimize for M1/M2/M3 chips
- Add memory management for large PDFs

**Files:**
- `src/docling_hybrid/backends/deepseek_mlx.py` (from stub)
- `tests/unit/backends/test_deepseek_mlx.py`

**Dependencies:**
- mlx>=0.10.0
- mlx-vlm>=0.1.0

---

### 2.2 Block-Level Processing
**Priority:** High
**Effort:** High

**Description:**
Process individual document blocks (tables, figures, formulas) separately for higher accuracy.

**Tasks:**
- Implement document layout analysis
- Create block extraction pipeline
- Add specialized VLM prompts per block type
- Merge block results into coherent document

**Architecture:**
```
PDF → Layout Analysis → Block Extraction → Per-Block VLM → Merge → Markdown
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                 Tables      Formulas
                    │             │
                    ▼             ▼
              table_to_md   formula_to_latex
```

**Files:**
- `src/docling_hybrid/blocks/` (new module)
- `src/docling_hybrid/blocks/extractor.py`
- `src/docling_hybrid/blocks/merger.py`

---

### 2.3 Multi-Format Export
**Priority:** Medium
**Effort:** Medium

**Description:**
Export to formats beyond Markdown: HTML, DOCX, LaTeX.

**Tasks:**
- Create exporter base class
- Implement HTML exporter with styling
- Implement DOCX exporter with python-docx
- Implement LaTeX exporter for academic docs

**Files:**
- `src/docling_hybrid/exporters/base.py`
- `src/docling_hybrid/exporters/html.py`
- `src/docling_hybrid/exporters/docx.py`
- `src/docling_hybrid/exporters/latex.py`

---

### 2.4 Streaming Output
**Priority:** Medium
**Effort:** Low

**Description:**
Stream Markdown output as pages complete instead of waiting for full document.

**Tasks:**
- Implement async generator for page results
- Add streaming CLI option
- Support partial file writes

**API:**
```python
async for page_result in pipeline.convert_pdf_stream(pdf_path):
    print(page_result.content)
```

---

## Phase 3: Advanced Features

### 3.1 Evaluation Framework
**Priority:** High (for quality assurance)
**Effort:** High

**Description:**
Comprehensive evaluation framework for comparing backends and measuring quality.

**Components:**
- Ground truth dataset management
- OCR accuracy metrics (CER, WER, BLEU)
- Table structure evaluation
- Formula accuracy evaluation
- Performance benchmarking

**Files:**
- `src/docling_hybrid/eval/metrics.py`
- `src/docling_hybrid/eval/dataset.py`
- `src/docling_hybrid/eval/runner.py`
- `tests/eval/` (evaluation test suite)

---

### 3.2 Caching Layer
**Priority:** Medium
**Effort:** Medium

**Description:**
Cache page rendering and OCR results to avoid reprocessing.

**Features:**
- Page image hash-based caching
- OCR result caching with TTL
- Disk and Redis backends
- Cache invalidation strategies

**Files:**
- `src/docling_hybrid/cache/base.py`
- `src/docling_hybrid/cache/disk.py`
- `src/docling_hybrid/cache/redis.py`

---

### 3.3 Distributed Processing
**Priority:** Low
**Effort:** High

**Description:**
Support distributed processing across multiple machines for large document batches.

**Options:**
1. **Celery + Redis:** Task queue for batch processing
2. **Ray:** Distributed computing framework
3. **Kubernetes Jobs:** Container-based scaling

**Architecture:**
```
Coordinator → Task Queue → Worker Nodes → Result Aggregation
     │              │
     └──────────────┴──── Shared Storage (S3/GCS)
```

---

### 3.4 API Server
**Priority:** Medium
**Effort:** Medium

**Description:**
REST API server for integration with web applications.

**Endpoints:**
- `POST /convert` - Submit PDF for conversion
- `GET /status/{job_id}` - Check conversion status
- `GET /result/{job_id}` - Get conversion result
- `GET /backends` - List available backends

**Files:**
- `src/docling_hybrid/server/app.py`
- `src/docling_hybrid/server/routes.py`
- `src/docling_hybrid/server/models.py`

---

## Phase 4: Enterprise Features

### 4.1 Multi-Tenancy
**Priority:** Low (enterprise only)
**Effort:** High

**Description:**
Support multiple isolated tenants with separate configurations and quotas.

**Features:**
- Tenant isolation
- Rate limiting per tenant
- Usage tracking and billing hooks
- Custom backend configurations

---

### 4.2 Plugin System
**Priority:** Low
**Effort:** High

**Description:**
Allow third-party extensions for custom backends, exporters, and processors.

**Plugin Types:**
- Backend plugins (new VLM providers)
- Exporter plugins (new output formats)
- Processor plugins (custom post-processing)

**Architecture:**
```python
# Plugin registration
from docling_hybrid import register_backend

@register_backend("my-backend")
class MyCustomBackend(OcrVlmBackend):
    ...
```

---

### 4.3 Audit Logging
**Priority:** Low (enterprise only)
**Effort:** Low

**Description:**
Comprehensive audit logging for compliance and debugging.

**Features:**
- All API calls logged
- Document access tracking
- Error correlation IDs
- Log export to SIEM systems

---

## Implementation Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| DeepSeek MLX | High | Medium | P1 |
| Block Processing | High | High | P1 |
| Multi-Format Export | Medium | Medium | P2 |
| Streaming Output | Medium | Low | P2 |
| Evaluation Framework | High | High | P2 |
| Caching Layer | Medium | Medium | P2 |
| API Server | Medium | Medium | P3 |
| Distributed Processing | Low | High | P4 |
| Multi-Tenancy | Low | High | P4 |
| Plugin System | Low | High | P4 |
| Audit Logging | Low | Low | P4 |

---

## Technology Considerations

### MLX Backend
- Requires macOS 13.3+ with Apple Silicon
- MLX provides 10-100x speedup over CPU
- Memory efficient through unified memory

### Distributed Processing
- Ray is simpler for Python-native workloads
- Celery better for existing infrastructure
- Kubernetes for cloud-native deployments

### Caching
- Redis for distributed cache
- SQLite for single-machine disk cache
- Consider S3 for cloud deployments

---

## Contribution Guidelines

When implementing extensions:

1. **Create a design doc** before starting
2. **Follow existing patterns** from core modules
3. **Add comprehensive tests** (unit + integration)
4. **Document public APIs** thoroughly
5. **Consider backwards compatibility**

### Extension Checklist
- [ ] Design document approved
- [ ] Implementation complete
- [ ] Unit tests passing
- [ ] Integration tests added
- [ ] Documentation updated
- [ ] Performance benchmarked
- [ ] Code reviewed

---

## Notes for Future Developers

### Architecture Principles
1. **Async-first:** All IO-bound operations should be async
2. **Plugin-friendly:** Use abstract base classes and factories
3. **Configuration-driven:** Behavior controlled via config, not code
4. **Observable:** Structured logging for all operations

### Common Patterns
- Backend factory pattern in `backends/factory.py`
- Fallback chain in `backends/fallback.py`
- Progress callbacks in `orchestrator/pipeline.py`
- Configuration validation in `common/config.py`

### Testing Patterns
- Use `pytest-asyncio` for async tests
- Mock external APIs with `aioresponses`
- Use fixtures from `conftest.py`
- Mark slow tests with `@pytest.mark.slow`
