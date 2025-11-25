# Benchmarks Guide

**Version:** 1.0
**Last Updated:** 2024-11-25
**Status:** Sprint 2

---

## Table of Contents

- [Overview](#overview)
- [Running Benchmarks](#running-benchmarks)
- [Benchmark Categories](#benchmark-categories)
- [Interpreting Results](#interpreting-results)
- [Performance Baselines](#performance-baselines)
- [Configuration for Benchmarks](#configuration-for-benchmarks)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The docling-hybrid-ocr benchmark suite measures system performance across multiple dimensions:

- **Throughput**: Pages processed per minute
- **Memory Usage**: Peak and average memory consumption
- **Latency**: API response times and rendering speed
- **Concurrency**: Scaling with worker count
- **Resource Efficiency**: Memory-per-page ratios

### Why Benchmarks Matter

1. **Performance Tracking**: Detect regressions before they reach production
2. **Capacity Planning**: Understand resource requirements for workload sizing
3. **Optimization Targets**: Identify bottlenecks and improvement opportunities
4. **Configuration Tuning**: Find optimal settings for different scenarios

---

## Running Benchmarks

### Quick Start

Run all benchmarks:
```bash
pytest tests/benchmarks/ -v --benchmark
```

Run specific benchmark categories:
```bash
# Performance/throughput tests
pytest tests/benchmarks/test_performance.py -v --benchmark

# Memory profiling tests
pytest tests/benchmarks/test_memory.py -v --benchmark
```

Run with detailed output:
```bash
pytest tests/benchmarks/ -v --benchmark -s
```

### Selective Execution

Run only fast benchmarks (skip slow tests):
```bash
pytest tests/benchmarks/ -v --benchmark -m "not slow"
```

Run specific test:
```bash
pytest tests/benchmarks/test_performance.py::TestThroughputBenchmarks::test_pages_per_minute_10_pages -v
```

### Integration Tests

Run end-to-end integration tests:
```bash
pytest tests/integration/test_pipeline_e2e.py -v --integration
```

---

## Benchmark Categories

### 1. Throughput Benchmarks (`test_performance.py`)

**Purpose**: Measure pages processed per minute under various conditions.

**Key Tests**:
- `test_single_page_conversion_time`: Baseline single-page performance
- `test_pages_per_minute_10_pages`: Standard throughput measurement
- `test_pages_per_minute_50_pages`: Sustained throughput
- `test_realistic_api_latency_10_pages`: With realistic VLM API delays
- `test_concurrent_vs_sequential_speedup`: Concurrency benefits
- `test_scaling_with_worker_count`: Worker scaling efficiency

**Expected Results**:
```
Fast Mock Backend (10ms latency):
  Single page:     < 1.0s
  10 pages:        > 30 pages/min
  50 pages:        > 20 pages/min

Slow Mock Backend (500ms latency):
  10 pages:        10-20 pages/min (with 2-4 workers)
```

**What to Watch**:
- Throughput should increase with worker count (up to 4-8 workers)
- Diminishing returns beyond 8 workers
- Consistent performance across document sizes

### 2. Memory Benchmarks (`test_memory.py`)

**Purpose**: Profile memory usage and detect leaks.

**Key Tests**:
- `test_peak_memory_10_pages`: Baseline memory usage
- `test_peak_memory_50_pages`: Memory scaling
- `test_peak_memory_100_pages`: Stress test
- `test_memory_scaling_by_page_count`: Linear scaling verification
- `test_repeated_conversions_no_leak`: Memory leak detection
- `test_memory_with_concurrent_workers`: Concurrency memory cost

**Expected Results**:
```
Memory Usage (150 DPI):
  10 pages:   < 200 MB peak
  50 pages:   < 500 MB peak
  100 pages:  < 1024 MB peak

Per-page memory: 2-5 MB
```

**What to Watch**:
- Memory should scale roughly linearly with page count
- No significant growth across repeated conversions
- Peak memory should be predictable from page count

### 3. Rendering Benchmarks

**Purpose**: Measure PDF-to-PNG rendering performance.

**Key Tests**:
- `test_page_rendering_time`: Average rendering speed
- `test_dpi_impact_on_rendering`: DPI vs speed tradeoff

**Expected Results**:
```
Rendering Time (per page):
  72 DPI:   < 0.1s
  150 DPI:  < 0.3s
  200 DPI:  < 0.5s
  300 DPI:  < 1.0s
```

### 4. Latency Benchmarks

**Purpose**: Measure API call response times.

**Key Tests**:
- `test_backend_call_latency`: Single call latency distribution
- `test_concurrent_backend_calls`: Latency under load

**Expected Results**:
```
Mock Backend Latency:
  Average: 10-20ms
  P95:     < 50ms
  P99:     < 100ms

Real VLM APIs (typical):
  Average: 200-800ms
  P95:     1000-2000ms
```

### 5. End-to-End Integration (`test_pipeline_e2e.py`)

**Purpose**: Test complete conversion pipeline with realistic scenarios.

**Key Tests**:
- `test_complete_conversion_with_mocked_backend`: Full pipeline
- `test_conversion_with_options`: Option handling
- `test_partial_conversion_with_errors`: Error recovery
- `test_concurrent_page_processing`: Concurrency verification
- `test_multiple_documents_sequential`: Batch scenarios
- `test_large_batch_memory_efficiency`: Resource management

**What to Watch**:
- All pages processed successfully
- Error handling doesn't crash pipeline
- Memory doesn't accumulate across documents
- Proper resource cleanup

---

## Interpreting Results

### Performance Indicators

**Good Performance**:
- ✅ Throughput > 30 pages/min (with fast backend)
- ✅ Memory < 10 MB per page
- ✅ Speedup > 1.5x with 4 workers vs 1 worker
- ✅ No memory leaks (stable across iterations)

**Performance Issues**:
- ⚠️ Throughput < 20 pages/min
- ⚠️ Memory > 15 MB per page
- ⚠️ Speedup < 1.3x with 4 workers
- ⚠️ Memory growth > 50% across iterations

### Regression Detection

Compare results against baselines:

```bash
# Run benchmarks and save results
pytest tests/benchmarks/ --benchmark -v > benchmark_results.txt

# Compare with previous run
diff baseline_results.txt benchmark_results.txt
```

### Performance Regression Criteria

A performance regression occurs when:
1. Throughput decreases by > 20%
2. Memory increases by > 30%
3. Any test that previously passed now fails

---

## Performance Baselines

### Hardware: Standard Development Machine

**Specs**: 12GB RAM, 4 CPU cores, SSD

**Baseline Results** (as of Sprint 2):

```
Throughput:
  10 pages (fast mock):   35-45 pages/min
  50 pages (fast mock):   25-35 pages/min
  10 pages (realistic):   12-18 pages/min

Memory:
  10 pages:   150-180 MB peak
  50 pages:   400-450 MB peak
  100 pages:  750-850 MB peak

Rendering (150 DPI):
  Average:    0.2-0.3s per page

Concurrency Speedup:
  1 → 2 workers: 1.6-1.8x
  1 → 4 workers: 2.2-2.8x
  1 → 8 workers: 2.5-3.2x
```

### Hardware: Production Server

**Specs**: 32GB RAM, 16 CPU cores, NVMe SSD

**Expected Results** (estimated):

```
Throughput:
  10 pages:   50-70 pages/min
  50 pages:   40-60 pages/min

Memory:
  100 pages:  600-700 MB peak

Concurrency Speedup:
  1 → 8 workers:  4-6x
  1 → 16 workers: 5-8x
```

---

## Configuration for Benchmarks

### Benchmark Configuration

The benchmark suite uses optimized settings in `tests/benchmarks/conftest.py`:

```python
benchmark_config_dict = {
    "logging": {
        "level": "WARNING",  # Reduce logging overhead
    },
    "resources": {
        "max_workers": 4,
        "max_memory_mb": 4096,
        "page_render_dpi": 150,  # Balance quality/speed
        "http_timeout_s": 30,
        "http_retry_attempts": 2,
    },
}
```

### Test PDF Generation

Test PDFs are generated using ReportLab:
- `sample_pdf_1_page`: Single page, minimal content
- `sample_pdf_10_pages`: 10 pages, standard content
- `sample_pdf_50_pages`: 50 pages for stress testing
- `sample_pdf_100_pages`: 100 pages for memory testing

### Mock Backends

Two mock backends simulate different latencies:

**Fast Mock Backend** (10ms latency):
- Simulates optimized local processing
- Used for throughput and concurrency tests

**Slow Mock Backend** (500ms latency):
- Simulates realistic VLM API response times
- Used for realistic performance testing

---

## Continuous Integration

### Running in CI

Add to your CI pipeline:

```yaml
# .github/workflows/benchmarks.yml
name: Benchmarks

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run benchmarks
        run: |
          pytest tests/benchmarks/ -v --benchmark -m "not slow"
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark_results.txt
```

### Benchmark Thresholds

Set pass/fail thresholds in tests:

```python
# Fail if throughput too low
assert pages_per_minute > 30, f"Too slow: {pages_per_minute:.1f} pages/min"

# Fail if memory too high
assert peak_mb < 500, f"Memory too high: {peak_mb:.1f}MB"
```

---

## Troubleshooting

### Benchmark Tests Failing

**Issue**: Benchmark tests fail with timeout
**Cause**: Backend mocking not working correctly
**Solution**:
```bash
# Check that aioresponses is installed
pip install aioresponses

# Run with verbose output
pytest tests/benchmarks/ -v -s
```

**Issue**: Memory tests report incorrect values
**Cause**: Garbage collection not running
**Solution**: Tests already include `gc.collect()` calls. If issues persist:
```python
import gc
gc.collect()
gc.collect()  # Call twice to be sure
```

**Issue**: Inconsistent throughput measurements
**Cause**: Background processes or CPU throttling
**Solution**:
- Close unnecessary applications
- Run benchmarks when system is idle
- Use dedicated benchmark hardware
- Run multiple times and take average

### Performance Optimization

If benchmarks reveal poor performance:

1. **Low Throughput**:
   - Increase `max_workers` in config
   - Check backend API latency
   - Verify network connectivity
   - Consider local inference backend

2. **High Memory Usage**:
   - Reduce `page_render_dpi`
   - Decrease `max_workers` (less concurrent pages in memory)
   - Use `max_pages` to process in batches
   - Check for memory leaks in custom code

3. **Poor Concurrency Scaling**:
   - Verify backend is async-capable
   - Check for synchronous bottlenecks
   - Profile with async profiler
   - Consider connection pooling

### Profiling Tools

**Memory Profiling**:
```bash
# Use memory_profiler
pip install memory-profiler
python -m memory_profiler tests/benchmarks/test_memory.py
```

**CPU Profiling**:
```bash
# Use cProfile
python -m cProfile -o profile.stats -m pytest tests/benchmarks/test_performance.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

**Async Profiling**:
```bash
# Use py-spy
pip install py-spy
py-spy record -o profile.svg -- pytest tests/benchmarks/
```

---

## Best Practices

### When to Run Benchmarks

1. **Before Merging PRs**: Run quick benchmarks to catch regressions
2. **Weekly/Nightly**: Full benchmark suite on main branch
3. **Before Releases**: Complete performance validation
4. **After Infrastructure Changes**: Verify performance on new hardware

### Benchmark Hygiene

1. **Consistent Environment**:
   - Use same hardware for comparisons
   - Close background applications
   - Ensure adequate cooling (avoid thermal throttling)

2. **Multiple Runs**:
   - Run benchmarks 3-5 times
   - Discard outliers
   - Report median or mean

3. **Document Changes**:
   - Note any config changes
   - Record hardware specs
   - Track baseline evolution

### Adding New Benchmarks

When adding new benchmarks:

1. Use `@pytest.mark.benchmark` decorator
2. Add to appropriate test class
3. Include clear assertions with thresholds
4. Print human-readable results
5. Document in this guide

Example:
```python
@pytest.mark.benchmark
async def test_new_feature_performance(benchmark_pipeline, sample_pdf_10_pages):
    """Test performance of new feature X."""
    start = time.time()
    result = await benchmark_pipeline.convert_pdf(
        sample_pdf_10_pages,
        options=ConversionOptions(enable_feature_x=True)
    )
    elapsed = time.time() - start

    print(f"\n  Feature X performance: {elapsed:.2f}s")
    assert elapsed < 5.0, f"Feature X too slow: {elapsed:.2f}s"
```

---

## Future Enhancements

**Planned for Sprint 3+**:

- [ ] Historical benchmark tracking
- [ ] Automated regression detection
- [ ] Performance dashboard
- [ ] GPU benchmark suite (for local inference)
- [ ] Network bandwidth impact tests
- [ ] Comparison with alternative OCR systems

---

## References

- **Test Files**:
  - `tests/benchmarks/test_performance.py` - Throughput benchmarks
  - `tests/benchmarks/test_memory.py` - Memory profiling
  - `tests/benchmarks/conftest.py` - Fixtures and configuration
  - `tests/integration/test_pipeline_e2e.py` - End-to-end tests

- **Related Documentation**:
  - `docs/ARCHITECTURE.md` - System architecture
  - `docs/TROUBLESHOOTING.md` - General troubleshooting
  - `CLAUDE.md` - Development guide

---

*Document Version: 1.0*
*Created: 2024-11-25 (Sprint 2)*
*Author: Dev-07 (QA/Test Engineer)*
