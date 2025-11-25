"""DeepSeek vLLM backend implementation.

This module provides a fully functional backend for OCR/VLM operations
using DeepSeek-VL model via a local vLLM server with OpenAI-compatible API.

The backend:
- Connects to local vLLM server (typically http://localhost:8000)
- Uses OpenAI-compatible chat completions endpoint
- Encodes images as base64 data URLs
- Handles response parsing (string or list formats)
- Provides specialized prompts for page, table, and formula extraction

Usage:
    from docling_hybrid.backends import make_backend

    config = OcrBackendConfig(
        name="deepseek-vllm",
        model="deepseek-ai/deepseek-vl-7b-chat",
        base_url="http://localhost:8000/v1/chat/completions",
    )

    backend = make_backend(config)
    markdown = await backend.page_to_markdown(image_bytes, page_num=1, doc_id="doc-123")
"""

import asyncio
import base64
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
from docling_hybrid.common.retry import retry_with_rate_limit

logger = get_logger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class RateLimitError(BackendResponseError):
    """Exception raised when API rate limit is exceeded.

    This exception captures rate limit information including the Retry-After
    header value when available.
    """

    def __init__(
        self,
        message: str,
        backend_name: str,
        retry_after: float | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, backend_name=backend_name, **kwargs)
        self.retry_after = retry_after


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


