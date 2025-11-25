# Block Processing Interface Documentation

**Status:** Interface Defined (Sprint 1)
**Implementation:** Sprint 6
**Owner:** D09 (Block Processing)

## Overview

The block processing interface enables fine-grained OCR at the block level (paragraphs, tables, formulas) rather than entire pages. This approach allows:

1. **Specialized backends** - Route tables to table-optimized OCR, formulas to LaTeX extraction
2. **Multi-backend ensemble** - Run multiple backends per block and merge results
3. **Better quality** - Focused extraction often outperforms whole-page OCR
4. **Flexibility** - Mix approaches (Docling native + VLM OCR) for best results

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PDF Document                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              BlockSegmenter (via Docling)                        │
│  • Convert PDF to DoclingDocument                               │
│  • Extract blocks with type and geometry                        │
│  • Map Docling labels → BlockType enum                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    List[Block] per page
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BlockRouter                                    │
│  • Apply routing rules                                          │
│  • Select backend(s) for each block                            │
│  • Choose method (page/table/formula)                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        (backend_name, method_name) per block
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend Processing                                  │
│  • Render block region to image                                 │
│  • Call backend method                                          │
│  • Collect candidate results                                    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              List[BackendCandidate]
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BlockMerger                                     │
│  • Apply merge policy                                           │
│  • Select or combine results                                    │
│  • Produce final content                                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   HybridDocument
```

## Core Types

### BlockType Enum

```python
class BlockType(str, Enum):
    """Type of document block."""
    HEADING = "heading"           # Section headings
    PARAGRAPH = "paragraph"       # Regular text
    LIST_ITEM = "list_item"       # Bulleted/numbered items
    TABLE = "table"               # Table structures
    FIGURE = "figure"             # Images, diagrams
    FORMULA = "formula"           # Math equations
    CODE = "code"                 # Code blocks
    FOOTNOTE = "footnote"         # Footnotes
    CAPTION = "caption"           # Figure/table captions
    OTHER = "other"               # Unclassified
```

### Block Dataclass

```python
@dataclass
class Block:
    """Representation of a document block with location and content."""
    id: str                                        # "block-a1b2c3d4"
    block_type: BlockType                          # PARAGRAPH, TABLE, etc.
    page_index: int                                # 0-based page number
    bbox: tuple[float, float, float, float]        # (x1, y1, x2, y2) in PDF points
    content: str | None = None                     # Pre-extracted text from Docling
    confidence: float | None = None                # Docling confidence (0.0-1.0)
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional info
```

**Notes:**
- `bbox` coordinates are in PDF points (1/72 inch) with origin typically at bottom-left
- `content` may be populated by Docling for digital PDFs, None for scanned
- `confidence` reflects Docling's confidence in block detection/classification

### RoutingRule Model

```python
class RoutingRule(BaseModel):
    """Configuration for routing blocks to backends."""
    block_type: BlockType              # Type this rule applies to
    backends: list[str]                # Backend names in priority order
    use_specialized_prompt: bool       # Use table_to_markdown, formula_to_latex
    fallback_to_page: bool            # Fall back to page_to_markdown on error
    max_candidates: int                # Number of backends to try (1+ for multi-backend)
```

**Example:**
```python
# Route tables to specialized backend with fallback
table_rule = RoutingRule(
    block_type=BlockType.TABLE,
    backends=["deepseek-vllm", "nemotron-openrouter"],
    use_specialized_prompt=True,
    fallback_to_page=True,
    max_candidates=2,  # Try both backends for comparison
)
```

### BlockProcessingOptions Model

```python
class BlockProcessingOptions(BaseModel):
    """Options for block-level processing."""
    enabled: bool                      # Enable block-level (vs page-level)
    routing_rules: list[RoutingRule]   # Rules per block type
    merge_policy: Literal[...]         # "prefer_first", "vote", "llm_arbitrate", etc.
    min_block_confidence: float        # Skip blocks below this confidence
    skip_low_confidence: bool          # Skip vs. process anyway
```

## Protocols

### BlockSegmenterProtocol

Extracts blocks from Docling documents.

```python
class BlockSegmenterProtocol(Protocol):
    def segment_page(
        self,
        docling_doc: Any,  # DoclingDocument
        page_index: int,
    ) -> list[Block]:
        """Extract blocks from a single page."""
        ...

    def segment_document(
        self,
        pdf_path: Path,
    ) -> dict[int, list[Block]]:
        """Extract blocks from entire document.

        Returns:
            Dictionary mapping page_index → list of blocks
        """
        ...
