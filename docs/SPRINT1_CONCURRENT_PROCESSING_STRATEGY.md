# Sprint 1 Concurrent Processing Strategy

**Author:** D01 (Tech Lead)
**Date:** 2025-11-25
**Sprint:** Sprint 1 - Hardening & Testing
**Task:** S1-D03-01 (Pipeline Lead)
**Version:** 1.0

## Executive Summary

This document defines the concurrent processing strategy for the Docling Hybrid OCR pipeline. The goal is to move from sequential page processing to concurrent processing, improving throughput by 5-10x while maintaining correctness and resource constraints.

**Current State:** Sequential processing (1 page at a time)
**Target State:** Concurrent processing with configurable parallelism
**Expected Improvement:** 5-10x throughput on multi-page documents
**Resource Safety:** Semaphore-based concurrency limits

---

## 1. Problem Statement

### 1.1 Current Implementation

The current pipeline processes pages sequentially:

```python
# Current implementation in orchestrator/pipeline.py
async def convert_pdf(self, pdf_path: Path, ...) -> ConversionResult:
    # ...
    page_results = []
    for page_index in pages_to_process:
        result = await self._process_page(pdf_path, page_index, doc_id, options)
        page_results.append(result)
    # ...
```

**Performance Impact:**
- 10-page PDF with 3s per page = 30 seconds total
- No parallelism despite async code
- Underutilizes available resources

### 1.2 Performance Analysis

**Baseline Measurements (Estimated):**
```
Single Page:
├── PDF Rendering: 200ms
├── API Call: 2,500ms  (network + VLM processing)
└── Parsing: 50ms
TOTAL: ~2,750ms per page

10-Page Document (Sequential):
└── 10 × 2,750ms = 27,500ms = 27.5 seconds

10-Page Document (Concurrent, 4 workers):
└── ceil(10 / 4) × 2,750ms = 3 × 2,750ms = 8,250ms = 8.3 seconds
    Speedup: 3.3x
```

**Bottleneck:** API calls dominate processing time, making concurrency highly effective.

---

## 2. Design Goals

### 2.1 Functional Goals

1. **Correctness:** Maintain exact page order in output
2. **Parallelism:** Process multiple pages concurrently
3. **Resource Safety:** Respect memory and worker limits
4. **Error Isolation:** One page failure doesn't stop others
5. **Progress Tracking:** Report progress during conversion

### 2.2 Non-Functional Goals

1. **Performance:** 5-10x throughput improvement
2. **Scalability:** Handle 1 to 1000 pages efficiently
3. **Resource Awareness:** Work within 12GB RAM constraints
4. **Configurability:** Easy to tune for different environments
5. **Maintainability:** Clear, readable async code

### 2.3 Constraints

1. **Memory:** Max 4GB for page processing (configurable)
2. **Workers:** Default 2 (local), up to 8 (production)
3. **API Limits:** Respect rate limits (handled by retry logic)
4. **Page Order:** Must maintain original page sequence

---

## 3. Architectural Approach

### 3.1 Concurrency Model

**Choice:** `asyncio.gather()` with semaphore-based limiting

**Rationale:**
- ✅ Built into Python stdlib (no new dependencies)
- ✅ Works naturally with async/await
- ✅ Efficient resource usage (event loop)
- ✅ Clean exception handling with `return_exceptions=True`
- ✅ Semaphore provides backpressure

**Alternatives Considered:**
- ❌ Threading: GIL limits effectiveness, more complex
- ❌ Multiprocessing: High overhead, serialization issues
- ❌ asyncio.Queue: More complex, no clear benefit

### 3.2 Resource Control

**Semaphore Pattern:**
```python
semaphore = asyncio.Semaphore(max_workers)

async def process_with_limit(page_index):
    async with semaphore:
        return await self._process_page(page_index, ...)

tasks = [process_with_limit(i) for i in page_indices]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Why Semaphore:**
- Limits concurrent operations to `max_workers`
- Prevents memory exhaustion
- Provides automatic queuing
- Thread-safe in asyncio

### 3.3 Exception Handling

**Strategy:** `return_exceptions=True` in `gather()`

```python
results = await asyncio.gather(*tasks, return_exceptions=True)

for idx, result in enumerate(results):
    if isinstance(result, Exception):
        # Handle error, log, create error placeholder
        logger.error("page_failed", page=idx, error=str(result))
        page_results.append(create_error_page_result(idx, result))
    else:
        page_results.append(result)
