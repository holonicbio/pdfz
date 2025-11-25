"""Abstract interfaces for block-level processing.

This module defines the abstract interfaces that must be implemented
to enable block-level OCR processing with hybrid backend support.

Key Interfaces:
- BlockSegmenterProtocol: Extract blocks from Docling documents
- BlockRouterProtocol: Route blocks to appropriate backends
- BlockMergerProtocol: Merge results from multiple backends

Usage:
    from docling_hybrid.blocks.base import BlockSegmenterProtocol

    class MySegmenter(BlockSegmenterProtocol):
        def segment_page(self, docling_doc, page_index):
            # Implementation
            ...

Note:
    This is part of Sprint 1 interface definition. Concrete implementations
    will be added in Sprint 6 (Block-Level Processing).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol

from docling_hybrid.blocks.types import Block, BlockType, RoutingRule
from docling_hybrid.common.models import BackendCandidate


class BlockSegmenterProtocol(Protocol):
    """Protocol for extracting blocks from Docling documents.

    Implementations convert Docling's DoclingDocument structure into
    our Block representation, mapping Docling labels to BlockType enum
    and extracting geometry information.

    Methods:
        segment_page: Extract blocks from a single page
        segment_document: Extract blocks from entire document

    Example Implementation:
        >>> from docling.document_converter import DocumentConverter
        >>>
        >>> class DoclingSegmenter(BlockSegmenterProtocol):
        ...     def __init__(self):
        ...         self.converter = DocumentConverter()
        ...
        ...     def segment_page(self, docling_doc, page_index):
        ...         blocks = []
        ...         for node, _ in docling_doc.iterate_items():
        ...             if node.prov and node.prov[0].page_no == page_index + 1:
        ...                 block = self._convert_node_to_block(node, page_index)
        ...                 blocks.append(block)
        ...         return blocks
        ...
        ...     def segment_document(self, pdf_path):
        ...         result = self.converter.convert(str(pdf_path))
        ...         # Extract blocks from all pages...
        ...         return blocks_by_page
    """

    def segment_page(
        self,
        docling_doc: Any,  # docling.datamodel.document.DoclingDocument
        page_index: int,
    ) -> list[Block]:
        """Extract blocks from a single page of a Docling document.

        Args:
            docling_doc: Docling DoclingDocument object
            page_index: Zero-based page index

        Returns:
            List of Block objects for this page, in reading order

        Raises:
            ValueError: If page_index is out of range
            RuntimeError: If block extraction fails

        Note:
            Blocks should be returned in reading order as determined
            by Docling's layout analysis.
        """
        ...

    def segment_document(
        self,
        pdf_path: Path,
    ) -> dict[int, list[Block]]:
        """Extract blocks from all pages of a PDF document.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary mapping page_index (0-based) to list of blocks

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            RuntimeError: If document conversion or segmentation fails

        Example:
            >>> segmenter = DoclingSegmenter()
            >>> blocks_by_page = segmenter.segment_document(Path("doc.pdf"))
            >>> for page_idx, blocks in blocks_by_page.items():
            ...     print(f"Page {page_idx}: {len(blocks)} blocks")
        """
        ...


class BlockRouterProtocol(Protocol):
    """Protocol for routing blocks to appropriate backends.

    Implementations use routing rules to decide which backend(s) should
    process each block, and which backend method to use (page_to_markdown,
    table_to_markdown, formula_to_latex).

    Methods:
        get_backend_for_block: Determine backend and method for a block
        get_all_backends_for_block: Get all backends (for multi-backend mode)

    Example Implementation:
        >>> class RuleBasedRouter(BlockRouterProtocol):
        ...     def __init__(self, rules: list[RoutingRule]):
        ...         self.rules = {r.block_type: r for r in rules}
        ...
        ...     def get_backend_for_block(self, block, available_backends):
        ...         rule = self.rules.get(block.block_type)
        ...         if rule:
        ...             for backend in rule.backends:
        ...                 if backend in available_backends:
        ...                     method = self._get_method(block.block_type, rule)
        ...                     return (backend, method)
        ...         # Default fallback
        ...         return (available_backends[0], "page_to_markdown")
    """

    def get_backend_for_block(
        self,
        block: Block,
        available_backends: list[str],
    ) -> tuple[str, str]:
        """Get backend and method for processing a block.

        Args:
            block: Block to route
            available_backends: List of available backend names

        Returns:
            Tuple of (backend_name, method_name)
            method_name is one of: "page_to_markdown", "table_to_markdown",
            "formula_to_latex"

        Raises:
            ValueError: If no suitable backend found

        Example:
            >>> router = RuleBasedRouter(rules)
            >>> backend, method = router.get_backend_for_block(
            ...     table_block,
            ...     ["deepseek-vllm", "nemotron-openrouter"]
            ... )
            >>> print(f"Use {backend}.{method}")
        """
        ...

    def get_all_backends_for_block(
        self,
        block: Block,
        available_backends: list[str],
    ) -> list[tuple[str, str]]:
        """Get all backends to try for a block (multi-backend mode).

        Args:
            block: Block to route
            available_backends: List of available backend names

        Returns:
            List of (backend_name, method_name) tuples in priority order

        Example:
            >>> router = RuleBasedRouter(rules)
            >>> backends = router.get_all_backends_for_block(
            ...     table_block,
            ...     ["deepseek-vllm", "nemotron-openrouter", "docling-native"]
            ... )
            >>> for backend, method in backends:
            ...     # Try each backend...
            ...     pass
        """
        ...


class BlockMergerProtocol(Protocol):
    """Protocol for merging results from multiple backends.

    Implementations apply merge strategies (voting, arbitration, preference)
    to select or combine results from multiple backend candidates.

    Methods:
        merge: Select/combine candidates to produce final content

    Example Implementation:
        >>> class PreferFirstMerger(BlockMergerProtocol):
        ...     def merge(self, candidates, block):
        ...         for candidate in candidates:
        ...             if candidate.score and candidate.score > 0.5:
        ...                 return candidate.content
        ...         raise ValueError("No acceptable candidate found")
    """

    def merge(
        self,
        candidates: list[BackendCandidate],
        block: Block,
    ) -> str:
        """Merge multiple backend outputs into final content.

        Args:
            candidates: List of candidate outputs from different backends
            block: Original block (for context)

        Returns:
            Final merged content string

        Raises:
            ValueError: If no valid candidate found or merge fails

        Example:
            >>> merger = PreferFirstMerger()
            >>> candidates = [
            ...     BackendCandidate(backend_name="backend1", content="# Title", score=0.9),
            ...     BackendCandidate(backend_name="backend2", content="# Title", score=0.85),
            ... ]
            >>> final = merger.merge(candidates, block)
        """
        ...


class BlockProcessorProtocol(Protocol):
    """Protocol for complete block-level processing pipeline.

    Combines segmentation, routing, OCR, and merging into a unified workflow.
    This is the main interface for block-level document processing.

    Methods:
        process_document: Convert entire document using block-level approach

    Example Implementation:
        >>> class HybridBlockProcessor(BlockProcessorProtocol):
        ...     def __init__(self, segmenter, router, merger, backends):
        ...         self.segmenter = segmenter
        ...         self.router = router
        ...         self.merger = merger
        ...         self.backends = backends
        ...
        ...     async def process_document(self, pdf_path, options):
        ...         # Segment document into blocks
        ...         blocks_by_page = self.segmenter.segment_document(pdf_path)
        ...
        ...         # Process each block
        ...         for page_idx, blocks in blocks_by_page.items():
        ...             for block in blocks:
        ...                 # Route to backend
        ...                 backend_name, method = self.router.get_backend_for_block(...)
        ...                 # Render block region
        ...                 image_bytes = render_region(pdf_path, block.bbox)
        ...                 # OCR with backend
        ...                 result = await backend.process(image_bytes, method)
        ...                 # Store result
        ...                 ...
        ...         return hybrid_document
    """

    async def process_document(
        self,
        pdf_path: Path,
        options: Any,  # BlockProcessingOptions
    ) -> Any:  # HybridDocument
        """Process entire document using block-level approach.

        Args:
            pdf_path: Path to PDF file
            options: Block processing configuration

        Returns:
            HybridDocument with processed blocks

        Raises:
            FileNotFoundError: If PDF doesn't exist
            RuntimeError: If processing fails

        Note:
            This is the main entry point for block-level processing.
            It orchestrates all steps: segmentation, routing, OCR, and merging.
        """
        ...
