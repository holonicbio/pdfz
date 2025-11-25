# Sprint 1 Test Coverage Requirements

**Author:** D01 (Tech Lead)
**Date:** 2025-11-25
**Sprint:** Sprint 1 - Hardening & Testing
**Version:** 1.0

## Executive Summary

This document defines the test coverage requirements for Sprint 1 and establishes the testing standards for the Docling Hybrid OCR project. The primary goal is to achieve **>85% test coverage** on all Sprint 1 deliverables while establishing a robust testing infrastructure for future development.

**Key Objectives:**
1. Establish comprehensive test infrastructure
2. Achieve >85% coverage on modified code
3. Create mocked integration tests for all backends
4. Ensure all critical paths have test coverage
5. Document testing patterns for future sprints

---

## 1. Overall Coverage Targets

### 1.1 Sprint 1 Targets

| Category | Target | Measurement |
|----------|--------|-------------|
| **Overall Project** | >80% | Lines covered / total lines |
| **Modified Code** | >85% | Lines in changed files |
| **New Code** | >90% | Lines in new files |
| **Critical Paths** | 100% | Core conversion flow |
| **Error Paths** | >75% | Exception handling |

### 1.2 Module-Specific Targets

| Module | Target Coverage | Priority | Notes |
|--------|----------------|----------|-------|
| `common/` | >90% | P0 | Foundation - must be rock solid |
| `backends/` | >85% | P0 | Critical for functionality |
| `renderer/` | >85% | P0 | Critical for functionality |
| `orchestrator/` | >85% | P0 | Core pipeline |
| `cli/` | >70% | P1 | User-facing, harder to test |
| `blocks/` | >60% | P2 | Stub for Phase 2 |
| `eval/` | >60% | P2 | Stub for Phase 2 |

### 1.3 Exclusions

The following are explicitly excluded from coverage requirements:
- `__repr__` methods
- `__str__` methods
- `if __name__ == "__main__"` blocks
- `TYPE_CHECKING` blocks
- Abstract methods (but concrete implementations must be tested)
- Stub implementations (deepseek_*_stub.py)

---

## 2. Test Pyramid Strategy

### 2.1 Test Distribution

```
         /\
        /E2E\         5% - Real API calls (manual/smoke tests)
       /------\       - Use actual OpenRouter API
      /  Integ \     25% - Mocked HTTP, full component integration
     /----------\    - Use aioresponses for HTTP mocking
    /    Unit    \   70% - Pure logic, no I/O
   /--------------\  - Fast, isolated, deterministic
```

### 2.2 Test Level Definitions

**Unit Tests (70% of total)**
- Test single functions or classes in isolation
- No network I/O, no file I/O (use mocks)
- Fast execution (<1ms per test typically)
- Deterministic results

**Integration Tests (25% of total)**
- Test interactions between components
- Use mocked HTTP (aioresponses)
- Test data flow through multiple layers
- Moderate execution time (<100ms per test)

**End-to-End Tests (5% of total)**
- Test complete user flows
- May use real APIs (rate limited)
- Slow execution (seconds per test)
- Run manually or in nightly builds

---

## 3. Component Testing Requirements

### 3.1 Common Module (D04)

**Owner:** D04 (Infrastructure)
**Target Coverage:** >90%

#### 3.1.1 config.py

**Must Test:**
- ✅ Load from TOML file
- ✅ Environment variable overrides
- ✅ Missing file handling
- ✅ Invalid TOML syntax
- ✅ get_backend_config() with valid/invalid names
- ✅ Singleton behavior of get_config()
- ✅ Validation errors for invalid values

**Test Cases:**
```python
def test_load_config_from_file()
def test_env_var_overrides_file()
def test_missing_config_file_uses_defaults()
def test_invalid_toml_raises_error()
def test_get_backend_config_valid_name()
def test_get_backend_config_invalid_name_raises()
def test_config_singleton_returns_same_instance()
def test_config_validation_invalid_log_level()
def test_config_validation_invalid_dpi()
```

