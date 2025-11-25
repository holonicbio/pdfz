"""PDF page rendering utilities.

This module provides functions to render PDF pages to images
suitable for VLM inference.

Usage:
    from docling_hybrid.renderer import render_page_to_png_bytes
    
    # Render a single page
    image_bytes = render_page_to_png_bytes(
        pdf_path=Path("document.pdf"),
        page_index=0,  # 0-indexed
        dpi=200,
    )
    
    # Use with backend
    markdown = await backend.page_to_markdown(image_bytes, page_num=1, doc_id="doc-123")
"""

from docling_hybrid.renderer.core import (
    get_page_count,
    render_page_to_png_bytes,
    render_region_to_png_bytes,
)

__all__ = [
    "render_page_to_png_bytes",
    "render_region_to_png_bytes",
    "get_page_count",
]
