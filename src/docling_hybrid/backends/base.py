"""Abstract base class for OCR/VLM backends.

This module defines the interface that all OCR/VLM backends must implement.
The interface is designed to support:

1. Page-level OCR (minimal core)
2. Table extraction (extended scope)
3. Formula extraction (extended scope)

All methods are async to support concurrent processing.

Usage:
    class MyBackend(OcrVlmBackend):
        async def page_to_markdown(self, image_bytes, page_num, doc_id):
            # Implementation
            pass
        
        async def table_to_markdown(self, image_bytes, meta):
            # Implementation
            pass
        
        async def formula_to_latex(self, image_bytes, meta):
            # Implementation
            pass
"""

from abc import ABC, abstractmethod
from typing import Any

from docling_hybrid.common.models import OcrBackendConfig


class OcrVlmBackend(ABC):
    """Abstract base class for OCR/VLM backends.
    
    All OCR/VLM backends must inherit from this class and implement
    the abstract methods. The interface is designed to be simple
    and backend-agnostic.
    
    Attributes:
        config: Backend configuration (model, URL, API key, etc.)
        name: Backend name (from config)
    
    Methods:
        page_to_markdown: Convert full page image to Markdown
        table_to_markdown: Convert table image to Markdown table
        formula_to_latex: Convert formula image to LaTeX
    
    Example:
        >>> backend = MyBackend(config)
        >>> markdown = await backend.page_to_markdown(
        ...     image_bytes=png_bytes,
        ...     page_num=1,
        ...     doc_id="doc-123"
        ... )
    """
    
    def __init__(self, config: OcrBackendConfig) -> None:
        """Initialize the backend with configuration.
        
        Args:
            config: Backend configuration containing:
                - name: Backend identifier
                - model: Model ID for the provider
                - base_url: API endpoint URL
                - api_key: Authentication token (optional)
                - extra_headers: Additional HTTP headers
                - temperature: Generation temperature
                - max_tokens: Max response tokens
        """
        self.config = config
        self.name = config.name
    
    @abstractmethod
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert a full page image to Markdown.
        
        This is the primary method for the minimal core. It takes
        a rendered page image and returns the full page content
        as GitHub-flavored Markdown.
        
        Args:
            image_bytes: PNG image bytes of the rendered page
            page_num: Page number (1-indexed) for context
            doc_id: Document identifier for logging/tracking
        
        Returns:
            Markdown string representing the page content.
            Should include:
            - Headings (# ## ###)
            - Paragraphs
            - Lists (- or 1.)
            - Tables (| syntax)
            - Inline formulas ($...$)
            - Block formulas ($$...$$)
            - <FIGURE> placeholders for images
        
        Raises:
            BackendError: If OCR/VLM processing fails
            BackendTimeoutError: If request times out
            BackendConnectionError: If cannot connect to backend
        
        Example:
            >>> with open("page.png", "rb") as f:
            ...     image_bytes = f.read()
            >>> md = await backend.page_to_markdown(image_bytes, 1, "doc-123")
            >>> print(md)
            # Introduction
            
            This paper presents a novel approach to...
        """
        pass
    
    @abstractmethod
    async def table_to_markdown(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a table image to Markdown table syntax.
        
        Takes a cropped image containing only a table and returns
        the table content in Markdown table format.
        
        Note: This method is defined for interface stability but
        is not used in the minimal core. Implementation is optional
        for Phase 1.
        
        Args:
            image_bytes: PNG image bytes of the cropped table region
            meta: Metadata about the table:
                - doc_id: Document identifier
                - page_num: Page number
                - block_id: Block identifier
                - bbox: Bounding box coordinates (optional)
                - expected_rows: Expected number of rows (optional)
                - expected_cols: Expected number of columns (optional)
        
        Returns:
            Markdown table string using pipe (|) syntax.
            Example:
                | Header 1 | Header 2 |
                |----------|----------|
                | Cell 1   | Cell 2   |
        
        Raises:
            BackendError: If table extraction fails
            NotImplementedError: If not implemented (acceptable for Phase 1)
        
        Example:
            >>> md = await backend.table_to_markdown(table_bytes, {
            ...     "doc_id": "doc-123",
            ...     "page_num": 1,
            ... })
        """
        pass
    
    @abstractmethod
    async def formula_to_latex(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a formula image to LaTeX.
        
        Takes a cropped image containing only a formula and returns
        the LaTeX representation.
        
        Note: This method is defined for interface stability but
        is not used in the minimal core. Implementation is optional
        for Phase 1.
        
        Args:
            image_bytes: PNG image bytes of the cropped formula region
            meta: Metadata about the formula:
                - doc_id: Document identifier
                - page_num: Page number
                - block_id: Block identifier
                - bbox: Bounding box coordinates (optional)
                - is_inline: Whether formula is inline (optional)
        
        Returns:
            LaTeX string representing the formula.
            Should NOT include delimiters ($, $$).
            Example: "\\frac{1}{2}mv^2"
        
        Raises:
            BackendError: If formula extraction fails
            NotImplementedError: If not implemented (acceptable for Phase 1)
        
        Example:
            >>> latex = await backend.formula_to_latex(formula_bytes, {
            ...     "doc_id": "doc-123",
            ...     "page_num": 1,
            ... })
            >>> print(latex)
            \\frac{1}{2}mv^2
        """
        pass
    
    async def close(self) -> None:
        """Close any open connections or resources.
        
        Called when the backend is no longer needed. Override in
        subclasses if cleanup is required.
        
        Default implementation does nothing.
        """
        pass
    
    async def __aenter__(self) -> "OcrVlmBackend":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name!r}, model={self.config.model!r})"