**Coverage:** File coverage >95%

#### 3.1.2 models.py

**Must Test:**
- ✅ All Pydantic model validation
- ✅ Field validators (e.g., log level, DPI range)
- ✅ Default values
- ✅ Optional vs required fields
- ✅ Serialization/deserialization

**Test Cases:**
```python
def test_ocr_backend_config_valid()
def test_ocr_backend_config_missing_required_field()
def test_page_result_model()
def test_conversion_result_model()
def test_model_to_dict()
def test_model_from_dict()
```

**Coverage:** File coverage >95%

#### 3.1.3 errors.py

**Must Test:**
- ✅ Exception hierarchy
- ✅ Error message construction
- ✅ Exception raising and catching

**Test Cases:**
```python
def test_base_error_hierarchy()
def test_configuration_error()
def test_backend_error_with_context()
def test_validation_error()
```

**Coverage:** File coverage >90%

#### 3.1.4 ids.py

**Must Test:**
- ✅ ID generation uniqueness
- ✅ ID format (prefix-uuid structure)
- ✅ Collision resistance (generate 10,000 IDs)

**Test Cases:**
```python
def test_generate_id_unique()
def test_generate_id_format()
def test_generate_doc_id()
def test_id_collision_resistance()
```

**Coverage:** File coverage >95%

#### 3.1.5 logging.py

**Must Test:**
- ✅ Logger initialization
- ✅ Context binding
- ✅ Context clearing
- ✅ JSON vs text format

**Test Cases:**
```python
def test_get_logger()
def test_bind_context()
def test_clear_context()
def test_log_format_json()
def test_log_format_text()
```

**Coverage:** File coverage >85%

#### 3.1.6 retry.py (NEW in Sprint 1)

**Must Test:**
- ✅ Retry logic with exponential backoff
- ✅ Max retries enforcement
- ✅ Retryable vs non-retryable exceptions
- ✅ Backoff timing accuracy

**Test Cases:**
```python
def test_retry_success_on_first_attempt()
def test_retry_success_on_third_attempt()
def test_retry_max_retries_exceeded()
def test_retry_exponential_backoff_timing()
def test_retry_non_retryable_exception_immediate_fail()
def test_retry_respects_max_delay()
```

**Coverage:** File coverage >95%

---

### 3.2 Backends Module (D02)

**Owner:** D02 (Backend Lead)
**Target Coverage:** >85%

#### 3.2.1 base.py

**Must Test:**
- ✅ Abstract method enforcement
- ✅ Context manager protocol
- ✅ Base class initialization

**Test Cases:**
```python
def test_backend_abc_cannot_instantiate()
def test_backend_subclass_must_implement_methods()
def test_backend_context_manager()
def test_backend_repr()
```

**Coverage:** File coverage >90%

#### 3.2.2 factory.py

**Must Test:**
- ✅ make_backend() with valid names
- ✅ make_backend() with invalid names
- ✅ list_backends()
- ✅ register_backend()
- ✅ Backend registration overwrite

**Test Cases:**
```python
def test_make_backend_nemotron()
def test_make_backend_invalid_name_raises()
def test_list_backends_includes_all_registered()
def test_register_custom_backend()
def test_register_backend_overwrites_existing()
```

**Coverage:** File coverage >95%

#### 3.2.3 openrouter_nemotron.py

**Must Test:**
- ✅ Initialization with config
- ✅ Base64 image encoding
- ✅ Message building (OpenAI format)
- ✅ HTTP POST with correct headers
- ✅ Content extraction (string format)
- ✅ Content extraction (list format)
- ✅ Error handling (4xx, 5xx)
- ✅ Timeout handling
- ✅ Connection error handling
- ✅ Missing API key error
- ✅ **NEW:** Retry logic (Sprint 1)
- ✅ **NEW:** Rate limit handling (Sprint 1)

