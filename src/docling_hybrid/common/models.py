"""Shared data models for Docling Hybrid OCR.

This module defines the core data structures used throughout the system.
All models use Pydantic for validation and serialization.

Key Models:
- OcrBackendConfig: Configuration for OCR/VLM backends
- BackendCandidate: Output from a single backend
- PageResult: OCR result for a single page
- HybridBlock: Block-level result (extended scope)
- HybridDocument: Full document result (extended scope)

Usage:
    from docling_hybrid.common.models import OcrBackendConfig, PageResult
    
    config = OcrBackendConfig(
        name="nemotron-openrouter",
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
    )
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ContentType(str, Enum):
    """Content type for backend outputs."""
    MARKDOWN = "markdown"
    LATEX = "latex"
    TEXT = "text"
    HTML = "html"


class BlockType(str, Enum):
    """Type of document block (for extended scope)."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    CODE = "code"
    FOOTNOTE = "footnote"
    CAPTION = "caption"
    OTHER = "other"


class OcrBackendConfig(BaseModel):
    """Configuration for an OCR/VLM backend.
    
    This model encapsulates all configuration needed to communicate
    with a specific OCR/VLM backend service.
    
    Attributes:
        name: Backend identifier (e.g., "nemotron-openrouter")
        model: Model identifier for the provider
        base_url: Base HTTP endpoint URL
        api_key: Authentication token (optional, often from env var)
        extra_headers: Additional HTTP headers (e.g., HTTP-Referer)
        temperature: Generation temperature (0.0 = deterministic)
        max_tokens: Maximum tokens in response
    
    Example:
        >>> config = OcrBackendConfig(
        ...     name="nemotron-openrouter",
        ...     model="nvidia/nemotron-nano-12b-v2-vl:free",
        ...     base_url="https://openrouter.ai/api/v1/chat/completions",
        ...     api_key="sk-...",  # Usually from env var
        ...     temperature=0.0,
        ... )
    """
    name: str = Field(
        description="Backend identifier (e.g., 'nemotron-openrouter')"
    )
    model: str = Field(
        description="Model identifier for the provider"
    )
    base_url: str = Field(
        description="Base HTTP endpoint URL"
    )
    api_key: str | None = Field(
        default=None,
        description="Authentication token (often loaded from environment)"
    )
    extra_headers: dict[str, str] | None = Field(
        default=None,
        description="Additional HTTP headers (e.g., HTTP-Referer for OpenRouter)"
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Generation temperature (0.0 = deterministic)"
    )
    max_tokens: int = Field(
        default=8192,
        ge=1,
        le=128000,
        description="Maximum tokens in response"
    )
    
    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure base_url is a valid HTTP(S) URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")  # Remove trailing slash for consistency


class BackendCandidate(BaseModel):
    """Output from a single backend for a block or page.
    
    Represents one backend's attempt at extracting content.
    Used for multi-backend ensemble and arbitration.
    
    Attributes:
        backend_name: Name of the backend that produced this output
        content: Extracted content (Markdown, LaTeX, etc.)
        content_type: Type of content
        score: Optional confidence or quality score
        metadata: Additional information (model, latency, etc.)
    
    Example:
        >>> candidate = BackendCandidate(
        ...     backend_name="nemotron-openrouter",
        ...     content="# Introduction\\n\\nThis paper presents...",
        ...     content_type=ContentType.MARKDOWN,
        ...     score=0.95,
        ...     metadata={"model": "nemotron-nano-12b-v2-vl", "latency_ms": 2500}
        ... )
    """
    backend_name: str = Field(
        description="Name of the backend that produced this output"
    )
    content: str = Field(
        description="Extracted content (Markdown, LaTeX, etc.)"
    )
    content_type: ContentType = Field(
        default=ContentType.MARKDOWN,
        description="Type of content"
    )
    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence or quality score (0.0-1.0)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional information (model, latency, diagnostics)"
    )


