# Sprint 2 Plan: Backend Expansion & Production Readiness

**Sprint:** Sprint 2
**Duration:** 2 Weeks (Weeks 5-6)
**Start Date:** After Sprint 1 Completion
**Status:** PLANNING

---

## Sprint Goals

1. **Implement DeepSeek vLLM Backend** - First local backend option
2. **Add Performance Testing** - Benchmarks and profiling
3. **Production Hardening** - Docker, health checks, monitoring
4. **CLI Enhancements** - Better UX, progress hooks
5. **Documentation Polish** - User guides, API docs

---

## Task Breakdown

### P0 Tasks (Critical) - Must Complete

#### S2-T01: DeepSeek vLLM Backend Implementation
**Owner:** Dev-02 (Backend Developer)
**Estimate:** 4-5 days
**Dependencies:** None

**Description:**
Implement the DeepSeek vLLM backend for local GPU inference.

**Deliverables:**
- `backends/deepseek_vllm.py` - Full implementation
- Support for DeepSeek-VL-7B model
- Async HTTP client to local vLLM server
- Proper error handling (connection, timeout)
- Unit tests
- Integration tests (mocked)

**Acceptance Criteria:**
- [ ] Backend passes all interface tests
- [ ] Handles vLLM-specific response format
- [ ] Supports configurable base_url
- [ ] Retry logic works correctly
- [ ] Documentation complete

---

#### S2-T02: Backend Fallback Chain
**Owner:** Dev-02 (Backend Developer)
**Estimate:** 2 days
**Dependencies:** S2-T01

**Description:**
Implement fallback mechanism when primary backend fails.

**Deliverables:**
- Fallback configuration in TOML
- Automatic retry on different backend
- Logging of fallback events
- Unit tests

**Configuration Example:**
```toml
[backends]
default = "deepseek-vllm"
fallback = ["nemotron-openrouter"]
max_fallback_attempts = 2
```

---

#### S2-T03: Pipeline Progress Hooks
**Owner:** Dev-03 (Pipeline Developer)
**Estimate:** 2 days
**Dependencies:** None

**Description:**
Add progress callback system for real-time status updates.

**Deliverables:**
- ProgressCallback protocol
- Per-page progress events
- CLI integration with real progress
- Unit tests

**API:**
```python
async def convert_pdf(
    pdf_path: Path,
    progress_callback: ProgressCallback | None = None,
) -> ConversionResult:
    ...

# Progress callback receives:
# - page_started(page_num, total)
# - page_completed(page_num, total, result)
# - conversion_completed(result)
```

---

### P1 Tasks (Important) - Should Complete

#### S2-T04: Performance Benchmarking Suite
**Owner:** Dev-07 (QA/Test)
**Estimate:** 3 days
**Dependencies:** S2-T01

**Description:**
Create comprehensive performance benchmarks.

**Deliverables:**
- `tests/benchmarks/` directory
- Memory profiling tests
- Throughput benchmarks (pages/minute)
- API latency measurements
- Benchmark results documentation

**Metrics to Track:**
- Pages per minute (single/concurrent)
- Memory usage (peak, average)
- API latency (p50, p95, p99)
- Image encoding time
- Total conversion time

---

#### S2-T05: Docker Setup
**Owner:** Dev-04 (DevOps)
**Estimate:** 2 days
**Dependencies:** None

**Description:**
Create Docker configuration for deployment.

**Deliverables:**
- `Dockerfile` - Multi-stage build
- `docker-compose.yml` - Development setup
- `.dockerignore`
- Documentation for Docker usage

**Requirements:**
- Python 3.11+ base image
- Minimal image size (<500MB)
- Environment variable configuration
- Volume mounts for config/output

---

#### S2-T06: Health Check Endpoint
**Owner:** Dev-04 (DevOps)
**Estimate:** 1 day
**Dependencies:** None

**Description:**
Add health check for deployment monitoring.

**Deliverables:**
- `/health` endpoint (if adding HTTP server)
- Or CLI `health` command
- Backend connectivity check
- Configuration validation

---

#### S2-T07: CLI Batch Processing
**Owner:** Dev-06 (CLI)
**Estimate:** 2 days
**Dependencies:** S2-T03

**Description:**
Add batch conversion of multiple PDFs.

**Deliverables:**
- `convert-batch` CLI command
- Directory scanning
- Parallel file processing
- Summary report

**Usage:**
```bash
docling-hybrid-ocr convert-batch ./pdfs/ --output-dir ./output/
docling-hybrid-ocr convert-batch ./pdfs/*.pdf --parallel 4
```

---

### P2 Tasks (Nice to Have) - If Time Permits

#### S2-T08: API Documentation Generation
**Owner:** Dev-08 (Docs)
**Estimate:** 2 days
**Dependencies:** None

**Description:**
Generate comprehensive API documentation.

**Deliverables:**
- pdoc/mkdocs configuration
- Auto-generated API reference
- Usage examples in docs
- Published to docs site (optional)

---

#### S2-T09: Telemetry/Metrics Collection
**Owner:** Dev-04 (DevOps)
**Estimate:** 2 days
**Dependencies:** S2-T04

