# Format Exporters

This module provides export to multiple output formats.

## Overview

**Status:** ○ Stub - Future phase
**Purpose:** Export conversion results to various formats beyond Markdown

## Planned Features

The exporters module will support multiple output formats:

### Planned Formats
- **Markdown** (baseline - already supported)
- **Docling JSON:** Structured document representation
- **HTML:** Web-ready output
- **LaTeX:** Academic/publishing format
- **DOCX:** Microsoft Word (via python-docx)
- **PDF:** Annotated PDF with extracted text layer

### Planned Architecture

```
exporters/
├── __init__.py         # Package exports
├── base.py             # Exporter interface
├── markdown.py         # Markdown exporter (implemented in pipeline)
├── docling_json.py     # Docling JSON format
├── html.py             # HTML export
├── latex.py            # LaTeX export
└── docx.py             # Word document export
```

### Planned API

```python
from docling_hybrid.exporters import (
    MarkdownExporter,
    DoclingJsonExporter,
    HtmlExporter,
)

# Convert to multiple formats
result = await pipeline.convert_pdf(pdf_path)

# Export to HTML
html_exporter = HtmlExporter()
html = html_exporter.export(result)
with open("output.html", "w") as f:
    f.write(html)

# Export to Docling JSON
json_exporter = DoclingJsonExporter()
doc_json = json_exporter.export(result)
with open("output.json", "w") as f:
    f.write(doc_json)
```

### Current Status

Currently contains:
- `__init__.py`: Empty stub module

Markdown export is currently handled directly in the pipeline.

## Future Development

This module will be implemented in Phase 2+:
1. Exporter base class and interface
2. Format-specific exporters
3. Template system for HTML/LaTeX
4. CLI integration for format selection

## See Also

- [../README.md](../README.md) - Package overview
- [../orchestrator/README.md](../orchestrator/README.md) - Current Markdown output
- [../../CLAUDE.md](../../CLAUDE.md) - Development roadmap
