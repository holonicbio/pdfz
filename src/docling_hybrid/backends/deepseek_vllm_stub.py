"""DeepSeek-OCR backend stub for vLLM on CUDA Linux.

This module provides a stub implementation for the DeepSeek-OCR model
served via vLLM on CUDA Linux systems.

STATUS: STUB - Raises NotImplementedError
PRIORITY: Phase 2 (Sprint 3-4)

When implemented, this backend will:
- Connect to a local vLLM server running DeepSeek-OCR
- Use OpenAI-compatible API format
- Reuse the same prompts as OpenRouterNemotronBackend

Prerequisites for implementation:
- CUDA-capable GPU (recommended: 24GB+ VRAM)
- vLLM installed and configured
- DeepSeek-OCR model downloaded

Intended usage:
    # Start vLLM server (separate process)
    # python -m vllm.entrypoints.openai.api_server \\
    #     --model deepseek-ai/DeepSeek-OCR \\
    #     --port 8000
    
    config = OcrBackendConfig(
        name="deepseek-vllm",
        model="deepseek-ai/DeepSeek-OCR",
        base_url="http://localhost:8000/v1/chat/completions",
    )
    
    backend = DeepseekOcrVllmBackend(config)
    markdown = await backend.page_to_markdown(image_bytes, 1, "doc-123")
"""

from typing import Any

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.logging import get_logger
from docling_hybrid.common.models import OcrBackendConfig

logger = get_logger(__name__)


class DeepseekOcrVllmBackend(OcrVlmBackend):
    """DeepSeek-OCR backend using vLLM on CUDA Linux.
    
    STATUS: STUB - Not yet implemented
    
    This backend will provide high-performance local inference
    using DeepSeek-OCR served via vLLM.
    
    Implementation Notes:
    - Will use OpenAI-compatible API (vLLM serves this by default)
    - Can reuse most of OpenRouterNemotronBackend's HTTP logic
    - Should support batched inference for higher throughput
    
    Configuration:
        name: "deepseek-vllm"
        model: "deepseek-ai/DeepSeek-OCR" (or local path)
        base_url: "http://localhost:8000/v1/chat/completions"
        
    Attributes:
        config: Backend configuration
        name: "deepseek-vllm"
    """
    
    def __init__(self, config: OcrBackendConfig) -> None:
        """Initialize the DeepSeek vLLM backend.
        
        Args:
            config: Backend configuration
            
        Note:
            Currently only logs initialization. Full implementation
            will establish connection to vLLM server.
        """
        super().__init__(config)
        
        logger.warning(
            "backend_stub_initialized",
            backend=self.name,
            message="DeepSeek vLLM backend is a stub - not yet implemented",
        )
    
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert a full page image to Markdown.
        
        STUB: Raises NotImplementedError
        
        Implementation plan:
        1. Encode image as base64
        2. Build chat completion request (same format as OpenRouter)
        3. POST to local vLLM server
        4. Parse response and return Markdown
        
        Args:
            image_bytes: PNG image bytes of the rendered page
            page_num: Page number (1-indexed)
            doc_id: Document identifier
            
        Returns:
            Markdown string representing the page content
            
        Raises:
            NotImplementedError: This is a stub implementation
        """
        raise NotImplementedError(
            "DeepseekOcrVllmBackend.page_to_markdown() is not yet implemented.\n"
            "\n"
            "To implement:\n"
            "1. Ensure vLLM is running with DeepSeek-OCR model\n"
            "2. Copy HTTP logic from OpenRouterNemotronBackend\n"
            "3. Use same prompts (PAGE_TO_MARKDOWN_PROMPT)\n"
            "4. Connect to local vLLM server instead of OpenRouter\n"
            "\n"
            "See: docs/components/BACKENDS.md for full specification"
        )
    
    async def table_to_markdown(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a table image to Markdown table syntax.
        
        STUB: Raises NotImplementedError
        
        Args:
            image_bytes: PNG image bytes of the cropped table
            meta: Metadata (doc_id, page_num, etc.)
            
        Returns:
            Markdown table string
            
        Raises:
            NotImplementedError: This is a stub implementation
        """
        raise NotImplementedError(
            "DeepseekOcrVllmBackend.table_to_markdown() is not yet implemented.\n"
            "See: docs/components/BACKENDS.md for specification"
        )
    
    async def formula_to_latex(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a formula image to LaTeX.
        
        STUB: Raises NotImplementedError
        
        Args:
            image_bytes: PNG image bytes of the cropped formula
            meta: Metadata (doc_id, page_num, etc.)
            
        Returns:
            LaTeX string (without delimiters)
            
        Raises:
            NotImplementedError: This is a stub implementation
        """
        raise NotImplementedError(
            "DeepseekOcrVllmBackend.formula_to_latex() is not yet implemented.\n"
            "See: docs/components/BACKENDS.md for specification"
        )
