"""Unit tests for batch processing functionality.

Tests the batch conversion module including:
- File discovery with glob patterns
- Parallel batch processing
- Error handling per file
- Summary report generation
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docling_hybrid.cli.batch import (
    BatchFileResult,
    BatchResult,
    convert_batch,
    convert_single_file,
    find_pdf_files,
    format_batch_summary,
)
from docling_hybrid.common.errors import BackendError, ValidationError
from docling_hybrid.orchestrator import ConversionOptions, ConversionResult


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_pdfs(tmp_path: Path) -> list[Path]:
    """Create sample PDF files for testing."""
    pdf_files = []
    for i in range(3):
        pdf = tmp_path / f"test_{i}.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%")
        pdf_files.append(pdf)
    return pdf_files


@pytest.fixture
def nested_pdfs(tmp_path: Path) -> tuple[Path, list[Path]]:
    """Create nested directory structure with PDFs."""
    # Create subdirectories
    subdir1 = tmp_path / "subdir1"
    subdir2 = tmp_path / "subdir2"
    subdir1.mkdir()
    subdir2.mkdir()

    pdf_files = []

    # Root level
    pdf = tmp_path / "root.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%")
    pdf_files.append(pdf)

    # Subdir 1
    pdf = subdir1 / "sub1.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%")
    pdf_files.append(pdf)

    # Subdir 2
    pdf = subdir2 / "sub2.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%")
    pdf_files.append(pdf)

    return tmp_path, pdf_files


@pytest.fixture
def mock_pipeline():
    """Create a mock HybridPipeline."""
    pipeline = MagicMock()
    pipeline.__aenter__ = AsyncMock(return_value=pipeline)
    pipeline.__aexit__ = AsyncMock()

    # Mock successful conversion
    mock_result = MagicMock(spec=ConversionResult)
    mock_result.processed_pages = 5
    mock_result.total_pages = 5
    mock_result.backend_name = "test-backend"
    mock_result.output_path = Path("/output/test.md")

    pipeline.convert_pdf = AsyncMock(return_value=mock_result)

    return pipeline


@pytest.fixture
def mock_config():
    """Create a mock Config."""
    config = MagicMock()
    config.resources.max_workers = 2
    return config


# ============================================================================
# File Discovery Tests
# ============================================================================

class TestFindPdfFiles:
    """Tests for find_pdf_files function."""

    def test_finds_pdf_files(self, sample_pdfs: list[Path], tmp_path: Path):
        """Test finding PDF files in directory."""
        found = find_pdf_files(tmp_path)

        assert len(found) == 3
        assert all(p.suffix == ".pdf" for p in found)
        assert set(found) == set(sample_pdfs)

    def test_finds_files_with_pattern(self, tmp_path: Path):
        """Test finding files with custom pattern."""
        # Create mixed files
        (tmp_path / "test_1.pdf").write_bytes(b"%PDF-1.4\n%")
        (tmp_path / "test_2.pdf").write_bytes(b"%PDF-1.4\n%")
        (tmp_path / "ignore_3.pdf").write_bytes(b"%PDF-1.4\n%")

        found = find_pdf_files(tmp_path, pattern="test_*.pdf")

        assert len(found) == 2
        assert all("test_" in p.name for p in found)

    def test_recursive_search(self, nested_pdfs: tuple[Path, list[Path]]):
        """Test recursive file search."""
        root_dir, expected_files = nested_pdfs

        # Non-recursive (should only find root level)
        found = find_pdf_files(root_dir, recursive=False)
        assert len(found) == 1

        # Recursive (should find all)
        found = find_pdf_files(root_dir, recursive=True)
        assert len(found) == 3
        assert set(found) == set(expected_files)

    def test_sorts_results(self, tmp_path: Path):
        """Test that results are sorted by name."""
        # Create files in random order
        (tmp_path / "c.pdf").write_bytes(b"%PDF-1.4\n%")
        (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4\n%")
        (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4\n%")

        found = find_pdf_files(tmp_path)

        names = [p.name for p in found]
        assert names == ["a.pdf", "b.pdf", "c.pdf"]

    def test_error_on_nonexistent_dir(self):
        """Test error when directory doesn't exist."""
        with pytest.raises(ValueError, match="does not exist"):
            find_pdf_files(Path("/nonexistent/path"))

    def test_error_on_file_input(self, tmp_path: Path):
        """Test error when input is a file, not directory."""
        file_path = tmp_path / "test.pdf"
        file_path.write_bytes(b"%PDF-1.4\n%")

        with pytest.raises(ValueError, match="not a directory"):
            find_pdf_files(file_path)

    def test_empty_directory(self, tmp_path: Path):
        """Test handling of empty directory."""
        found = find_pdf_files(tmp_path)
        assert found == []


# ============================================================================
# Single File Conversion Tests
# ============================================================================

