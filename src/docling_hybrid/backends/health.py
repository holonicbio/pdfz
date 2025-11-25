"""Backend health checking utilities.

This module provides utilities for checking the health and connectivity
of OCR/VLM backends.

Key Features:
- Individual backend health checks
- Bulk health checking for all configured backends
- Health status reporting
- Connectivity verification

Usage:
    from docling_hybrid.backends.health import check_backend_health, check_all_backends

    # Check single backend
    is_healthy = await check_backend_health(backend)

    # Check all configured backends
    results = await check_all_backends(config)
    for result in results:
        print(f"{result.backend_name}: {result.status}")
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.backends.factory import make_backend
from docling_hybrid.common.config import Config
from docling_hybrid.common.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status for a backend."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class BackendHealthResult:
    """Result of a backend health check.

    Attributes:
        backend_name: Name of the backend
        status: Health status
        latency_ms: Response latency in milliseconds (None if check failed)
        error_message: Error message if unhealthy
        metadata: Additional information
    """
    backend_name: str
    status: HealthStatus
    latency_ms: float | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None

    def is_healthy(self) -> bool:
        """Check if backend is healthy."""
        return self.status == HealthStatus.HEALTHY

    def __repr__(self) -> str:
        """String representation."""
        if self.latency_ms:
            return f"{self.backend_name}: {self.status.value} ({self.latency_ms:.0f}ms)"
        return f"{self.backend_name}: {self.status.value}"


async def check_backend_health(
    backend: OcrVlmBackend,
    timeout: float = 10.0,
) -> BackendHealthResult:
    """Check health of a single backend.

    Args:
        backend: Backend to check
        timeout: Timeout in seconds (default: 10.0)

    Returns:
        Health check result
    """
    import time

    logger.debug(
        "health_check_started",
        backend_name=backend.name,
        timeout=timeout,
    )

    # Check if backend has health_check method
    if not hasattr(backend, 'health_check'):
        logger.warning(
            "backend_no_health_check_method",
            backend_name=backend.name,
        )
        return BackendHealthResult(
            backend_name=backend.name,
            status=HealthStatus.UNKNOWN,
            error_message="Backend does not implement health_check method",
        )

    try:
        start_time = time.time()

        # Run health check with timeout
        is_healthy = await asyncio.wait_for(
            backend.health_check(),
            timeout=timeout,
        )

        elapsed_ms = (time.time() - start_time) * 1000

        if is_healthy:
            logger.info(
                "health_check_passed",
                backend_name=backend.name,
                latency_ms=elapsed_ms,
            )
            return BackendHealthResult(
                backend_name=backend.name,
                status=HealthStatus.HEALTHY,
                latency_ms=elapsed_ms,
            )
        else:
            logger.warning(
                "health_check_failed",
                backend_name=backend.name,
                latency_ms=elapsed_ms,
            )
            return BackendHealthResult(
                backend_name=backend.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=elapsed_ms,
                error_message="Backend reported unhealthy status",
            )

    except asyncio.TimeoutError:
        logger.error(
            "health_check_timeout",
            backend_name=backend.name,
            timeout=timeout,
        )
        return BackendHealthResult(
            backend_name=backend.name,
            status=HealthStatus.ERROR,
            error_message=f"Health check timed out after {timeout}s",
        )

    except Exception as e:
        logger.error(
            "health_check_exception",
            backend_name=backend.name,
            error=str(e),
            error_type=type(e).__name__,
        )
        return BackendHealthResult(
            backend_name=backend.name,
            status=HealthStatus.ERROR,
            error_message=f"{type(e).__name__}: {str(e)}",
        )


async def check_all_backends(
    config: Config,
    timeout: float = 10.0,
    include_fallbacks: bool = True,
) -> list[BackendHealthResult]:
    """Check health of all configured backends.

    Args:
        config: Application configuration
        timeout: Timeout per backend in seconds (default: 10.0)
        include_fallbacks: Whether to check fallback backends (default: True)

    Returns:
        List of health check results
    """
    logger.info(
        "checking_all_backends",
        include_fallbacks=include_fallbacks,
    )

    results = []

    # Get backend names to check
    backend_names = []

    # Add default backend
    default_backend = config.backends.default
    if default_backend:
        backend_names.append(default_backend)

    # Add fallback backends
    if include_fallbacks:
        fallback_backends = config.backends.fallback or []
        backend_names.extend(fallback_backends)

    # Remove duplicates while preserving order
    seen = set()
    backend_names = [x for x in backend_names if not (x in seen or seen.add(x))]

    logger.debug(
        "backends_to_check",
        backends=backend_names,
        count=len(backend_names),
    )

    # Check each backend
    for backend_name in backend_names:
        try:
            # Get backend configuration
            backend_config = config.backends.get_backend_config(backend_name)

            # Create backend instance
            backend = make_backend(backend_config)

            # Run health check
            result = await check_backend_health(backend, timeout=timeout)
            results.append(result)

            # Clean up
            await backend.close()

        except Exception as e:
            logger.error(
                "backend_check_failed",
                backend_name=backend_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            results.append(BackendHealthResult(
                backend_name=backend_name,
                status=HealthStatus.ERROR,
                error_message=f"Failed to create backend: {str(e)}",
            ))

    # Log summary
    healthy_count = sum(1 for r in results if r.is_healthy())
    logger.info(
        "health_check_summary",
        total_backends=len(results),
        healthy=healthy_count,
        unhealthy=len(results) - healthy_count,
    )

    return results


async def get_health_summary(
    config: Config,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Get overall health summary.

    Args:
        config: Application configuration
        timeout: Timeout per backend in seconds

    Returns:
        Dictionary with health summary
    """
    results = await check_all_backends(config, timeout=timeout)

    healthy_count = sum(1 for r in results if r.is_healthy())
    total_count = len(results)

    # Determine overall status
    if healthy_count == 0:
        overall_status = "critical"
    elif healthy_count < total_count:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "overall_status": overall_status,
        "total_backends": total_count,
        "healthy_backends": healthy_count,
        "unhealthy_backends": total_count - healthy_count,
        "backends": [
            {
                "name": r.backend_name,
                "status": r.status.value,
                "latency_ms": r.latency_ms,
                "error": r.error_message,
            }
            for r in results
        ],
    }


def format_health_results(results: list[BackendHealthResult]) -> str:
    """Format health check results as human-readable text.

    Args:
        results: List of health check results

    Returns:
        Formatted string
    """
    lines = []

    for result in results:
        # Status symbol
        if result.status == HealthStatus.HEALTHY:
            symbol = "✓"
        elif result.status == HealthStatus.UNHEALTHY:
            symbol = "✗"
        elif result.status == HealthStatus.UNKNOWN:
            symbol = "?"
        else:
            symbol = "⚠"

        # Build line
        line = f"{symbol} {result.backend_name}: {result.status.value}"

        if result.latency_ms:
            line += f" (latency: {result.latency_ms:.0f}ms)"

        if result.error_message:
            line += f"\n  Error: {result.error_message}"

        lines.append(line)

    # Add summary
    healthy_count = sum(1 for r in results if r.is_healthy())
    total_count = len(results)

    if healthy_count == total_count:
        status_text = "All systems operational"
    elif healthy_count == 0:
        status_text = "All backends unhealthy"
    else:
        status_text = f"{healthy_count}/{total_count} backends healthy"

    lines.append("")
    lines.append(f"Overall: {status_text}")

    return "\n".join(lines)
