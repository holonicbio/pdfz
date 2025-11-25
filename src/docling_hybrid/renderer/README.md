# PDF Renderer

This module handles the conversion of PDF pages to PNG images for VLM processing.

## Overview

**Status:** ✅ Complete
**Purpose:** Fast, memory-efficient PDF page rendering using pypdfium2

The renderer module provides functions and classes for converting PDF pages to PNG images optimized for Vision-Language Model (VLM) inference. It uses pypdfium2 for fast, reliable rendering with minimal dependencies.

## Module Contents

```
renderer/
├── __init__.py         # Package exports
└── core.py             # Main rendering functionality
```

## Core Functions

### 1. `get_page_count(pdf_path: Path) -> int`

Get the total number of pages in a PDF.

```python
from pathlib import Path
from docling_hybrid.renderer import get_page_count

pdf_path = Path("document.pdf")
count = get_page_count(pdf_path)
print(f"Document has {count} pages")
```

**Args:**
- `pdf_path`: Path to the PDF file

**Returns:**
- Number of pages (int)

**Raises:**
- `ValidationError`: If PDF file doesn't exist
- `RenderingError`: If PDF cannot be opened

### 2. `render_page_to_png_bytes(pdf_path, page_index, dpi=200) -> bytes`

Render a single PDF page to PNG bytes.

```python
from pathlib import Path
from docling_hybrid.renderer import render_page_to_png_bytes

# Render page 1 (index 0) at 200 DPI
image_bytes = render_page_to_png_bytes(
    pdf_path=Path("document.pdf"),
    page_index=0,  # 0-indexed
    dpi=200,
)

# Check size
print(f"Image size: {len(image_bytes) / 1024:.1f} KB")

# Save to file
with open("page1.png", "wb") as f:
    f.write(image_bytes)
```

**Args:**
- `pdf_path`: Path to the PDF file
- `page_index`: Page index (0-based, so page 1 = index 0)
- `dpi`: Resolution in dots per inch (default: 200)

**DPI Guidelines:**
- **72 DPI:** Low quality, fast, ~100KB per page
- **150 DPI:** Medium quality (local dev), ~300KB per page
- **200 DPI:** Good quality (recommended), ~500KB per page
- **300 DPI:** High quality, slower, ~1MB per page
- **600 DPI:** Maximum, very slow, ~4MB per page

**Returns:**
- PNG image as bytes (RGB format)

**Raises:**
- `ValidationError`: If PDF doesn't exist, page index invalid, or DPI out of range
- `RenderingError`: If rendering fails

**Note:** This function opens and closes the PDF for each call. For batch processing, use `PdfRenderer` class or `render_pdf_pages()` instead.

### 3. `render_region_to_png_bytes(pdf_path, page_index, bbox, dpi=200, padding=10) -> bytes`

Render a specific region of a PDF page (useful for tables, figures).

```python
from pathlib import Path
from docling_hybrid.renderer import render_region_to_png_bytes

# Extract a table region (coordinates in PDF points, 1/72 inch)
image_bytes = render_region_to_png_bytes(
    pdf_path=Path("document.pdf"),
    page_index=0,
    bbox=(72, 400, 540, 600),  # (x1, y1, x2, y2)
    dpi=200,
    padding=10,  # Add 10 pixels padding around region
)
```

**Args:**
- `pdf_path`: Path to the PDF file
- `page_index`: Page index (0-based)
- `bbox`: Bounding box `(x1, y1, x2, y2)` in PDF coordinates
  - Origin is bottom-left of page
  - Units are points (1/72 inch)
- `dpi`: Resolution in dots per inch (default: 200)
- `padding`: Pixels of padding around the region (default: 10)

**Returns:**
- PNG image of the cropped region as bytes

**Raises:**
- `ValidationError`: If inputs are invalid
- `RenderingError`: If rendering fails

**Note:** This is part of the extended scope for block-level processing. The minimal core only uses full-page rendering.

### 4. `render_pdf_pages(pdf_path, page_indices=None, dpi=200) -> List[bytes]`

Convenience function for batch rendering with automatic cleanup.