class TestConvertSingleFile:
    """Tests for convert_single_file function."""

    @pytest.mark.asyncio
    async def test_successful_conversion(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_pipeline,
    ):
        """Test successful single file conversion."""
        pdf_path = sample_pdfs[0]
        output_dir = tmp_path / "output"

        result = await convert_single_file(
            pdf_path=pdf_path,
            output_dir=output_dir,
            pipeline=mock_pipeline,
            options=ConversionOptions(),
        )

        assert result.success is True
        assert result.source_path == pdf_path
        assert result.result is not None
        assert result.error is None

        # Check pipeline was called correctly
        mock_pipeline.convert_pdf.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_output_directory(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_pipeline,
    ):
        """Test that output directory is created."""
        pdf_path = sample_pdfs[0]
        output_dir = tmp_path / "nested" / "output"

        await convert_single_file(
            pdf_path=pdf_path,
            output_dir=output_dir,
            pipeline=mock_pipeline,
            options=ConversionOptions(),
        )

        assert output_dir.exists()
        assert output_dir.is_dir()

    @pytest.mark.asyncio
    async def test_handles_validation_error(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_pipeline,
    ):
        """Test handling of validation errors."""
        pdf_path = sample_pdfs[0]
        output_dir = tmp_path / "output"

        # Make pipeline raise ValidationError
        mock_pipeline.convert_pdf.side_effect = ValidationError(
            "Invalid PDF",
            details={"path": str(pdf_path)}
        )

        result = await convert_single_file(
            pdf_path=pdf_path,
            output_dir=output_dir,
            pipeline=mock_pipeline,
            options=ConversionOptions(),
        )

        assert result.success is False
        assert result.error is not None
        assert "Invalid PDF" in result.error

    @pytest.mark.asyncio
    async def test_handles_backend_error(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_pipeline,
    ):
        """Test handling of backend errors."""
        pdf_path = sample_pdfs[0]
        output_dir = tmp_path / "output"

        # Make pipeline raise BackendError
        mock_pipeline.convert_pdf.side_effect = BackendError(
            "Backend failed",
            backend_name="test-backend"
        )

        result = await convert_single_file(
            pdf_path=pdf_path,
            output_dir=output_dir,
            pipeline=mock_pipeline,
            options=ConversionOptions(),
        )

        assert result.success is False
        assert result.error is not None
        assert "Backend failed" in result.error

    @pytest.mark.asyncio
    async def test_handles_generic_exception(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_pipeline,
    ):
        """Test handling of unexpected exceptions."""
        pdf_path = sample_pdfs[0]
        output_dir = tmp_path / "output"

        # Make pipeline raise generic exception
        mock_pipeline.convert_pdf.side_effect = RuntimeError("Unexpected error")

        result = await convert_single_file(
            pdf_path=pdf_path,
            output_dir=output_dir,
            pipeline=mock_pipeline,
            options=ConversionOptions(),
        )

        assert result.success is False
        assert result.error is not None
        assert "RuntimeError" in result.error
        assert "Unexpected error" in result.error


# ============================================================================
# Batch Conversion Tests
# ============================================================================