```

**Implementation Notes:**
- Use `DocumentConverter` from `docling` package
- Iterate `docling_doc.iterate_items()` to access nodes
- Map Docling labels to `BlockType`:
  - "text" → PARAGRAPH
  - "title", "section_header" → HEADING
  - "list_item" → LIST_ITEM
  - "table" → TABLE
  - "figure", "picture" → FIGURE
  - "formula", "equation" → FORMULA
  - Others → OTHER
- Extract geometry from `node.prov[0].bbox` (if available)
- Handle coordinate origin (typically BOTTOMLEFT for PDFs)

**Docling Integration:**
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(str(pdf_path))
docling_doc = result.document

for node, _ in docling_doc.iterate_items():
    if node.prov and len(node.prov) > 0:
        page_no = node.prov[0].page_no  # 1-indexed
        bbox = node.prov[0].bbox        # BoundingBox with l, t, r, b
        # Convert to Block...
```

### BlockRouterProtocol

Routes blocks to appropriate backends.

```python
class BlockRouterProtocol(Protocol):
    def get_backend_for_block(
        self,
        block: Block,
        available_backends: list[str],
    ) -> tuple[str, str]:
        """Get (backend_name, method_name) for a block."""
        ...

    def get_all_backends_for_block(
        self,
        block: Block,
        available_backends: list[str],
    ) -> list[tuple[str, str]]:
        """Get all backends to try (multi-backend mode)."""
        ...
```

**Implementation Strategy:**
1. Match block type to routing rule
2. Find first available backend from rule's priority list
3. Select method:
   - TABLE + use_specialized_prompt → "table_to_markdown"
   - FORMULA + use_specialized_prompt → "formula_to_latex"
   - Otherwise → "page_to_markdown"
4. For multi-backend: return up to `max_candidates` backends

**Example:**
```python
class RuleBasedRouter:
    def __init__(self, rules: list[RoutingRule]):
        self.rules = {r.block_type: r for r in rules}

    def get_backend_for_block(self, block, available_backends):
        rule = self.rules.get(block.block_type)
        if rule:
            for backend in rule.backends:
                if backend in available_backends:
                    method = self._select_method(block.block_type, rule)
                    return (backend, method)
        # Default fallback
        return (available_backends[0], "page_to_markdown")

    def _select_method(self, block_type, rule):
        if not rule.use_specialized_prompt:
            return "page_to_markdown"
        if block_type == BlockType.TABLE:
            return "table_to_markdown"
        elif block_type == BlockType.FORMULA:
            return "formula_to_latex"
        else:
            return "page_to_markdown"
```

### BlockMergerProtocol

Merges results from multiple backends.

```python
class BlockMergerProtocol(Protocol):
    def merge(
        self,
        candidates: list[BackendCandidate],
        block: Block,
    ) -> str:
        """Select/combine candidates to produce final content."""
        ...
```

**Merge Policies:**

1. **prefer_first** - Use first successful result
   ```python
   for candidate in candidates:
       if candidate.score and candidate.score > threshold:
           return candidate.content
   ```

2. **prefer_backend** - Prefer specific backend
   ```python
   for candidate in candidates:
       if candidate.backend_name == preferred and candidate.score > threshold:
           return candidate.content
   # Fallback to first successful
   ```

3. **vote** - Majority voting by similarity
   ```python
   # Group similar results
   # Return most common
   ```

4. **llm_arbitrate** - Use LLM to choose/merge
   ```python
   prompt = build_arbitration_prompt(candidates, block)
   decision = await arbitrator_backend.page_to_markdown(prompt)
   return parse_decision(decision)
   ```

5. **ensemble** - Weighted combination
   ```python
   # Combine based on confidence scores
   ```

### BlockProcessorProtocol

Complete block-level processing pipeline.

```python
class BlockProcessorProtocol(Protocol):
    async def process_document(
        self,
        pdf_path: Path,
        options: BlockProcessingOptions,
    ) -> HybridDocument:
        """Process entire document using block-level approach."""
        ...
```