```

**Benefits:**
- One page failure doesn't cancel other pages
- All pages are attempted
- Errors are logged with context
- User gets partial results

---

## 4. Implementation Design

### 4.1 Modified Pipeline Architecture

```python
class HybridPipeline:
    async def convert_pdf(self, pdf_path: Path, ...) -> ConversionResult:
        # 1. Setup
        doc_id = generate_doc_id()
        page_indices = self._get_pages_to_process(...)
        max_workers = options.max_workers or self.config.resources.max_workers

        # 2. Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_workers)

        # 3. Create tasks with semaphore wrapper
        async def process_with_limit(page_index: int) -> PageResult:
            async with semaphore:
                return await self._process_page(
                    pdf_path, page_index, doc_id, options
                )

        # 4. Create all tasks
        tasks = [process_with_limit(idx) for idx in page_indices]

        # 5. Execute concurrently with exception isolation
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 6. Process results (maintain order, handle errors)
        page_results = self._process_results(results, page_indices, options)

        # 7. Continue with concatenation, output writing, etc.
        # ...
```

### 4.2 Helper Methods

#### 4.2.1 Process Results

```python
def _process_results(
    self,
    results: list[PageResult | Exception],
    page_indices: list[int],
    options: ConversionOptions,
) -> list[PageResult]:
    """Process gather results, handle errors, maintain order.

    Args:
        results: Results from asyncio.gather (may include exceptions)
        page_indices: Original page indices (for ordering)
        options: Conversion options (error handling strategy)

    Returns:
        List of PageResult objects in correct order
    """
    page_results = []

    for idx, (page_index, result) in enumerate(zip(page_indices, results)):
        page_num = page_index + 1

        if isinstance(result, Exception):
            # Handle error based on options.on_page_error
            if options.on_page_error == "raise":
                # Re-raise first error encountered
                raise result
            elif options.on_page_error == "placeholder":
                page_results.append(PageResult(
                    page_index=page_index,
                    page_num=page_num,
                    content=f"<!-- ERROR: Page {page_num} failed: {result} -->",
                    status="error",
                    error=str(result),
                ))
            else:  # "skip"
                logger.warning("page_skipped", page=page_num, error=str(result))
                # Don't append anything (skip this page)
        else:
            # Success - add result
            page_results.append(result)

    return page_results
```

#### 4.2.2 Get Pages to Process

```python
def _get_pages_to_process(
    self,
    total_pages: int,
    options: ConversionOptions,
) -> list[int]:
    """Determine which pages to process based on options.

    Args:
        total_pages: Total pages in PDF
        options: Conversion options (start_page, max_pages)

    Returns:
        List of 0-indexed page indices to process
    """
    start = options.start_page
    end = total_pages

    if options.max_pages is not None:
        end = min(start + options.max_pages, total_pages)

    if start >= total_pages:
        raise ValidationError(
            f"start_page ({start}) >= total_pages ({total_pages})"
        )

    return list(range(start, end))
```

### 4.3 Configuration

**Add to ConversionOptions:**
```python
@dataclass
class ConversionOptions:
    max_pages: int | None = None
    start_page: int = 0
    dpi: int = 200
    backend_name: str | None = None
    include_page_separators: bool = True
    on_page_error: Literal["skip", "raise", "placeholder"] = "skip"
    max_workers: int | None = None  # NEW: Override config max_workers
```

**Add to ResourcesConfig:**
```python
class ResourcesConfig(BaseModel):
    max_workers: int = Field(default=8, ge=1, le=64)
    max_memory_mb: int = Field(default=16384, ge=512)
    page_render_dpi: int = Field(default=200, ge=72, le=600)
    http_timeout_s: int = Field(default=120, ge=10, le=600)
    http_retry_attempts: int = Field(default=3, ge=1, le=10)
    # NEW: Concurrency control
    enable_concurrent_processing: bool = Field(default=True)
```

---

## 5. Memory Management

### 5.1 Memory Considerations

**Per-Page Memory Usage (Estimated):**
```
DPI 150:
├── PDF Page Object: ~10MB (in pypdfium2)
├── PNG Image: ~300KB
├── Base64 Encoded: ~400KB
├── API Response: ~50KB
├── Processing Overhead: ~20MB
└── TOTAL per page: ~30MB

With 4 concurrent workers:
└── 4 × 30MB = 120MB

