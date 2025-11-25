"""Docling Hybrid OCR - PDF to Markdown conversion with VLM backends.

This package provides a hybrid approach to PDF conversion that combines
Docling's PDF parsing with vision-language model (VLM) OCR backends.

Key Features:
- Page-level OCR using VLM backends (Nemotron, DeepSeek)
- Pluggable backend architecture
- Async processing for performance
- Configurable for resource-constrained environments

Quick Start:
    from pathlib import Path
    from docling_hybrid.common.config import init_config
    from docling_hybrid.orchestrator import HybridPipeline
    
    # Initialize config
    config = init_config(Path("configs/local.toml"))
    
    # Convert PDF
    pipeline = HybridPipeline(config)
    result = await pipeline.convert_pdf(Path("document.pdf"))
    
    print(result.markdown)

CLI Usage:
    docling-hybrid-ocr convert document.pdf
    docling-hybrid-ocr convert document.pdf --backend nemotron-openrouter
    docling-hybrid-ocr backends

Components:
- docling_hybrid.common: Shared utilities, config, models
- docling_hybrid.backends: OCR/VLM backend implementations
- docling_hybrid.renderer: PDF page rendering
- docling_hybrid.orchestrator: Conversion pipeline
- docling_hybrid.cli: Command-line interface
"""

__version__ = "0.1.0"
__author__ = "Docling Hybrid Team"

# Convenience imports
from docling_hybrid.backends import make_backend, OcrVlmBackend
from docling_hybrid.common.config import Config, init_config, get_config
from docling_hybrid.common.models import OcrBackendConfig, PageResult
from docling_hybrid.orchestrator import HybridPipeline, ConversionResult

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "init_config",
    "get_config",
    # Backends
    "OcrVlmBackend",
    "OcrBackendConfig",
    "make_backend",
    # Pipeline
    "HybridPipeline",
    "ConversionResult",
    "PageResult",
]
