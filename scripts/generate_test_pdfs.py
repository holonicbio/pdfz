#!/usr/bin/env python3
"""Generate sample PDF files for testing.

This script creates various PDF files with different content types
for end-to-end testing of the docling-hybrid-ocr CLI.

Requirements:
    pip install reportlab
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from pathlib import Path
import sys

def create_simple_pdf(output_path: Path):
    """Create a simple single-page PDF with plain text."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Simple Test Document")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, "This is a simple one-page PDF for testing.")
    c.drawString(100, 700, "It contains only plain text.")
    c.drawString(100, 680, "")
    c.drawString(100, 660, "The purpose of this document is to test basic OCR functionality")
    c.drawString(100, 640, "with the docling-hybrid-ocr command-line tool.")
    c.save()
    print(f"Created {output_path.name}")


def create_multi_page_pdf(output_path: Path):
    """Create a multi-page PDF."""
    c = canvas.Canvas(str(output_path), pagesize=letter)

    for page_num in range(1, 4):
        c.setFont("Helvetica-Bold", 18)
        c.drawString(100, 750, f"Page {page_num} of 3")
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, f"This is page number {page_num}.")
        c.drawString(100, 680, "This PDF contains multiple pages for testing pagination.")
        c.drawString(100, 660, "")
        c.drawString(100, 640, f"Page {page_num} content:")

        # Add some unique content per page
        y = 620
        for i in range(5):
            c.drawString(100, y, f"Line {i+1} on page {page_num}")
            y -= 20

        if page_num < 3:
            c.showPage()

    c.save()
    print(f"Created {output_path.name}")


def create_table_test_pdf(output_path: Path):
    """Create a PDF with table-like content."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Table Test Document")
    c.setFont("Helvetica", 10)

    # Draw a simple table
    y = 700
    c.drawString(100, y, "ID")
    c.drawString(200, y, "Name")
    c.drawString(350, y, "Description")
    c.drawString(500, y, "Value")
    c.line(100, y-5, 580, y-5)  # horizontal line

    data = [
        ("1", "Item A", "First test item", "$10.00"),
        ("2", "Item B", "Second test item", "$25.50"),
        ("3", "Item C", "Third test item", "$15.75"),
        ("4", "Item D", "Fourth test item", "$8.25"),
        ("5", "Item E", "Fifth test item", "$32.00"),
    ]

    y -= 20
    for row in data:
        c.drawString(100, y, row[0])
        c.drawString(200, y, row[1])
        c.drawString(350, y, row[2])
        c.drawString(500, y, row[3])
        y -= 20

    c.save()
    print(f"Created {output_path.name}")


def create_small_text_pdf(output_path: Path):
    """Create a PDF with various text sizes."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "Text Size Test")

    y = 700
    sizes = [6, 8, 10, 12, 14, 16, 18]
    for size in sizes:
        c.setFont("Helvetica", size)
        c.drawString(100, y, f"This text is {size} points")
        y -= size + 10

    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(100, y, "This document tests OCR accuracy with different text sizes.")

    c.save()
    print(f"Created {output_path.name}")


def create_mixed_content_pdf(output_path: Path):
    """Create a PDF with mixed content types."""
    c = canvas.Canvas(str(output_path), pagesize=letter)

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 750, "Mixed Content Document")

    # Heading 1
    y = 710
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, y, "1. Introduction")

    # Paragraph
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(100, y, "This document contains various types of content to test comprehensive")
    y -= 15
    c.drawString(100, y, "OCR and markdown extraction capabilities.")

    # Heading 2
    y -= 30
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, y, "2. List Example")

    # Bulleted list
    y -= 30
    c.setFont("Helvetica", 12)
    bullets = [
        "First item in the list",
        "Second item with more detail",
        "Third item for completeness",
    ]
    for bullet in bullets:
        c.drawString(120, y, f"• {bullet}")
        y -= 20

    # Heading 3
    y -= 20
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, y, "3. Conclusion")

    # Final paragraph
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(100, y, "This mixed content PDF helps ensure the OCR system can handle")
    y -= 15
    c.drawString(100, y, "various document structures and formatting styles.")

    c.save()
    print(f"Created {output_path.name}")


def main():
    """Generate all test PDFs."""
    # Determine output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "tests" / "fixtures" / "sample_pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating test PDFs in: {output_dir}")
    print()

    # Create all test PDFs
    create_simple_pdf(output_dir / "simple.pdf")
    create_multi_page_pdf(output_dir / "multi_page.pdf")
    create_table_test_pdf(output_dir / "table_test.pdf")
    create_small_text_pdf(output_dir / "small_text.pdf")
    create_mixed_content_pdf(output_dir / "mixed_content.pdf")

    print()
    print("All test PDFs created successfully!")
    print()
    print("Generated files:")
    for pdf in sorted(output_dir.glob("*.pdf")):
        size = pdf.stat().st_size
        print(f"  {pdf.name} ({size:,} bytes)")


if __name__ == "__main__":
    try:
        import reportlab
    except ImportError:
        print("Error: reportlab is not installed")
        print("Install it with: pip install reportlab")
        sys.exit(1)

    main()