**High-Level Flow:**
```python
async def process_document(self, pdf_path, options):
    # 1. Segment document
    blocks_by_page = self.segmenter.segment_document(pdf_path)

    # 2. Process each block
    hybrid_blocks = []
    for page_idx, blocks in blocks_by_page.items():
        for block in blocks:
            # Skip low confidence
            if block.confidence and block.confidence < options.min_block_confidence:
                if options.skip_low_confidence:
                    continue

            # Route to backend(s)
            if options.routing_rules:
                backends = self.router.get_all_backends_for_block(block, available)
            else:
                backends = [(default_backend, "page_to_markdown")]

            # Render block region
            image_bytes = self.renderer.render_region(
                pdf_path, block.page_index, block.bbox
            )

            # Process with backend(s)
            candidates = []
            for backend_name, method in backends:
                backend = self.backends[backend_name]
                result = await self._call_backend_method(backend, method, image_bytes, block)
                candidates.append(result)

            # Merge results
            final_content = self.merger.merge(candidates, block)

            # Create HybridBlock
            hybrid_block = HybridBlock(
                id=block.id,
                block_type=block.block_type,
                geometry=...,
                candidates=candidates,
                final_content=final_content,
                ...
            )
            hybrid_blocks.append(hybrid_block)

    # 3. Assemble document
    return HybridDocument(
        doc_id=generate_id("doc"),
        source_path=str(pdf_path),
        blocks=hybrid_blocks,
        ...
    )
```

## Usage Examples

### Basic Block-Level Processing

```python
from pathlib import Path
from docling_hybrid.blocks import (
    BlockProcessorProtocol,
    BlockProcessingOptions,
    BlockType,
    RoutingRule,
)

# Configure routing rules
options = BlockProcessingOptions(
    enabled=True,
    routing_rules=[
        RoutingRule(
            block_type=BlockType.TABLE,
            backends=["deepseek-vllm"],
            use_specialized_prompt=True,
            max_candidates=1,
        ),
        RoutingRule(
            block_type=BlockType.FORMULA,
            backends=["deepseek-vllm"],
            use_specialized_prompt=True,
            max_candidates=1,
        ),
    ],
    merge_policy="prefer_first",
    min_block_confidence=0.5,
)

# Process document (Sprint 6+)
processor: BlockProcessorProtocol = create_processor(config)
result = await processor.process_document(
    Path("document.pdf"),
    options
)

# Export to markdown
markdown = result.export_to_markdown()
print(markdown)
```

### Multi-Backend Ensemble

```python
# Configure multi-backend for tables
table_rule = RoutingRule(
    block_type=BlockType.TABLE,
    backends=["deepseek-vllm", "nemotron-openrouter", "gpt-4-vision"],
    use_specialized_prompt=True,
    max_candidates=3,  # Try all three
)

options = BlockProcessingOptions(
    enabled=True,
    routing_rules=[table_rule],
    merge_policy="vote",  # Use majority voting
)

result = await processor.process_document(pdf_path, options)

# Inspect candidates for a table
for block in result.blocks:
    if block.block_type == BlockType.TABLE:
        print(f"Table: {len(block.candidates)} candidates")
        for candidate in block.candidates:
            print(f"  {candidate.backend_name}: score={candidate.score}")
        print(f"Chosen: {block.final_content[:100]}...")
```

### Custom Segmenter

```python
from docling.document_converter import DocumentConverter
from docling_hybrid.blocks import BlockSegmenterProtocol, Block, BlockType

class MyDoclingSegmenter:
    """Custom segmenter using Docling."""

    def __init__(self):
        self.converter = DocumentConverter()
        self.label_map = {
            "text": BlockType.PARAGRAPH,
            "title": BlockType.HEADING,
            "section_header": BlockType.HEADING,
            "table": BlockType.TABLE,
            "figure": BlockType.FIGURE,
            "picture": BlockType.FIGURE,
            "formula": BlockType.FORMULA,
            "equation": BlockType.FORMULA,
            "code": BlockType.CODE,
            "list_item": BlockType.LIST_ITEM,
        }

    def segment_page(self, docling_doc, page_index):
        blocks = []
        for node, _ in docling_doc.iterate_items():
            if not node.prov or len(node.prov) == 0:
                continue

            prov = node.prov[0]
            if prov.page_no != page_index + 1:  # Docling uses 1-indexed
                continue

            # Map label to BlockType
            label = node.label if hasattr(node, 'label') else 'text'
            block_type = self.label_map.get(label, BlockType.OTHER)

            # Extract geometry
            if prov.bbox:
                bbox = (prov.bbox.l, prov.bbox.t, prov.bbox.r, prov.bbox.b)
            else:
                continue  # Skip blocks without geometry

            # Create Block
            block = Block(
                id=generate_id("block"),
                block_type=block_type,
                page_index=page_index,
                bbox=bbox,
                content=node.text if hasattr(node, 'text') else None,
                metadata={
                    "docling_label": label,
                    "docling_id": node.self_ref if hasattr(node, 'self_ref') else None,
                }
            )
            blocks.append(block)

        return blocks

    def segment_document(self, pdf_path):
        result = self.converter.convert(str(pdf_path))
        docling_doc = result.document

        # Get page count
        max_page = 0
        for node, _ in docling_doc.iterate_items():
            if node.prov and len(node.prov) > 0:
                max_page = max(max_page, node.prov[0].page_no)

        # Segment each page
        blocks_by_page = {}
        for page_index in range(max_page):
            blocks_by_page[page_index] = self.segment_page(docling_doc, page_index)

        return blocks_by_page
```

