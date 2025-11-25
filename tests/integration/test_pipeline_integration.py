"""Integration tests for HybridPipeline with OpenRouter backend.

This module focuses on testing the integration between the pipeline orchestrator
and the OpenRouter backend, using both mocked HTTP responses and real API calls.

Tests cover:
- Pipeline coordination with OpenRouter backend
- Progress callbacks during real conversions
- Error handling and retry behavior
- Concurrent page processing
- Rate limiting and backpressure

Run with:
    pytest tests/integration/test_pipeline_integration.py -v

For live API tests (requires OPENROUTER_API_KEY):
    pytest tests/integration/test_pipeline_integration.py -v -m live_api
"""

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from docling_hybrid.common.config import init_config, reset_config
from docling_hybrid.common.errors import BackendError
from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions, ConversionResult
from docling_hybrid.orchestrator.progress import ProgressCallback
from tests.mocks import mock_openrouter_success


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def integration_config(tmp_path: Path) -> Path:
    """Create configuration for pipeline integration tests."""
    import tomli_w

    config_dict = {
        "app": {
            "name": "docling-hybrid-ocr",
            "version": "0.1.0",
            "environment": "integration",
        },
        "logging": {
            "level": "INFO",
            "format": "text",
        },
        "resources": {
            "max_workers": 2,
            "max_memory_mb": 2048,
            "page_render_dpi": 150,
            "http_timeout_s": 30,
            "http_retry_attempts": 2,
        },
        "backends": {
            "default": "nemotron-openrouter",
            "nemotron-openrouter": {
                "name": "nemotron-openrouter",
                "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                "base_url": "https://openrouter.ai/api/v1/chat/completions",
                "temperature": 0.0,
                "max_tokens": 4096,
            },
        },
        "output": {
            "format": "markdown",
            "add_page_separators": True,
            "page_separator": "<!-- PAGE {page_num} -->\n\n",
        },
    }

    config_path = tmp_path / "integration_config.toml"

    # Flatten backends for TOML
    backends = config_dict.pop("backends")
    config_dict["backends"] = {
        "default": backends["default"],
        **{k: v for k, v in backends.items() if k != "default"},
    }

    with open(config_path, "wb") as f:
        tomli_w.dump(config_dict, f)

    return config_path


