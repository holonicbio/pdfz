"""Data models for the conversion pipeline.

This module defines the input options and output structures
for the hybrid conversion pipeline.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from docling_hybrid.common.models import PageResult


class ConversionOptions(BaseModel):
    """Options for PDF conversion.
    
    Attributes:
        backend_name: Name of backend to use (or None for default)
        dpi: Page rendering DPI
        add_page_separators: Whether to add page separator comments
        page_separator_format: Format string for page separators
        max_pages: Maximum pages to process (None for all)
        start_page: First page to process (1-indexed)
    """
    backend_name: str | None = Field(
        default=None,
        description="Backend to use (None = use default from config)"
    )
    dpi: int | None = Field(
        default=None,
        ge=72,
        le=600,
        description="Page rendering DPI (None = use config value)"
    )
    add_page_separators: bool = Field(
        default=True,
        description="Add <!-- PAGE N --> comments between pages"
    )
    page_separator_format: str = Field(
        default="<!-- PAGE {page_num} -->\n\n",
        description="Format string for page separators"
    )
    max_pages: int | None = Field(
        default=None,
        ge=1,
        description="Maximum pages to process (None = all pages)"
    )
    start_page: int = Field(
        default=1,
        ge=1,
        description="First page to process (1-indexed)"
    )


class ConversionResult(BaseModel):
    """Result of PDF conversion.
    
    Attributes:
        doc_id: Document identifier
        source_path: Path to source PDF
        output_path: Path to output file (if written)
        markdown: Full Markdown content
        page_results: Per-page results
        total_pages: Total pages in PDF
        processed_pages: Number of pages processed
        backend_name: Backend used for conversion
        metadata: Additional conversion metadata
    """
    doc_id: str = Field(
        description="Document identifier"
    )
    source_path: Path = Field(
        description="Path to source PDF"
    )
    output_path: Path | None = Field(
        default=None,
        description="Path to output file (if written)"
    )
    markdown: str = Field(
        description="Full Markdown content"
    )
    page_results: list[PageResult] = Field(
        default_factory=list,
        description="Per-page conversion results"
    )
    total_pages: int = Field(
        ge=1,
        description="Total pages in source PDF"
    )
    processed_pages: int = Field(
        ge=0,
        description="Number of pages successfully processed"
    )
    backend_name: str = Field(
        description="Backend used for conversion"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (timing, errors, etc.)"
    )
    
    class Config:
        arbitrary_types_allowed = True