```python
from pathlib import Path
from docling_hybrid.renderer import render_pdf_pages

# Render specific pages
images = render_pdf_pages(
    Path("document.pdf"),
    page_indices=[0, 5, 10],  # Pages 1, 6, 11
    dpi=200,
)

# Render all pages
all_images = render_pdf_pages(Path("document.pdf"))

# Process results
for i, image_bytes in enumerate(images):
    print(f"Page {i}: {len(image_bytes) / 1024:.1f} KB")
```

**Args:**
- `pdf_path`: Path to the PDF file
- `page_indices`: List of page indices (0-based). If None, renders all pages.
- `dpi`: Resolution in dots per inch (default: 200)

**Returns:**
- List of PNG images as bytes

**Raises:**
- `ValidationError`: If PDF doesn't exist or page indices invalid
- `RenderingError`: If PDF cannot be opened or rendering fails

## PdfRenderer Class

Memory-efficient renderer for batch processing. Keeps the PDF open across multiple renders to avoid repeated open/close overhead.

### Usage

```python
from pathlib import Path
from docling_hybrid.renderer import PdfRenderer

# Basic usage
with PdfRenderer(Path("document.pdf")) as renderer:
    print(f"Total pages: {renderer.page_count}")

    # Render pages one by one
    for i in range(renderer.page_count):
        image_bytes = renderer.render_page(i, dpi=200)
        # Process image_bytes...

# Render specific pages
with PdfRenderer(Path("document.pdf")) as renderer:
    pages_to_render = [0, 5, 10, 15]  # Pages 1, 6, 11, 16
    for page_idx in pages_to_render:
        image_bytes = renderer.render_page(page_idx)
        # Process...

# Batch render all at once
with PdfRenderer(Path("document.pdf")) as renderer:
    # Render all pages
    all_images = renderer.render_pages()

    # Or specific pages
    selected_images = renderer.render_pages([0, 1, 2], dpi=150)
```

### Methods

**`__init__(pdf_path: Path)`**
Initialize the renderer.

**`__enter__() -> PdfRenderer`**
Open the PDF document. Called automatically by `with` statement.

**`__exit__(exc_type, exc_val, exc_tb)`**
Close the PDF document. Called automatically when exiting `with` block.

**`page_count: int`** (property)
Get the number of pages in the PDF.

**`render_page(page_index: int, dpi: int = 200) -> bytes`**
Render a single page to PNG bytes.

**`render_pages(page_indices: List[int] | None = None, dpi: int = 200) -> List[bytes]`**
Render multiple pages in batch.

### Advantages Over `render_page_to_png_bytes()`

1. **Memory efficient:** PDF opened once, not per page
2. **Faster for multiple pages:** No repeated open/close overhead
3. **Context manager:** Automatic cleanup on exit
4. **Progress tracking:** Can track page_count during processing

### When to Use Each

**Use `render_page_to_png_bytes()` when:**
- Rendering a single page
- Quick one-off operations
- Simplicity is preferred

**Use `PdfRenderer` when:**
- Rendering multiple pages from same PDF
- Processing entire documents
- Memory efficiency matters
- Need progress tracking

## Output Format

All rendering functions produce PNG images with the following characteristics:

- **Format:** PNG (lossless compression)
- **Color mode:** RGB
- **Optimization:** PNG optimize flag enabled
- **Scale:** DPI/72 (pypdfium2 default is 72 DPI)
- **Size:** Varies with DPI and page content
  - Text-heavy: 200-800 KB at 200 DPI
  - Image-heavy: 1-5 MB at 200 DPI

### Why PNG?

1. **Lossless:** No quality degradation
2. **VLM-friendly:** Most VLMs expect lossless formats
3. **Good compression:** Efficient for text and diagrams
4. **Universal support:** Works everywhere

### Why RGB?

VLMs typically expect RGB input. Even if the PDF is grayscale, we convert to RGB for consistency.

## Common Patterns

### Pattern 1: Single Page Processing