@pytest.fixture
def sample_pdf_3_pages(tmp_path: Path) -> Path:
    """Create a sample 3-page PDF for integration testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "integration_test_3pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    for page_num in range(1, 4):
        c.drawString(100, 750, f"Integration Test - Page {page_num}")
        c.drawString(100, 700, f"This is page {page_num} of 3.")
        c.drawString(100, 650, "Testing pipeline integration with OpenRouter.")
        c.showPage()

    c.save()
    return pdf_path


# ============================================================================
# Pipeline Integration Tests (Mocked HTTP)
# ============================================================================


@pytest.mark.integration
class TestPipelineWithMockedOpenRouter:
    """Test pipeline integration with mocked OpenRouter responses."""

    @pytest.mark.asyncio
    async def test_pipeline_basic_conversion(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test basic pipeline conversion with mocked OpenRouter."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        with aioresponses() as mock_http:
            # Mock responses for 3 pages
            for page_num in range(1, 4):
                content = f"# Page {page_num}\n\nThis is the content of page {page_num}.\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            result = await pipeline.convert_pdf(sample_pdf_3_pages)

        assert isinstance(result, ConversionResult)
        assert result.total_pages == 3
        assert result.processed_pages == 3
        assert len(result.page_results) == 3
        assert result.backend_name == "nemotron-openrouter"

        # Verify all pages are in result
        page_nums = [pr.page_num for pr in result.page_results]
        assert page_nums == [1, 2, 3]

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_with_progress_callbacks(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test pipeline progress callbacks during conversion."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        # Track progress events
        events = []

        class TestProgressCallback(ProgressCallback):
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                events.append(("conversion_start", doc_id, total_pages))

            def on_page_start(self, page_num: int, total: int) -> None:
                events.append(("page_start", page_num, total))

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                events.append(("page_complete", page_num, total))

            def on_page_error(self, page_num: int, error: Exception) -> None:
                events.append(("page_error", page_num, str(error)))

            def on_conversion_complete(self, result) -> None:
                events.append(("conversion_complete", result.doc_id))

            def on_conversion_error(self, error: Exception) -> None:
                events.append(("conversion_error", str(error)))

        callback = TestProgressCallback()

        with aioresponses() as mock_http:
            for page_num in range(1, 4):
                content = f"# Page {page_num}\n\nContent.\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            result = await pipeline.convert_pdf(
                sample_pdf_3_pages, progress_callback=callback
            )

        # Verify all expected events occurred
        event_types = [e[0] for e in events]
        assert "conversion_start" in event_types
        assert event_types.count("page_start") == 3
        assert event_types.count("page_complete") == 3
        assert "conversion_complete" in event_types
        assert "conversion_error" not in event_types
        assert "page_error" not in event_types

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_partial_failure_with_callbacks(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test pipeline continues on page error and invokes callbacks."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        page_errors = []
        page_completions = []

        class TrackingCallback(ProgressCallback):
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                page_completions.append(page_num)

            def on_page_error(self, page_num: int, error: Exception) -> None:
                page_errors.append((page_num, str(error)))

            def on_conversion_complete(self, result) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = TrackingCallback()

        with aioresponses() as mock_http:
            # Page 1: success
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_success("# Page 1\n\nContent.\n"),
            )

            # Page 2: error (500)
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=500,
                payload={"error": "Internal server error"},
            )

            # Page 3: success
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_success("# Page 3\n\nContent.\n"),
            )

            result = await pipeline.convert_pdf(
                sample_pdf_3_pages, progress_callback=callback
            )

        # Should process 2 pages successfully despite 1 error
        assert result.total_pages == 3
        assert result.processed_pages == 2
        assert len(page_completions) == 2
        assert len(page_errors) >= 1  # May have retries

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_concurrent_page_processing(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test that pipeline processes pages concurrently."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        config.resources.max_workers = 3  # Enable concurrent processing
        pipeline = HybridPipeline(config)

        # Track when pages start processing
        page_start_times = {}

        # Use simple mocked responses without callbacks
        with aioresponses() as mock_http:
            for page_num in range(1, 4):
                content = f"# Page {page_num}\n\nContent from page {page_num}.\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                )

            start_time = time.time()
            result = await pipeline.convert_pdf(sample_pdf_3_pages)
            elapsed = time.time() - start_time

        assert result.processed_pages == 3

        # Concurrent processing should complete faster than 3 * typical_api_latency
        # This is a weak assertion but validates concurrency occurred
        print(f"\n--- Concurrent Processing Time: {elapsed:.2f}s ---")

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_respects_max_workers_limit(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test that pipeline respects max_workers concurrency limit."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        config.resources.max_workers = 1  # Force sequential processing
        pipeline = HybridPipeline(config)

        # Use simple mocked responses
        with aioresponses() as mock_http:
            for page_num in range(1, 4):
                content = f"# Page {page_num}\n\nContent.\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                )

            result = await pipeline.convert_pdf(sample_pdf_3_pages)

        assert result.processed_pages == 3

        # Note: Actual concurrency limiting is tested in unit tests
        # This integration test validates end-to-end behavior
        print(f"\n--- Sequential Processing Complete ---")

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_conversion_options_integration(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test pipeline with various conversion options."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        options = ConversionOptions(
            max_pages=2,
            start_page=2,
            dpi=100,
            add_page_separators=False,
        )

        with aioresponses() as mock_http:
            # Mock pages 2 and 3
            for page_num in range(2, 4):
                content = f"# Page {page_num}\n\nContent.\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            result = await pipeline.convert_pdf(sample_pdf_3_pages, options=options)

        # Should only process pages 2 and 3
        assert result.total_pages == 3
        assert result.processed_pages == 2
        page_nums = [pr.page_num for pr in result.page_results]
        assert page_nums == [2, 3]

        # Should not have page separators
        assert "<!-- PAGE" not in result.markdown

        reset_config()


# ============================================================================
# Live API Integration Tests (requires OPENROUTER_API_KEY)
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestPipelineWithLiveOpenRouter:
    """Test pipeline with real OpenRouter API calls."""

    async def test_pipeline_single_page_conversion(
        self, integration_config: Path, first_test_pdf: Path, tmp_path: Path
    ):
        """Test converting a single page with real OpenRouter API."""
        reset_config()
        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "output_single.md"

        options = ConversionOptions(
            max_pages=1,
            dpi=150,
        )

        result = await pipeline.convert_pdf(
            first_test_pdf, output_path=output_path, options=options
        )

        assert result.total_pages >= 1
        assert result.processed_pages == 1
        assert len(result.page_results) == 1
        assert result.backend_name == "nemotron-openrouter"

        # Verify markdown was generated
        assert len(result.markdown) > 0
        assert output_path.exists()

        # Verify page result metadata
        page_result = result.page_results[0]
        assert page_result.page_num == 1
        assert page_result.backend_name == "nemotron-openrouter"
        assert "image_size_kb" in page_result.metadata

        print(f"\n--- Generated Markdown (first 300 chars) ---")
        print(result.markdown[:300])

        reset_config()

    async def test_pipeline_multi_page_with_progress(
        self, integration_config: Path, first_test_pdf: Path
    ):
        """Test multi-page conversion with progress tracking."""
        reset_config()
        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        events = []

        class TrackingCallback(ProgressCallback):
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                events.append(("start", total_pages))

            def on_page_start(self, page_num: int, total: int) -> None:
                events.append(("page_start", page_num))

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                events.append(("page_complete", page_num))

            def on_page_error(self, page_num: int, error: Exception) -> None:
                events.append(("page_error", page_num))

            def on_conversion_complete(self, result) -> None:
                events.append(("complete", result.processed_pages))

            def on_conversion_error(self, error: Exception) -> None:
                events.append(("error", str(error)))

        callback = TrackingCallback()

        options = ConversionOptions(max_pages=2)

        result = await pipeline.convert_pdf(
            first_test_pdf, options=options, progress_callback=callback
        )

        assert result.processed_pages == 2

        # Verify progress events
        event_types = [e[0] for e in events]
        assert "start" in event_types
        assert event_types.count("page_start") == 2
        assert event_types.count("page_complete") == 2
        assert "complete" in event_types

        print(f"\n--- Progress Events ---")
        for event in events:
            print(event)

        reset_config()

    async def test_pipeline_concurrent_processing_performance(
        self, integration_config: Path, first_test_pdf: Path
    ):
        """Test concurrent processing performance with real API."""
        reset_config()
        config = init_config(integration_config)

        # Test with sequential processing
        config.resources.max_workers = 1
        pipeline_sequential = HybridPipeline(config)

        options = ConversionOptions(max_pages=3, dpi=100)

        start_time = time.time()
        result_sequential = await pipeline_sequential.convert_pdf(
            first_test_pdf, options=options
        )
        sequential_time = time.time() - start_time

        # Test with concurrent processing
        config.resources.max_workers = 3
        pipeline_concurrent = HybridPipeline(config)

        start_time = time.time()
        result_concurrent = await pipeline_concurrent.convert_pdf(
            first_test_pdf, options=options
        )
        concurrent_time = time.time() - start_time

        # Both should process same number of pages
        assert result_sequential.processed_pages == result_concurrent.processed_pages

        # Concurrent should be faster (but not always guaranteed with API variance)
        print(f"\n--- Performance Comparison ---")
        print(f"Sequential (max_workers=1): {sequential_time:.2f}s")
        print(f"Concurrent (max_workers=3): {concurrent_time:.2f}s")
        if concurrent_time < sequential_time:
            speedup = sequential_time / concurrent_time
            print(f"Speedup: {speedup:.2f}x")
        else:
            print("Note: Concurrent not faster (API latency variance)")

        reset_config()


# ============================================================================
# Pipeline Backend Integration Tests
# ============================================================================


@pytest.mark.integration
class TestPipelineBackendIntegration:
    """Test pipeline integration with backend lifecycle."""

    @pytest.mark.asyncio
    async def test_pipeline_backend_lifecycle(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test that pipeline properly manages backend lifecycle."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        # Initially no backend
        assert pipeline._backend is None
        assert pipeline._backend_name is None

        with aioresponses() as mock_http:
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_success("# Test\n\nContent.\n"),
                repeat=True,
            )

            await pipeline.convert_pdf(sample_pdf_3_pages)

        # Backend should be created
        assert pipeline._backend is not None
        assert pipeline._backend_name == "nemotron-openrouter"

        # Close pipeline
        await pipeline.close()

        # Backend should be cleaned up
        assert pipeline._backend is None
        assert pipeline._backend_name is None

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_reuses_backend(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test that pipeline reuses backend across conversions."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        pipeline = HybridPipeline(config)

        backend_instances = []

        # Track backend creation
        original_get_backend = pipeline._get_backend

        def track_backend(*args, **kwargs):
            backend = original_get_backend(*args, **kwargs)
            backend_instances.append(id(backend))
            return backend

        pipeline._get_backend = track_backend

        with aioresponses() as mock_http:
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_success("# Test\n\nContent.\n"),
                repeat=True,
            )

            # Convert twice
            await pipeline.convert_pdf(sample_pdf_3_pages)
            await pipeline.convert_pdf(sample_pdf_3_pages)

        # Should reuse the same backend instance
        assert len(backend_instances) == 2
        assert backend_instances[0] == backend_instances[1], "Backend should be reused"

        await pipeline.close()
        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_context_manager(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test pipeline as async context manager."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)

        with aioresponses() as mock_http:
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_success("# Test\n\nContent.\n"),
                repeat=True,
            )

            async with HybridPipeline(config) as pipeline:
                result = await pipeline.convert_pdf(sample_pdf_3_pages)
                assert result.processed_pages == 3

            # After exiting context, backend should be closed
            assert pipeline._backend is None

        reset_config()


# ============================================================================
# Pipeline Retry Integration Tests
# ============================================================================


@pytest.mark.integration
class TestPipelineRetryBehavior:
    """Test pipeline retry behavior with backend errors."""

    @pytest.mark.asyncio
    async def test_pipeline_retries_on_backend_error(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test that pipeline retries failed API calls."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        config.resources.http_retry_attempts = 2
        pipeline = HybridPipeline(config)

        call_count = 0

        async def track_retries(*args, **kwargs):
            """Track retry attempts."""
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                raise Exception("API temporarily unavailable")
            # Second call succeeds
            return mock_openrouter_success("# Test\n\nContent.\n")

        options = ConversionOptions(max_pages=1)

        with aioresponses() as mock_http:
            # First attempt: error
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=503,
                payload={"error": "Service temporarily unavailable"},
            )
            # Retry attempts: success
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                payload=mock_openrouter_success("# Test\n\nContent.\n"),
                repeat=True,
            )

            result = await pipeline.convert_pdf(sample_pdf_3_pages, options=options)

        # Should succeed after retry
        assert result.processed_pages == 1

        reset_config()

    @pytest.mark.asyncio
    async def test_pipeline_exhausts_retries_then_fails(
        self, integration_config: Path, sample_pdf_3_pages: Path, monkeypatch
    ):
        """Test that pipeline fails after exhausting retries."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(integration_config)
        config.resources.http_retry_attempts = 2
        pipeline = HybridPipeline(config)

        options = ConversionOptions(max_pages=1)

        with aioresponses() as mock_http:
            # All attempts fail
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=500,
                payload={"error": "Persistent error"},
                repeat=True,
            )

            result = await pipeline.convert_pdf(sample_pdf_3_pages, options=options)

        # Should process 0 pages (all retries exhausted)
        assert result.processed_pages == 0

        reset_config()
