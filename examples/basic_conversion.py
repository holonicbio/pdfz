#!/usr/bin/env python3
"""
Basic PDF to Markdown Conversion Example

This example demonstrates the simplest way to convert a PDF to Markdown
using Docling Hybrid OCR.

Usage:
    python examples/basic_conversion.py path/to/document.pdf

Requirements:
    - OPENROUTER_API_KEY environment variable must be set
    - Config file at configs/local.toml (or configs/default.toml)
"""

import asyncio
import sys
from pathlib import Path

from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.common.errors import DoclingHybridError


async def basic_conversion(pdf_path: Path) -> None:
    """
    Convert a PDF to Markdown using default settings.

    Args:
        pdf_path: Path to the PDF file to convert

    Returns:
        None (writes output to .md file)
    """
    try:
        print(f"📄 Converting: {pdf_path}")
        print("=" * 60)

        # Step 1: Initialize configuration
        # This loads settings from configs/local.toml and environment variables
        print("\n1️⃣  Initializing configuration...")
        config = init_config(Path("configs/local.toml"))
        print(f"   ✓ Using backend: {config.backends.default}")
        print(f"   ✓ Max workers: {config.resources.max_workers}")
        print(f"   ✓ DPI: {config.resources.page_render_dpi}")

        # Step 2: Create pipeline
        print("\n2️⃣  Creating pipeline...")
        pipeline = HybridPipeline(config)
        print("   ✓ Pipeline ready")

        # Step 3: Convert PDF
        # Output path is automatically set to same name with .md extension
        print("\n3️⃣  Converting PDF to Markdown...")
        output_path = pdf_path.with_suffix(".md")

        result = await pipeline.convert_pdf(
            pdf_path=pdf_path,
            output_path=output_path
        )

        # Step 4: Display results
        print("\n4️⃣  Conversion complete!")
        print(f"   ✓ Processed: {result.processed_pages}/{result.total_pages} pages")
        print(f"   ✓ Backend: {result.backend_name}")
        print(f"   ✓ Output: {result.output_path}")
        print(f"   ✓ Content length: {len(result.markdown)} characters")

        # Display first few lines of output
        print("\n📝 Preview (first 500 characters):")
        print("-" * 60)
        print(result.markdown[:500])
        if len(result.markdown) > 500:
            print("...")
        print("-" * 60)

        # Show per-page statistics
        print("\n📊 Per-page statistics:")
        for page_result in result.page_results:
            chars = len(page_result.content)
            print(f"   Page {page_result.page_num:3d}: {chars:5d} characters")

        print(f"\n✅ Success! Markdown saved to: {output_path}")

    except FileNotFoundError:
        print(f"\n❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    except DoclingHybridError as e:
        print(f"\n❌ Conversion error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python examples/basic_conversion.py <pdf_file>")
        print("\nExample:")
        print("  python examples/basic_conversion.py document.pdf")
        sys.exit(1)

    # Get PDF path from command line
    pdf_path = Path(sys.argv[1])

    # Check if file exists
    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == ".pdf":
        print(f"❌ Error: File must be a PDF, got: {pdf_path.suffix}")
        sys.exit(1)

    # Run async conversion
    asyncio.run(basic_conversion(pdf_path))


if __name__ == "__main__":
    main()