```python
from pathlib import Path
from docling_hybrid.renderer import render_page_to_png_bytes

pdf_path = Path("document.pdf")

# Render first page
page1_bytes = render_page_to_png_bytes(pdf_path, page_index=0, dpi=200)

# Send to VLM backend
markdown = await backend.page_to_markdown(page1_bytes, page_num=1, doc_id="doc-123")
```

### Pattern 2: Batch Processing with PdfRenderer

```python
from pathlib import Path
from docling_hybrid.renderer import PdfRenderer

pdf_path = Path("document.pdf")
results = []

with PdfRenderer(pdf_path) as renderer:
    for i in range(renderer.page_count):
        # Render page
        image_bytes = renderer.render_page(i, dpi=200)

        # Process with backend
        markdown = await backend.page_to_markdown(
            image_bytes,
            page_num=i+1,  # 1-indexed for display
            doc_id=doc_id
        )
        results.append(markdown)
```

### Pattern 3: Error Handling

```python
from docling_hybrid.common.errors import ValidationError, RenderingError
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)

try:
    image_bytes = render_page_to_png_bytes(pdf_path, page_index, dpi=200)
except ValidationError as e:
    logger.error("invalid_input", **e.details)
    # Handle invalid input (file not found, bad page index, etc.)
except RenderingError as e:
    logger.error("rendering_failed", **e.details)
    # Handle rendering failure (corrupted PDF, etc.)
```

### Pattern 4: Adaptive DPI

```python
from docling_hybrid.renderer import render_page_to_png_bytes
from docling_hybrid.common.config import get_config

config = get_config()
dpi = config.resources.page_render_dpi  # From config

# Or based on memory constraints
import psutil
mem = psutil.virtual_memory()

if mem.available < 4 * 1024**3:  # Less than 4GB available
    dpi = 100  # Low DPI
elif mem.available < 8 * 1024**3:  # Less than 8GB available
    dpi = 150  # Medium DPI
else:
    dpi = 200  # Default DPI

image_bytes = render_page_to_png_bytes(pdf_path, page_index, dpi=dpi)
```

### Pattern 5: Progress Tracking

```python
from docling_hybrid.renderer import PdfRenderer
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)

with PdfRenderer(pdf_path) as renderer:
    total = renderer.page_count
    logger.info("rendering_started", total_pages=total)

    for i in range(total):
        image_bytes = renderer.render_page(i)
        logger.info("page_rendered", page=i+1, total=total, progress_pct=(i+1)/total*100)
```

## Performance Considerations

### Rendering Speed

Typical rendering times at 200 DPI:
- **Simple text page:** 200-400ms
- **Complex diagrams:** 400-800ms
- **Image-heavy page:** 800-1500ms

Factors affecting speed:
- **DPI:** Higher DPI = slower (linear scaling)
- **Page complexity:** More objects = slower
- **Page size:** Larger pages = slower

### Memory Usage

Per-page memory during rendering:
- **72 DPI:** ~5 MB
- **150 DPI:** ~10 MB
- **200 DPI:** ~15 MB
- **300 DPI:** ~30 MB

For batch processing with `PdfRenderer`:
- **Base overhead:** ~20-50 MB (PDF document)
- **Per-page during render:** As above
- **Peak memory:** Base + largest page

### Optimization Tips

1. **Use lower DPI for development:** 100-150 DPI speeds up iteration
2. **Use PdfRenderer for batches:** Amortizes PDF open/close overhead
3. **Process pages sequentially:** Avoid loading all images in memory
4. **Close PDFs promptly:** Use context managers to ensure cleanup
5. **Monitor memory:** Use `psutil` to track memory usage

## Configuration

Rendering settings from `Config`:

```toml
[resources]
page_render_dpi = 200        # Default DPI for rendering
max_workers = 8              # For concurrent page processing
max_memory_mb = 16384        # Memory limit (affects max concurrent renders)
```

Access in code:

```python
from docling_hybrid.common.config import get_config

config = get_config()
dpi = config.resources.page_render_dpi
```

## Dependencies

- **pypdfium2:** Fast PDF rendering library (C++ based, Python bindings)
- **Pillow (PIL):** Image manipulation and PNG export

