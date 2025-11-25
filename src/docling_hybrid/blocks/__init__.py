"""Block-level processing for hybrid OCR.

STATUS: STUB - Extended scope (Phase 2)

This module will provide:
- Block segmentation from DoclingDocument
- Backend routing per block type
- Multi-backend candidate generation
- Deterministic merge policies
- Optional LLM arbitration

The block-level approach provides finer control than page-level OCR:
- Tables → TableBackend for better structure
- Formulas → FormulaBackend for LaTeX
- Text → DoclingNative for digital PDFs, OCR for scanned

Planned Components:
- BlockSegmenter: Extract blocks from DoclingDocument
- BlockRouter: Decide which backends to use per block
- CandidateMerger: Combine multiple backend outputs
- LLMArbitrator: Resolve conflicts using an LLM

Planned Usage:
    from docling_hybrid.blocks import BlockProcessor
    
    processor = BlockProcessor(config)
    hybrid_document = await processor.process(docling_document)
"""

# Placeholder for future implementation
__all__ = []
