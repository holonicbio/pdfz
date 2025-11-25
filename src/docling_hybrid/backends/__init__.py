"""OCR/VLM Backend implementations.

This module provides the backend abstraction layer for OCR/VLM operations.

Architecture:
    OcrVlmBackend (ABC)
    ├── OpenRouterNemotronBackend (implemented)
    ├── DeepseekOcrVllmBackend (stub)
    └── DeepseekOcrMlxBackend (stub)

Usage:
    from docling_hybrid.backends import make_backend
    from docling_hybrid.common.models import OcrBackendConfig
    
    config = OcrBackendConfig(
        name="nemotron-openrouter",
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key="sk-...",
    )
    
    backend = make_backend(config)
    markdown = await backend.page_to_markdown(image_bytes, page_num=1, doc_id="doc-123")
"""

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.backends.factory import list_backends, make_backend, register_backend
from docling_hybrid.backends.openrouter_nemotron import OpenRouterNemotronBackend

# Stubs are imported but raise NotImplementedError when used
from docling_hybrid.backends.deepseek_mlx_stub import DeepseekOcrMlxBackend
from docling_hybrid.backends.deepseek_vllm_stub import DeepseekOcrVllmBackend

__all__ = [
    # Base class
    "OcrVlmBackend",
    # Factory
    "make_backend",
    "list_backends",
    "register_backend",
    # Implementations
    "OpenRouterNemotronBackend",
    # Stubs
    "DeepseekOcrVllmBackend",
    "DeepseekOcrMlxBackend",
]
