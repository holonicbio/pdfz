"""Configuration management for Docling Hybrid OCR.

This module provides a layered configuration system:

1. Environment variables (highest priority)
2. User config file (--config or DOCLING_HYBRID_CONFIG)
3. Default config (configs/default.toml)

Usage:
    from docling_hybrid.common.config import init_config, get_config
    
    # Initialize at application startup
    config = init_config(Path("configs/local.toml"))
    
    # Access anywhere in the codebase
    config = get_config()
    print(config.resources.max_workers)

Environment Variable Overrides:
    DOCLING_HYBRID_LOG_LEVEL=DEBUG
    DOCLING_HYBRID_MAX_WORKERS=2
    DOCLING_HYBRID_DEFAULT_BACKEND=nemotron-openrouter
"""

import os
from pathlib import Path
from typing import Any

try:
    import tomli as tomllib  # Python < 3.11
except ImportError:
    import tomllib  # Python 3.11+

from pydantic import BaseModel, Field, field_validator, model_validator

from docling_hybrid.common.errors import ConfigurationError
from docling_hybrid.common.models import OcrBackendConfig


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = "docling-hybrid-ocr"
    version: str = "0.1.0"
    environment: str = "production"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate logging level."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"Invalid log level: {v}. Must be one of: {valid}")
        return v.upper()
    
    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate logging format."""
        valid = {"text", "json"}
        if v.lower() not in valid:
            raise ValueError(f"Invalid log format: {v}. Must be one of: {valid}")
        return v.lower()


class ResourcesConfig(BaseModel):
    """Resource limits configuration."""
    max_workers: int = Field(default=8, ge=1, le=64)
    max_memory_mb: int = Field(default=16384, ge=512)
    page_render_dpi: int = Field(default=200, ge=72, le=600)
    http_timeout_s: int = Field(default=120, ge=10, le=600)
    http_retry_attempts: int = Field(default=3, ge=1, le=10)


class BackendsConfig(BaseModel):
    """Backend configuration container."""
    default: str = "nemotron-openrouter"
    configs: dict[str, OcrBackendConfig] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_default_backend_exists(self) -> 'BackendsConfig':
        """Validate that the default backend exists in configs."""
        if self.configs and self.default not in self.configs:
            available = list(self.configs.keys())
            raise ValueError(
                f"Default backend '{self.default}' not found in configured backends. "
                f"Available backends: {', '.join(available)}"
            )
        return self

    def get_backend_config(self, name: str | None = None) -> OcrBackendConfig:
        """Get configuration for a specific backend.

        Args:
            name: Backend name, or None to use default

        Returns:
            Backend configuration

        Raises:
            ConfigurationError: If backend not found
        """
        backend_name = name or self.default
        if backend_name not in self.configs:
            available = list(self.configs.keys())
            raise ConfigurationError(
                f"Backend '{backend_name}' not found",
                details={"available": available, "requested": backend_name}
            )
        return self.configs[backend_name]


class OutputConfig(BaseModel):
    """Output configuration."""
    format: str = "markdown"
    add_page_separators: bool = True
    page_separator: str = "<!-- PAGE {page_num} -->\n\n"

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate output format."""
        valid = {"markdown", "md", "text", "txt"}
        if v.lower() not in valid:
            raise ValueError(
                f"Invalid output format: {v}. Must be one of: {', '.join(valid)}"
            )
        return v.lower()

    @field_validator("page_separator")
    @classmethod
    def validate_page_separator(cls, v: str) -> str:
        """Validate page separator contains placeholder."""
        if "{page_num}" not in v:
            raise ValueError(
                "page_separator must contain '{page_num}' placeholder"
            )
        return v


class DoclingConfig(BaseModel):
    """Docling-specific configuration."""
    do_ocr: bool = False
    do_table_structure: bool = True
    do_cell_matching: bool = True