**Test Cases:**
```python
def test_backend_init()
def test_encode_image_base64()
def test_build_messages_page_to_markdown()
def test_post_chat_success_string_content()
def test_post_chat_success_list_content()
def test_post_chat_error_4xx()
def test_post_chat_error_5xx()
def test_post_chat_timeout()
def test_post_chat_connection_error()
def test_missing_api_key_raises()
def test_retry_on_transient_failure()  # NEW Sprint 1
def test_rate_limit_429_respects_retry_after()  # NEW Sprint 1
```

**Coverage:** File coverage >90%

**HTTP Mocking:**
Use `aioresponses` to mock HTTP calls:
```python
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_post_chat_success(mock_backend_config):
    with aioresponses() as m:
        m.post(
            'https://openrouter.ai/api/v1/chat/completions',
            payload={'choices': [{'message': {'content': '# Test'}}]}
        )
        backend = OpenRouterNemotronBackend(mock_backend_config)
        result = await backend.page_to_markdown(b'fake_image', 1, 'doc-1')
        assert result == '# Test'
```

---

### 3.3 Renderer Module (D05)

**Owner:** D05 (Renderer Specialist)
**Target Coverage:** >85%

#### 3.3.1 core.py

**Must Test:**
- ✅ get_page_count() with valid PDF
- ✅ get_page_count() with invalid PDF
- ✅ render_page_to_png_bytes() with valid page
- ✅ render_page_to_png_bytes() with out-of-range page
- ✅ PNG output is valid (check magic bytes)
- ✅ DPI affects output size
- ✅ **NEW:** Memory optimization (Sprint 1)

**Test Cases:**
```python
def test_get_page_count_valid_pdf()
def test_get_page_count_invalid_pdf_raises()
def test_render_page_valid()
def test_render_page_out_of_range_raises()
def test_render_page_produces_valid_png()
def test_render_page_dpi_affects_size()
def test_render_page_memory_usage()  # NEW Sprint 1
```

**Coverage:** File coverage >90%

**Test Data:**
Need sample PDFs in `tests/fixtures/`:
- `sample_1page.pdf` (simple text)
- `sample_3page.pdf` (multi-page)
- `sample_with_table.pdf` (table content)
- `corrupted.pdf` (invalid PDF for error testing)

---

### 3.4 Orchestrator Module (D03)

**Owner:** D03 (Pipeline Lead)
**Target Coverage:** >85%

#### 3.4.1 pipeline.py

**Must Test:**
- ✅ Pipeline initialization
- ✅ convert_pdf() with single page
- ✅ convert_pdf() with multi-page
- ✅ convert_pdf() with max_pages limit
- ✅ convert_pdf() with start_page offset
- ✅ Error handling per page
- ✅ Page separator insertion
- ✅ Output file writing
- ✅ **NEW:** Concurrent processing (Sprint 1)
- ✅ **NEW:** Semaphore-based concurrency limit (Sprint 1)

**Test Cases:**
```python
def test_pipeline_init()
def test_convert_pdf_single_page()
def test_convert_pdf_multi_page()
def test_convert_pdf_max_pages_limit()
def test_convert_pdf_start_page_offset()
def test_convert_pdf_page_error_skip()
def test_convert_pdf_page_error_placeholder()
def test_convert_pdf_page_separators()
def test_convert_pdf_writes_output_file()
def test_convert_pdf_concurrent()  # NEW Sprint 1
def test_convert_pdf_respects_max_workers()  # NEW Sprint 1
def test_convert_pdf_maintains_page_order()  # NEW Sprint 1
```

**Coverage:** File coverage >85%

#### 3.4.2 models.py

**Must Test:**
- ✅ ConversionOptions validation
- ✅ ConversionResult model
- ✅ PageResult model

**Test Cases:**
```python
def test_conversion_options_defaults()
def test_conversion_options_validation()
def test_conversion_result_model()
def test_page_result_model()
```

**Coverage:** File coverage >90%

---

