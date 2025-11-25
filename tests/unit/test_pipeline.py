"""Unit tests for the HybridPipeline orchestrator."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docling_hybrid.common.config import Config, init_config
from docling_hybrid.common.errors import ValidationError
from docling_hybrid.common.models import PageResult
from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions, ConversionResult


@pytest.fixture
def test_config(test_config_dict):
    """Create a test config object."""
    from docling_hybrid.common.config import Config
    return Config.model_validate(test_config_dict)


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a minimal test PDF file."""
    pdf_path = tmp_path / "test.pdf"
    # Minimal PDF header - just enough to not fail validation
    # This is a 1-page minimal PDF
    minimal_pdf = (
        b'%PDF-1.4\n'
        b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
        b'2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n'
        b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n'
        b'xref\n'
        b'0 4\n'
        b'0000000000 65535 f\n'
        b'0000000009 00000 n\n'
        b'0000000058 00000 n\n'
        b'0000000115 00000 n\n'
        b'trailer<</Size 4/Root 1 0 R>>\n'
        b'startxref\n'
        b'178\n'
        b'%%EOF'
    )
    pdf_path.write_bytes(minimal_pdf)
    return pdf_path


class TestHybridPipelineInit:
    """Tests for HybridPipeline initialization."""

    def test_init(self, test_config):
        """Test pipeline initialization."""
        pipeline = HybridPipeline(test_config)

        assert pipeline.config == test_config
        assert pipeline._backend is None
        assert pipeline._backend_name is None

    def test_get_backend_default(self, test_config, with_api_key):
        """Test getting default backend."""
        pipeline = HybridPipeline(test_config)

        backend = pipeline._get_backend()

        assert backend is not None
        assert backend.name == "nemotron-openrouter"
        assert pipeline._backend is backend
        assert pipeline._backend_name == "nemotron-openrouter"

    def test_get_backend_reuse(self, test_config, with_api_key):
        """Test backend is reused when same name."""
        pipeline = HybridPipeline(test_config)

        backend1 = pipeline._get_backend("nemotron-openrouter")
        backend2 = pipeline._get_backend("nemotron-openrouter")

        assert backend1 is backend2


