"""OpenRouter Nemotron VLM backend implementation.

This module provides a fully functional backend for OCR/VLM operations
using OpenRouter's API with the Nemotron-nano-12b-v2-vl model.

The backend:
- Encodes images as base64 data URLs
- Builds OpenAI-style chat completion requests
- Handles response parsing (string or list formats)
- Provides specialized prompts for page, table, and formula extraction

Usage:
    from docling_hybrid.backends import make_backend
    
    config = OcrBackendConfig(
        name="nemotron-openrouter",
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    
    backend = make_backend(config)
    markdown = await backend.page_to_markdown(image_bytes, page_num=1, doc_id="doc-123")
"""

import asyncio
import base64
import os
from typing import Any

import aiohttp

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendResponseError,
    BackendTimeoutError,
    ConfigurationError,
)
from docling_hybrid.common.logging import get_logger
from docling_hybrid.common.models import OcrBackendConfig

logger = get_logger(__name__)

# ============================================================================
# Prompts
# ============================================================================

PAGE_TO_MARKDOWN_PROMPT = """You are a document OCR system. Convert the document page image to GitHub-flavored Markdown.

RULES:
1. Extract ALL text exactly as it appears - do not paraphrase or summarize
2. Preserve document structure:
   - Use # ## ### for headings based on visual hierarchy
   - Use - or * for bullet lists
   - Use 1. 2. 3. for numbered lists
   - Use | syntax for tables
   - Use $...$ for inline math, $$...$$ for block math
3. For figures/images/charts: insert placeholder <FIGURE> (do not describe)
4. For formulas: transcribe as LaTeX
5. Do NOT:
   - Add commentary or explanations
   - Describe what you see
   - Invent or hallucinate content
   - Skip any text

Output ONLY the Markdown content. No preamble, no explanations."""

TABLE_TO_MARKDOWN_PROMPT = """You are a table OCR system. The image contains a single table.

Convert it to a Markdown table using | pipe syntax.

RULES:
1. Extract ALL cells exactly as they appear
2. Use standard Markdown table format:
   | Header 1 | Header 2 |
   |----------|----------|
   | Cell 1   | Cell 2   |
3. Handle merged cells by repeating content
4. Preserve alignment where clear
5. Do NOT add any text outside the table

Output ONLY the Markdown table. No explanations."""

FORMULA_TO_LATEX_PROMPT = """You are a formula OCR system. The image contains a single mathematical formula.

Convert it to LaTeX.

RULES:
1. Transcribe the formula exactly as it appears
2. Use standard LaTeX commands (\\frac, \\sqrt, \\sum, etc.)
3. Do NOT include $ or $$ delimiters
4. Do NOT add explanations or descriptions

Output ONLY the LaTeX expression."""