### 3.5 CLI Module (D06)

**Owner:** D06 (CLI Lead)
**Target Coverage:** >70%

#### 3.5.1 main.py

**Must Test:**
- ✅ CLI initialization
- ✅ convert command parsing
- ✅ backends command
- ✅ info command
- ✅ Error message display
- ✅ **NEW:** Progress bar (Sprint 1)

**Test Cases:**
```python
def test_cli_convert_command()
def test_cli_backends_command()
def test_cli_info_command()
def test_cli_version()
def test_cli_help_text()
def test_cli_error_handling()
def test_cli_progress_bar()  # NEW Sprint 1
```

**Coverage:** File coverage >70%

**Note:** CLI testing can use Typer's `CliRunner`:
```python
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["convert", "test.pdf"])
assert result.exit_code == 0
```

---

## 4. Integration Test Requirements

### 4.1 Renderer + Backend Integration (D07)

**Must Test:**
- ✅ Rendered PNG can be processed by backend
- ✅ Full page OCR flow works
- ✅ Error propagation through layers

**Test Cases:**
```python
@pytest.mark.integration
async def test_renderer_output_compatible_with_backend()

@pytest.mark.integration
async def test_full_page_ocr_flow()

@pytest.mark.integration
async def test_error_propagation()
```

**Mocking:** Use `aioresponses` to mock HTTP:
```python
@pytest.mark.integration
async def test_full_page_ocr_flow(sample_pdf_path):
    with aioresponses() as m:
        m.post(OPENROUTER_URL, payload=mock_success_response())

        # Render page
        renderer = PypdfiumRenderer()
        image = renderer.render_page(sample_pdf_path, 0)

        # OCR page
        backend = make_backend(test_config)
        async with backend:
            result = await backend.page_to_markdown(image, 1, "test-doc")

        assert "# " in result  # Has markdown heading
```

### 4.2 Pipeline Integration (D07)

**Must Test:**
- ✅ End-to-end conversion with mocked backend
- ✅ Multi-page processing
- ✅ Error recovery

**Test Cases:**
```python
@pytest.mark.integration
async def test_pipeline_e2e_mocked()

@pytest.mark.integration
async def test_pipeline_multi_page()

@pytest.mark.integration
async def test_pipeline_error_recovery()
```

---

## 5. Test Infrastructure Requirements

### 5.1 Fixtures (conftest.py)

**Required Fixtures:**
```python
@pytest.fixture
def test_config() -> Config:
    """Load test configuration."""

@pytest.fixture
def sample_pdf_path() -> Path:
    """Path to single-page test PDF."""

@pytest.fixture
def sample_pdf_multipage_path() -> Path:
    """Path to multi-page test PDF."""

@pytest.fixture
def sample_image_bytes() -> bytes:
    """Sample PNG image bytes."""

@pytest.fixture
def mock_backend_config() -> OcrBackendConfig:
    """Mock backend configuration."""

@pytest.fixture
def mock_backend() -> MockOcrVlmBackend:
    """Mock backend for testing."""
```

### 5.2 Mock Infrastructure (NEW Sprint 1)

**File:** `tests/mocks/http_responses.py`
**Owner:** D07

**Required Mocks:**
```python
def mock_openrouter_success(content: str = "# Test") -> dict:
    """Mock successful OpenRouter response."""

def mock_openrouter_error(status: int, message: str) -> CallbackResult:
    """Mock error OpenRouter response."""

def mock_openrouter_timeout() -> Exception:
    """Mock timeout exception."""

def mock_openrouter_rate_limit(retry_after: int = 60) -> CallbackResult:
    """Mock 429 rate limit response."""
```

### 5.3 Test Data

**Required Files in `tests/fixtures/`:**
- `sample_1page.pdf` - Simple single page document
- `sample_3page.pdf` - Multi-page document
- `sample_with_table.pdf` - Document with table
- `sample_with_formula.pdf` - Document with mathematical formula
- `corrupted.pdf` - Invalid PDF for error testing

