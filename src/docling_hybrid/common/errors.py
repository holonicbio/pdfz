"""Error types for Docling Hybrid OCR.

This module defines the exception hierarchy used throughout the system.
All custom exceptions inherit from DoclingHybridError for easy catching.

Exception Hierarchy:
    DoclingHybridError (base)
    ├── ConfigurationError - Invalid or missing configuration
    ├── ValidationError - Invalid input data
    ├── BackendError - Backend communication/processing errors
    │   ├── BackendConnectionError - Cannot connect to backend
    │   ├── BackendTimeoutError - Backend request timed out
    │   └── BackendResponseError - Invalid response from backend
    └── RenderingError - PDF rendering errors

Usage:
    from docling_hybrid.common.errors import BackendError, ConfigurationError
    
    try:
        result = await backend.page_to_markdown(image_bytes)
    except BackendError as e:
        logger.error("backend_failed", error=str(e))
        raise
"""

from typing import Any


class DoclingHybridError(Exception):
    """Base exception for all Docling Hybrid OCR errors.
    
    All custom exceptions in this project inherit from this class,
    making it easy to catch any project-specific error:
    
        try:
            result = process_document(pdf_path)
        except DoclingHybridError as e:
            handle_error(e)
    
    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional context
    """
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize the error.
        
        Args:
            message: Human-readable error message
            details: Optional additional context (e.g., file paths, parameters)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation with details if present."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message
    
    def __repr__(self) -> str:
        """Return repr with class name."""
        return f"{self.__class__.__name__}({self.message!r}, details={self.details!r})"


class ConfigurationError(DoclingHybridError):
    """Configuration is invalid or missing.
    
    Raised when:
    - Config file not found
    - Config file has invalid syntax
    - Required configuration value is missing
    - Configuration value is invalid
    
    Example:
        if not api_key:
            raise ConfigurationError(
                "Missing OPENROUTER_API_KEY environment variable",
                details={"env_var": "OPENROUTER_API_KEY"}
            )
    """
    pass


class ValidationError(DoclingHybridError):
    """Input validation failed.
    
    Raised when:
    - PDF path doesn't exist
    - PDF file is invalid or corrupted
    - Input parameters are out of range
    - Required input is missing
    
    Example:
        if not pdf_path.exists():
            raise ValidationError(
                f"PDF file not found: {pdf_path}",
                details={"path": str(pdf_path)}
            )
    """
    pass


class BackendError(DoclingHybridError):
    """Backend communication or processing error.
    
    Base class for all backend-related errors.
    
    Attributes:
        backend_name: Name of the backend that failed
    """
    
    def __init__(
        self,
        message: str,
        backend_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize backend error.
        
        Args:
            message: Error message
            backend_name: Name of the backend that failed
            details: Additional context
        """
        details = details or {}
        if backend_name:
            details["backend"] = backend_name
        super().__init__(message, details)
        self.backend_name = backend_name


class BackendConnectionError(BackendError):
    """Cannot connect to backend service.
    
    Raised when:
    - Network connection fails
    - DNS resolution fails
    - Backend service is unreachable
    
    Example:
        except aiohttp.ClientConnectorError as e:
            raise BackendConnectionError(
                "Cannot connect to OpenRouter API",
                backend_name="nemotron-openrouter",
                details={"url": base_url, "error": str(e)}
            )
    """
    pass


class BackendTimeoutError(BackendError):
    """Backend request timed out.
    
    Raised when:
    - HTTP request times out
    - Backend takes too long to respond
    
    Example:
        except asyncio.TimeoutError:
            raise BackendTimeoutError(
                f"Request timed out after {timeout}s",
                backend_name="nemotron-openrouter",
                details={"timeout_s": timeout, "page": page_num}
            )
    """
    pass


class BackendResponseError(BackendError):
    """Invalid or unexpected response from backend.
    
    Raised when:
    - HTTP status is not 2xx
    - Response is not valid JSON
    - Response structure is unexpected
    - Backend returns an error message
    
    Attributes:
        status_code: HTTP status code if available
        response_body: Raw response body if available
    
    Example:
        if response.status != 200:
            raise BackendResponseError(
                f"Backend returned status {response.status}",
                backend_name="nemotron-openrouter",
                status_code=response.status,
                response_body=await response.text(),
            )
    """
    
    def __init__(
        self,
        message: str,
        backend_name: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize response error.
        
        Args:
            message: Error message
            backend_name: Name of the backend
            status_code: HTTP status code
            response_body: Raw response body
            details: Additional context
        """
        details = details or {}
        if status_code is not None:
            details["status_code"] = status_code
        if response_body is not None:
            # Truncate long response bodies
            if len(response_body) > 500:
                details["response_body"] = response_body[:500] + "..."
            else:
                details["response_body"] = response_body
        super().__init__(message, backend_name, details)
        self.status_code = status_code
        self.response_body = response_body


class RenderingError(DoclingHybridError):
    """PDF rendering failed.
    
    Raised when:
    - PDF cannot be opened
    - Page cannot be rendered
    - Image conversion fails
    
    Example:
        except Exception as e:
            raise RenderingError(
                f"Failed to render page {page_index}",
                details={"page": page_index, "pdf": str(pdf_path), "error": str(e)}
            )
    """
    pass