With 8 concurrent workers:
└── 8 × 30MB = 240MB
```

**Safety Margin:**
- Local dev (12GB total, 4GB available): Use 2 workers
- Production (32GB total, 16GB available): Use 8 workers

### 5.2 Memory Safety Strategy

**Approach 1: Semaphore (Chosen)**
- Limit concurrent tasks to `max_workers`
- Each task holds memory only during its execution
- Automatic cleanup when task completes
- Simple, effective

**Approach 2: Batch Processing (Future)**
```python
# Process in batches of max_workers
for batch_start in range(0, len(pages), max_workers):
    batch = pages[batch_start:batch_start + max_workers]
    results = await asyncio.gather(*[process(p) for p in batch])
```

**Recommendation:** Start with Approach 1 (semaphore), add Approach 2 if needed.

---

## 6. Progress Tracking

### 6.1 Progress Callback Design

**Interface:**
```python
from typing import Protocol

class ProgressCallback(Protocol):
    """Callback for progress updates."""

    def __call__(
        self,
        current: int,
        total: int,
        page_num: int | None = None,
        status: str = "processing",
    ) -> None:
        """Report progress.

        Args:
            current: Current page count (0-indexed)
            total: Total pages to process
            page_num: Current page number (1-indexed, optional)
            status: Status message (e.g., "processing", "completed")
        """
        ...
```

**Usage in Pipeline:**
```python
async def convert_pdf(
    self,
    pdf_path: Path,
    output_path: Path | None = None,
    options: ConversionOptions | None = None,
    progress_callback: ProgressCallback | None = None,
) -> ConversionResult:
    # ...

    # Report progress as pages complete
    completed = 0
    for idx, result in enumerate(results):
        completed += 1
        if progress_callback:
            progress_callback(
                current=completed,
                total=len(page_indices),
                page_num=page_indices[idx] + 1,
                status="completed" if not isinstance(result, Exception) else "error",
            )
```

**CLI Integration:**
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Converting...", total=total_pages)

    def update_progress(current, total, page_num=None, status="processing"):
        progress.update(task, completed=current)

    result = await pipeline.convert_pdf(
        pdf_path,
        progress_callback=update_progress,
    )
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Test Cases:**
```python
@pytest.mark.asyncio
async def test_concurrent_processing_maintains_order():
    """Verify pages are returned in correct order despite concurrency."""
    # Mock slow pages (page 2 takes longest)
    # Verify results are [page1, page2, page3] not [page1, page3, page2]

@pytest.mark.asyncio
async def test_concurrent_processing_respects_max_workers():
    """Verify no more than max_workers pages process simultaneously."""
    # Track concurrent calls
    # Verify never exceeds max_workers

@pytest.mark.asyncio
async def test_concurrent_processing_handles_page_error():
    """Verify one page error doesn't stop others."""
    # Make page 2 fail
    # Verify pages 1 and 3 still succeed

@pytest.mark.asyncio
async def test_concurrent_processing_with_small_doc():
    """Verify works correctly with pages < max_workers."""
    # 2 pages with 8 workers
    # Should work fine

@pytest.mark.asyncio
async def test_concurrent_processing_with_large_doc():
    """Verify works correctly with pages >> max_workers."""
    # 100 pages with 4 workers
    # Should complete in ~25 batches
```

### 7.2 Integration Tests

**Test Cases:**
```python
@pytest.mark.integration
async def test_e2e_concurrent_conversion():
    """End-to-end test with mocked backend."""
    # Use aioresponses to mock HTTP
    # Convert 10-page PDF
    # Verify correct result

@pytest.mark.integration
async def test_concurrent_memory_usage():
    """Verify memory doesn't exceed limits."""
    # Use memory_profiler
    # Convert 50-page PDF
    # Verify peak memory < max_memory_mb
```

### 7.3 Performance Tests

**Benchmarks:**
```python
@pytest.mark.benchmark
async def test_concurrent_vs_sequential_speedup():
    """Measure speedup from concurrency."""
    # Run same PDF sequentially and concurrently
    # Measure time difference
    # Assert speedup > 2x for 10-page doc with 4 workers