**Generation:** Can use PyPDF2 or reportlab to generate programmatically

---

## 6. Coverage Measurement

### 6.1 Running Coverage

**Commands:**
```bash
# Run with coverage
pytest tests/unit --cov=src/docling_hybrid --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check coverage threshold
pytest tests/unit --cov=src/docling_hybrid --cov-fail-under=85
```

### 6.2 CI Integration

**GitHub Actions:**
```yaml
# .github/workflows/test.yml
- name: Run tests with coverage
  run: |
    pytest tests/unit \
      --cov=src/docling_hybrid \
      --cov-report=xml \
      --cov-fail-under=85

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

### 6.3 Coverage Reports

**Required Reports:**
1. **Terminal Summary** - Quick view during development
2. **HTML Report** - Detailed line-by-line view
3. **XML Report** - For CI/CD integration
4. **Badge** - Display on README (optional)

---

## 7. Test Quality Standards

### 7.1 Test Naming Convention

```python
# Pattern: test_<function>_<scenario>_<expected_result>

# Good examples:
def test_make_backend_valid_name_returns_instance()
def test_make_backend_invalid_name_raises_error()
def test_render_page_out_of_range_raises_validation_error()

# Bad examples:
def test_backend()  # Too vague
def test_error()  # What error?
def test_case_1()  # Meaningless name
```

### 7.2 Test Structure

**Use AAA Pattern:**
```python
def test_make_backend_creates_correct_type():
    # Arrange
    config = OcrBackendConfig(
        name="nemotron-openrouter",
        model="test-model",
        api_key="test-key"
    )

    # Act
    backend = make_backend(config)

    # Assert
    assert isinstance(backend, OpenRouterNemotronBackend)
    assert backend.name == "nemotron-openrouter"
```

### 7.3 Test Independence

**Each test must:**
- ✅ Be runnable in isolation
- ✅ Not depend on other tests
- ✅ Clean up after itself
- ✅ Not modify global state
- ✅ Be deterministic (no randomness)

**Bad Example:**
```python
# Don't do this!
global_backend = None

def test_create_backend():
    global global_backend
    global_backend = make_backend(config)

def test_use_backend():  # Depends on previous test!
    result = await global_backend.page_to_markdown(...)
```

**Good Example:**
```python
@pytest.fixture
def backend(test_config):
    backend = make_backend(test_config)
    yield backend
    backend.close()  # Cleanup

def test_create_backend(backend):
    assert backend is not None

def test_use_backend(backend):
    result = await backend.page_to_markdown(...)
```

### 7.4 Assertion Quality

**Good Assertions:**
```python
# Specific
assert result.page_count == 3
assert result.status == "success"
assert "# Title" in result.markdown

# With helpful messages
assert result.page_count == expected_count, \
    f"Expected {expected_count} pages but got {result.page_count}"
```

**Bad Assertions:**
```python
# Too vague
assert result  # What are we checking?
assert len(result.pages) > 0  # Any number > 0 passes

# Testing implementation details
assert result._internal_cache is not None  # Brittle!
```

---

## 8. Performance Testing

### 8.1 Performance Benchmarks

**Target:** Sprint 1 should establish baseline performance metrics

**Benchmarks to Measure:**
```python
@pytest.mark.benchmark
def test_render_page_performance():
    """Measure page rendering time."""
    # Target: <100ms for 200 DPI

@pytest.mark.benchmark
async def test_backend_response_time():
    """Measure backend API call time (mocked)."""
    # Target: <50ms (excluding network)

@pytest.mark.benchmark
async def test_pipeline_throughput():
    """Measure pages per second."""
    # Target: >10 pages/second (with concurrency)
```

### 8.2 Memory Testing

**Target:** Ensure no memory leaks

**Test Pattern:**
```python
import tracemalloc