## Testing Strategy

### Unit Testing Protocols

```python
# tests/unit/blocks/test_router.py

def test_router_selects_specialized_backend():
    rule = RoutingRule(
        block_type=BlockType.TABLE,
        backends=["deepseek-vllm", "nemotron"],
        use_specialized_prompt=True,
    )
    router = RuleBasedRouter([rule])

    table_block = Block(
        id="b1", block_type=BlockType.TABLE,
        page_index=0, bbox=(0, 0, 100, 100)
    )

    backend, method = router.get_backend_for_block(
        table_block,
        ["deepseek-vllm", "nemotron"]
    )

    assert backend == "deepseek-vllm"
    assert method == "table_to_markdown"


def test_router_fallback_to_page():
    rule = RoutingRule(
        block_type=BlockType.TABLE,
        backends=["missing-backend"],
        use_specialized_prompt=True,
        fallback_to_page=True,
    )
    router = RuleBasedRouter([rule])

    table_block = Block(
        id="b1", block_type=BlockType.TABLE,
        page_index=0, bbox=(0, 0, 100, 100)
    )

    backend, method = router.get_backend_for_block(
        table_block,
        ["nemotron"]  # "missing-backend" not available
    )

    assert backend == "nemotron"
    assert method == "page_to_markdown"
```

### Integration Testing

```python
# tests/integration/blocks/test_block_processing.py

async def test_block_processor_end_to_end(sample_pdf):
    """Test complete block processing pipeline."""
    # Create processor with real components
    segmenter = DoclingSegmenter()
    router = RuleBasedRouter(rules)
    merger = PreferFirstMerger()
    backends = {"nemotron": create_nemotron_backend()}

    processor = HybridBlockProcessor(
        segmenter=segmenter,
        router=router,
        merger=merger,
        backends=backends,
    )

    options = BlockProcessingOptions(enabled=True, routing_rules=[...])

    result = await processor.process_document(sample_pdf, options)

    assert isinstance(result, HybridDocument)
    assert len(result.blocks) > 0
    assert result.export_to_markdown()
```

## Implementation Timeline

**Sprint 1 (Current):**
- ✅ Define all interfaces (BlockSegmenter, BlockRouter, BlockMerger, BlockProcessor)
- ✅ Define all data types (BlockType, Block, RoutingRule, BlockProcessingOptions)
- ✅ Document interface contracts
- ✅ Create design document

**Sprint 6 (Weeks 11-12):**
- Implement DoclingSegmenter
- Implement RuleBasedRouter
- Implement PreferFirstMerger
- Implement HybridBlockProcessor
- Add region rendering to renderer
- Integration tests

**Sprint 7 (Weeks 13-14):**
- Implement additional merge strategies (vote, llm_arbitrate)
- Multi-backend support
- Performance optimization

**Sprint 8 (Weeks 15-16):**
- Evaluation metrics for block-level OCR
- Documentation and examples
- Production hardening

## References

### Docling Documentation
- [Docling GitHub Repository](https://github.com/docling-project/docling)
- [Docling Documentation](https://docling-project.github.io/docling/)
- [Docling Document Concept](https://docling-project.github.io/docling/concepts/docling_document/)
- [Docling PyPI Package](https://pypi.org/project/docling/)

### Related Documentation
- `docs/ARCHITECTURE.md` - System architecture overview
- `docs/components/BACKENDS.md` - Backend interface documentation
- `docs/components/RENDERER.md` - Renderer interface documentation
- `docs/design/BLOCK_PROCESSING.md` - Block processing design document

### Research Papers
- [Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion](https://arxiv.org/html/2501.17887v1)
- [IBM Research Blog: Docling for Generative AI](https://research.ibm.com/blog/docling-generative-AI)

---

**Document Version:** 1.0
**Last Updated:** Sprint 1, Day 8
**Next Review:** Sprint 6 kickoff
