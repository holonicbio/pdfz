"""Unit tests for PDF rendering functionality.

Tests cover:
- Single page rendering
- Batch rendering with PdfRenderer
- Memory optimization features
- Error handling
- Edge cases
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from docling_hybrid.common.errors import RenderingError, ValidationError
from docling_hybrid.renderer.core import (
    PdfRenderer,
    get_page_count,
    render_page_to_png_bytes,
    render_pdf_pages,
    render_region_to_png_bytes,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Create a minimal test PDF with a single page."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        pytest.skip("reportlab not available for PDF generation")

    pdf_path = tmp_path / "test_document.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Page 1
    c.drawString(100, 750, "Test Document - Page 1")
    c.drawString(100, 700, "This is a test page for renderer testing.")
    c.showPage()

    c.save()
    return pdf_path


@pytest.fixture
def multipage_pdf_path(tmp_path: Path) -> Path:
    """Create a test PDF with multiple pages."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        pytest.skip("reportlab not available for PDF generation")

    pdf_path = tmp_path / "multipage_document.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Page 1
    c.drawString(100, 750, "Test Document - Page 1")
    c.showPage()

    # Page 2
    c.drawString(100, 750, "Test Document - Page 2")
    c.showPage()

    # Page 3
    c.drawString(100, 750, "Test Document - Page 3")
    c.showPage()

    c.save()
    return pdf_path


@pytest.fixture
def nonexistent_pdf_path(tmp_path: Path) -> Path:
    """Path to a PDF that doesn't exist."""
    return tmp_path / "nonexistent.pdf"


# ============================================================================
# Tests: get_page_count
# ============================================================================


def test_get_page_count_single_page(sample_pdf_path):
    """Test getting page count for single-page PDF."""
    count = get_page_count(sample_pdf_path)
    assert count == 1


def test_get_page_count_multiple_pages(multipage_pdf_path):
    """Test getting page count for multi-page PDF."""
    count = get_page_count(multipage_pdf_path)
    assert count == 3


def test_get_page_count_nonexistent_file(nonexistent_pdf_path):
    """Test error handling for nonexistent PDF."""
    with pytest.raises(ValidationError) as exc_info:
        get_page_count(nonexistent_pdf_path)

    assert "not found" in str(exc_info.value).lower()
    assert str(nonexistent_pdf_path) in str(exc_info.value)


# ============================================================================
# Tests: render_page_to_png_bytes
# ============================================================================


def test_render_page_basic(sample_pdf_path):
    """Test basic page rendering."""
    image_bytes = render_page_to_png_bytes(sample_pdf_path, 0, dpi=72)

    # Verify PNG format
    assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')

    # Verify image can be loaded
    image = Image.open(io.BytesIO(image_bytes))
    assert image.format == "PNG"
    assert image.mode == "RGB"
    assert image.size[0] > 0
    assert image.size[1] > 0


def test_render_page_different_dpi(sample_pdf_path):
    """Test rendering at different DPI values."""
    # Low DPI
    image_72 = render_page_to_png_bytes(sample_pdf_path, 0, dpi=72)
    size_72 = Image.open(io.BytesIO(image_72)).size

    # High DPI
    image_200 = render_page_to_png_bytes(sample_pdf_path, 0, dpi=200)
    size_200 = Image.open(io.BytesIO(image_200)).size

    # Higher DPI should produce larger images
    assert size_200[0] > size_72[0]
    assert size_200[1] > size_72[1]


def test_render_page_invalid_page_index_negative(sample_pdf_path):
    """Test error for negative page index."""
    with pytest.raises(ValidationError) as exc_info:
        render_page_to_png_bytes(sample_pdf_path, -1)

    assert "non-negative" in str(exc_info.value).lower()


def test_render_page_invalid_page_index_out_of_range(sample_pdf_path):
    """Test error for page index out of range."""
    with pytest.raises(ValidationError) as exc_info:
        render_page_to_png_bytes(sample_pdf_path, 999)

    assert "out of range" in str(exc_info.value).lower()


def test_render_page_invalid_dpi_too_low(sample_pdf_path):
    """Test error for DPI too low."""
    with pytest.raises(ValidationError) as exc_info:
        render_page_to_png_bytes(sample_pdf_path, 0, dpi=50)

    assert "between 72 and 600" in str(exc_info.value)


def test_render_page_invalid_dpi_too_high(sample_pdf_path):
    """Test error for DPI too high."""
    with pytest.raises(ValidationError) as exc_info:
        render_page_to_png_bytes(sample_pdf_path, 0, dpi=1000)

    assert "between 72 and 600" in str(exc_info.value)


def test_render_page_nonexistent_file(nonexistent_pdf_path):
    """Test error for nonexistent PDF file."""
    with pytest.raises(ValidationError) as exc_info:
        render_page_to_png_bytes(nonexistent_pdf_path, 0)

    assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Tests: PdfRenderer (Memory-Efficient Batch Rendering)