class TestHybridPipelineProcessSinglePage:
    """Tests for _process_single_page method."""

    @pytest.mark.asyncio
    async def test_process_single_page_success(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test successful single page processing."""
        pipeline = HybridPipeline(test_config)

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline._process_single_page(
                pdf_path=sample_pdf_path,
                page_idx=0,
                dpi=150,
                backend=mock_backend,
                backend_name="mock-backend",
                doc_id="doc-123",
                total_pages=5,
            )

        assert result is not None
        assert isinstance(result, PageResult)
        assert result.page_num == 1
        assert result.doc_id == "doc-123"
        assert result.backend_name == "mock-backend"
        assert result.content == "# Mock Page\n\nContent here."
        mock_backend.page_to_markdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_single_page_rendering_error(
        self, test_config, sample_pdf_path, mock_backend
    ):
        """Test handling of rendering error."""
        pipeline = HybridPipeline(test_config)

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            side_effect=Exception("Rendering failed"),
        ):
            result = await pipeline._process_single_page(
                pdf_path=sample_pdf_path,
                page_idx=0,
                dpi=150,
                backend=mock_backend,
                backend_name="mock-backend",
                doc_id="doc-123",
                total_pages=5,
            )

        assert result is None
        mock_backend.page_to_markdown.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_single_page_backend_error(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test handling of backend error."""
        pipeline = HybridPipeline(test_config)
        mock_backend.page_to_markdown.side_effect = Exception("Backend failed")

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline._process_single_page(
                pdf_path=sample_pdf_path,
                page_idx=0,
                dpi=150,
                backend=mock_backend,
                backend_name="mock-backend",
                doc_id="doc-123",
                total_pages=5,
            )

        assert result is None
        mock_backend.page_to_markdown.assert_called_once()


class TestHybridPipelineConvertPdf:
    """Tests for convert_pdf method."""

    @pytest.mark.asyncio
    async def test_convert_pdf_file_not_found(self, test_config):
        """Test error when PDF file doesn't exist."""
        pipeline = HybridPipeline(test_config)

        with pytest.raises(ValidationError) as exc_info:
            await pipeline.convert_pdf(Path("/nonexistent/file.pdf"))

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_convert_pdf_single_page(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test converting a single-page PDF."""
        pipeline = HybridPipeline(test_config)

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=1,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(sample_pdf_path)

        assert isinstance(result, ConversionResult)
        assert result.total_pages == 1
        assert result.processed_pages == 1
        assert len(result.page_results) == 1
        assert result.markdown == "# Mock Page\n\nContent here."
        assert result.output_path.exists()
        mock_backend.page_to_markdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_pdf_multiple_pages(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test converting a multi-page PDF."""
        pipeline = HybridPipeline(test_config)

        # Mock backend to return different content per page
        page_contents = ["# Page 1", "# Page 2", "# Page 3"]
        mock_backend.page_to_markdown.side_effect = page_contents

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=3,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(sample_pdf_path)

        assert result.total_pages == 3
        assert result.processed_pages == 3
        assert len(result.page_results) == 3
        # Check pages are in order
        for i, page_result in enumerate(result.page_results):
            assert page_result.page_num == i + 1
        assert mock_backend.page_to_markdown.call_count == 3

    @pytest.mark.asyncio
    async def test_convert_pdf_with_options(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test converting with custom options."""
        pipeline = HybridPipeline(test_config)

        options = ConversionOptions(
            dpi=100,
            max_pages=2,
            add_page_separators=True,
        )

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=5,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(sample_pdf_path, options=options)

        assert result.total_pages == 5
        assert result.processed_pages == 2  # Only 2 pages due to max_pages
        assert "<!-- PAGE" in result.markdown  # Has page separators
        assert mock_backend.page_to_markdown.call_count == 2

    @pytest.mark.asyncio
    async def test_convert_pdf_partial_failure(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test conversion continues after page failure."""
        pipeline = HybridPipeline(test_config)

        # Mock backend to fail on second page
        mock_backend.page_to_markdown.side_effect = [
            "# Page 1",
            Exception("OCR failed"),
            "# Page 3",
        ]

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=3,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(sample_pdf_path)

        assert result.total_pages == 3
        assert result.processed_pages == 2  # Pages 1 and 3 succeeded
        assert len(result.page_results) == 2
        # Verify the successful pages
        assert result.page_results[0].page_num == 1
        assert result.page_results[1].page_num == 3

    @pytest.mark.asyncio
    async def test_convert_pdf_concurrent_execution(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test that pages are processed concurrently."""
        pipeline = HybridPipeline(test_config)

        # Track call order
        call_order = []

        async def track_call(image_bytes, page_num, doc_id):
            call_order.append(("start", page_num))
            await asyncio.sleep(0.01)  # Simulate work
            call_order.append(("end", page_num))
            return f"# Page {page_num}"

        mock_backend.page_to_markdown.side_effect = track_call

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=3,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(sample_pdf_path)

        # Verify concurrent execution
        # With concurrent execution, we should see multiple "start" events
        # before the first "end" event (if max_workers >= 2)
        start_events = [e for e in call_order if e[0] == "start"]
        first_end_idx = next(i for i, e in enumerate(call_order) if e[0] == "end")

        # At least 2 pages should start before the first one ends
        # (assuming max_workers >= 2 in test config)
        starts_before_first_end = len([e for e in call_order[:first_end_idx] if e[0] == "start"])
        if test_config.resources.max_workers >= 2:
            assert starts_before_first_end >= 2, "Pages should process concurrently"

    @pytest.mark.asyncio
    async def test_convert_pdf_respects_semaphore_limit(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test that semaphore limits concurrent execution."""
        # Set max_workers to 1 for this test
        test_config.resources.max_workers = 1
        pipeline = HybridPipeline(test_config)

        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrency(image_bytes, page_num, doc_id):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return f"# Page {page_num}"

        mock_backend.page_to_markdown.side_effect = track_concurrency

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=3,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            await pipeline.convert_pdf(sample_pdf_path)

        # With max_workers=1, we should never have more than 1 concurrent execution
        assert max_concurrent <= 1, "Semaphore should limit concurrency"

    @pytest.mark.asyncio
    async def test_convert_pdf_custom_output_path(
        self, test_config, sample_pdf_path, tmp_path, sample_image_bytes, mock_backend
    ):
        """Test specifying custom output path."""
        pipeline = HybridPipeline(test_config)
        output_path = tmp_path / "custom_output.md"

        with patch(
            "docling_hybrid.orchestrator.pipeline.make_backend",
            return_value=mock_backend,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.get_page_count",
            return_value=1,
        ), patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(sample_pdf_path, output_path=output_path)

        assert result.output_path == output_path
        assert output_path.exists()


class TestHybridPipelineContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager(self, test_config, with_api_key):
        """Test pipeline as async context manager."""
        async with HybridPipeline(test_config) as pipeline:
            assert pipeline is not None
            # Backend should be cleaned up on exit

    @pytest.mark.asyncio
    async def test_close_cleans_backend(self, test_config, with_api_key):
        """Test that close() cleans up backend."""
        pipeline = HybridPipeline(test_config)

        # Create a backend
        backend = pipeline._get_backend()
        assert pipeline._backend is not None

        # Close pipeline
        await pipeline.close()

        # Backend should be cleared
        assert pipeline._backend is None
        assert pipeline._backend_name is None


class TestHybridPipelineProgressCallbacks:
    """Tests for progress callback integration."""

    @pytest.mark.asyncio
    async def test_convert_with_progress_callback(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test conversion with progress callback."""
        pipeline = HybridPipeline(test_config)
        pipeline._backend = mock_backend
        pipeline._backend_name = "mock-backend"

        # Track callback invocations
        events = []

        class TrackingCallback:
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                events.append(("start", doc_id, total_pages))

            def on_page_start(self, page_num: int, total: int) -> None:
                events.append(("page_start", page_num, total))

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                events.append(("page_complete", page_num, total))

            def on_page_error(self, page_num: int, error: Exception) -> None:
                events.append(("page_error", page_num, str(error)))

            def on_conversion_complete(self, result) -> None:
                events.append(("complete", result.doc_id))

            def on_conversion_error(self, error: Exception) -> None:
                events.append(("error", str(error)))

        callback = TrackingCallback()

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(
                pdf_path=sample_pdf_path,
                progress_callback=callback,
            )

        # Verify callback was invoked
        assert len(events) >= 3  # start, page_start, page_complete, complete
        assert events[0][0] == "start"
        assert events[-1][0] == "complete"
        assert events[-1][1] == result.doc_id

    @pytest.mark.asyncio
    async def test_convert_without_progress_callback(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test conversion works without progress callback."""
        pipeline = HybridPipeline(test_config)
        pipeline._backend = mock_backend
        pipeline._backend_name = "mock-backend"

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            result = await pipeline.convert_pdf(
                pdf_path=sample_pdf_path,
                progress_callback=None,  # Explicitly None
            )

        assert result is not None
        assert result.processed_pages == 1

    @pytest.mark.asyncio
    async def test_callback_error_does_not_stop_conversion(
        self, test_config, sample_pdf_path, sample_image_bytes, mock_backend
    ):
        """Test that callback errors don't stop conversion."""
        pipeline = HybridPipeline(test_config)
        pipeline._backend = mock_backend
        pipeline._backend_name = "mock-backend"

        class ErrorCallback:
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                raise ValueError("Callback error")

            def on_page_start(self, page_num: int, total: int) -> None:
                raise ValueError("Callback error")

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                raise ValueError("Callback error")

            def on_page_error(self, page_num: int, error: Exception) -> None:
                raise ValueError("Callback error")

            def on_conversion_complete(self, result) -> None:
                raise ValueError("Callback error")

            def on_conversion_error(self, error: Exception) -> None:
                raise ValueError("Callback error")

        callback = ErrorCallback()

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            return_value=sample_image_bytes,
        ):
            # Should not raise despite callback errors
            result = await pipeline.convert_pdf(
                pdf_path=sample_pdf_path,
                progress_callback=callback,
            )

        assert result is not None
        assert result.processed_pages == 1

    @pytest.mark.asyncio
    async def test_page_error_callback_invoked(
        self, test_config, sample_pdf_path, mock_backend
    ):
        """Test that on_page_error is called when page processing fails."""
        pipeline = HybridPipeline(test_config)
        pipeline._backend = mock_backend
        pipeline._backend_name = "mock-backend"

        page_errors = []

        class TrackingCallback:
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                pass

            def on_page_error(self, page_num: int, error: Exception) -> None:
                page_errors.append((page_num, str(error)))

            def on_conversion_complete(self, result) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = TrackingCallback()

        with patch(
            "docling_hybrid.orchestrator.pipeline.render_page_to_png_bytes",
            side_effect=RuntimeError("Render failed"),
        ):
            result = await pipeline.convert_pdf(
                pdf_path=sample_pdf_path,
                progress_callback=callback,
            )

        # Should have called on_page_error
        assert len(page_errors) == 1
        assert page_errors[0][0] == 1
        assert "Render failed" in page_errors[0][1]

    @pytest.mark.asyncio
    async def test_conversion_error_callback_invoked(
        self, test_config, sample_pdf_path, mock_backend
    ):
        """Test that on_conversion_error is called when conversion fails."""
        pipeline = HybridPipeline(test_config)

        conversion_errors = []

        class TrackingCallback:
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(self, page_num: int, total: int, result) -> None:
                pass

            def on_page_error(self, page_num: int, error: Exception) -> None:
                pass

            def on_conversion_complete(self, result) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                conversion_errors.append(str(error))

        callback = TrackingCallback()

        # Cause an error by using non-existent PDF
        non_existent_pdf = sample_pdf_path.parent / "non_existent.pdf"

        with pytest.raises(ValidationError):
            await pipeline.convert_pdf(
                pdf_path=non_existent_pdf,
                progress_callback=callback,
            )

        # Should have called on_conversion_error
        assert len(conversion_errors) == 1
        assert "not found" in conversion_errors[0].lower()
