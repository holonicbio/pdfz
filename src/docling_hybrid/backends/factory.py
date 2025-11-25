"""Backend factory for creating OCR/VLM backend instances.

This module provides the single entry point for creating backend instances.
The factory maps backend names to their implementations and handles
configuration validation.

Usage:
    from docling_hybrid.backends import make_backend
    from docling_hybrid.common.models import OcrBackendConfig
    
    # Using config object
    config = OcrBackendConfig(
        name="nemotron-openrouter",
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
    )
    backend = make_backend(config)
    
    # Using Config object from file
    from docling_hybrid.common.config import get_config
    config = get_config()
    backend = make_backend(config.backends.get_backend_config())
"""

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.backends.deepseek_mlx_stub import DeepseekOcrMlxBackend
from docling_hybrid.backends.deepseek_vllm import DeepSeekVLLMBackend
from docling_hybrid.backends.openrouter_nemotron import OpenRouterNemotronBackend
from docling_hybrid.common.errors import ConfigurationError
from docling_hybrid.common.logging import get_logger
from docling_hybrid.common.models import OcrBackendConfig

logger = get_logger(__name__)

# Registry of backend names to implementation classes
BACKEND_REGISTRY: dict[str, type[OcrVlmBackend]] = {
    "nemotron-openrouter": OpenRouterNemotronBackend,
    "deepseek-vllm": DeepSeekVLLMBackend,
    "deepseek-mlx": DeepseekOcrMlxBackend,
}


def make_backend(config: OcrBackendConfig) -> OcrVlmBackend:
    """Create an OCR/VLM backend instance from configuration.
    
    This is the canonical factory function for creating backend instances.
    It looks up the backend class by name and instantiates it with the
    provided configuration.
    
    Args:
        config: Backend configuration containing:
            - name: Backend identifier (must be in BACKEND_REGISTRY)
            - model: Model ID for the provider
            - base_url: API endpoint URL
            - Other provider-specific settings
    
    Returns:
        Configured backend instance ready for use
    
    Raises:
        ConfigurationError: If backend name is not recognized
    
    Available Backends:
        - "nemotron-openrouter": OpenRouter API with Nemotron model (✓ implemented)
        - "deepseek-vllm": DeepSeek-OCR via vLLM (stub)
        - "deepseek-mlx": DeepSeek-OCR via MLX (stub)
    
    Examples:
        >>> config = OcrBackendConfig(
        ...     name="nemotron-openrouter",
        ...     model="nvidia/nemotron-nano-12b-v2-vl:free",
        ...     base_url="https://openrouter.ai/api/v1/chat/completions",
        ...     api_key="sk-...",
        ... )
        >>> backend = make_backend(config)
        >>> isinstance(backend, OpenRouterNemotronBackend)
        True
        
        >>> # Using application config
        >>> from docling_hybrid.common.config import get_config
        >>> app_config = get_config()
        >>> backend_config = app_config.backends.get_backend_config("nemotron-openrouter")
        >>> backend = make_backend(backend_config)
    
    Note:
        Backend instances should be used as async context managers when possible:
        
        >>> async with make_backend(config) as backend:
        ...     result = await backend.page_to_markdown(...)
        
        This ensures proper cleanup of HTTP sessions and other resources.
    """
    # Normalize name to lowercase for case-insensitive matching
    name = config.name.lower()
    
    # Look up backend class
    if name not in BACKEND_REGISTRY:
        available = sorted(BACKEND_REGISTRY.keys())
        raise ConfigurationError(
            f"Unknown backend: '{config.name}'",
            details={
                "requested": config.name,
                "available": available,
                "hint": f"Use one of: {', '.join(available)}",
            }
        )
    
    backend_class = BACKEND_REGISTRY[name]
    
    logger.info(
        "creating_backend",
        backend=name,
        model=config.model,
        base_url=config.base_url,
        backend_class=backend_class.__name__,
    )
    
    # Instantiate and return
    return backend_class(config)


def list_backends() -> list[str]:
    """List all available backend names.
    
    Returns:
        Sorted list of registered backend names
        
    Example:
        >>> backends = list_backends()
        >>> print(backends)
        ['deepseek-mlx', 'deepseek-vllm', 'nemotron-openrouter']
    """
    return sorted(BACKEND_REGISTRY.keys())


def register_backend(name: str, backend_class: type[OcrVlmBackend]) -> None:
    """Register a new backend implementation.
    
    Allows extending the system with custom backends at runtime.
    
    Args:
        name: Backend name (will be lowercased)
        backend_class: Backend implementation class
        
    Raises:
        ValueError: If name is already registered
        
    Example:
        >>> class MyCustomBackend(OcrVlmBackend):
        ...     # Implementation
        ...     pass
        >>> register_backend("my-backend", MyCustomBackend)
        >>> backend = make_backend(OcrBackendConfig(name="my-backend", ...))
    """
    name = name.lower()
    
    if name in BACKEND_REGISTRY:
        raise ValueError(
            f"Backend '{name}' is already registered. "
            f"Use a different name or remove the existing registration."
        )
    
    if not issubclass(backend_class, OcrVlmBackend):
        raise ValueError(
            f"Backend class must inherit from OcrVlmBackend, "
            f"got {backend_class.__name__}"
        )
    
    BACKEND_REGISTRY[name] = backend_class
    
    logger.info(
        "backend_registered",
        name=name,
        backend_class=backend_class.__name__,
    )