```

---

## 8. Rollout Plan

### 8.1 Implementation Phases

**Phase 1: Core Implementation (Days 1-2)**
1. Add semaphore-based concurrency to pipeline.py
2. Modify convert_pdf() to use asyncio.gather()
3. Add _process_results() helper
4. Add unit tests

**Phase 2: Configuration (Day 2)**
1. Add max_workers to ConversionOptions
2. Add enable_concurrent_processing to ResourcesConfig
3. Update config files (local.toml, default.toml)
4. Add configuration tests

**Phase 3: Progress Tracking (Day 3)**
1. Add ProgressCallback protocol
2. Integrate into convert_pdf()
3. Update CLI to use progress bar
4. Add progress tests

**Phase 4: Testing & Validation (Day 4)**
1. Run integration tests
2. Performance benchmarking
3. Memory profiling
4. Bug fixes

### 8.2 Feature Flag

**Configuration:**
```toml
[resources]
enable_concurrent_processing = true  # Can disable if issues found
max_workers = 4
```

**Fallback:**
If `enable_concurrent_processing = false`, use original sequential logic.

```python
if self.config.resources.enable_concurrent_processing:
    # Use new concurrent implementation
    results = await self._convert_concurrent(...)
else:
    # Use old sequential implementation (preserved for safety)
    results = await self._convert_sequential(...)
```

### 8.3 Monitoring

**Metrics to Track:**
```python
logger.info(
    "conversion_complete",
    doc_id=doc_id,
    total_pages=len(page_results),
    concurrent_enabled=self.config.resources.enable_concurrent_processing,
    max_workers=max_workers,
    duration_seconds=duration,
    pages_per_second=len(page_results) / duration,
)
```

---

## 9. Edge Cases

### 9.1 Single Page Document

**Scenario:** 1-page PDF with max_workers=8

**Behavior:**
- Only 1 task created
- Semaphore doesn't matter
- No concurrency overhead
- Works correctly

**Test:**
```python
async def test_concurrent_single_page():
    result = await pipeline.convert_pdf(single_page_pdf, max_workers=8)
    assert len(result.page_results) == 1
```

### 9.2 Workers > Pages

**Scenario:** 3-page PDF with max_workers=8

**Behavior:**
- 3 tasks created
- All run immediately (semaphore allows all)
- Maximum parallelism achieved
- Works correctly

### 9.3 All Pages Fail

**Scenario:** All pages throw exceptions

**Behavior:**
- All results are exceptions
- _process_results() handles based on options.on_page_error
- If "skip": Returns empty page_results
- If "placeholder": Returns error placeholders
- If "raise": Raises first exception

**Test:**
```python
async def test_concurrent_all_pages_fail():
    # Mock backend to always fail
    with pytest.raises(BackendError):
        await pipeline.convert_pdf(pdf, options=ConversionOptions(on_page_error="raise"))
```

### 9.4 Memory Exhaustion

**Scenario:** max_workers too high, system runs out of memory

**Behavior:**
- Semaphore prevents too many concurrent tasks
- If memory exhaustion still occurs:
  - Reduce max_workers in config
  - Reduce DPI (smaller images)
  - Use max_pages to process fewer pages

**Prevention:**
```python
# In config validation
@field_validator("max_workers")
@classmethod
def validate_max_workers(cls, v: int, info: ValidationInfo) -> int:
    max_memory_mb = info.data.get("max_memory_mb", 16384)
    # Rough estimate: 30MB per worker
    max_safe_workers = max_memory_mb // 30
    if v > max_safe_workers:
        logger.warning(
            "max_workers_high",
            requested=v,
            safe_max=max_safe_workers,
            max_memory_mb=max_memory_mb,
        )
    return v
```

---

## 10. Performance Projections

### 10.1 Expected Speedup

**Model:**
```
Speedup = min(num_pages, max_workers) / ceil(num_pages / max_workers)

Examples:
- 10 pages, 4 workers: 4 / ceil(10/4) = 4 / 3 = 1.33x
- 10 pages, 2 workers: 2 / ceil(10/2) = 2 / 5 = 0.4x (no, wait...)

Correct formula:
Sequential time: num_pages × time_per_page
Concurrent time: ceil(num_pages / max_workers) × time_per_page
Speedup = num_pages / ceil(num_pages / max_workers)

