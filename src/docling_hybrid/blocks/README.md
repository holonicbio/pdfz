# Document Blocks

This module handles block-level document processing.

## Overview

**Status:** ○ Stub - Future phase
**Purpose:** Extract and classify document blocks (tables, figures, formulas)

## Planned Features

The blocks module will provide granular document structure extraction:

### Block Types
- **Headings:** Section titles and headers
- **Paragraphs:** Text blocks
- **Lists:** Bulleted and numbered lists
- **Tables:** Structured data tables
- **Figures:** Images, charts, diagrams
- **Formulas:** Mathematical equations
- **Code:** Code blocks
- **Footnotes:** References and notes
- **Captions:** Figure/table captions

### Planned Architecture

```
blocks/
├── __init__.py         # Package exports
├── base.py             # Block interface (stub)
├── types.py            # Block type definitions
├── extractors/         # Block extraction logic
│   ├── table.py        # Table extraction
│   ├── figure.py       # Figure extraction
│   └── formula.py      # Formula extraction
└── classifiers/        # Block classification
    └── ml_classifier.py
```

### Planned API

```python
from docling_hybrid.blocks import extract_blocks

# Extract all blocks from a page
blocks = await extract_blocks(page_image, page_num)

# Process specific block types
tables = [b for b in blocks if b.type == BlockType.TABLE]
for table in tables:
    markdown = await backend.table_to_markdown(table.image_bytes)
```

### Current Status

Currently contains:
- `base.py`: Stub interface for block extraction
- `types.py`: Block type enums (imported from common.models)

These serve as placeholders for future development.

## Future Development

This module will be implemented in Phase 2+:
1. Block detection using layout analysis
2. Block classification
3. Specialized processing per block type
4. Structure preservation in output

## See Also

- [../README.md](../README.md) - Package overview
- [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) - Extended scope planning
- [../../CLAUDE.md](../../CLAUDE.md) - Development roadmap
