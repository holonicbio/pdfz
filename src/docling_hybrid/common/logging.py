"""Logging configuration for Docling Hybrid OCR.

This module provides structured logging using structlog.
Logs can be output as human-readable text (for development)
or JSON (for production/aggregation).

Usage:
    from docling_hybrid.common.logging import setup_logging, get_logger
    
    # Initialize logging at application startup
    setup_logging(level="DEBUG", format="text")
    
    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("processing_started", doc_id="doc-123", pages=10)
    logger.error("backend_failed", error="timeout", backend="nemotron")
"""

import logging
import sys
from typing import Literal

import structlog

LogFormat = Literal["text", "json"]


def setup_logging(
    level: str = "INFO",
    format: LogFormat = "text",
) -> None:
    """Configure structured logging for the application.
    
    Should be called once at application startup, before any logging occurs.
    Configures both structlog and the standard logging library.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format:
            - "text": Human-readable, colored output for terminals
            - "json": Structured JSON, one event per line
    
    Examples:
        >>> # Development setup
        >>> setup_logging(level="DEBUG", format="text")
        
        >>> # Production setup
        >>> setup_logging(level="INFO", format="json")
    
    Note:
        Calling this function multiple times will reconfigure logging.
        This is generally not recommended but can be useful for testing.
    """
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Shared processors for all configurations
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Format-specific processors
    if format == "json":
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
        force=True,  # Allow reconfiguration
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance for a module.
    
    Returns a structlog logger that supports structured key-value logging.
    
    Args:
        name: Logger name, typically __name__ of the calling module
    
    Returns:
        Configured structlog logger
    
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("event_name", key1="value1", key2=42)
        
        >>> # Logs output as:
        >>> # 2024-01-01T12:00:00 [info] event_name key1=value1 key2=42
        
        >>> # Or in JSON format:
        >>> # {"event": "event_name", "key1": "value1", "key2": 42, ...}
    
    Note:
        Logger names should follow module hierarchy (use __name__).
        This allows filtering logs by module path.
    """
    return structlog.get_logger(name)


def bind_context(**kwargs) -> None:
    """Bind context variables to all subsequent log messages.
    
    Useful for adding request-scoped or document-scoped context
    that should appear in all log messages.
    
    Args:
        **kwargs: Key-value pairs to bind to log context
    
    Examples:
        >>> bind_context(doc_id="doc-123", request_id="req-456")
        >>> logger.info("processing")  # Includes doc_id and request_id
        
        >>> # Clear context when done
        >>> clear_context()
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables.
    
    Should be called at the end of a request or document processing
    to prevent context from leaking to subsequent operations.
    """
    structlog.contextvars.clear_contextvars()
