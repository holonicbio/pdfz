"""Backend fallback chain for resilient OCR processing.

This module implements automatic fallback logic when the primary backend fails.
The fallback chain tries backends in order until one succeeds or all fail.

Key Features:
- Automatic backend switching on transient failures
- Configurable fallback order
- Health check integration
- Detailed logging of fallback events
- Selective error handling (won't fallback on auth errors)

Usage:
    from docling_hybrid.backends.fallback import FallbackChain
    from docling_hybrid.backends import make_backend

    # Create backends
    primary = make_backend(primary_config)
    fallback1 = make_backend(fallback1_config)

    # Create fallback chain
    chain = FallbackChain(
        primary=primary,
        fallbacks=[fallback1],
        max_attempts_per_backend=2,
    )

    # Use chain like a regular backend
    async with chain:
        markdown = await chain.page_to_markdown(image_bytes, 1, "doc-123")
"""

import asyncio
from typing import Any, Callable

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendError,
    BackendResponseError,
    BackendTimeoutError,
)
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)


class FallbackChain:
    """Manages backend fallback logic for resilient OCR processing.

    The fallback chain tries backends in order:
    1. Primary backend (with retries)
    2. First fallback (with retries)
    3. Second fallback (with retries)
    ... and so on

    Fallback is triggered by:
    - Connection errors (cannot reach backend)
    - Timeout errors (backend too slow)
    - Server errors (5xx responses)

    Fallback is NOT triggered by:
    - Authentication errors (401, 403)
    - Client errors (4xx except rate limits)
    - Validation errors

    Attributes:
        primary: Primary backend to try first
        fallbacks: List of fallback backends to try in order
        max_attempts_per_backend: Max attempts per backend before moving to next
        fallback_on_errors: Error types that trigger fallback

    Example:
        >>> chain = FallbackChain(
        ...     primary=vllm_backend,
        ...     fallbacks=[openrouter_backend],
        ...     max_attempts_per_backend=2,
        ... )
        >>> async with chain:
        ...     result = await chain.page_to_markdown(image, 1, "doc-123")
    """

    def __init__(
        self,
        primary: OcrVlmBackend,
        fallbacks: list[OcrVlmBackend] | None = None,
        max_attempts_per_backend: int = 2,
        fallback_on_errors: tuple[type[Exception], ...] | None = None,
    ) -> None:
        """Initialize the fallback chain.

        Args:
            primary: Primary backend to try first
            fallbacks: List of fallback backends (default: empty list)
            max_attempts_per_backend: Max attempts per backend (default: 2)
            fallback_on_errors: Error types that trigger fallback
                (default: connection, timeout, server errors)
        """
        self.primary = primary
        self.fallbacks = fallbacks or []
        self.max_attempts_per_backend = max_attempts_per_backend

        # Default fallback-triggering errors
        if fallback_on_errors is None:
            fallback_on_errors = (
                BackendConnectionError,
                BackendTimeoutError,
                BackendResponseError,  # Will check status code
            )
        self.fallback_on_errors = fallback_on_errors

        # All backends in order
        self.all_backends = [primary] + self.fallbacks

        logger.info(
            "fallback_chain_initialized",
            primary_backend=primary.name,
            fallback_backends=[b.name for b in self.fallbacks],
            total_backends=len(self.all_backends),
            max_attempts_per_backend=max_attempts_per_backend,
        )

    def _should_fallback(self, error: Exception) -> bool:
        """Determine if error should trigger fallback.

        Args:
            error: Exception that occurred

        Returns:
            True if should try next backend, False if should fail immediately
        """
        # Check if error type is in fallback list
        if not isinstance(error, self.fallback_on_errors):
            logger.debug(
                "error_not_fallback_eligible",
                error_type=type(error).__name__,
                error=str(error),
            )
            return False

        # Special handling for BackendResponseError
        if isinstance(error, BackendResponseError):
            status_code = getattr(error, 'status_code', None)

            # Don't fallback on auth errors (401, 403)
            if status_code in (401, 403):
                logger.debug(
                    "auth_error_no_fallback",
                    status_code=status_code,
                    error=str(error),
                )
                return False

            # Don't fallback on other 4xx errors (except 429 rate limit)
            if status_code and 400 <= status_code < 500 and status_code != 429:
                logger.debug(
                    "client_error_no_fallback",
                    status_code=status_code,
                    error=str(error),
                )
                return False

            # Fallback on 5xx server errors and rate limits
            if status_code and (status_code >= 500 or status_code == 429):
                logger.debug(
                    "server_error_triggers_fallback",
                    status_code=status_code,
                    error=str(error),
                )
                return True

        # Fallback on connection and timeout errors
        return True

    async def execute_with_fallback(
        self,
        operation: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute an operation with automatic fallback.

        Tries each backend in order until one succeeds or all fail.

        Args:
            operation: Async operation to execute (e.g., backend.page_to_markdown)
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result from successful backend

        Raises:
            BackendError: If all backends fail
        """
        last_error: Exception | None = None
        context = kwargs.get('context', {})

        for backend_index, backend in enumerate(self.all_backends):
            is_primary = backend_index == 0
            backend_type = "primary" if is_primary else f"fallback_{backend_index}"

            logger.info(
                "trying_backend",
                backend_type=backend_type,
                backend_name=backend.name,
                backend_index=backend_index,
                total_backends=len(self.all_backends),
                **context,
            )

            # Try this backend with retries
            for attempt in range(self.max_attempts_per_backend):
                try:
                    # Execute operation with this backend
                    # Replace 'self' in operation with current backend
                    result = await operation(backend, *args, **kwargs)

                    # Success!
                    if not is_primary:
                        logger.warning(
                            "fallback_succeeded",
                            backend_type=backend_type,
                            backend_name=backend.name,
                            attempt=attempt + 1,
                            total_attempts=self.max_attempts_per_backend,
                            **context,
                        )
                    else:
                        logger.debug(
                            "primary_backend_succeeded",
                            backend_name=backend.name,
                            attempt=attempt + 1,
                            **context,
                        )

                    return result

                except Exception as e:
                    last_error = e

                    # Check if we should retry with this backend
                    if attempt < self.max_attempts_per_backend - 1:
                        logger.warning(
                            "backend_attempt_failed_retrying",
                            backend_type=backend_type,
                            backend_name=backend.name,
                            attempt=attempt + 1,
                            max_attempts=self.max_attempts_per_backend,
                            error=str(e),
                            error_type=type(e).__name__,
                            **context,
                        )
                        # Small delay before retry
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue

                    # All attempts for this backend failed
                    logger.warning(
                        "backend_exhausted",
                        backend_type=backend_type,
                        backend_name=backend.name,
                        attempts=self.max_attempts_per_backend,
                        error=str(e),
                        error_type=type(e).__name__,
                        **context,
                    )

                    # Check if we should fallback to next backend
                    if not self._should_fallback(e):
                        logger.error(
                            "non_fallback_error_aborting",
                            backend_name=backend.name,
                            error=str(e),
                            error_type=type(e).__name__,
                            **context,
                        )
                        raise

                    # Try next backend
                    break

        # All backends failed
        logger.error(
            "all_backends_failed",
            total_backends=len(self.all_backends),
            last_error=str(last_error) if last_error else None,
            last_error_type=type(last_error).__name__ if last_error else None,
            **context,
        )

        if last_error:
            raise last_error

        raise BackendError(
            "All backends in fallback chain failed",
            details={
                "backends_tried": [b.name for b in self.all_backends],
                **context,
            }
        )

    async def get_healthy_backend(self) -> OcrVlmBackend | None:
        """Get the first healthy backend in the chain.

        Checks health of all backends and returns the first healthy one.

        Returns:
            First healthy backend, or None if all unhealthy
        """
        logger.debug(
            "checking_backend_health",
            total_backends=len(self.all_backends),
        )

        for backend in self.all_backends:
            # Check if backend has health_check method
            if not hasattr(backend, 'health_check'):
                logger.debug(
                    "backend_no_health_check",
                    backend_name=backend.name,
                )
                # Assume healthy if no health check
                return backend

            try:
                is_healthy = await backend.health_check()

                if is_healthy:
                    logger.info(
                        "healthy_backend_found",
                        backend_name=backend.name,
                    )
                    return backend
                else:
                    logger.warning(
                        "backend_unhealthy",
                        backend_name=backend.name,
                    )

            except Exception as e:
                logger.warning(
                    "health_check_error",
                    backend_name=backend.name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        logger.error(
            "no_healthy_backends",
            total_backends=len(self.all_backends),
        )

        return None

    # ============================================================================
    # OcrVlmBackend Interface
    # ============================================================================

    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str,
    ) -> str:
        """Convert a full page image to Markdown with fallback.

        Args:
            image_bytes: PNG image bytes
            page_num: Page number (1-indexed)
            doc_id: Document identifier

        Returns:
            Markdown string

        Raises:
            BackendError: If all backends fail
        """
        async def operation(backend: OcrVlmBackend, *args, **kwargs):
            return await backend.page_to_markdown(*args, **kwargs)

        return await self.execute_with_fallback(
            operation,
            image_bytes,
            page_num,
            doc_id,
            context={"doc_id": doc_id, "page_num": page_num, "operation": "page_to_markdown"},
        )

    async def table_to_markdown(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a table image to Markdown with fallback.

        Args:
            image_bytes: PNG image bytes
            meta: Metadata

        Returns:
            Markdown table string

        Raises:
            BackendError: If all backends fail
        """
        async def operation(backend: OcrVlmBackend, *args, **kwargs):
            return await backend.table_to_markdown(*args, **kwargs)

        return await self.execute_with_fallback(
            operation,
            image_bytes,
            meta,
            context={**meta, "operation": "table_to_markdown"},
        )

    async def formula_to_latex(
        self,
        image_bytes: bytes,
        meta: dict[str, Any],
    ) -> str:
        """Convert a formula image to LaTeX with fallback.

        Args:
            image_bytes: PNG image bytes
            meta: Metadata

        Returns:
            LaTeX string

        Raises:
            BackendError: If all backends fail
        """
        async def operation(backend: OcrVlmBackend, *args, **kwargs):
            return await backend.formula_to_latex(*args, **kwargs)

        return await self.execute_with_fallback(
            operation,
            image_bytes,
            meta,
            context={**meta, "operation": "formula_to_latex"},
        )

    async def close(self) -> None:
        """Close all backends in the chain."""
        logger.debug(
            "closing_fallback_chain",
            total_backends=len(self.all_backends),
        )

        for backend in self.all_backends:
            try:
                await backend.close()
                logger.debug(
                    "backend_closed",
                    backend_name=backend.name,
                )
            except Exception as e:
                logger.warning(
                    "backend_close_error",
                    backend_name=backend.name,
                    error=str(e),
                )

    async def __aenter__(self) -> "FallbackChain":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

    @property
    def name(self) -> str:
        """Get chain name (for compatibility with backend interface)."""
        return f"fallback_chain({self.primary.name})"

    @property
    def config(self):
        """Get primary backend config (for compatibility)."""
        return self.primary.config
