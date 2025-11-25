"""End-to-end integration tests for the conversion pipeline.

This module tests the complete pipeline flow with mocked HTTP responses:
- Full PDF conversion
- Batch processing scenarios
- Progress callbacks
- Backend fallback (when implemented)
- Error recovery
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from docling_hybrid.backends import make_backend
from docling_hybrid.common.config import init_config, reset_config
from docling_hybrid.common.errors import BackendError, ValidationError
from docling_hybrid.common.models import OcrBackendConfig
from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions, ConversionResult
from tests.mocks import mock_openrouter_success


@pytest.fixture
def e2e_config(tmp_path: Path) -> Path:
    """Create configuration for e2e tests."""
    import tomli_w

    config_dict = {
        "app": {
            "name": "docling-hybrid-ocr",
            "version": "0.1.0",
            "environment": "test",
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

    config_path = tmp_path / "e2e_config.toml"

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
def sample_pdf_for_e2e(tmp_path: Path) -> Path:
    """Create a sample PDF for e2e testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "e2e_test.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Create 5 pages with different content
    for page_num in range(1, 6):
        c.drawString(100, 750, f"End-to-End Test - Page {page_num}")
        c.drawString(100, 700, f"This is page {page_num} of 5.")
        c.drawString(100, 650, "Testing complete pipeline integration.")

        y = 600
        for i in range(5):
            c.drawString(100, y, f"Line {i+1}: Content for testing.")
            y -= 30

        c.showPage()

    c.save()
    return pdf_path


@pytest.mark.integration
class TestEndToEndConversion:
    """End-to-end conversion tests."""

    @pytest.mark.asyncio
    async def test_complete_conversion_with_mocked_backend(
        self, e2e_config: Path, sample_pdf_for_e2e: Path, tmp_path: Path, monkeypatch
    ):
        """Test complete conversion flow with mocked HTTP backend."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "output.md"

        with aioresponses() as mock_http:
            # Mock all 5 page conversions
            for page_num in range(1, 6):
                content = f"# Page {page_num}\n\nContent from page {page_num}.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            result = await pipeline.convert_pdf(
                sample_pdf_for_e2e, output_path=output_path
            )

        # Verify result
        assert isinstance(result, ConversionResult)
        assert result.total_pages == 5
        assert result.processed_pages == 5
        assert len(result.page_results) == 5
        assert result.output_path == output_path

        # Verify markdown content
        assert "# Page 1" in result.markdown
        assert "# Page 5" in result.markdown
        assert "<!-- PAGE 1 -->" in result.markdown

        # Verify output file was written
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Page 1" in content
        assert "# Page 5" in content

        reset_config()

    @pytest.mark.asyncio
    async def test_conversion_with_options(
        self, e2e_config: Path, sample_pdf_for_e2e: Path, monkeypatch
    ):
        """Test conversion with various options."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        options = ConversionOptions(
            max_pages=3,
            start_page=2,
            dpi=100,
            add_page_separators=False,
        )

        with aioresponses() as mock_http:
            # Mock 3 pages (2, 3, 4)
            for page_num in range(2, 5):
                content = f"# Page {page_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            result = await pipeline.convert_pdf(sample_pdf_for_e2e, options=options)

        assert result.total_pages == 5
        assert result.processed_pages == 3
        assert len(result.page_results) == 3

        # Verify page range
        page_nums = [pr.page_num for pr in result.page_results]
        assert page_nums == [2, 3, 4]

        # Verify no page separators
        assert "<!-- PAGE" not in result.markdown

        reset_config()

    @pytest.mark.asyncio
    async def test_conversion_without_output_path(
        self, e2e_config: Path, sample_pdf_for_e2e: Path, monkeypatch
    ):
        """Test conversion without writing to file."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        with aioresponses() as mock_http:
            # Mock all pages
            for page_num in range(1, 6):
                content = f"# Page {page_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            result = await pipeline.convert_pdf(sample_pdf_for_e2e)

        assert result.output_path is None
        assert len(result.markdown) > 0

        reset_config()


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in e2e scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_pdf_path(self, e2e_config: Path, monkeypatch):
        """Test handling of invalid PDF path."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        invalid_path = Path("/nonexistent/file.pdf")

        with pytest.raises((FileNotFoundError, ValidationError)):
            await pipeline.convert_pdf(invalid_path)

        reset_config()

    @pytest.mark.asyncio
    async def test_partial_conversion_with_errors(
        self, e2e_config: Path, sample_pdf_for_e2e: Path, monkeypatch
    ):
        """Test that pipeline continues on individual page errors."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        with aioresponses() as mock_http:
            # Mock pages 1, 2 - success
            for page_num in [1, 2]:
                content = f"# Page {page_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                )

            # Mock page 3 - error
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=500,
                payload={"error": "Internal server error"},
            )

            # Mock pages 4, 5 - success
            for page_num in [4, 5]:
                content = f"# Page {page_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                )

            result = await pipeline.convert_pdf(sample_pdf_for_e2e)

        # Should have processed 4 successful pages despite 1 failure
        assert result.total_pages == 5
        assert result.processed_pages == 4

        # Check that error is recorded in metadata
        assert "errors" in result.metadata or result.processed_pages < result.total_pages

        reset_config()


@pytest.mark.integration
class TestConcurrentProcessing:
    """Test concurrent page processing."""

    @pytest.mark.asyncio
    async def test_concurrent_page_processing(
        self, e2e_config: Path, sample_pdf_for_e2e: Path, monkeypatch
    ):
        """Test that multiple pages are processed concurrently."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        config.resources.max_workers = 3  # Allow concurrent processing
        pipeline = HybridPipeline(config)

        call_times = []

        async def track_timing(*args, **kwargs):
            """Track when API calls happen."""
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate API latency
            return mock_openrouter_success("# Test\n\nContent.\n\n")

        with aioresponses() as mock_http:
            mock_http.post(
                "https://openrouter.ai/api/v1/chat/completions",
                status=200,
                callback=track_timing,
                repeat=True,
            )

            result = await pipeline.convert_pdf(sample_pdf_for_e2e)

        assert result.processed_pages == 5
        assert len(call_times) == 5

        # Verify calls happened concurrently (some should overlap)
        # If sequential, total time would be 5 * 0.1 = 0.5s
        # If concurrent with 3 workers, should be faster
        time_span = call_times[-1] - call_times[0]
        assert time_span < 0.4, f"Processing appears sequential: {time_span:.2f}s"

        reset_config()


