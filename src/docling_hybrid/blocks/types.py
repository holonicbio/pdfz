"""Data types for block-level processing.

This module defines types for block segmentation, routing, and merging.

Key Types:
- BlockType: Enumeration of document block types
- Block: Representation of a document block with geometry
- RoutingRule: Configuration for routing blocks to backends
- BlockProcessingOptions: Options for block-level processing

Usage:
    from docling_hybrid.blocks.types import BlockType, Block, RoutingRule

    rule = RoutingRule(
        block_type=BlockType.TABLE,
        backends=["deepseek-vllm", "nemotron-openrouter"],
        use_specialized_prompt=True,
    )
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    """Type of document block.

    These types map to Docling's DocItem labels and enable
    intelligent routing to specialized backends.

    Values:
        HEADING: Section headings (h1, h2, etc.)
        PARAGRAPH: Regular paragraph text
        LIST_ITEM: List item (bulleted or numbered)
        TABLE: Table structure
        FIGURE: Image, chart, diagram
        FORMULA: Mathematical formula or equation
        CODE: Code block
        FOOTNOTE: Footnote or endnote
        CAPTION: Figure or table caption
        OTHER: Unclassified content
    """
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


@dataclass
class Block:
    """Representation of a document block with location and content.

    A Block represents a logical unit of content extracted from a document,
    with its type, position, and optional content. Blocks are created by
    BlockSegmenter implementations from Docling's DocItem nodes.

    Attributes:
        id: Unique block identifier (e.g., "block-a1b2c3d4")
        block_type: Type of content (paragraph, table, etc.)
        page_index: Zero-based page index
        bbox: Bounding box (x1, y1, x2, y2) in page coordinates
        content: Extracted text content (if available from Docling)
        confidence: Confidence score from Docling (0.0-1.0)
        metadata: Additional information (Docling type, source reference, etc.)

    Example:
        >>> block = Block(
        ...     id="block-123",
        ...     block_type=BlockType.PARAGRAPH,
        ...     page_index=0,
        ...     bbox=(72.0, 144.0, 540.0, 216.0),
        ...     content="This is a paragraph extracted by Docling.",
        ...     confidence=0.95,
        ...     metadata={"docling_label": "text", "docling_id": "abc123"}
        ... )

    Note:
        Coordinates in bbox are in PDF points (1/72 inch) with origin
        typically at bottom-left corner of the page.
    """
    id: str
    block_type: BlockType
    page_index: int
    bbox: tuple[float, float, float, float]
    content: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate bbox coordinates."""
        if len(self.bbox) != 4:
            raise ValueError(f"bbox must have 4 coordinates, got {len(self.bbox)}")
        x1, y1, x2, y2 = self.bbox
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"Invalid bbox coordinates: {self.bbox}")


class RoutingRule(BaseModel):
    """Configuration for routing blocks to backends.

    Routing rules determine which backend(s) to use for processing
    specific block types, and whether to use specialized prompts.

    Attributes:
        block_type: Type of block this rule applies to
        backends: List of backend names in priority order
        use_specialized_prompt: If True, use specialized methods (table_to_markdown,
                               formula_to_latex). If False, use page_to_markdown.
        fallback_to_page: If True and specialized backend fails, fall back to
                         page-level OCR with generic backend
        max_candidates: Maximum number of backends to try (for multi-backend mode)

    Example:
        >>> rule = RoutingRule(
        ...     block_type=BlockType.TABLE,
        ...     backends=["deepseek-vllm", "nemotron-openrouter"],
        ...     use_specialized_prompt=True,
        ...     fallback_to_page=True,
        ...     max_candidates=2,
        ... )

    Notes:
        - Backends are tried in order until success or max_candidates reached
        - Setting max_candidates > 1 enables multi-backend mode for this block type
        - Specialized prompts (table_to_markdown, formula_to_latex) may produce
          better results than page_to_markdown for certain block types
    """
    block_type: BlockType = Field(
        description="Type of block this rule applies to"
    )
    backends: list[str] = Field(
        min_length=1,
        description="List of backend names in priority order"
    )
    use_specialized_prompt: bool = Field(
        default=True,
        description="Use specialized backend methods (e.g., table_to_markdown)"
    )
    fallback_to_page: bool = Field(
        default=True,
        description="Fall back to page-level OCR if specialized backend fails"
    )
    max_candidates: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum number of backends to try (1 = single backend)"
    )


class BlockProcessingOptions(BaseModel):
    """Options for block-level processing.

    Controls how blocks are segmented, routed, and merged during
    document conversion.

    Attributes:
        enabled: Enable block-level processing (vs page-level only)
        routing_rules: Rules for routing block types to backends
        merge_policy: Strategy for merging multi-backend results
        min_block_confidence: Minimum confidence to process block (0.0-1.0)
        skip_low_confidence: Skip blocks below min_block_confidence

    Example:
        >>> options = BlockProcessingOptions(
        ...     enabled=True,
        ...     routing_rules=[
        ...         RoutingRule(
        ...             block_type=BlockType.TABLE,
        ...             backends=["deepseek-vllm"],
        ...             use_specialized_prompt=True,
        ...         ),
        ...     ],
        ...     merge_policy="prefer_first",
        ...     min_block_confidence=0.5,
        ... )

    Note:
        This is part of Sprint 1 interface definition. Full implementation
        will be added in Sprint 6 (Block-Level Processing).
    """
    enabled: bool = Field(
        default=False,
        description="Enable block-level processing"
    )
    routing_rules: list[RoutingRule] = Field(
        default_factory=list,
        description="Rules for routing block types to backends"
    )
    merge_policy: Literal[
        "prefer_first",
        "prefer_backend",
        "vote",
        "llm_arbitrate",
        "ensemble"
    ] = Field(
        default="prefer_first",
        description="Strategy for merging multi-backend results"
    )
    min_block_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to process a block"
    )
    skip_low_confidence: bool = Field(
        default=True,
        description="Skip blocks below min_block_confidence threshold"
    )
