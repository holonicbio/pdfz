# Block Processing Design Document

**Author:** D09 (Block Processing Lead)
**Created:** Sprint 1, Week 2
**Status:** Design Approved
**Implementation:** Sprint 6

## Executive Summary

This document describes the design for block-level OCR processing in Docling Hybrid OCR. Block-level processing enables fine-grained extraction where different document elements (tables, formulas, paragraphs) are processed by specialized backends optimized for those content types.

**Key Benefits:**
- **Better Quality:** Specialized backends outperform generic page-level OCR for specific content types
- **Flexibility:** Mix approaches (Docling native + VLM OCR) for optimal results
- **Multi-Backend:** Compare outputs from multiple models and merge intelligently
- **Efficiency:** Skip or prioritize blocks based on confidence scores

## Background

### Current State (Sprint 1-4)

The Minimal Core system (v0.1.0) processes PDFs at the page level:
1. Render entire page to PNG
2. Send to VLM backend (OpenRouter/Nemotron)
3. Extract Markdown from entire page

**Limitations:**
- Tables often have formatting errors in whole-page OCR
- Formulas may not extract to proper LaTeX
- No way to use specialized backends for specific content types
- Cannot leverage Docling's native PDF text extraction

### Target State (Sprint 6+)

Block-level processing enables:
1. Segment page into blocks (via Docling)
2. Route blocks to appropriate backends
3. Use specialized prompts (table_to_markdown, formula_to_latex)
4. Optionally run multiple backends per block
5. Merge results intelligently

## Research Findings: Docling API

### What is Docling?

Docling is an open-source toolkit from IBM Research for document conversion, hosted by the LF AI & Data Foundation. It uses vision models to dissect page layouts and classify document elements.

**Key Features:**
- Layout analysis with object detection
- Block classification (text, tables, figures, formulas, etc.)
- Bounding box extraction
- Reading order determination
- Multi-format support (PDF, DOCX, PPTX, etc.)

