"""Core PDF rendering functionality.

This module handles the conversion of PDF pages to PNG images
using pypdfium2, which provides fast, memory-efficient rendering.

The rendered images are optimized for VLM inference:
- PNG format (lossless)
- Configurable DPI (default 200)
- RGB color mode

Usage:
    from pathlib import Path
    from docling_hybrid.renderer.core import render_page_to_png_bytes
    
    # Render page 1 (index 0) at 200 DPI
    image_bytes = render_page_to_png_bytes(
        pdf_path=Path("document.pdf"),
        page_index=0,
        dpi=200,
    )
"""

import io
from pathlib import Path
from typing import Tuple

import pypdfium2 as pdfium
from PIL import Image

from docling_hybrid.common.errors import RenderingError, ValidationError
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)


def get_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Number of pages in the PDF
        
    Raises:
        ValidationError: If PDF file doesn't exist
        RenderingError: If PDF cannot be opened
        
    Example:
        >>> count = get_page_count(Path("document.pdf"))
        >>> print(f"Document has {count} pages")
    """
    if not pdf_path.exists():
        raise ValidationError(
            f"PDF file not found: {pdf_path}",
            details={"path": str(pdf_path)}
        )
    
    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
        count = len(pdf)
        pdf.close()
        return count
    except Exception as e:
        raise RenderingError(
            f"Failed to open PDF: {e}",
            details={"path": str(pdf_path), "error": str(e)}
        ) from e


def render_page_to_png_bytes(
    pdf_path: Path,
    page_index: int,
    dpi: int = 200,
) -> bytes:
    """Render a PDF page to PNG bytes.
    
    Converts a single PDF page to a PNG image suitable for VLM inference.
    The output is RGB format, optimized for model input.
    
    Args:
        pdf_path: Path to the PDF file
        page_index: Page index (0-based)
        dpi: Resolution in dots per inch (default: 200)
            - 72 DPI: Low quality, fast, ~100KB per page
            - 150 DPI: Medium quality, ~300KB per page
            - 200 DPI: Good quality (recommended), ~500KB per page
            - 300 DPI: High quality, slower, ~1MB per page
    
    Returns:
        PNG image as bytes
        
    Raises:
        ValidationError: If PDF file doesn't exist or page index is invalid
        RenderingError: If page cannot be rendered
        
    Example:
        >>> # Render first page at default DPI
        >>> image_bytes = render_page_to_png_bytes(
        ...     pdf_path=Path("document.pdf"),
        ...     page_index=0,
        ... )
        >>> len(image_bytes)  # ~500KB for typical page
        512345
        
        >>> # Lower DPI for faster processing
        >>> image_bytes = render_page_to_png_bytes(
        ...     pdf_path=Path("document.pdf"),
        ...     page_index=0,
        ...     dpi=150,
        ... )
    
    Note:
        The function opens and closes the PDF for each call. For batch
        processing, consider using render_document_pages() instead.
    """
    # Validate inputs
    if not pdf_path.exists():
        raise ValidationError(
            f"PDF file not found: {pdf_path}",
            details={"path": str(pdf_path)}
        )
    
    if page_index < 0:
        raise ValidationError(
            f"Page index must be non-negative, got {page_index}",
            details={"page_index": page_index}
        )
    
    if dpi < 72 or dpi > 600:
        raise ValidationError(
            f"DPI must be between 72 and 600, got {dpi}",
            details={"dpi": dpi, "hint": "Use 150-200 for local dev, 200-300 for production"}
        )
    
    try:
        # Open PDF
        pdf = pdfium.PdfDocument(str(pdf_path))
        
        # Validate page index
        if page_index >= len(pdf):
            pdf.close()
            raise ValidationError(
                f"Page index {page_index} out of range (PDF has {len(pdf)} pages)",
                details={"page_index": page_index, "total_pages": len(pdf)}
            )
        
        # Get page
        page = pdf[page_index]
        
        # Calculate scale factor for DPI (pypdfium2 default is 72 DPI)
        scale = dpi / 72.0
        
        # Render to bitmap
        bitmap = page.render(
            scale=scale,
            rotation=0,
        )
        
        # Convert to PIL Image
        pil_image = bitmap.to_pil()
        
        # Ensure RGB mode
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        
        # Export to PNG bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG", optimize=True)
        png_bytes = buffer.getvalue()
        
        # Cleanup
        pdf.close()
        
        logger.debug(
            "page_rendered",
            pdf=str(pdf_path),
            page_index=page_index,
            dpi=dpi,
            size_kb=len(png_bytes) // 1024,
        )
        
        return png_bytes
        
    except ValidationError:
        raise
    except Exception as e:
        raise RenderingError(
            f"Failed to render page {page_index}: {e}",
            details={
                "path": str(pdf_path),
                "page_index": page_index,
                "dpi": dpi,
                "error": str(e),
            }
        ) from e


def render_region_to_png_bytes(
    pdf_path: Path,
    page_index: int,
    bbox: Tuple[float, float, float, float],
    dpi: int = 200,
    padding: int = 10,
) -> bytes:
    """Render a specific region of a PDF page to PNG bytes.
    
    Crops a rectangular region from a PDF page, useful for extracting
    tables, figures, or formulas for specialized processing.
    
    Args:
        pdf_path: Path to the PDF file
        page_index: Page index (0-based)
        bbox: Bounding box (x1, y1, x2, y2) in PDF coordinates
            - Origin is bottom-left of page
            - Units are points (1/72 inch)
        dpi: Resolution in dots per inch (default: 200)
        padding: Pixels of padding around the region (default: 10)
    
    Returns:
        PNG image of the cropped region as bytes
        
    Raises:
        ValidationError: If inputs are invalid
        RenderingError: If rendering fails
        
    Example:
        >>> # Extract a table region
        >>> image_bytes = render_region_to_png_bytes(
        ...     pdf_path=Path("document.pdf"),
        ...     page_index=0,
        ...     bbox=(72, 400, 540, 600),  # x1, y1, x2, y2
        ... )
    
    Note:
        This is part of the extended scope. For the minimal core,
        only full-page rendering is used.
    """
    # Validate inputs
    if not pdf_path.exists():
        raise ValidationError(
            f"PDF file not found: {pdf_path}",
            details={"path": str(pdf_path)}
        )
    
    if len(bbox) != 4:
        raise ValidationError(
            f"bbox must have 4 elements (x1, y1, x2, y2), got {len(bbox)}",
            details={"bbox": bbox}
        )
    
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1:
        raise ValidationError(
            f"Invalid bbox: x2 must be > x1 and y2 must be > y1",
            details={"bbox": bbox}
        )
    
    try:
        # First render the full page
        full_page_bytes = render_page_to_png_bytes(pdf_path, page_index, dpi)
        
        # Load as PIL image
        pil_image = Image.open(io.BytesIO(full_page_bytes))
        
        # Get page dimensions for coordinate conversion
        pdf = pdfium.PdfDocument(str(pdf_path))
        page = pdf[page_index]
        page_width, page_height = page.get_size()
        pdf.close()
        
        # Convert PDF coordinates to image coordinates
        # PDF origin is bottom-left, image origin is top-left
        scale = dpi / 72.0
        
        img_x1 = int(x1 * scale) - padding
        img_y1 = int((page_height - y2) * scale) - padding  # Flip Y
        img_x2 = int(x2 * scale) + padding
        img_y2 = int((page_height - y1) * scale) + padding  # Flip Y
        
        # Clamp to image bounds
        img_x1 = max(0, img_x1)
        img_y1 = max(0, img_y1)
        img_x2 = min(pil_image.width, img_x2)
        img_y2 = min(pil_image.height, img_y2)
        
        # Crop
        cropped = pil_image.crop((img_x1, img_y1, img_x2, img_y2))
        
        # Export to PNG bytes
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG", optimize=True)
        png_bytes = buffer.getvalue()
        
        logger.debug(
            "region_rendered",
            pdf=str(pdf_path),
            page_index=page_index,
            bbox=bbox,
            size_kb=len(png_bytes) // 1024,
        )
        
        return png_bytes
        
    except ValidationError:
        raise
    except Exception as e:
        raise RenderingError(
            f"Failed to render region on page {page_index}: {e}",
            details={
                "path": str(pdf_path),
                "page_index": page_index,
                "bbox": bbox,
                "error": str(e),
            }
        ) from e
