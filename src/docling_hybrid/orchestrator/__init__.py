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
from docling_hybrid.orchestrator.progress import ProgressCallback, is_progress_callback
from docling_hybrid.orchestrator.callbacks import (
    ConsoleProgressCallback,
    FileProgressCallback,
    CompositeProgressCallback,
)
from docling_hybrid.orchestrator.events import (
    ProgressEvent,
    ProgressEventType,
    ConversionStartEvent,
    PageStartEvent,
    PageCompleteEvent,
    PageErrorEvent,
    ConversionCompleteEvent,
    ConversionErrorEvent,
    EventQueueCallback,
    to_dict as event_to_dict,
    from_dict as event_from_dict,
)

__all__ = [
    # Pipeline
    "HybridPipeline",
    "ConversionResult",
    "ConversionOptions",
    # Progress
    "ProgressCallback",
    "is_progress_callback",
    # Callbacks
    "ConsoleProgressCallback",
    "FileProgressCallback",
    "CompositeProgressCallback",
    # Events
    "ProgressEvent",
    "ProgressEventType",
    "ConversionStartEvent",
    "PageStartEvent",
    "PageCompleteEvent",
    "PageErrorEvent",
    "ConversionCompleteEvent",
    "ConversionErrorEvent",
    "EventQueueCallback",
    "event_to_dict",
    "event_from_dict",
]