# ============================================================================


def test_pdf_renderer_context_manager(sample_pdf_path):
    """Test PdfRenderer context manager basic usage."""
    with PdfRenderer(sample_pdf_path) as renderer:
        assert renderer.page_count == 1
        assert renderer._pdf is not None


def test_pdf_renderer_closes_pdf(sample_pdf_path):
    """Test that PdfRenderer properly closes PDF on exit."""
    renderer = PdfRenderer(sample_pdf_path)
    with renderer:
        pass
    assert renderer._pdf is None


def test_pdf_renderer_render_single_page(sample_pdf_path):
    """Test rendering a single page with PdfRenderer."""
    with PdfRenderer(sample_pdf_path) as renderer:
        image_bytes = renderer.render_page(0, dpi=72)

        # Verify PNG format
        assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')

        # Verify image properties
        image = Image.open(io.BytesIO(image_bytes))
        assert image.format == "PNG"
        assert image.mode == "RGB"


def test_pdf_renderer_render_multiple_pages(multipage_pdf_path):
    """Test rendering multiple pages efficiently."""
    with PdfRenderer(multipage_pdf_path) as renderer:
        assert renderer.page_count == 3

        # Render all pages
        pages = []
        for i in range(renderer.page_count):
            image_bytes = renderer.render_page(i, dpi=72)
            pages.append(image_bytes)

        assert len(pages) == 3
        # All pages should be valid PNGs
        for page_bytes in pages:
            assert page_bytes.startswith(b'\x89PNG\r\n\x1a\n')


def test_pdf_renderer_batch_render_specific_pages(multipage_pdf_path):
    """Test batch rendering specific pages."""
    with PdfRenderer(multipage_pdf_path) as renderer:
        # Render pages 0 and 2
        images = renderer.render_pages([0, 2], dpi=72)

        assert len(images) == 2
        for img_bytes in images:
            assert img_bytes.startswith(b'\x89PNG\r\n\x1a\n')


def test_pdf_renderer_batch_render_all_pages(multipage_pdf_path):
    """Test batch rendering all pages (None argument)."""
    with PdfRenderer(multipage_pdf_path) as renderer:
        # Render all pages
        images = renderer.render_pages(dpi=72)

        assert len(images) == 3
        for img_bytes in images:
            assert img_bytes.startswith(b'\x89PNG\r\n\x1a\n')


def test_pdf_renderer_used_outside_context_manager(sample_pdf_path):
    """Test error when using PdfRenderer outside context manager."""
    renderer = PdfRenderer(sample_pdf_path)

    # Should raise RuntimeError when accessing page_count
    with pytest.raises(RuntimeError) as exc_info:
        _ = renderer.page_count

    assert "context manager" in str(exc_info.value).lower()

    # Should raise RuntimeError when rendering
    with pytest.raises(RuntimeError) as exc_info:
        renderer.render_page(0)

    assert "context manager" in str(exc_info.value).lower()


def test_pdf_renderer_invalid_page_index(sample_pdf_path):
    """Test PdfRenderer error handling for invalid page index."""
    with PdfRenderer(sample_pdf_path) as renderer:
        with pytest.raises(ValidationError) as exc_info:
            renderer.render_page(999)

        assert "out of range" in str(exc_info.value).lower()


def test_pdf_renderer_nonexistent_file(nonexistent_pdf_path):
    """Test PdfRenderer error for nonexistent file."""
    with pytest.raises(ValidationError) as exc_info:
        PdfRenderer(nonexistent_pdf_path)

    assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Tests: render_pdf_pages (Convenience Function)
# ============================================================================


def test_render_pdf_pages_specific_pages(multipage_pdf_path):
    """Test convenience function for batch rendering."""
    images = render_pdf_pages(multipage_pdf_path, [0, 2], dpi=72)

    assert len(images) == 2
    for img_bytes in images:
        assert img_bytes.startswith(b'\x89PNG\r\n\x1a\n')


def test_render_pdf_pages_all_pages(multipage_pdf_path):
    """Test batch rendering all pages with convenience function."""
    images = render_pdf_pages(multipage_pdf_path, dpi=72)

    assert len(images) == 3
    for img_bytes in images:
        assert img_bytes.startswith(b'\x89PNG\r\n\x1a\n')


def test_render_pdf_pages_single_page(sample_pdf_path):
    """Test batch rendering with single page."""
    images = render_pdf_pages(sample_pdf_path, [0], dpi=72)

    assert len(images) == 1
    assert images[0].startswith(b'\x89PNG\r\n\x1a\n')