**Description:**
Add optional telemetry for monitoring.

**Deliverables:**
- Metrics collection (Prometheus format)
- Conversion success/failure rates
- Backend usage statistics
- Opt-in configuration

---

#### S2-T10: Configuration Validation Tool
**Owner:** Dev-04 (DevOps)
**Estimate:** 1 day
**Dependencies:** None

**Description:**
CLI tool to validate configuration files.

**Deliverables:**
- `validate-config` CLI command
- Schema validation
- Connection testing
- Clear error messages

**Usage:**
```bash
docling-hybrid-ocr validate-config --config configs/local.toml
```

---

## Sprint 2 Timeline

```
Week 5:
┌─────────────────────────────────────────────────────────────┐
│ Day 1-2  │ Day 3-4  │ Day 5    │ Day 6-7  │ Day 8-9      │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ S2-T01   │ S2-T01   │ S2-T01   │ S2-T01   │ S2-T02       │
│ vLLM     │ vLLM     │ vLLM     │ vLLM     │ Fallback     │
│ Backend  │ Backend  │ Backend  │ Backend  │ Chain        │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ S2-T05   │ S2-T05   │ S2-T06   │ S2-T03   │ S2-T03       │
│ Docker   │ Docker   │ Health   │ Progress │ Progress     │
│ Setup    │ Setup    │ Check    │ Hooks    │ Hooks        │
└─────────────────────────────────────────────────────────────┘

Week 6:
┌─────────────────────────────────────────────────────────────┐
│ Day 1-2  │ Day 3-4  │ Day 5    │ Day 6-7  │ Day 8-9      │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ S2-T02   │ S2-T04   │ S2-T04   │ S2-T04   │ Integration  │
│ Fallback │ Bench-   │ Bench-   │ Bench-   │ Testing      │
│          │ marks    │ marks    │ marks    │              │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ S2-T07   │ S2-T07   │ S2-T08   │ S2-T08   │ Sprint       │
│ Batch    │ Batch    │ API      │ API      │ Review       │
│ Process  │ Process  │ Docs     │ Docs     │              │
└─────────────────────────────────────────────────────────────┘
```

---

## Developer Assignments

### Required Developers: 4-5

| Role | ID | Responsibilities | Time |
|------|-----|-----------------|------|
| **Backend Dev** | Dev-02 | S2-T01 (vLLM), S2-T02 (Fallback) | 100% |
| **Pipeline Dev** | Dev-03 | S2-T03 (Progress Hooks) | 50% |
| **DevOps** | Dev-04 | S2-T05 (Docker), S2-T06 (Health), S2-T09 (Telemetry), S2-T10 (Config) | 100% |
| **CLI Dev** | Dev-06 | S2-T07 (Batch Processing) | 50% |
| **QA/Test** | Dev-07 | S2-T04 (Benchmarks), Integration Testing | 75% |
| **Docs** | Dev-08 | S2-T08 (API Docs) | 25% |

### Developer Breakdown

**Full-time (100%):** 2 developers
- Dev-02: Backend implementation
- Dev-04: DevOps/Infrastructure

**Part-time (50-75%):** 3 developers
- Dev-03: Pipeline enhancements (50%)
- Dev-06: CLI enhancements (50%)
- Dev-07: Testing (75%)

**Minimal (25%):** 1 developer
- Dev-08: Documentation (25%)

**Total FTE:** ~4 FTE

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| vLLM API compatibility issues | Medium | High | Early testing with real vLLM server |
| Docker image size bloat | Low | Medium | Multi-stage builds, minimal deps |
| Performance regression | Low | High | Benchmark baseline before changes |
| Fallback chain complexity | Medium | Medium | Clear logging, simple config |

---

## Success Criteria

### Sprint 2 Definition of Done

1. **DeepSeek vLLM Backend**
   - [ ] All interface methods implemented
   - [ ] Unit tests pass (>90% coverage)
   - [ ] Integration tests with mocked vLLM
   - [ ] Documentation complete

2. **Fallback Chain**
   - [ ] Configuration working
   - [ ] Automatic fallback tested
   - [ ] Logging verified

3. **Progress Hooks**
   - [ ] Callback protocol defined
   - [ ] CLI shows real progress
   - [ ] Tests pass

4. **Docker**
   - [ ] Builds successfully
   - [ ] docker-compose works
   - [ ] Image size <500MB

5. **Benchmarks**
   - [ ] Benchmark suite created
   - [ ] Baseline results documented
   - [ ] CI integration (optional)

---

## Dependencies

### External Dependencies
- vLLM server (for real integration testing)
- Docker runtime
- GPU access (optional, for local testing)

### Internal Dependencies
- Sprint 1 completion ✅
- Backend interface stable ✅
- Test infrastructure ready ✅

---

## Sprint 2 Kickoff Checklist

- [ ] All Sprint 1 tasks verified complete
- [ ] Developer assignments confirmed
- [ ] vLLM test environment available
- [ ] Docker environment ready
- [ ] Benchmark baseline captured

---

*Document Version: 1.0*
*Created: 2024-11-25*