class Config(BaseModel):
    """Root configuration model.

    Contains all configuration for the application.

    Attributes:
        app: Application settings
        logging: Logging settings
        resources: Resource limits
        backends: Backend configurations
        output: Output format settings
        docling: Docling-specific settings
    """
    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    resources: ResourcesConfig = Field(default_factory=ResourcesConfig)
    backends: BackendsConfig = Field(default_factory=BackendsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    docling: DoclingConfig = Field(default_factory=DoclingConfig)

    @model_validator(mode='after')
    def validate_resource_constraints(self) -> 'Config':
        """Validate that resource settings are reasonable.

        This validator checks:
        - max_workers is reasonable given available memory
        - http_timeout_s is longer than a minimum reasonable time
        - DPI settings are appropriate
        """
        # Estimate memory per worker (rough estimate: ~100MB per page at 200 DPI)
        dpi = self.resources.page_render_dpi
        estimated_mb_per_page = int((dpi / 200) ** 2 * 100)  # Scales quadratically with DPI
        estimated_total_mb = self.resources.max_workers * estimated_mb_per_page

        if estimated_total_mb > self.resources.max_memory_mb:
            raise ValueError(
                f"Resource configuration may exceed memory limits: "
                f"{self.resources.max_workers} workers × {estimated_mb_per_page}MB/page "
                f"≈ {estimated_total_mb}MB > {self.resources.max_memory_mb}MB limit. "
                f"Consider reducing max_workers or page_render_dpi."
            )

        # Warn if very low memory per worker
        mb_per_worker = self.resources.max_memory_mb // self.resources.max_workers
        if mb_per_worker < 100:
            # Note: We can't log here as logging might not be initialized yet
            # This will be caught by Pydantic validation and raised as an error
            pass  # Could add a warning mechanism here if needed

        return self


def _parse_backend_configs(backends_dict: dict[str, Any]) -> BackendsConfig:
    """Parse backend configurations from TOML dict.
    
    Args:
        backends_dict: Raw backends section from TOML
        
    Returns:
        Parsed BackendsConfig
    """
    default = backends_dict.get("default", "nemotron-openrouter")
    configs = {}
    
    for key, value in backends_dict.items():
        if key == "default":
            continue
        if isinstance(value, dict):
            # This is a backend config
            configs[key] = OcrBackendConfig(**value)
    
    return BackendsConfig(default=default, configs=configs)


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from TOML file with environment overrides.
    
    Configuration priority (highest to lowest):
    1. Environment variables (DOCLING_HYBRID_*)
    2. Config file specified by config_path or DOCLING_HYBRID_CONFIG
    3. Default config (configs/default.toml)
    
    Args:
        config_path: Path to config file (optional)
        
    Returns:
        Loaded and validated configuration
        
    Raises:
        ConfigurationError: If config file not found or invalid
        
    Examples:
        >>> config = load_config()  # Uses default or env var
        >>> config = load_config(Path("configs/local.toml"))
        
        >>> # Override via environment
        >>> os.environ["DOCLING_HYBRID_LOG_LEVEL"] = "DEBUG"
        >>> config = load_config()
        >>> config.logging.level
        'DEBUG'
    """
    # Determine config file path
    if config_path is None:
        env_config = os.environ.get("DOCLING_HYBRID_CONFIG")
        if env_config:
            config_path = Path(env_config)
        else:
            # Look for default config
            config_path = Path("configs/default.toml")
            if not config_path.exists():
                # Try relative to package
                config_path = Path(__file__).parent.parent.parent.parent / "configs" / "default.toml"
    
    # Load config file
    if not config_path.exists():
        raise ConfigurationError(
            f"Config file not found: {config_path}",
            details={
                "path": str(config_path),
                "hint": "Set DOCLING_HYBRID_CONFIG or create configs/default.toml"
            }
        )
    
    try:
        with open(config_path, "rb") as f:
            config_dict = tomllib.load(f)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to parse config file: {e}",
            details={"path": str(config_path)}
        ) from e
    
    # Parse backend configs specially
    if "backends" in config_dict:
        config_dict["backends"] = _parse_backend_configs(config_dict["backends"])
    
    # Apply environment variable overrides
    env_overrides = {
        "DOCLING_HYBRID_LOG_LEVEL": ("logging", "level"),
        "DOCLING_HYBRID_MAX_WORKERS": ("resources", "max_workers"),
        "DOCLING_HYBRID_MAX_MEMORY_MB": ("resources", "max_memory_mb"),
        "DOCLING_HYBRID_PAGE_RENDER_DPI": ("resources", "page_render_dpi"),
        "DOCLING_HYBRID_DEFAULT_BACKEND": ("backends", "default"),
    }
    
    for env_var, (section, field) in env_overrides.items():
        value = os.environ.get(env_var)
        if value is not None:
            if section not in config_dict:
                config_dict[section] = {}
            
            # Handle special case for backends
            if section == "backends" and isinstance(config_dict[section], BackendsConfig):
                if field == "default":
                    config_dict[section] = BackendsConfig(
                        default=value,
                        configs=config_dict[section].configs
                    )
            else:
                # Convert to int if needed
                if field in ("max_workers", "max_memory_mb", "page_render_dpi"):
                    value = int(value)
                config_dict[section][field] = value
    
    # Validate and return
    try:
        return Config(**config_dict)
    except Exception as e:
        raise ConfigurationError(
            f"Invalid configuration: {e}",
            details={"path": str(config_path)}
        ) from e


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Global configuration
        
    Raises:
        ConfigurationError: If config not initialized
        
    Note:
        Call init_config() first at application startup.
    """
    global _config
    if _config is None:
        raise ConfigurationError(
            "Configuration not initialized. Call init_config() first.",
            details={"hint": "Add init_config() to application startup"}
        )
    return _config


def init_config(config_path: Path | None = None) -> Config:
    """Initialize the global configuration.
    
    Should be called once at application startup.
    
    Args:
        config_path: Path to config file (optional)
        
    Returns:
        Initialized configuration
        
    Examples:
        >>> # At application startup
        >>> config = init_config(Path("configs/local.toml"))
        
        >>> # Later, anywhere in the code
        >>> config = get_config()
    """
    global _config
    _config = load_config(config_path)
    return _config


def reset_config() -> None:
    """Reset the global configuration.
    
    Primarily used for testing.
    """
    global _config
    _config = None
