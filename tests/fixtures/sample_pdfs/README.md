# Sample Test PDFs

This directory contains sample PDF files for end-to-end CLI testing.

## Required Test PDFs

The following PDF files should be present for comprehensive testing:

### 1. simple.pdf
- **Purpose:** Basic single-page PDF with plain text
- **Content:** Simple paragraphs of text, no complex formatting
- **Pages:** 1
- **Use case:** Testing basic conversion functionality

### 2. multi_page.pdf
- **Purpose:** Multi-page document
- **Content:** 3-5 pages with text on each page
- **Pages:** 3-5
- **Use case:** Testing pagination, page numbering, and batch processing

### 3. table_test.pdf
- **Purpose:** Document with table structures
- **Content:** Simple tables with rows and columns
- **Pages:** 1-2
- **Use case:** Testing table recognition and markdown table generation

### 4. small_text.pdf
- **Purpose:** Document with various text sizes
- **Content:** Text in different font sizes (6pt to 16pt)
- **Pages:** 1
- **Use case:** Testing OCR accuracy with small text

### 5. mixed_content.pdf
- **Purpose:** Document with mixed content types
- **Content:** Text, headings, lists, and simple formatting
- **Pages:** 2-3
- **Use case:** Testing comprehensive document structure extraction

## Generating Test PDFs

### Option 1: Using Python with reportlab

```bash
pip install reportlab
python3 scripts/generate_test_pdfs.py
```

### Option 2: Manual Creation

Create PDFs manually using any PDF creation tool and save them in this directory.

### Option 3: Download Samples

Download sample PDFs from public sources:
- https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
- Or create your own using LibreOffice, Google Docs, etc.

## Testing Usage

These PDFs are used in:
- `tests/e2e/test_cli_e2e.py` - End-to-end CLI tests
- Manual testing: `docling-hybrid-ocr convert tests/fixtures/sample_pdfs/simple.pdf`

## Notes

- Keep PDFs small (< 100KB each) for fast test execution
- PDFs should be in English for consistent OCR results
- Avoid copyrighted content - use generated or public domain content only