Examples:
- 10 pages, 4 workers: 10 / ceil(2.5) = 10 / 3 = 3.33x
- 10 pages, 2 workers: 10 / ceil(5) = 10 / 5 = 2.0x
- 100 pages, 8 workers: 100 / ceil(12.5) = 100 / 13 = 7.69x
```

### 10.2 Real-World Expectations

**Factors Reducing Speedup:**
- API rate limiting (may serialize some requests)
- Network variability
- System overhead
- Memory pressure

**Conservative Estimates:**
- 2 workers: 1.5-1.8x speedup (vs 2.0x theoretical)
- 4 workers: 2.5-3.0x speedup (vs 3.3x theoretical)
- 8 workers: 4.0-6.0x speedup (vs 7.7x theoretical)

**Measurement:**
Track actual speedups in production and adjust expectations.

---

## 11. Risks and Mitigation

### 11.1 Risk: Increased Memory Usage

**Impact:** HIGH
**Probability:** MEDIUM

**Mitigation:**
1. Use semaphore to limit concurrent tasks
2. Default to conservative max_workers (2 for local, 4 for prod)
3. Add memory monitoring and alerting
4. Provide clear error messages if OOM occurs
5. Document memory requirements in docs

### 11.2 Risk: API Rate Limiting

**Impact:** MEDIUM
**Probability:** MEDIUM

**Mitigation:**
1. Implement retry logic with exponential backoff (S1-D02-01)
2. Respect Retry-After headers
3. Add rate limit detection (429 status codes)
4. Consider adaptive max_workers based on rate limits
5. Document rate limits in docs

### 11.3 Risk: Increased Complexity

**Impact:** MEDIUM
**Probability:** LOW

**Mitigation:**
1. Keep implementation simple (asyncio.gather + semaphore)
2. Comprehensive unit tests
3. Clear documentation
4. Feature flag to disable if needed
5. Code review by D01 and D03

### 11.4 Risk: Ordering Issues

**Impact:** HIGH
**Probability:** LOW

**Mitigation:**
1. Maintain page_indices list for correct ordering
2. Process results in same order as page_indices
3. Comprehensive tests for ordering
4. Use enumerate() to track indices

---

## 12. Success Criteria

### 12.1 Functional

- ✅ All pages processed correctly
- ✅ Page order maintained in output
- ✅ Error handling works per configuration
- ✅ Works with 1 to 1000 page documents
- ✅ Feature flag allows disabling

### 12.2 Performance

- ✅ 2-worker setup: >1.5x speedup on 10-page doc
- ✅ 4-worker setup: >2.5x speedup on 10-page doc
- ✅ 8-worker setup: >4.0x speedup on 50-page doc
- ✅ Memory usage within configured limits

### 12.3 Quality

- ✅ Unit tests pass with >95% coverage
- ✅ Integration tests pass
- ✅ No flaky tests
- ✅ Performance tests show expected speedup
- ✅ Code review approved

---

## 13. Implementation Checklist

### 13.1 Code Changes

- [ ] Modify `orchestrator/pipeline.py`:
  - [ ] Add semaphore creation
  - [ ] Change to asyncio.gather()
  - [ ] Add _process_results() helper
  - [ ] Add progress callback support
- [ ] Modify `orchestrator/models.py`:
  - [ ] Add max_workers to ConversionOptions
- [ ] Modify `common/config.py`:
  - [ ] Add enable_concurrent_processing to ResourcesConfig
- [ ] Update `configs/local.toml`:
  - [ ] Set max_workers = 2
  - [ ] Set enable_concurrent_processing = true
- [ ] Update `configs/default.toml`:
  - [ ] Set max_workers = 4 (conservative)
  - [ ] Set enable_concurrent_processing = true

### 13.2 Tests

- [ ] Unit tests:
  - [ ] test_concurrent_processing_maintains_order
  - [ ] test_concurrent_processing_respects_max_workers
  - [ ] test_concurrent_processing_handles_page_error
  - [ ] test_concurrent_processing_single_page
  - [ ] test_concurrent_processing_workers_gt_pages
- [ ] Integration tests:
  - [ ] test_e2e_concurrent_conversion
  - [ ] test_concurrent_memory_usage
- [ ] Performance tests:
  - [ ] test_concurrent_speedup_measurement

### 13.3 Documentation

- [ ] Update CLAUDE.md with concurrent processing info
- [ ] Update LOCAL_DEV.md with max_workers guidance
- [ ] Add docstrings to new methods
- [ ] Update ARCHITECTURE.md diagram

---

## 14. Conclusion

This concurrent processing strategy provides:

1. **Significant Performance Improvement:** 2-7x speedup
2. **Resource Safety:** Semaphore-based limits
3. **Correctness:** Maintains page order, error isolation
4. **Configurability:** Easy to tune for different environments
5. **Testability:** Clear test strategy

**Implementation Estimate:** 4 days
**Owner:** D03 (Pipeline Lead)
**Task ID:** S1-D03-01

**Status:** ✅ Ready for implementation

---

**Document Status:** ✅ Complete
**Owner:** D01 (Tech Lead)
**Reviewed By:** D03 (Pipeline Lead)
**Next Review:** Day 4 of implementation