class TestConvertBatch:
    """Tests for convert_batch function."""

    @pytest.mark.asyncio
    async def test_successful_batch(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_config,
    ):
        """Test successful batch conversion."""
        output_dir = tmp_path / "output"

        with patch("docling_hybrid.cli.batch.HybridPipeline") as MockPipeline:
            # Setup mock
            mock_pipeline = MagicMock()
            mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
            mock_pipeline.__aexit__ = AsyncMock()

            mock_result = MagicMock(spec=ConversionResult)
            mock_result.processed_pages = 5
            mock_result.total_pages = 5
            mock_result.backend_name = "test-backend"

            mock_pipeline.convert_pdf = AsyncMock(return_value=mock_result)
            MockPipeline.return_value = mock_pipeline

            # Run batch
            result = await convert_batch(
                input_paths=sample_pdfs,
                output_dir=output_dir,
                config=mock_config,
                parallel=2,
            )

            # Check results
            assert result.total_files == 3
            assert result.successful == 3
            assert result.failed == 0
            assert result.success_rate == 100.0
            assert len(result.file_results) == 3

    @pytest.mark.asyncio
    async def test_parallel_processing(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_config,
    ):
        """Test that files are processed in parallel."""
        output_dir = tmp_path / "output"

        with patch("docling_hybrid.cli.batch.HybridPipeline") as MockPipeline:
            # Setup mock with delay to test parallelism
            mock_pipeline = MagicMock()
            mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
            mock_pipeline.__aexit__ = AsyncMock()

            async def slow_convert(*args, **kwargs):
                await asyncio.sleep(0.1)
                mock_result = MagicMock(spec=ConversionResult)
                mock_result.processed_pages = 5
                return mock_result

            mock_pipeline.convert_pdf = slow_convert
            MockPipeline.return_value = mock_pipeline

            # Run batch with parallel=3 (all at once)
            import time
            start = time.time()
            result = await convert_batch(
                input_paths=sample_pdfs,
                output_dir=output_dir,
                config=mock_config,
                parallel=3,
            )
            elapsed = time.time() - start

            # With parallelism, should take ~0.1s (not 0.3s)
            assert elapsed < 0.25, f"Took {elapsed}s, expected <0.25s"
            assert result.successful == 3

    @pytest.mark.asyncio
    async def test_handles_partial_failures(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_config,
    ):
        """Test handling when some files fail."""
        output_dir = tmp_path / "output"

        with patch("docling_hybrid.cli.batch.HybridPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
            mock_pipeline.__aexit__ = AsyncMock()

            # Make second file fail
            call_count = 0

            async def sometimes_fail(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise ValidationError("Test error")
                mock_result = MagicMock(spec=ConversionResult)
                mock_result.processed_pages = 5
                return mock_result

            mock_pipeline.convert_pdf = sometimes_fail
            MockPipeline.return_value = mock_pipeline

            result = await convert_batch(
                input_paths=sample_pdfs,
                output_dir=output_dir,
                config=mock_config,
                parallel=1,
            )

            # Check results
            assert result.total_files == 3
            assert result.successful == 2
            assert result.failed == 1
            assert result.success_rate == pytest.approx(66.7, abs=0.1)

    @pytest.mark.asyncio
    async def test_error_on_empty_input(
        self,
        tmp_path: Path,
        mock_config,
    ):
        """Test error when input_paths is empty."""
        with pytest.raises(ValueError, match="No input files"):
            await convert_batch(
                input_paths=[],
                output_dir=tmp_path / "output",
                config=mock_config,
            )

    @pytest.mark.asyncio
    async def test_creates_output_directory(
        self,
        sample_pdfs: list[Path],
        tmp_path: Path,
        mock_config,
    ):
        """Test that output directory is created."""
        output_dir = tmp_path / "nested" / "output"

        with patch("docling_hybrid.cli.batch.HybridPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
            mock_pipeline.__aexit__ = AsyncMock()
            mock_result = MagicMock(spec=ConversionResult)
            mock_result.processed_pages = 5
            mock_pipeline.convert_pdf = AsyncMock(return_value=mock_result)
            MockPipeline.return_value = mock_pipeline

            await convert_batch(
                input_paths=sample_pdfs,
                output_dir=output_dir,
                config=mock_config,
            )

            assert output_dir.exists()


# ============================================================================
# Batch Result Tests
# ============================================================================

class TestBatchResult:
    """Tests for BatchResult class."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = BatchResult(
            total_files=10,
            successful=7,
            failed=3,
        )
        assert result.success_rate == 70.0

    def test_success_rate_zero_files(self):
        """Test success rate with zero files."""
        result = BatchResult(
            total_files=0,
            successful=0,
            failed=0,
        )
        assert result.success_rate == 0.0

    def test_success_rate_all_success(self):
        """Test success rate with all successes."""
        result = BatchResult(
            total_files=5,
            successful=5,
            failed=0,
        )
        assert result.success_rate == 100.0


# ============================================================================
# Summary Formatting Tests
# ============================================================================

class TestFormatBatchSummary:
    """Tests for format_batch_summary function."""

    def test_formats_successful_batch(self):
        """Test formatting of fully successful batch."""
        mock_result = MagicMock(spec=ConversionResult)
        mock_result.processed_pages = 10

        file_results = [
            BatchFileResult(
                source_path=Path("test1.pdf"),
                success=True,
                result=mock_result,
            ),
            BatchFileResult(
                source_path=Path("test2.pdf"),
                success=True,
                result=mock_result,
            ),
        ]

        result = BatchResult(
            total_files=2,
            successful=2,
            failed=0,
            file_results=file_results,
            elapsed_seconds=5.5,
        )

        summary = format_batch_summary(result)

        assert "Total files: 2" in summary
        assert "Successful: 2" in summary
        assert "Failed: 0" in summary
        assert "100.0%" in summary
        assert "5.5s" in summary
        assert "test1.pdf" in summary
        assert "test2.pdf" in summary

    def test_formats_batch_with_failures(self):
        """Test formatting of batch with failures."""
        mock_result = MagicMock(spec=ConversionResult)
        mock_result.processed_pages = 10

        file_results = [
            BatchFileResult(
                source_path=Path("test1.pdf"),
                success=True,
                result=mock_result,
            ),
            BatchFileResult(
                source_path=Path("test2.pdf"),
                success=False,
                error="Validation failed: Test error",
            ),
        ]

        result = BatchResult(
            total_files=2,
            successful=1,
            failed=1,
            file_results=file_results,
            elapsed_seconds=5.5,
        )

        summary = format_batch_summary(result)

        assert "Total files: 2" in summary
        assert "Successful: 1" in summary
        assert "Failed: 1" in summary
        assert "Failed Files" in summary
        assert "test2.pdf" in summary
        assert "Validation failed" in summary

    def test_truncates_long_errors(self):
        """Test that long errors are truncated."""
        long_error = "x" * 200

        file_results = [
            BatchFileResult(
                source_path=Path("test.pdf"),
                success=False,
                error=long_error,
            ),
        ]

        result = BatchResult(
            total_files=1,
            successful=0,
            failed=1,
            file_results=file_results,
        )

        summary = format_batch_summary(result)

        # Should be truncated to ~100 chars
        assert long_error not in summary
        assert "..." in summary