@pytest.mark.memory
async def test_pipeline_memory_usage():
    """Ensure memory doesn't grow unbounded."""
    tracemalloc.start()

    for _ in range(100):
        result = await pipeline.convert_pdf(small_pdf)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory should not grow linearly with iterations
    assert current < peak * 1.1  # Within 10% of peak
```

---

## 9. Sprint 1 Test Deliverables

### 9.1 Test Files to Create

**Priority 0 (Must Have):**
1. ✅ `tests/mocks/http_responses.py` - HTTP mock utilities
2. ✅ `tests/integration/test_renderer_backend.py` - Renderer + Backend
3. ✅ `tests/unit/test_retry.py` - Retry logic tests
4. ✅ `tests/unit/test_pipeline_concurrent.py` - Concurrent processing

**Priority 1 (Should Have):**
1. ✅ `tests/integration/test_pipeline_e2e.py` - Full pipeline tests
2. ✅ Expand `tests/unit/test_backends.py` - More backend tests
3. ✅ Expand `tests/unit/test_common.py` - More common tests

**Priority 2 (Nice to Have):**
1. ⚪ `tests/benchmarks/test_performance.py` - Performance benchmarks
2. ⚪ `tests/memory/test_memory.py` - Memory tests

### 9.2 Coverage Report

**Sprint 1 Exit Criteria:**
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
src/docling_hybrid/__init__.py              10      0   100%
src/docling_hybrid/common/config.py        150     10    93%
src/docling_hybrid/common/models.py        120      5    96%
src/docling_hybrid/common/errors.py         50      2    96%
src/docling_hybrid/common/ids.py            30      1    97%
src/docling_hybrid/common/logging.py        40      5    88%
src/docling_hybrid/common/retry.py          50      2    96%  <- NEW
src/docling_hybrid/backends/base.py         60      3    95%
src/docling_hybrid/backends/factory.py      40      2    95%
src/docling_hybrid/backends/openrouter.py  200     25    88%
src/docling_hybrid/renderer/core.py        100     12    88%
src/docling_hybrid/orchestrator/pipeline   150     20    87%
src/docling_hybrid/cli/main.py            100     35    65%
-----------------------------------------------------------
TOTAL                                     1100    122    89%
```

**Target:** >85% overall, >90% on new code

---

## 10. Testing Best Practices

### 10.1 When to Mock

**Mock when:**
- ✅ Testing HTTP clients (use aioresponses)
- ✅ Testing file I/O (use temporary files or mocks)
- ✅ Testing external services
- ✅ Testing slow operations

**Don't mock when:**
- ⛔ Testing pure functions
- ⛔ Testing data models (Pydantic)
- ⛔ Testing internal logic
- ⛔ Over-mocking makes tests brittle

### 10.2 Test Maintenance

**Keep tests maintainable:**
1. **DRY:** Use fixtures for common setup
2. **Readable:** Use descriptive names and comments
3. **Fast:** Mock slow operations
4. **Isolated:** Each test is independent
5. **Documented:** Explain complex test scenarios

### 10.3 Test Review Checklist

Before merging, ensure:
- [ ] All new code has tests
- [ ] All tests pass locally
- [ ] Coverage meets requirements
- [ ] Tests are documented
- [ ] No flaky tests
- [ ] Performance is acceptable

---

## 11. Conclusion

### 11.1 Success Criteria

Sprint 1 testing is successful when:
- ✅ Overall coverage >85%
- ✅ All critical paths have tests
- ✅ HTTP mocking infrastructure in place
- ✅ Integration tests pass
- ✅ No test flakiness
- ✅ CI runs tests on every PR

### 11.2 Next Steps

After Sprint 1:
1. Maintain >85% coverage on all new code
2. Add more integration tests in Sprint 2+
3. Consider mutation testing for critical paths
4. Set up performance regression testing

---

**Document Status:** ✅ Complete
**Owner:** D01 (Tech Lead)
**Reviewed By:** D07 (Testing Lead)
**Next Review:** Sprint 1 Day 8
