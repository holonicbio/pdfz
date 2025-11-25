"""Health check functionality for Docling Hybrid OCR.

This module provides health checking for:
- Configuration validation
- Backend connectivity
- System resources

Usage:
    from docling_hybrid.common.health import check_system_health

    result = await check_system_health(config)
    if result.overall_status == HealthStatus.HEALTHY:
        print("System is healthy")
"""

import asyncio
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
from pydantic import ValidationError

from docling_hybrid.common.config import Config, init_config
from docling_hybrid.common.errors import BackendError, ConfigurationError
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component."""

    name: str
    status: HealthStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None


@dataclass
class SystemHealth:
    """Overall system health status."""

    overall_status: HealthStatus
    components: list[ComponentHealth]
    timestamp: float

    @property
    def healthy_count(self) -> int:
        """Number of healthy components."""
        return sum(1 for c in self.components if c.status == HealthStatus.HEALTHY)

    @property
    def degraded_count(self) -> int:
        """Number of degraded components."""
        return sum(1 for c in self.components if c.status == HealthStatus.DEGRADED)

    @property
    def unhealthy_count(self) -> int:
        """Number of unhealthy components."""
        return sum(1 for c in self.components if c.status == HealthStatus.UNHEALTHY)

    def is_healthy(self) -> bool:
        """Check if system is fully healthy."""
        return self.overall_status == HealthStatus.HEALTHY

    def is_degraded(self) -> bool:
        """Check if system is degraded but operational."""
        return self.overall_status == HealthStatus.DEGRADED


async def check_config_health(config_path: Path | None = None) -> ComponentHealth:
    """Check configuration file health.

    Args:
        config_path: Path to config file, or None for default

    Returns:
        ComponentHealth for configuration
    """
    try:
        # Try to load config
        config = init_config(config_path)

        # Validate required settings
        issues = []

        # Check backends config
        if not config.backends.configs:
            issues.append("No backends configured")

        if config.backends.default not in config.backends.configs:
            issues.append(f"Default backend '{config.backends.default}' not found")

        # Check for API keys if using OpenRouter
        if config.backends.default == "nemotron-openrouter":
            backend_config = config.backends.get_backend_config()
            if not backend_config.api_key:
                issues.append("OPENROUTER_API_KEY not set")

        if issues:
            return ComponentHealth(
                name="Configuration",
                status=HealthStatus.DEGRADED,
                message=f"Configuration has {len(issues)} issue(s)",
                details={"issues": issues, "config_path": str(config_path) if config_path else "default"}
            )

        return ComponentHealth(
            name="Configuration",
            status=HealthStatus.HEALTHY,
            message="Configuration is valid",
            details={"config_path": str(config_path) if config_path else "default"}
        )

    except ValidationError as e:
        return ComponentHealth(
            name="Configuration",
            status=HealthStatus.UNHEALTHY,
            message="Configuration validation failed",
            details={"error": str(e), "config_path": str(config_path) if config_path else "default"}
        )

    except ConfigurationError as e:
        return ComponentHealth(
            name="Configuration",
            status=HealthStatus.UNHEALTHY,
            message=e.message,
            details=e.details or {}
        )

    except Exception as e:
        return ComponentHealth(
            name="Configuration",
            status=HealthStatus.UNHEALTHY,
            message=f"Failed to load configuration: {e}",
            details={"error": str(e), "config_path": str(config_path) if config_path else "default"}
        )


async def check_backend_health(
    backend_name: str,
    base_url: str,
    api_key: str | None = None,
    timeout: int = 10,
) -> ComponentHealth:
    """Check backend connectivity and health.

    Args:
        backend_name: Name of the backend
        base_url: Base URL for the backend API
        api_key: API key for authentication
        timeout: Request timeout in seconds

    Returns:
        ComponentHealth for the backend
    """
    import time

    start_time = time.time()

    try:
        # For OpenRouter, check /api/v1/models endpoint
        if "openrouter.ai" in base_url:
            check_url = "https://openrouter.ai/api/v1/models"
        else:
            # For local backends (vLLM), check /health or /v1/models
            if base_url.endswith("/v1/chat/completions"):
                check_url = base_url.replace("/v1/chat/completions", "/health")
            else:
                check_url = f"{base_url.rstrip('/')}/health"

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                check_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                latency_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    return ComponentHealth(
                        name=f"{backend_name} Backend",
                        status=HealthStatus.HEALTHY,
                        message="Backend is reachable",
                        details={"url": base_url, "check_url": check_url},
                        latency_ms=latency_ms
                    )
                elif response.status == 401 or response.status == 403:
                    return ComponentHealth(
                        name=f"{backend_name} Backend",
                        status=HealthStatus.UNHEALTHY,
                        message="Authentication failed",
                        details={
                            "url": base_url,
                            "status": response.status,
                            "hint": "Check your API key"
                        },
                        latency_ms=latency_ms
                    )
                else:
                    return ComponentHealth(
                        name=f"{backend_name} Backend",
                        status=HealthStatus.DEGRADED,
                        message=f"Backend returned status {response.status}",
                        details={"url": base_url, "status": response.status},
                        latency_ms=latency_ms
                    )

    except asyncio.TimeoutError:
        return ComponentHealth(
            name=f"{backend_name} Backend",
            status=HealthStatus.UNHEALTHY,
            message=f"Connection timeout after {timeout}s",
            details={"url": base_url, "timeout": timeout}
        )

    except aiohttp.ClientConnectorError as e:
        return ComponentHealth(
            name=f"{backend_name} Backend",
            status=HealthStatus.UNHEALTHY,
            message="Connection refused",
            details={"url": base_url, "error": str(e)}
        )

    except Exception as e:
        return ComponentHealth(
            name=f"{backend_name} Backend",
            status=HealthStatus.UNHEALTHY,
            message=f"Health check failed: {type(e).__name__}",
            details={"url": base_url, "error": str(e)}
        )


async def check_system_resources() -> ComponentHealth:
    """Check system resource availability.

    Returns:
        ComponentHealth for system resources
    """
    try:
        import psutil

        # Get memory info
        memory = psutil.virtual_memory()
        available_mb = memory.available / 1024 / 1024
        percent_used = memory.percent

        # Get CPU info
        cpu_percent = psutil.cpu_percent(interval=0.1)

        details = {
            "memory_available_mb": int(available_mb),
            "memory_percent_used": percent_used,
            "cpu_percent": cpu_percent
        }

        # Determine status
        if available_mb < 1024:  # Less than 1GB available
            return ComponentHealth(
                name="System Resources",
                status=HealthStatus.DEGRADED,
                message="Low memory available",
                details=details
            )
        elif percent_used > 90:
            return ComponentHealth(
                name="System Resources",
                status=HealthStatus.DEGRADED,
                message="High memory usage",
                details=details
            )
        else:
            return ComponentHealth(
                name="System Resources",
                status=HealthStatus.HEALTHY,
                message="Sufficient resources available",
                details=details
            )

    except ImportError:
        # psutil not available, skip resource check
        return ComponentHealth(
            name="System Resources",
            status=HealthStatus.HEALTHY,
            message="Resource monitoring not available (psutil not installed)",
            details={"skipped": True}
        )

    except Exception as e:
        return ComponentHealth(
            name="System Resources",
            status=HealthStatus.DEGRADED,
            message="Failed to check system resources",
            details={"error": str(e)}
        )


async def check_python_version() -> ComponentHealth:
    """Check Python version compatibility.

    Returns:
        ComponentHealth for Python version
    """
    required_major = 3
    required_minor = 11

    current_major = sys.version_info.major
    current_minor = sys.version_info.minor

    if current_major < required_major or (
        current_major == required_major and current_minor < required_minor
    ):
        return ComponentHealth(
            name="Python Version",
            status=HealthStatus.UNHEALTHY,
            message=f"Python {required_major}.{required_minor}+ required",
            details={
                "required": f"{required_major}.{required_minor}+",
                "current": f"{current_major}.{current_minor}.{sys.version_info.micro}"
            }
        )

    return ComponentHealth(
        name="Python Version",
        status=HealthStatus.HEALTHY,
        message=f"Python {current_major}.{current_minor}.{sys.version_info.micro}",
        details={
            "version": f"{current_major}.{current_minor}.{sys.version_info.micro}"
        }
    )


async def check_system_health(
    config: Config,
    check_backends: bool = True,
    backend_timeout: int = 10,
) -> SystemHealth:
    """Perform comprehensive system health check.

    Args:
        config: Application configuration
        check_backends: Whether to check backend connectivity
        backend_timeout: Timeout for backend checks in seconds

    Returns:
        SystemHealth with overall status and component details
    """
    import time

    timestamp = time.time()
    components: list[ComponentHealth] = []

    # Check Python version
    components.append(await check_python_version())

    # Check configuration (already loaded, so just validate it)
    try:
        # Validate required settings
        issues = []

        if not config.backends.configs:
            issues.append("No backends configured")

        if config.backends.default not in config.backends.configs:
            issues.append(f"Default backend '{config.backends.default}' not found")

        if issues:
            components.append(ComponentHealth(
                name="Configuration",
                status=HealthStatus.DEGRADED,
                message=f"Configuration has {len(issues)} issue(s)",
                details={"issues": issues}
            ))
        else:
            components.append(ComponentHealth(
                name="Configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration is valid",
                details={}
            ))
    except Exception as e:
        components.append(ComponentHealth(
            name="Configuration",
            status=HealthStatus.UNHEALTHY,
            message=f"Configuration error: {e}",
            details={"error": str(e)}
        ))

    # Check backends
    if check_backends:
        # Check default backend
        try:
            backend_config = config.backends.get_backend_config()
            backend_health = await check_backend_health(
                backend_name=backend_config.name,
                base_url=backend_config.base_url,
                api_key=backend_config.api_key,
                timeout=backend_timeout
            )
            components.append(backend_health)
        except Exception as e:
            components.append(ComponentHealth(
                name=f"{config.backends.default} Backend",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check backend: {e}",
                details={"error": str(e)}
            ))

    # Check system resources
    components.append(await check_system_resources())

    # Determine overall status
    if all(c.status == HealthStatus.HEALTHY for c in components):
        overall = HealthStatus.HEALTHY
    elif any(c.status == HealthStatus.UNHEALTHY for c in components):
        overall = HealthStatus.UNHEALTHY
    else:
        overall = HealthStatus.DEGRADED

    return SystemHealth(
        overall_status=overall,
        components=components,
        timestamp=timestamp
    )


def format_health_report(health: SystemHealth, verbose: bool = False) -> str:
    """Format health check results as a human-readable report.

    Args:
        health: SystemHealth to format
        verbose: Include detailed information

    Returns:
        Formatted string report
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("Docling Hybrid OCR - System Health Check")
    lines.append("=" * 60)
    lines.append("")

    # Overall status
    status_icon = {
        HealthStatus.HEALTHY: "✓",
        HealthStatus.DEGRADED: "⚠",
        HealthStatus.UNHEALTHY: "✗"
    }

    icon = status_icon[health.overall_status]
    lines.append(f"Overall Status: {icon} {health.overall_status.value.upper()}")
    lines.append(f"Components: {health.healthy_count} healthy, {health.degraded_count} degraded, {health.unhealthy_count} unhealthy")
    lines.append("")

    # Component details
    lines.append("Component Status:")
    lines.append("-" * 60)

    for component in health.components:
        icon = status_icon[component.status]
        latency = f" ({component.latency_ms:.0f}ms)" if component.latency_ms else ""
        lines.append(f"{icon} {component.name}: {component.message}{latency}")

        if verbose and component.details:
            for key, value in component.details.items():
                if key not in ("error",):  # Show errors separately
                    lines.append(f"    {key}: {value}")

            if "error" in component.details:
                lines.append(f"    Error: {component.details['error']}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
