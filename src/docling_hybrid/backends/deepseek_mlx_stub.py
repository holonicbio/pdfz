"""DeepSeek-OCR backend stub for MLX on macOS.

This module provides a stub implementation for the DeepSeek-OCR model
running via MLX on macOS systems (Apple Silicon).

STATUS: STUB - Raises NotImplementedError
PRIORITY: Phase 2 (Sprint 4)

When implemented, this backend will support two strategies:

Strategy 1: Direct Python API
- Use mlx_vlm.generate() directly in Python
- Lower latency for single requests
- Simpler setup

Strategy 2: Local HTTP Server
- Run MLX as a sidecar service with OpenAI-compatible API
- Better for batched/concurrent requests
- Matches other backend implementations

Prerequisites for implementation:
- macOS with Apple Silicon (M1/M2/M3)
- MLX and mlx-vlm installed
- DeepSeek-OCR-MLX model downloaded

Intended usage:
    config = OcrBackendConfig(
        name="deepseek-mlx",
        model="deepseek-ai/DeepSeek-OCR",
        base_url="http://localhost:8080/v1/chat/completions",  # If using HTTP
    )
    
    backend = DeepseekOcrMlxBackend(config)
    markdown = await backend.page_to_markdown(image_bytes, 1, "doc-123")
"""

from typing import Any

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.logging import get_logger
from docling_hybrid.common.models import OcrBackendConfig

logger = get_logger(__name__)


class DeepseekOcrMlxBackend(OcrVlmBackend):
    """DeepSeek-OCR backend using MLX on macOS.
    
    STATUS: STUB - Not yet implemented
    
    This backend will provide efficient local inference on Apple Silicon
    using the MLX framework and mlx-vlm library.
    
    Implementation Options:
    
    Option A: Direct mlx_vlm API
        ```python
        from mlx_vlm import generate
        
        output = generate(
            model_path="deepseek-ai/DeepSeek-OCR",
            prompt=prompt,
            images=[image],
            max_tokens=config.max_tokens,
        )
        ```
    
    Option B: HTTP Server (recommended for consistency)
        - Run mlx-vlm's HTTP server as a sidecar
        - Use same HTTP logic as OpenRouterNemotronBackend
        - Connect to localhost:8080
    
    Configuration:
        name: "deepseek-mlx"
        model: "deepseek-ai/DeepSeek-OCR" (or local path)
        base_url: "http://localhost:8080/v1/chat/completions" (Option B)
        
    Attributes:
        config: Backend configuration
        name: "deepseek-mlx"
    """
    
    def __init__(self, config: OcrBackendConfig) -> None:
        """Initialize the DeepSeek MLX backend.
        
        Args:
            config: Backend configuration
            
        Note:
            Currently only logs initialization. Full implementation
            will either load MLX model or connect to HTTP server.
        """
        super().__init__(config)
        
        logger.warning(
            "backend_stub_initialized",
            backend=self.name,
            message="DeepSeek MLX backend is a stub - not yet implemented",
        )
    
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert a full page image to Markdown.
        
        STUB: Raises NotImplementedError
        
        Implementation plan (Option B - HTTP):
        1. Encode image as base64
        2. Build chat completion request
        3. POST to local MLX HTTP server
        4. Parse response and return Markdown
        
        Implementation plan (Option A - Direct API):
        1. Convert image bytes to PIL Image
        2. Call mlx_vlm.generate() with prompt and image
        3. Return generated text
        
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
            "DeepseekOcrMlxBackend.page_to_markdown() is not yet implemented.\n"
            "\n"
            "This backend is for macOS with Apple Silicon.\n"
            "\n"
            "To implement:\n"
            "1. Install mlx and mlx-vlm: pip install mlx mlx-vlm\n"
            "2. Download DeepSeek-OCR model for MLX\n"
            "3. Choose implementation strategy:\n"
            "   - Option A: Direct mlx_vlm.generate() calls\n"
            "   - Option B: Run HTTP server, reuse OpenRouter logic\n"
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
            "DeepseekOcrMlxBackend.table_to_markdown() is not yet implemented.\n"
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
            "DeepseekOcrMlxBackend.formula_to_latex() is not yet implemented.\n"
            "See: docs/components/BACKENDS.md for specification"
        )