**References:**
- [Docling GitHub](https://github.com/docling-project/docling)
- [Docling Documentation](https://docling-project.github.io/docling/)
- [Research Paper (AAAI 2025)](https://arxiv.org/html/2501.17887v1)

### Docling API Structure

#### DoclingDocument

Docling converts documents to a unified `DoclingDocument` representation with:

**Content Items:**
- `texts` - TextItem objects (paragraphs, headings, equations)
- `tables` - TableItem objects
- `pictures` - PictureItem objects

**Content Structure:**
- `body` - Tree structure for main document body
- `furniture` - Headers, footers, page numbers
- `groups` - Containers for related items

#### Iteration API

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")
docling_doc = result.document

# Iterate through all items
for node, _ in docling_doc.iterate_items():
    data = node.model_dump()  # Convert to dict
    label = data['label']      # e.g., "text", "title", "table"
    text = data.get('text', '') # Text content (if available)
```

#### Block Geometry

Each `DocItem` contains provenance information:

```python
for node, _ in docling_doc.iterate_items():
    if node.prov and len(node.prov) > 0:
        prov = node.prov[0]
        page_no = prov.page_no      # 1-indexed page number
        bbox = prov.bbox            # BoundingBox object

        # BoundingBox properties
        left = bbox.l
        top = bbox.t
        right = bbox.r
        bottom = bbox.b
        coord_origin = bbox.coord_origin  # e.g., "BOTTOMLEFT"
```

**Important:** PDF coordinates typically use BOTTOMLEFT origin, where (0, 0) is the bottom-left corner of the page.

#### Label Types

Common Docling labels and their meanings:

| Docling Label | Description | Maps to BlockType |
|--------------|-------------|-------------------|
| `text` | Regular paragraph | PARAGRAPH |
| `title` | Document title | HEADING |
| `section_header` | Section heading | HEADING |
| `list_item` | Bulleted/numbered item | LIST_ITEM |
| `table` | Table structure | TABLE |
| `figure`, `picture` | Image, chart | FIGURE |
| `formula`, `equation` | Math expression | FORMULA |
| `code` | Code block | CODE |
| `page_header`, `page_footer` | Headers/footers | OTHER |

### Integration Strategy

**Approach: Wrapper Pattern**

Create a `DoclingSegmenter` that wraps Docling's API and converts to our `Block` representation:

```python
class DoclingSegmenter(BlockSegmenterProtocol):
    def __init__(self):
        self.converter = DocumentConverter()
        self.label_map = {
            "text": BlockType.PARAGRAPH,
            "title": BlockType.HEADING,
            # ... complete mapping
        }

    def segment_document(self, pdf_path):
        result = self.converter.convert(str(pdf_path))
        docling_doc = result.document

        blocks_by_page = {}
        for node, _ in docling_doc.iterate_items():
            block = self._convert_node_to_block(node)
            page_idx = block.page_index
            blocks_by_page.setdefault(page_idx, []).append(block)

        return blocks_by_page
```

## System Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     HybridPipeline                           │
│  Orchestrates page-level OR block-level processing         │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼ (page-level)                   ▼ (block-level)
┌──────────────┐                  ┌──────────────┐
│  Page Mode   │                  │  Block Mode  │
│  (Sprint 4)  │                  │ (Sprint 6+)  │
└──────────────┘                  └──────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
            ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
            │ Segmenter    │     │   Router     │     │   Merger     │
            │ (Docling)    │     │  (Rules)     │     │ (Policies)   │
            └──────────────┘     └──────────────┘     └──────────────┘
```

### Component Interactions

```
User
  │
  └─> HybridPipeline.convert_pdf(options)
        │
        ├─> If options.block_processing.enabled == False:
        │     └─> [Page-level flow - Sprint 1-4 implementation]
        │
        └─> If options.block_processing.enabled == True:
              │
              ├─> BlockSegmenter.segment_document(pdf_path)
              │     └─> Returns: dict[page_index, list[Block]]
              │
              ├─> For each page:
              │     ├─> For each block:
              │     │     │
              │     │     ├─> BlockRouter.get_backend_for_block(block)
              │     │     │     └─> Returns: (backend_name, method_name)
              │     │     │
              │     │     ├─> Renderer.render_region(page, block.bbox)
              │     │     │     └─> Returns: image_bytes (cropped to block)
              │     │     │
              │     │     ├─> Backend[backend_name].{method_name}(image_bytes)
              │     │     │     └─> Returns: BackendCandidate
              │     │     │
              │     │     └─> (Multi-backend mode)
              │     │           ├─> Repeat for each backend
              │     │           └─> BlockMerger.merge(candidates)
              │     │                 └─> Returns: final_content
              │     │
              │     └─> Assemble blocks → HybridDocument
              │
              └─> Return ConversionResult
```

## Design Decisions

### Decision 1: Protocol-Based Interfaces

**Choice:** Use Protocol classes (PEP 544) instead of ABC classes

**Rationale:**
- More flexible - implementations don't need to inherit
- Easier testing - can mock without inheritance
- Type checkers understand Protocols
- Matches Python community best practices

**Alternative Considered:** Abstract base classes
**Rejected Because:** Requires inheritance, less flexible for testing

### Decision 2: Docling as Primary Segmenter

**Choice:** Use Docling's native segmentation

**Rationale:**
- Battle-tested layout analysis
- Open source (MIT license)
- Active development by IBM Research
- Supports multiple document formats
- Good accuracy on complex layouts

**Alternative Considered:**
- LayoutLM-based segmentation
- Rule-based heuristics from PDF structure

**Rejected Because:**
- Would require training our own model
- Heuristics fail on complex documents

### Decision 3: Routing Rules Configuration

**Choice:** Declarative routing rules in configuration

**Rationale:**
- No code changes to adjust routing
- Easy to experiment with different strategies
- Clear documentation of routing decisions
- Can be overridden per-document if needed

**Example:**
```toml
[[block_processing.routing_rules]]
block_type = "table"
backends = ["deepseek-vllm", "nemotron-openrouter"]
use_specialized_prompt = true
fallback_to_page = true
max_candidates = 2
```

**Alternative Considered:** Hard-coded routing in code
**Rejected Because:** Inflexible, requires code changes

### Decision 4: Multi-Backend as Optional

**Choice:** Single backend by default, multi-backend opt-in

**Rationale:**
- Single backend is faster and cheaper
- Multi-backend adds API cost and latency
- Most blocks work fine with single backend
- Power users can enable for critical content

**Configuration:**
- `max_candidates = 1` → single backend (default)
- `max_candidates > 1` → multi-backend mode

### Decision 5: Merge Policies

**Choice:** Support multiple merge strategies

**Rationale:**
- Different use cases need different strategies
- Allow experimentation
- Future-proof for new approaches

**Implemented Policies:**
1. **prefer_first** - Fast, use first successful result
2. **prefer_backend** - Trust specific backend
3. **vote** - Majority consensus (requires similarity detection)
4. **llm_arbitrate** - Use LLM to choose/merge (expensive but smart)
5. **ensemble** - Weighted combination (future work)

### Decision 6: Block Coordinates in PDF Points

**Choice:** Use PDF points (1/72 inch) for bbox coordinates

**Rationale:**
- Native PDF coordinate system
- Matches Docling output
- Standard in PDF ecosystem
- Easy conversion to pixels: `pixels = points * (DPI / 72)`

**Alternative Considered:** Pixel coordinates
**Rejected Because:** DPI-dependent, requires extra conversion step

## Implementation Plan

### Sprint 6: Core Block Processing

**Week 1:**
- D09: Implement DoclingSegmenter
  - Integrate Docling DocumentConverter
  - Map labels to BlockType
  - Extract geometry from provenance
  - Handle coordinate systems

- D05: Add region rendering to Renderer
  - Implement render_region method
  - Handle bbox cropping
  - Coordinate conversion

**Week 2:**
- D09: Implement RuleBasedRouter
  - Load routing rules from config
  - Match blocks to rules
  - Select backend and method

- D09: Implement PreferFirstMerger
  - Basic merge strategy
  - Confidence threshold checking

- D03: Integrate into HybridPipeline
  - Add block_processing option
  - Route page-level vs block-level
  - Assemble HybridDocument

**Week 2 (continued):**
- D07: Integration tests
  - Test with sample PDFs
  - Verify block extraction
  - Verify routing logic

### Sprint 7: Multi-Backend & Advanced Merging

**Week 1:**
- D09: Implement VotingMerger
  - Similarity detection
  - Majority selection

- D09: Implement LlmArbitrationMerger
  - Arbitration prompt engineering
  - Result parsing

**Week 2:**
- D02: Multi-backend orchestration
  - Parallel backend calls
  - Timeout handling
  - Error aggregation

- D03: Performance optimization
  - Batch processing
  - Caching

### Sprint 8: Evaluation & Polish

- D10: Block-level evaluation metrics
- D09: Edge case handling
- D08: Documentation and examples

## Configuration Schema

### BlockProcessingOptions

```python
class BlockProcessingOptions(BaseModel):
    """Options for block-level processing."""

    enabled: bool = False
    """Enable block-level processing (vs page-level only)"""

    routing_rules: list[RoutingRule] = []
    """Rules for routing block types to backends"""

    merge_policy: Literal[
        "prefer_first",
        "prefer_backend",
        "vote",
        "llm_arbitrate",
        "ensemble"
    ] = "prefer_first"
    """Strategy for merging multi-backend results"""

    min_block_confidence: float = 0.5
    """Minimum confidence score to process a block (0.0-1.0)"""

    skip_low_confidence: bool = True
    """Skip blocks below min_block_confidence threshold"""
```

### Example Configuration (TOML)

```toml
[block_processing]
enabled = true
merge_policy = "prefer_first"
min_block_confidence = 0.6
skip_low_confidence = true

[[block_processing.routing_rules]]
block_type = "table"
backends = ["deepseek-vllm", "nemotron-openrouter"]
use_specialized_prompt = true
fallback_to_page = true
max_candidates = 2

[[block_processing.routing_rules]]
block_type = "formula"
backends = ["deepseek-vllm"]
use_specialized_prompt = true
fallback_to_page = false
max_candidates = 1

[[block_processing.routing_rules]]
block_type = "paragraph"
backends = ["docling-native", "nemotron-openrouter"]
use_specialized_prompt = false
fallback_to_page = false
max_candidates = 1
```

## Testing Strategy

### Unit Tests

```python
# tests/unit/blocks/test_segmenter.py
def test_docling_segmenter_maps_labels():
    """Verify label mapping to BlockType."""
    segmenter = DoclingSegmenter()
    assert segmenter.label_map["table"] == BlockType.TABLE
    assert segmenter.label_map["text"] == BlockType.PARAGRAPH

def test_segmenter_extracts_geometry():
    """Verify bbox extraction from provenance."""
    # Mock Docling node
    mock_node = create_mock_node(
        label="table",
        page_no=1,
        bbox=(100, 200, 400, 300)
    )

    segmenter = DoclingSegmenter()
    block = segmenter._convert_node_to_block(mock_node)

    assert block.block_type == BlockType.TABLE
    assert block.bbox == (100, 200, 400, 300)

# tests/unit/blocks/test_router.py
def test_router_uses_specialized_method():
    """Verify specialized method selection."""
    rule = RoutingRule(
        block_type=BlockType.TABLE,
        backends=["deepseek-vllm"],
        use_specialized_prompt=True,
    )
    router = RuleBasedRouter([rule])

    table_block = Block(
        id="b1", block_type=BlockType.TABLE,
        page_index=0, bbox=(0, 0, 100, 100)
    )

    backend, method = router.get_backend_for_block(
        table_block, ["deepseek-vllm"]
    )

    assert method == "table_to_markdown"

# tests/unit/blocks/test_merger.py
def test_prefer_first_merger():
    """Verify prefer_first strategy."""
    candidates = [
        BackendCandidate(backend_name="b1", content="Result 1", score=0.9),
        BackendCandidate(backend_name="b2", content="Result 2", score=0.85),
    ]

    merger = PreferFirstMerger(min_score=0.5)
    block = Block(id="b1", block_type=BlockType.TABLE, page_index=0, bbox=(0,0,100,100))

    result = merger.merge(candidates, block)
    assert result == "Result 1"
```

### Integration Tests

```python
# tests/integration/blocks/test_block_processing.py
async def test_block_processing_end_to_end(sample_pdf):
    """Test complete block processing pipeline."""
    options = BlockProcessingOptions(
        enabled=True,
        routing_rules=[
            RoutingRule(
                block_type=BlockType.TABLE,
                backends=["nemotron-openrouter"],
                use_specialized_prompt=True,
            )
        ],
        merge_policy="prefer_first",
    )

    pipeline = HybridPipeline(config)
    result = await pipeline.convert_pdf(sample_pdf, options)

    # Verify blocks were extracted
    assert len(result.blocks) > 0

    # Verify tables used specialized backend
    for block in result.blocks:
        if block.block_type == BlockType.TABLE:
            assert any(
                c.backend_name == "nemotron-openrouter"
                for c in block.candidates
            )
```

## Performance Considerations

### Memory Usage

**Per-Block Processing:**
- Docling document: ~50MB for 10-page PDF
- Block image rendering: ~100KB per block (DPI 150)
- Backend processing: ~500MB per concurrent request

**Optimization Strategies:**
- Release Docling document after segmentation
- Stream block processing (don't hold all in memory)
- Limit concurrent backend requests

### Processing Time

**Estimated Times (10-page PDF with 50 blocks):**
- Docling segmentation: ~5 seconds
- Block rendering: ~0.1s per block = 5 seconds
- Backend OCR: ~2s per block = 100 seconds (sequential)
  - With concurrency (4 workers): ~25 seconds
- Total: ~35 seconds

**Comparison to Page-Level:**
- Page-level: ~20 seconds (10 pages × 2s per page)
- Block-level overhead: ~15 seconds (+75%)

**Trade-off:** Higher quality for tables/formulas justifies the overhead.

### Cost Considerations

**API Costs:**
- Page-level: 10 API calls (1 per page)
- Block-level: 50 API calls (5 blocks per page average)
- Multi-backend (2×): 100 API calls

**Mitigation:**
- Use routing rules to limit expensive backends to critical blocks
- Cache Docling results for repeated processing
- Use local backends (vLLM/MLX) when available

## Risk Analysis

### Risk 1: Docling Segmentation Errors

**Probability:** Medium
**Impact:** High (incorrect blocks → incorrect content)

**Mitigation:**
- Confidence threshold filtering
- Fallback to page-level if too many low-confidence blocks
- Manual review interface for critical documents

### Risk 2: Coordinate System Mismatches

**Probability:** Low
**Impact:** High (wrong regions rendered)

**Mitigation:**
- Comprehensive coordinate conversion tests
- Visual debugging tools (render bbox overlays)
- Validate against known-good PDFs

### Risk 3: Performance Overhead

**Probability:** High
**Impact:** Medium (slower processing)

**Mitigation:**
- Make block-level opt-in (not default)
- Optimize concurrent processing
- Profile and optimize hot paths

### Risk 4: Increased Complexity

**Probability:** High
**Impact:** Medium (harder to debug, maintain)

**Mitigation:**
- Comprehensive documentation
- Clear logging at each step
- Extensive test coverage
- Gradual rollout (page-level stable first)

## Future Enhancements

### Phase 3: Advanced Features

1. **Hybrid Segmentation**
   - Combine Docling + custom heuristics
   - Learn from corrections

2. **Adaptive Routing**
   - Learn which backends work best for which blocks
   - Confidence-based routing

3. **Block Relationships**
   - Maintain parent-child relationships (captions, footnotes)
   - Preserve reading order across columns

4. **Streaming Processing**
   - Process blocks as they're segmented
   - Reduce memory footprint

## Conclusion

Block-level processing is a natural evolution of the Docling Hybrid OCR system, enabling specialized backends for different content types. By leveraging Docling's excellent layout analysis, we can route blocks intelligently and produce higher-quality output for complex documents.

**Key Success Factors:**
1. Clean interface definition (Sprint 1) ✅
2. Robust Docling integration (Sprint 6)
3. Flexible routing configuration (Sprint 6)
4. Comprehensive testing (Sprint 6-7)
5. Performance optimization (Sprint 7-8)

## Appendix: References

### Docling Research
- [Docling Project](https://github.com/docling-project/docling) - GitHub repository
- [Docling Documentation](https://docling-project.github.io/docling/) - Official docs
- [Docling Paper (AAAI 2025)](https://arxiv.org/html/2501.17887v1) - Research paper
- [IBM Research Blog](https://research.ibm.com/blog/docling-generative-AI) - Overview
- [Docling with LangChain](https://python.langchain.com/docs/integrations/document_loaders/docling/) - Integration example
- [Medium: Enhancing PDF-to-Markdown with Docling](https://medium.com/@shinimarykoshy1996/enhancing-pdf-to-markdown-extraction-with-docling-and-custom-bbox-logic-a71402bed088) - BBox usage

### Related Documentation
- `docs/interfaces/BLOCKS_INTERFACE.md` - Interface specification
- `docs/ARCHITECTURE.md` - System architecture
- `docs/components/BACKENDS.md` - Backend interface
- `docs/components/RENDERER.md` - Renderer interface
- `CLAUDE.md` - Master development context

---

**Document Version:** 1.0
**Approved By:** D01 (Tech Lead), Sprint 1
**Implementation Start:** Sprint 6
