"""Common utilities for Docling Hybrid OCR.

This module provides shared utilities used across all components:
- Configuration loading and validation
- ID generation
- Logging setup
- Shared data models
- Error types

Usage:
    from docling_hybrid.common import Config, get_config, generate_id
    from docling_hybrid.common.models import OcrBackendConfig
    from docling_hybrid.common.errors import DoclingHybridError
"""

from docling_hybrid.common.config import (
    Config,
    get_config,
    init_config,
    load_config,
)
from docling_hybrid.common.errors import (
    BackendError,
    ConfigurationError,
    DoclingHybridError,
    RenderingError,
    ValidationError,
)
from docling_hybrid.common.ids import generate_id, generate_timestamp_id
from docling_hybrid.common.logging import get_logger, setup_logging
from docling_hybrid.common.models import (
    BackendCandidate,
    OcrBackendConfig,
    PageResult,
)

__all__ = [
    # Config
    "Config",
    "get_config",
    "init_config",
    "load_config",
    # IDs
    "generate_id",
    "generate_timestamp_id",
    # Logging
    "setup_logging",
    "get_logger",
    # Models
    "OcrBackendConfig",
    "BackendCandidate",
    "PageResult",
    # Errors
    "DoclingHybridError",
    "ConfigurationError",
    "ValidationError",
    "BackendError",
    "RenderingError",
]
