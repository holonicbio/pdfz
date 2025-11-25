"""Pipeline orchestration for PDF to Markdown conversion.

This module coordinates the full conversion pipeline:
1. Load PDF via Docling
2. Render pages to images
3. Process pages through OCR backend
4. Concatenate results to Markdown

Usage:
    from docling_hybrid.orchestrator import HybridPipeline
    from docling_hybrid.common.config import get_config
    
    config = get_config()
    pipeline = HybridPipeline(config)
    
    # Convert a PDF to Markdown
    result = await pipeline.convert_pdf(
        pdf_path=Path("document.pdf"),
        output_path=Path("document.md"),  # Optional
    )
    
    print(result.markdown)  # Full document as Markdown
"""

from docling_hybrid.orchestrator.pipeline import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionResult, ConversionOptions

__all__ = [
    "HybridPipeline",
    "ConversionResult",
    "ConversionOptions",
]
