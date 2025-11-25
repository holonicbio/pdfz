# OpenRouter Integration Testing Guide

## Overview

This document describes the integration testing strategy for the Docling Hybrid OCR system using OpenRouter's VLM API. These tests validate the full pipeline with real API calls, ensuring production readiness.

**Status:** ✅ Implemented in Sprint 3
**Last Updated:** 2025-11-25

---

## Table of Contents

1. [Overview](#overview)
2. [Test Requirements](#test-requirements)
3. [Test Structure](#test-structure)
4. [Running Tests](#running-tests)
5. [Test Categories](#test-categories)
6. [Rate Limiting](#rate-limiting)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Test Requirements

### Required Environment Variables

```bash
# Required for all live API tests
export OPENROUTER_API_KEY="sk-or-v1-..."

# Optional: for tracking API usage
export DOCLING_HYBRID_HTTP_REFERER="https://your-project.com"
export DOCLING_HYBRID_X_TITLE="Your Project Name"
```

### Required Test Data

Integration tests require PDF files for testing. Tests use files matching the pattern `2511*.pdf` in the `pdfs/` directory:

```bash
# Project structure
docling-hybrid-ocr/
├── pdfs/                    # PDF test files directory
│   ├── 2511_sample1.pdf    # Test PDFs (starting with 2511)
│   └── 2511_sample2.pdf
└── tests/
    └── integration/         # Integration tests
```

If PDF files are not found, tests requiring them will be automatically skipped.

### Python Dependencies

```bash
pip install pytest pytest-asyncio aiohttp aioresponses
```

---

## Test Structure

### Test Files

```
tests/integration/
├── conftest.py                      # Integration test fixtures
├── test_openrouter_integration.py   # Main OpenRouter integration tests
├── test_openrouter_fallback.py      # Fallback chain tests
├── test_pipeline_e2e.py            # E2E pipeline tests (mocked)
└── test_backend_http.py            # HTTP error handling (mocked)
```

### Test Markers

Tests use pytest markers to control execution:

- **`@pytest.mark.live_api`** - Requires `OPENROUTER_API_KEY`, makes real API calls
- **`@pytest.mark.requires_pdfs`** - Requires PDF test files in `pdfs/` directory
- **`@pytest.mark.asyncio`** - Async test using pytest-asyncio

### Fixtures

**From `tests/integration/conftest.py`:**

- **`api_key`** - OpenRouter API key from environment
- **`pdfs_dir`** - Path to PDFs directory
- **`test_pdfs`** - List of test PDF files (2511*.pdf)
- **`first_test_pdf`** - First test PDF file
- **`openrouter_config`** - OpenRouter backend configuration dict

---

## Running Tests

### Run All Integration Tests

```bash
# Run all integration tests (requires API key + PDFs)
pytest tests/integration -v

# Run with output capture disabled (see print statements)
pytest tests/integration -v -s
```

### Run Specific Test Categories

```bash
# Only tests requiring live API
pytest tests/integration -v -m live_api

# Only tests requiring PDFs
pytest tests/integration -v -m requires_pdfs

# Only tests NOT requiring live API (mocked tests)
pytest tests/integration -v -m "not live_api"
```

### Run Specific Test Files

```bash
# OpenRouter integration tests
pytest tests/integration/test_openrouter_integration.py -v

# Fallback chain tests
pytest tests/integration/test_openrouter_fallback.py -v

# E2E pipeline tests (mocked)
pytest tests/integration/test_pipeline_e2e.py -v
```

### Run Specific Tests

```bash
# Single test by name
pytest tests/integration/test_openrouter_integration.py::TestOpenRouterBackend::test_single_page_ocr -v

# All tests in a class
pytest tests/integration/test_openrouter_integration.py::TestConcurrentProcessingWithRateLimiting -v
```

### Skip Live API Tests

If you don't have an API key or want to run only mocked tests:

```bash
# Skip all live API tests
pytest tests/integration -v -m "not live_api"
```

---

## Test Categories

### 1. Backend Tests (`TestOpenRouterBackend`)

Tests the OpenRouter backend directly with real API calls.

**Tests:**
- Backend initialization
- Single page OCR
- Health check

**Example:**
```bash
pytest tests/integration/test_openrouter_integration.py::TestOpenRouterBackend -v
```

### 2. Renderer Tests (`TestRendererWithPDFs`)

Tests PDF rendering functionality with real PDF files.

**Tests:**
- Getting page count
- Rendering pages to PNG
- PNG format validation

**Example:**
```bash
pytest tests/integration/test_openrouter_integration.py::TestRendererWithPDFs -v
```

### 3. Pipeline Integration (`TestPipelineIntegration`)

Tests the full conversion pipeline with OpenRouter backend.

**Tests:**
- Single page conversion
- Multi-page conversion (up to 3 pages)
- Output file generation

**Example:**
```bash
pytest tests/integration/test_openrouter_integration.py::TestPipelineIntegration -v
```

### 4. Concurrent Processing (`TestConcurrentProcessingWithRateLimiting`)

Tests concurrent page processing and rate limiting behavior.

**Tests:**
- Concurrent processing of multiple pages
- Rate limit handling with retries
- Performance timing

**Example:**
```bash
pytest tests/integration/test_openrouter_integration.py::TestConcurrentProcessingWithRateLimiting -v
```

**Expected behavior:**
- Multiple pages processed concurrently (max_workers=3)
- Automatic rate limit handling with exponential backoff
- Graceful retry on transient failures

### 5. Error Handling (`TestErrorHandlingWithRealAPI`)

Tests error handling scenarios with real API responses.

**Tests:**
- Invalid API key (401 errors)
- Backend health checks
- Error message quality

**Example:**
```bash
pytest tests/integration/test_openrouter_integration.py::TestErrorHandlingWithRealAPI -v
```

### 6. Fallback Chain (`TestFallbackChainWithOpenRouter`)

Tests backend fallback chain mechanism.

**Tests:**
- Fallback chain initialization
- Primary backend success (no fallback)
- Fallback on primary failure
- Multiple fallback backends
- All backends fail scenario

**Example:**
```bash
pytest tests/integration/test_openrouter_fallback.py::TestFallbackChainWithOpenRouter -v
```

**Key scenarios:**
- Primary succeeds → no fallback triggered
- Primary fails (401) → fallback succeeds
- Primary + fallback1 fail → fallback2 succeeds
- All fail → raises BackendError

### 7. Batch Processing (`TestAllPDFs`)

Tests processing of all available PDF files.

**Tests:**
- First page of each PDF
- Success rate tracking
- Summary statistics

**Example:**
```bash
pytest tests/integration/test_openrouter_integration.py::TestAllPDFs -v
```

**Note:** This test processes all PDFs starting with `2511` in the `pdfs/` directory. It includes delays between PDFs to respect rate limits.

---

## Rate Limiting

### OpenRouter Rate Limits

OpenRouter applies rate limits based on:
- Model (free tier has stricter limits)
- API key tier
- Time window (requests per minute/hour)

**Free tier model:**
- Model: `nvidia/nemotron-nano-12b-v2-vl:free`
- Limits: Variable, subject to change

### Rate Limit Handling

The system automatically handles rate limits:

1. **Retry with exponential backoff**
   - Initial delay: 2s
   - Max delay: 30s
   - Max retries: 5 (configurable)

2. **Retry-After header**
   - OpenRouter returns `Retry-After` header with 429 responses
   - System respects this value

3. **Test delays**
   - Integration tests include small delays between requests
   - Batch tests: 1s delay between PDFs

### Best Practices

```python
# Configure for rate limit tolerance
config = {
    "backends": {
        "nemotron-openrouter": {
            "max_retries": 5,              # More retries
            "retry_initial_delay": 2.0,    # Start with 2s delay
            "retry_max_delay": 30.0,       # Max 30s delay
        }
    }
}
```

### Monitoring Rate Limits

Watch for log messages:
```
rate_limit_exceeded backend=nemotron-openrouter retry_after=30.0
retrying_after_rate_limit attempt=2 delay=30.0
```

---

## Best Practices

### 1. Run Tests Locally Before CI

Always run integration tests locally with your API key before pushing:

```bash
# Quick smoke test
pytest tests/integration/test_openrouter_integration.py::TestOpenRouterBackend::test_single_page_ocr -v

# Full suite
pytest tests/integration -v
```

### 2. Use Test PDFs Wisely

- Keep test PDFs small (1-5 pages)
- Use `max_pages` option to limit processing
- Don't commit large PDFs to repo

### 3. Monitor API Usage

OpenRouter provides usage tracking:
- Check dashboard: https://openrouter.ai/activity
- Set budget limits to avoid surprises
- Use free-tier models for testing

### 4. Handle Flaky Tests

Integration tests with real APIs can be flaky:

```bash
# Retry failed tests once
pytest tests/integration -v --maxfail=1 --reruns 1
```

### 5. Parallel Test Execution

**Don't run integration tests in parallel** - they share API rate limits:

```bash
# ❌ Don't do this with live API tests
pytest tests/integration -v -n 4

# ✅ Run sequentially
pytest tests/integration -v
```

### 6. Environment Isolation

Use separate API keys for different environments:

```bash
# Development
export OPENROUTER_API_KEY="$DEV_API_KEY"

# CI/Testing
export OPENROUTER_API_KEY="$TEST_API_KEY"

# Production
export OPENROUTER_API_KEY="$PROD_API_KEY"
```

---

## Troubleshooting

### Issue: "OPENROUTER_API_KEY not set"

**Cause:** Environment variable not configured

**Solution:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Or create .env file and source it
echo 'OPENROUTER_API_KEY=sk-or-v1-...' > .env
source .env
```

### Issue: "No PDF files found"

**Cause:** Missing test PDFs in `pdfs/` directory

**Solution:**
1. Create `pdfs/` directory in project root
2. Add PDF files starting with `2511`:
   ```bash
   mkdir -p pdfs
   cp /path/to/test.pdf pdfs/2511_test.pdf
   ```

Tests will automatically skip if PDFs are not found.

### Issue: "API rate limit exceeded"

**Cause:** Too many requests in short time

**Solution:**
1. Wait for rate limit window to reset
2. Increase delays between tests:
   ```python
   await asyncio.sleep(2)  # Add delay
   ```
3. Reduce `max_workers` in config
4. Use paid tier for higher limits

### Issue: "Backend timeout"

**Cause:** OpenRouter API slow or unresponsive

**Solution:**
1. Increase timeout:
   ```python
   config = {
       "resources": {
           "http_timeout_s": 180,  # 3 minutes
       }
   }
   ```
2. Check OpenRouter status
3. Retry later

### Issue: "Invalid API key (401)"

**Cause:** Incorrect or expired API key

**Solution:**
1. Verify key: https://openrouter.ai/keys
2. Regenerate if needed
3. Update environment variable
4. Check for typos/whitespace

### Issue: "Tests taking too long"

**Cause:** Processing many pages/PDFs

**Solution:**
1. Use `max_pages` to limit:
   ```bash
   # In test
   options = ConversionOptions(max_pages=1)
   ```
2. Run subset of tests:
   ```bash
   pytest tests/integration -k "test_single_page" -v
   ```
3. Skip batch tests during development

### Issue: "Intermittent failures"

**Cause:** Network issues, API variability

**Solution:**
1. Add retries:
   ```bash
   pytest tests/integration -v --reruns 2
   ```
2. Check logs for patterns
3. Report persistent issues

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio

      - name: Run integration tests
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          pytest tests/integration -v -m live_api
```

**Security notes:**
- Store API key as GitHub secret
- Never commit API keys to repo
- Use separate key for CI

---

## Performance Benchmarks

Expected performance with OpenRouter (free tier):

| Operation | Time | Notes |
|-----------|------|-------|
| Single page OCR | 5-15s | Varies by model load |
| 3 pages (concurrent) | 10-20s | max_workers=3 |
| 3 pages (sequential) | 15-45s | max_workers=1 |
| Health check | 1-3s | Minimal request |

**Factors affecting performance:**
- Model availability
- API load
- Network latency
- Image size/complexity
- Concurrent workers

---

## API Usage Monitoring

### OpenRouter Dashboard

Monitor your usage:
- URL: https://openrouter.ai/activity
- View: requests, tokens, costs
- Set: budget limits, alerts

### Logging API Calls

Enable detailed logging:

```bash
export DOCLING_HYBRID_LOG_LEVEL=DEBUG
pytest tests/integration -v -s 2>&1 | tee test.log
```

Look for:
```
api_request_started backend=nemotron-openrouter model=nvidia/nemotron-nano-12b-v2-vl:free
api_request_completed backend=nemotron-openrouter content_length=1234
```

---

## Future Enhancements

Potential improvements for integration testing:

1. **Mock fallback modes**
   - Use VCR.py to record/replay API responses
   - Reduce API usage during development

2. **Performance regression tests**
   - Track OCR quality metrics
   - Monitor response times

3. **Multi-model testing**
   - Test different OpenRouter models
   - Compare quality/speed tradeoffs

4. **Chaos engineering**
   - Simulate network failures
   - Test resilience mechanisms

5. **Load testing**
   - Batch processing at scale
   - Concurrent document handling

---

## Related Documentation

- **[SPRINT3_PLAN.md](SPRINT3_PLAN.md)** - Sprint 3 testing strategy
- **[API_REFERENCE.md](API_REFERENCE.md)** - Python API documentation
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - General troubleshooting
- **[QUICK_START.md](QUICK_START.md)** - Getting started guide

---

## Support

For issues with integration tests:

1. Check this documentation
2. Review test logs
3. Verify API key and environment
4. Check OpenRouter status
5. Report issues: https://github.com/holonicbio/pdfz/issues