class DeepSeekVLLMBackend(OcrVlmBackend):
    """OCR/VLM backend using DeepSeek-VL via local vLLM server.

    This backend communicates with a vLLM server running the DeepSeek-VL model.
    The vLLM server provides an OpenAI-compatible API endpoint.

    Features:
    - Async HTTP requests for concurrent processing
    - Automatic retry on transient failures
    - Structured logging for debugging
    - Support for page, table, and formula extraction
    - Health check for server connectivity

    Configuration:
        The backend requires a running vLLM server. Start the server with:

        ```bash
        vllm serve deepseek-ai/deepseek-vl-7b-chat \\
            --port 8000 \\
            --max-model-len 4096
        ```

        Then configure the backend:
        ```python
        config = OcrBackendConfig(
            name="deepseek-vllm",
            model="deepseek-ai/deepseek-vl-7b-chat",
            base_url="http://localhost:8000/v1/chat/completions",
        )
        ```

    Example:
        >>> config = OcrBackendConfig(
        ...     name="deepseek-vllm",
        ...     model="deepseek-ai/deepseek-vl-7b-chat",
        ...     base_url="http://localhost:8000/v1/chat/completions",
        ... )
        >>> backend = DeepSeekVLLMBackend(config)
        >>> md = await backend.page_to_markdown(image_bytes, 1, "doc-123")
    """

    def __init__(self, config: OcrBackendConfig) -> None:
        """Initialize the DeepSeek vLLM backend.

        Args:
            config: Backend configuration
        """
        super().__init__(config)

        # vLLM typically doesn't require an API key for local deployment
        # But support it if provided for secured deployments
        self.api_key = config.api_key

        # Build headers
        self.headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # Add any extra headers
        if config.extra_headers:
            self.headers.update(config.extra_headers)

        # HTTP client (created lazily)
        self._session: aiohttp.ClientSession | None = None

        # Timeouts (vLLM can be slower for vision models)
        self._timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes

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

    async def _post_chat_inner(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> str:
        """Inner method that performs the actual HTTP request.

        This method is wrapped by _post_chat which adds retry logic.

        Args:
            messages: OpenAI-style messages array
            context: Logging context (doc_id, page_num, etc.)

        Returns:
            Text content from the response

        Raises:
            BackendConnectionError: Cannot connect to API
            BackendTimeoutError: Request timed out
            BackendResponseError: Invalid response (4xx, non-retryable 5xx)
            RateLimitError: Rate limit exceeded (429)
        """
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        session = await self._get_session()

        try:
            async with session.post(
                self.config.base_url,
                headers=self.headers,
                json=payload,
            ) as response:
                # Check for rate limiting (429)
                if response.status == 429:
                    retry_after = None
                    retry_after_header = response.headers.get("Retry-After")
                    if retry_after_header:
                        try:
                            retry_after = float(retry_after_header)
                        except ValueError:
                            logger.warning(
                                "invalid_retry_after_header",
                                retry_after_header=retry_after_header,
                                backend=self.name,
                                **context,
                            )

                    body = await response.text()
                    raise RateLimitError(
                        f"API rate limit exceeded (429)",
                        backend_name=self.name,
                        retry_after=retry_after,
                        status_code=429,
                        response_body=body[:500],  # Truncate for logging
                    )

                # Check for server errors (5xx) - these are retryable
                if 500 <= response.status < 600:
                    body = await response.text()
                    raise BackendResponseError(
                        f"API server error {response.status}",
                        backend_name=self.name,
                        status_code=response.status,
                        response_body=body[:500],
                    )

                # Check for other client errors (4xx) - these are NOT retryable
                if response.status >= 400 and response.status < 500:
                    body = await response.text()
                    # Use a different exception type for non-retryable errors
                    error = BackendResponseError(
                        f"API client error {response.status}",
                        backend_name=self.name,
                        status_code=response.status,
                        response_body=body[:500],
                    )
                    # Mark as non-retryable
                    error._retryable = False
                    raise error

                # Check for other non-200 statuses
                if response.status != 200:
                    body = await response.text()
                    raise BackendResponseError(
                        f"API returned unexpected status {response.status}",
                        backend_name=self.name,
                        status_code=response.status,
                        response_body=body[:500],
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

    async def _post_chat(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send chat completion request with automatic retry logic.

        This method wraps _post_chat_inner with retry logic for transient failures:
        - Rate limiting (429) with Retry-After header awareness
        - Server errors (5xx)
        - Connection errors
        - Timeouts

        Client errors (4xx except 429) are NOT retried.

        Args:
            messages: OpenAI-style messages array
            context: Logging context (doc_id, page_num, etc.)

        Returns:
            Text content from the response

        Raises:
            BackendError: After all retries exhausted or non-retryable error
        """
        context = context or {}

        logger.debug(
            "api_request_started",
            backend=self.name,
            model=self.config.model,
            max_retries=self.config.max_retries,
            **context,
        )

        def extract_retry_after(exc: Exception) -> float | None:
            """Extract Retry-After delay from RateLimitError."""
            if isinstance(exc, RateLimitError):
                return exc.retry_after
            return None

        def is_retryable_error(exc: Exception) -> bool:
            """Check if error should be retried."""
            # Don't retry 4xx client errors (except 429 which is RateLimitError)
            if isinstance(exc, BackendResponseError):
                # Check if marked as non-retryable
                if hasattr(exc, '_retryable') and not exc._retryable:
                    return False
                # Retry 5xx errors
                if hasattr(exc, 'status_code'):
                    return exc.status_code >= 500
            return True

        # Filter retryable exceptions
        retryable_exceptions = tuple(
            exc_type for exc_type in (
                RateLimitError,
                BackendResponseError,
                BackendConnectionError,
                BackendTimeoutError,
            )
        )

        # Wrap the inner call with retry logic
        try:
            content = await retry_with_rate_limit(
                lambda: self._post_chat_inner(messages, context),
                max_retries=self.config.max_retries,
                initial_delay=self.config.retry_initial_delay,
                exponential_base=self.config.retry_exponential_base,
                max_delay=self.config.retry_max_delay,
                retryable_exceptions=retryable_exceptions,
                rate_limit_exception_type=RateLimitError,
                extract_retry_after=extract_retry_after,
                context={
                    "backend": self.name,
                    "model": self.config.model,
                    **context,
                },
            )
        except BackendResponseError as e:
            # Check if it's a non-retryable 4xx error
            if hasattr(e, '_retryable') and not e._retryable:
                # Log and re-raise immediately
                logger.error(
                    "non_retryable_client_error",
                    backend=self.name,
                    status_code=getattr(e, 'status_code', None),
                    error=str(e),
                    **context,
                )
                raise

            # Otherwise, it's an error after retries exhausted
            logger.error(
                "api_request_failed_after_retries",
                backend=self.name,
                error=str(e),
                **context,
            )
            raise

        logger.debug(
            "api_request_completed",
            backend=self.name,
            content_length=len(content),
            **context,
        )

        return content

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

    async def health_check(self) -> bool:
        """Check if the vLLM server is healthy and responsive.

        Sends a minimal request to verify the server is running and accessible.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            session = await self._get_session()

            # Simple health check: send a minimal request
            # vLLM OpenAI-compatible API doesn't have a /health endpoint,
            # so we use a minimal completion request
            payload = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }

            async with session.post(
                self.config.base_url,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),  # Short timeout for health check
            ) as response:
                # Accept 200 as healthy
                # Even 4xx might be OK (e.g., model loading)
                if response.status < 500:
                    logger.debug(
                        "health_check_passed",
                        backend=self.name,
                        status=response.status,
                    )
                    return True
                else:
                    logger.warning(
                        "health_check_failed",
                        backend=self.name,
                        status=response.status,
                    )
                    return False

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(
                "health_check_error",
                backend=self.name,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
        except Exception as e:
            logger.error(
                "health_check_unexpected_error",
                backend=self.name,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

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