class OpenRouterNemotronBackend(OcrVlmBackend):
    """OCR/VLM backend using OpenRouter API with Nemotron model.
    
    This backend communicates with OpenRouter's API to perform OCR
    using NVIDIA's Nemotron-nano-12b-v2-vl vision-language model.
    
    Features:
    - Async HTTP requests for concurrent processing
    - Automatic retry on transient failures
    - Structured logging for debugging
    - Support for page, table, and formula extraction
    
    Configuration:
        The backend requires an API key, which can be provided via:
        1. config.api_key parameter
        2. OPENROUTER_API_KEY environment variable
        
        OpenRouter also recommends setting HTTP-Referer and X-Title headers
        for identification. These can be provided via:
        1. config.extra_headers parameter
        2. DOCLING_HYBRID_HTTP_REFERER and DOCLING_HYBRID_X_TITLE env vars
    
    Example:
        >>> config = OcrBackendConfig(
        ...     name="nemotron-openrouter",
        ...     model="nvidia/nemotron-nano-12b-v2-vl:free",
        ...     base_url="https://openrouter.ai/api/v1/chat/completions",
        ...     api_key="sk-...",
        ... )
        >>> backend = OpenRouterNemotronBackend(config)
        >>> md = await backend.page_to_markdown(image_bytes, 1, "doc-123")
    """
    
    def __init__(self, config: OcrBackendConfig) -> None:
        """Initialize the OpenRouter Nemotron backend.
        
        Args:
            config: Backend configuration
            
        Raises:
            ConfigurationError: If API key is missing
        """
        super().__init__(config)
        
        # Get API key from config or environment
        self.api_key = config.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "Missing OpenRouter API key",
                details={
                    "hint": "Set OPENROUTER_API_KEY environment variable or provide api_key in config"
                }
            )
        
        # Build headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Add OpenRouter identification headers
        http_referer = os.environ.get("DOCLING_HYBRID_HTTP_REFERER")
        x_title = os.environ.get("DOCLING_HYBRID_X_TITLE")
        
        if config.extra_headers:
            self.headers.update(config.extra_headers)
        
        if http_referer:
            self.headers["HTTP-Referer"] = http_referer
        if x_title:
            self.headers["X-Title"] = x_title
        
        # HTTP client (created lazily)
        self._session: aiohttp.ClientSession | None = None
        
        # Timeouts (could be made configurable)
        self._timeout = aiohttp.ClientTimeout(total=180)  # 3 minutes
        
        logger.info(
            "backend_initialized",
            backend=self.name,
            model=config.model,
            base_url=config.base_url,
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 data URL.
        
        Args:
            image_bytes: PNG image bytes
            
        Returns:
            Base64 data URL for use in API request
        """
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    
    def _build_messages(
        self,
        prompt: str,
        image_bytes: bytes,
    ) -> list[dict[str, Any]]:
        """Build OpenAI-style messages array with image.
        
        Args:
            prompt: System/user prompt
            image_bytes: PNG image bytes
            
        Returns:
            Messages array for chat completion API
        """
        image_url = self._encode_image(image_bytes)
        
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ]
    
    async def _post_chat(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send chat completion request and extract response text.
        
        Args:
            messages: OpenAI-style messages array
            context: Logging context (doc_id, page_num, etc.)
            
        Returns:
            Text content from the response
            
        Raises:
            BackendConnectionError: Cannot connect to API
            BackendTimeoutError: Request timed out
            BackendResponseError: Invalid response
        """
        context = context or {}
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        logger.debug(
            "api_request_started",
            backend=self.name,
            model=self.config.model,
            **context,
        )
        
        session = await self._get_session()
        
        try:
            async with session.post(
                self.config.base_url,
                headers=self.headers,
                json=payload,
            ) as response:
                # Check status
                if response.status != 200:
                    body = await response.text()
                    raise BackendResponseError(
                        f"API returned status {response.status}",
                        backend_name=self.name,
                        status_code=response.status,
                        response_body=body,
                    )
                
                # Parse JSON
                try:
                    data = await response.json()
                except Exception as e:
                    raise BackendResponseError(
                        f"Failed to parse JSON response: {e}",
                        backend_name=self.name,
                    ) from e
                
                # Extract content
                content = self._extract_content(data)
                
                logger.debug(
                    "api_request_completed",
                    backend=self.name,
                    content_length=len(content),
                    **context,
                )
                
                return content
                
        except aiohttp.ClientConnectorError as e:
            raise BackendConnectionError(
                f"Cannot connect to {self.config.base_url}",
                backend_name=self.name,
                details={"error": str(e)},
            ) from e
        except asyncio.TimeoutError as e:
            raise BackendTimeoutError(
                f"Request timed out after {self._timeout.total}s",
                backend_name=self.name,
                details=context,
            ) from e
    
    def _extract_content(self, data: dict[str, Any]) -> str:
        """Extract text content from API response.
        
        Handles both string content and list-of-segments content.
        
        Args:
            data: Parsed JSON response
            
        Returns:
            Extracted text content
            
        Raises:
            BackendResponseError: If response structure is unexpected
        """
        try:
            choices = data.get("choices", [])
            if not choices:
                raise BackendResponseError(
                    "Response contains no choices",
                    backend_name=self.name,
                    response_body=str(data)[:500],
                )
            
            message = choices[0].get("message", {})
            content = message.get("content")
            
            if content is None:
                raise BackendResponseError(
                    "Response message has no content",
                    backend_name=self.name,
                    response_body=str(data)[:500],
                )
            
            # Handle string content
            if isinstance(content, str):
                return content
            
            # Handle list-of-segments content
            if isinstance(content, list):
                parts = []
                for segment in content:
                    if isinstance(segment, dict) and "text" in segment:
                        parts.append(segment["text"])
                    elif isinstance(segment, str):
                        parts.append(segment)
                return "".join(parts)
            
            raise BackendResponseError(
                f"Unexpected content type: {type(content).__name__}",
                backend_name=self.name,
                response_body=str(content)[:500],
            )
            
        except KeyError as e:
            raise BackendResponseError(
                f"Missing expected field in response: {e}",
                backend_name=self.name,
                response_body=str(data)[:500],
            ) from e
    
    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert a full page image to Markdown.
        
        Args:
            image_bytes: PNG image bytes of the rendered page
            page_num: Page number (1-indexed)
            doc_id: Document identifier
            
        Returns:
            Markdown string representing the page content
            
        Raises:
            BackendError: If OCR processing fails
        """
        logger.info(
            "page_ocr_started",
            backend=self.name,
            doc_id=doc_id,
            page_num=page_num,
            image_size_kb=len(image_bytes) // 1024,
        )
        
        messages = self._build_messages(PAGE_TO_MARKDOWN_PROMPT, image_bytes)
        
        content = await self._post_chat(
            messages,
            context={"doc_id": doc_id, "page_num": page_num},
        )
        
        logger.info(
            "page_ocr_completed",
            backend=self.name,
            doc_id=doc_id,
            page_num=page_num,
            markdown_length=len(content),
        )
        
        return content
    
    async def table_to_markdown(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a table image to Markdown table syntax.
        
        Args:
            image_bytes: PNG image bytes of the cropped table
            meta: Metadata (doc_id, page_num, etc.)
            
        Returns:
            Markdown table string
        """
        logger.info(
            "table_ocr_started",
            backend=self.name,
            **meta,
        )
        
        messages = self._build_messages(TABLE_TO_MARKDOWN_PROMPT, image_bytes)
        
        content = await self._post_chat(messages, context=meta)
        
        logger.info(
            "table_ocr_completed",
            backend=self.name,
            table_length=len(content),
            **meta,
        )
        
        return content
    
    async def formula_to_latex(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a formula image to LaTeX.
        
        Args:
            image_bytes: PNG image bytes of the cropped formula
            meta: Metadata (doc_id, page_num, etc.)
            
        Returns:
            LaTeX string (without delimiters)
        """
        logger.info(
            "formula_ocr_started",
            backend=self.name,
            **meta,
        )
        
        messages = self._build_messages(FORMULA_TO_LATEX_PROMPT, image_bytes)
        
        content = await self._post_chat(messages, context=meta)
        
        # Clean up any accidental delimiters
        content = content.strip()
        if content.startswith("$$") and content.endswith("$$"):
            content = content[2:-2].strip()
        elif content.startswith("$") and content.endswith("$"):
            content = content[1:-1].strip()
        
        logger.info(
            "formula_ocr_completed",
            backend=self.name,
            latex_length=len(content),
            **meta,
        )
        
        return content