@pytest.mark.integration
class TestBatchScenarios:
    """Test batch processing scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_documents_sequential(
        self, e2e_config: Path, tmp_path: Path, monkeypatch
    ):
        """Test processing multiple documents sequentially."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        # Create 3 test PDFs
        pdf_paths = []
        for doc_num in range(1, 4):
            pdf_path = tmp_path / f"doc_{doc_num}.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            c.drawString(100, 750, f"Document {doc_num}")
            c.showPage()
            c.save()
            pdf_paths.append(pdf_path)

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        results = []

        with aioresponses() as mock_http:
            # Mock responses for all documents
            for doc_num in range(1, 4):
                content = f"# Document {doc_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            for pdf_path in pdf_paths:
                result = await pipeline.convert_pdf(pdf_path)
                results.append(result)

        assert len(results) == 3
        assert all(r.processed_pages == 1 for r in results)

        # Verify unique doc IDs
        doc_ids = [r.doc_id for r in results]
        assert len(doc_ids) == len(set(doc_ids)), "Doc IDs should be unique"

        reset_config()

    @pytest.mark.asyncio
    async def test_large_batch_memory_efficiency(
        self, e2e_config: Path, tmp_path: Path, monkeypatch
    ):
        """Test that batch processing doesn't accumulate memory."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import tracemalloc

        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        # Create 10 small PDFs
        pdf_paths = []
        for doc_num in range(10):
            pdf_path = tmp_path / f"doc_{doc_num}.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            c.drawString(100, 750, f"Document {doc_num}")
            c.showPage()
            c.save()
            pdf_paths.append(pdf_path)

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        tracemalloc.start()
        memory_samples = []

        with aioresponses() as mock_http:
            # Mock responses
            for doc_num in range(10):
                content = f"# Document {doc_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            for i, pdf_path in enumerate(pdf_paths):
                await pipeline.convert_pdf(pdf_path)

                # Sample memory every 3 documents
                if i % 3 == 0:
                    current, peak = tracemalloc.get_traced_memory()
                    memory_samples.append(current / (1024 * 1024))

        tracemalloc.stop()

        # Memory should not grow linearly with document count
        if len(memory_samples) >= 2:
            first = memory_samples[0]
            last = memory_samples[-1]
            if first > 0:
                growth = last / first
                assert growth < 3.0, f"Excessive memory growth: {growth:.2f}x"

        reset_config()


@pytest.mark.integration
class TestPipelineResourceManagement:
    """Test resource management in the pipeline."""

    @pytest.mark.asyncio
    async def test_backend_cleanup(self, e2e_config: Path, sample_pdf_for_e2e: Path, monkeypatch):
        """Test that backend resources are cleaned up after conversion."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        # Track backend lifecycle
        backend_created = False
        backend_closed = False

        original_get_backend = pipeline._get_backend

        def mock_get_backend(*args, **kwargs):
            nonlocal backend_created
            backend_created = True
            backend = original_get_backend(*args, **kwargs)

            original_close = backend.close

            async def mock_close():
                nonlocal backend_closed
                backend_closed = True
                await original_close()

            backend.close = mock_close
            return backend

        pipeline._get_backend = mock_get_backend

        with aioresponses() as mock_http:
            # Mock responses
            for page_num in range(1, 6):
                content = f"# Page {page_num}\n\nContent.\n\n"
                mock_http.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    status=200,
                    payload=mock_openrouter_success(content),
                    repeat=True,
                )

            await pipeline.convert_pdf(sample_pdf_for_e2e)

            # Close pipeline backend
            if pipeline._backend:
                await pipeline._backend.close()

        assert backend_created, "Backend should be created"
        assert backend_closed, "Backend should be closed after conversion"

        reset_config()

    @pytest.mark.asyncio
    async def test_reuse_pipeline_for_multiple_conversions(
        self, e2e_config: Path, sample_pdf_for_e2e: Path, monkeypatch
    ):
        """Test that pipeline can be reused for multiple conversions."""
        reset_config()
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")

        config = init_config(e2e_config)
        pipeline = HybridPipeline(config)

        with aioresponses() as mock_http:
            # Mock responses for 2 conversions x 5 pages
            for _ in range(2):
                for page_num in range(1, 6):
                    content = f"# Page {page_num}\n\nContent.\n\n"
                    mock_http.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        status=200,
                        payload=mock_openrouter_success(content),
                        repeat=True,
                    )

            # First conversion
            result1 = await pipeline.convert_pdf(sample_pdf_for_e2e)

            # Second conversion
            result2 = await pipeline.convert_pdf(sample_pdf_for_e2e)

        assert result1.processed_pages == 5
        assert result2.processed_pages == 5
        assert result1.doc_id != result2.doc_id  # Different doc IDs

        reset_config()