def test_render_pdf_pages_auto_cleanup(multipage_pdf_path):
    """Test that render_pdf_pages properly cleans up resources."""
    # Should not raise any warnings or errors
    images = render_pdf_pages(multipage_pdf_path, [0], dpi=72)
    assert len(images) == 1


# ============================================================================
# Tests: render_region_to_png_bytes
# ============================================================================


def test_render_region_basic(sample_pdf_path):
    """Test basic region rendering."""
    # Render a region (rough center of page)
    bbox = (100, 300, 500, 500)  # x1, y1, x2, y2 in PDF points
    image_bytes = render_region_to_png_bytes(
        sample_pdf_path,
        0,
        bbox,
        dpi=72,
        padding=10,
    )

    # Verify PNG format
    assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')

    # Verify image can be loaded
    image = Image.open(io.BytesIO(image_bytes))
    assert image.format == "PNG"
    assert image.mode == "RGB"

    # Region should be smaller than full page
    full_page = render_page_to_png_bytes(sample_pdf_path, 0, dpi=72)
    full_image = Image.open(io.BytesIO(full_page))
    assert image.size[0] < full_image.size[0]
    assert image.size[1] < full_image.size[1]


def test_render_region_invalid_bbox_length(sample_pdf_path):
    """Test error for invalid bbox length."""
    with pytest.raises(ValidationError) as exc_info:
        render_region_to_png_bytes(sample_pdf_path, 0, (100, 200, 300))

    assert "4 elements" in str(exc_info.value)


def test_render_region_invalid_bbox_coordinates(sample_pdf_path):
    """Test error for invalid bbox coordinates (x2 <= x1)."""
    with pytest.raises(ValidationError) as exc_info:
        render_region_to_png_bytes(sample_pdf_path, 0, (500, 300, 100, 500))

    assert "x2 must be > x1" in str(exc_info.value)


# ============================================================================
# Performance and Memory Tests
# ============================================================================


def test_batch_rendering_memory_efficiency(multipage_pdf_path):
    """Test that batch rendering reuses PDF handle (basic check)."""
    # This test verifies that we can render multiple pages without errors
    # In production, memory profiling tools would be used for detailed analysis
    with PdfRenderer(multipage_pdf_path) as renderer:
        # Render same page multiple times
        for _ in range(5):
            image_bytes = renderer.render_page(0, dpi=72)
            assert len(image_bytes) > 0

        # Render different pages
        for i in range(renderer.page_count):
            image_bytes = renderer.render_page(i, dpi=72)
            assert len(image_bytes) > 0


def test_compare_single_vs_batch_rendering(multipage_pdf_path):
    """Compare single-page vs batch rendering outputs."""
    # Single page rendering (opens/closes PDF each time)
    single_results = []
    for i in range(3):
        img_bytes = render_page_to_png_bytes(multipage_pdf_path, i, dpi=72)
        single_results.append(img_bytes)

    # Batch rendering (reuses PDF handle)
    with PdfRenderer(multipage_pdf_path) as renderer:
        batch_results = []
        for i in range(3):
            img_bytes = renderer.render_page(i, dpi=72)
            batch_results.append(img_bytes)

    # Results should be identical (or very similar)
    assert len(single_results) == len(batch_results)
    for i in range(3):
        # Image sizes should be similar (might differ slightly due to compression)
        assert abs(len(single_results[i]) - len(batch_results[i])) < 1000


# ============================================================================
# Integration-Style Tests
# ============================================================================


def test_full_workflow_single_page(sample_pdf_path):
    """Test complete workflow for single-page document."""
    # 1. Get page count
    count = get_page_count(sample_pdf_path)
    assert count == 1

    # 2. Render page
    image_bytes = render_page_to_png_bytes(sample_pdf_path, 0, dpi=150)

    # 3. Verify result
    assert len(image_bytes) > 0
    image = Image.open(io.BytesIO(image_bytes))
    assert image.format == "PNG"


def test_full_workflow_multipage_batch(multipage_pdf_path):
    """Test complete workflow for multi-page document with batch rendering."""
    # 1. Get page count
    count = get_page_count(multipage_pdf_path)
    assert count == 3

    # 2. Batch render all pages
    images = render_pdf_pages(multipage_pdf_path, dpi=150)

    # 3. Verify results
    assert len(images) == count
    for img_bytes in images:
        assert len(img_bytes) > 0
        image = Image.open(io.BytesIO(img_bytes))
        assert image.format == "PNG"


def test_error_recovery_invalid_then_valid(sample_pdf_path, nonexistent_pdf_path):
    """Test that renderer can recover from errors."""
    # 1. Try to render nonexistent file (should fail)
    with pytest.raises(ValidationError):
        render_page_to_png_bytes(nonexistent_pdf_path, 0)

    # 2. Render valid file (should succeed)
    image_bytes = render_page_to_png_bytes(sample_pdf_path, 0, dpi=72)
    assert len(image_bytes) > 0