### Why pypdfium2?

1. **Fast:** C++ implementation, significantly faster than pure-Python solutions
2. **Reliable:** Based on PDFium (Chrome's PDF renderer)
3. **Memory-efficient:** Streams rendering, doesn't load entire document
4. **No system dependencies:** Bundles PDFium library
5. **Cross-platform:** Works on Linux, macOS, Windows

## Testing

### Unit Tests

```bash
# Test rendering functions
pytest tests/unit/test_renderer.py -v

# Test specific function
pytest tests/unit/test_renderer.py::test_render_page_to_png_bytes -v
```

### Integration Tests

```bash
# Test with real PDFs
pytest tests/integration/test_pipeline_e2e.py -v
```

### Manual Testing

```python
from pathlib import Path
from docling_hybrid.renderer import render_page_to_png_bytes

# Render and save
image_bytes = render_page_to_png_bytes(Path("test.pdf"), 0, dpi=200)
with open("output.png", "wb") as f:
    f.write(image_bytes)

# Check with image viewer
# open output.png
```

## Troubleshooting

### "PDF file not found"

```python
ValidationError: PDF file not found: /path/to/document.pdf
```

**Solution:**
- Check that file path is correct
- Ensure file has `.pdf` extension
- Verify file permissions

### "Page index out of range"

```python
ValidationError: Page index 10 out of range (PDF has 5 pages)
```

**Solution:**
- Remember pages are 0-indexed (page 1 = index 0)
- Use `get_page_count()` to check total pages first

```python
from docling_hybrid.renderer import get_page_count, render_page_to_png_bytes

count = get_page_count(pdf_path)
for i in range(count):  # 0 to count-1
    image = render_page_to_png_bytes(pdf_path, i)
```

### "Failed to open PDF"

```python
RenderingError: Failed to open PDF: <error details>
```

**Causes:**
- PDF is corrupted
- PDF is encrypted/password-protected
- File is not actually a PDF

**Solution:**
- Try opening PDF in a viewer
- Check file integrity
- Decrypt PDF if encrypted

### "Out of memory"

**Symptoms:**
- Process killed during rendering
- `MemoryError` exception

**Solutions:**

1. **Lower DPI:**
   ```python
   image = render_page_to_png_bytes(pdf_path, page_index, dpi=100)
   ```

2. **Process pages sequentially (don't load all at once):**
   ```python
   # Good - processes one at a time
   with PdfRenderer(pdf_path) as renderer:
       for i in range(renderer.page_count):
           image = renderer.render_page(i)
           process_and_discard(image)

   # Bad - loads all in memory
   with PdfRenderer(pdf_path) as renderer:
       all_images = renderer.render_pages()  # May exhaust memory!
   ```

3. **Reduce concurrent workers:**
   ```bash
   docling-hybrid-ocr convert doc.pdf --max-workers 1
   ```

### "Rendering is too slow"

**Solutions:**

1. **Lower DPI:** 150 DPI is often sufficient
2. **Use PdfRenderer for batches:** Avoid repeated PDF open/close
3. **Profile page complexity:** Some pages may be exceptionally complex
4. **Check system load:** Ensure CPU isn't throttled

## Coordinate Systems

PDF and image rendering use different coordinate systems:

**PDF Coordinates:**
- Origin: Bottom-left corner
- Units: Points (1/72 inch)
- Y-axis: Upward

**Image Coordinates:**
- Origin: Top-left corner
- Units: Pixels
- Y-axis: Downward

**Conversion formula (used in `render_region_to_png_bytes`):**
```python
scale = dpi / 72.0
img_x = pdf_x * scale
img_y = (page_height - pdf_y) * scale  # Flip Y-axis
```

## See Also

- [../README.md](../README.md) - Package overview
- [../backends/README.md](../backends/README.md) - VLM backends that consume rendered images
- [../orchestrator/README.md](../orchestrator/README.md) - Pipeline that coordinates rendering
- [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) - System architecture
- [../../CLAUDE.md](../../CLAUDE.md) - Master development context
