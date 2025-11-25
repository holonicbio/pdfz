"""Command-line interface for Docling Hybrid OCR.

This module provides the CLI entrypoint for the hybrid OCR system.

Usage:
    # Convert a PDF to Markdown
    docling-hybrid-ocr convert document.pdf
    
    # Convert with options
    docling-hybrid-ocr convert document.pdf --output output.md --backend nemotron-openrouter
    
    # Show available backends
    docling-hybrid-ocr backends
    
    # Show version
    docling-hybrid-ocr --version
"""

from docling_hybrid.cli.main import app

__all__ = ["app"]