class PageResult(BaseModel):
    """OCR result for a single page.
    
    Contains the extracted content for one page, along with metadata
    about the extraction process.
    
    Attributes:
        page_num: Page number (1-indexed)
        doc_id: Document identifier
        content: Extracted Markdown content
        backend_name: Backend used for extraction
        candidates: All backend candidates (for multi-backend mode)
        metadata: Additional page information
    
    Example:
        >>> result = PageResult(
        ...     page_num=1,
        ...     doc_id="doc-a1b2c3d4",
        ...     content="# Title\\n\\nFirst paragraph...",
        ...     backend_name="nemotron-openrouter",
        ... )
    """
    page_num: int = Field(
        ge=1,
        description="Page number (1-indexed)"
    )
    doc_id: str = Field(
        description="Document identifier"
    )
    content: str = Field(
        description="Extracted Markdown content"
    )
    backend_name: str = Field(
        description="Backend used for extraction"
    )
    candidates: list[BackendCandidate] = Field(
        default_factory=list,
        description="All backend candidates (for multi-backend mode)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional page information (image size, processing time)"
    )


class BlockGeometry(BaseModel):
    """Geometry of a block within a page (extended scope).
    
    Attributes:
        page_index: Page index (0-based)
        bbox: Bounding box (x1, y1, x2, y2) in page coordinates
    """
    page_index: int = Field(
        ge=0,
        description="Page index (0-based)"
    )
    bbox: tuple[float, float, float, float] = Field(
        description="Bounding box (x1, y1, x2, y2) in page coordinates"
    )


class BlockSource(BaseModel):
    """Source information for a block (extended scope).
    
    Links a block back to its origin in the Docling document.
    
    Attributes:
        docling_block_id: Original block ID from Docling
        docling_type: Original block type from Docling
    """
    docling_block_id: str = Field(
        description="Original block ID from Docling"
    )
    docling_type: str = Field(
        description="Original block type from Docling"
    )


class HybridBlock(BaseModel):
    """Block-level result after merging (extended scope).
    
    Represents a single block (paragraph, table, formula, etc.)
    with its final content after backend arbitration.
    
    Attributes:
        id: Unique block identifier
        block_type: Type of block
        geometry: Position within page
        source: Link to original Docling block
        candidates: All backend outputs
        chosen_index: Index of chosen candidate
        final_content: Final merged/selected content
        merged_metadata: Information about merge decision
    
    Note:
        This is part of the extended scope and will be implemented
        in Phase 2 of the project.
    """
    id: str = Field(
        description="Unique block identifier"
    )
    block_type: BlockType = Field(
        description="Type of block"
    )
    geometry: BlockGeometry = Field(
        description="Position within page"
    )
    source: BlockSource = Field(
        description="Link to original Docling block"
    )
    candidates: list[BackendCandidate] = Field(
        default_factory=list,
        description="All backend outputs"
    )
    chosen_index: int = Field(
        default=0,
        ge=0,
        description="Index of chosen candidate"
    )
    final_content: str = Field(
        description="Final merged/selected content"
    )
    merged_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Information about merge decision"
    )


class HybridDocument(BaseModel):
    """Full document result (extended scope).
    
    Contains all blocks from a document with their final content.
    Supports export to multiple formats.
    
    Attributes:
        doc_id: Document identifier
        source_path: Original file path
        pages: List of page indices
        blocks: All blocks in document order
        metadata: Document-level metadata
    
    Note:
        This is part of the extended scope and will be implemented
        in Phase 2 of the project.
    """
    doc_id: str = Field(
        description="Document identifier"
    )
    source_path: str = Field(
        description="Original file path"
    )
    pages: list[int] = Field(
        description="List of page indices"
    )
    blocks: list[HybridBlock] = Field(
        default_factory=list,
        description="All blocks in document order"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document-level metadata"
    )
    
    def export_to_markdown(self) -> str:
        """Export document to Markdown format.
        
        Returns:
            Markdown string representation of document
            
        Note:
            Stub - full implementation in Phase 2
        """
        # Simple implementation: concatenate block contents
        parts = []
        for block in self.blocks:
            parts.append(block.final_content)
        return "\n\n".join(parts)
