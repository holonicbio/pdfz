"""Block-level processing for hybrid OCR.

STATUS: INTERFACE DEFINED (Sprint 1) - Implementation in Sprint 6

This module provides interfaces and types for block-level OCR processing:
- Block segmentation from DoclingDocument
- Backend routing per block type
- Multi-backend candidate generation
- Deterministic merge policies
- Optional LLM arbitration

The block-level approach provides finer control than page-level OCR:
- Tables → TableBackend for better structure
- Formulas → FormulaBackend for LaTeX
- Text → DoclingNative for digital PDFs, OCR for scanned

Components (Interfaces Defined in Sprint 1):
- BlockSegmenterProtocol: Extract blocks from DoclingDocument
- BlockRouterProtocol: Decide which backends to use per block
- BlockMergerProtocol: Combine multiple backend outputs
- BlockProcessorProtocol: Complete block-level pipeline

Data Types:
- BlockType: Enumeration of block types
- Block: Block representation with geometry
- RoutingRule: Configuration for backend routing
- BlockProcessingOptions: Processing configuration

Usage (Sprint 6+):
    from docling_hybrid.blocks import (
        BlockProcessorProtocol,
        BlockType,
        Block,
        RoutingRule,
    )

    # Concrete implementations will be available in Sprint 6
    processor = MyBlockProcessor(config)
    hybrid_document = await processor.process_document(pdf_path, options)
"""

from docling_hybrid.blocks.base import (
    BlockMergerProtocol,
    BlockProcessorProtocol,
    BlockRouterProtocol,
    BlockSegmenterProtocol,
)
from docling_hybrid.blocks.types import (
    Block,
    BlockProcessingOptions,
    BlockType,
    RoutingRule,
)

__all__ = [
    # Protocols
    "BlockSegmenterProtocol",
    "BlockRouterProtocol",
    "BlockMergerProtocol",
    "BlockProcessorProtocol",
    # Types
    "BlockType",
    "Block",
    "RoutingRule",
    "BlockProcessingOptions",
]
