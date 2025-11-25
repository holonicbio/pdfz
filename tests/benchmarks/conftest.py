"""Pytest configuration and fixtures for benchmarks.

This module provides fixtures for performance testing, including:
- Sample PDF generation of various sizes
- Mock backends for consistent benchmarking
- Resource monitoring utilities
"""

import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.config import Config, init_config, reset_config
from docling_hybrid.common.models import OcrBackendConfig, PageResult
from docling_hybrid.orchestrator import HybridPipeline


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def benchmark_config_dict() -> dict:
    """Configuration optimized for benchmarking."""
    return {
        "app": {
            "name": "docling-hybrid-ocr",
            "version": "0.1.0",
            "environment": "benchmark",
        },
        "logging": {
            "level": "WARNING",  # Reduce logging overhead
            "format": "text",
        },
        "resources": {
            "max_workers": 4,
            "max_memory_mb": 4096,
            "page_render_dpi": 150,  # Balance quality/speed
            "http_timeout_s": 30,
            "http_retry_attempts": 2,
        },
        "backends": {
            "default": "mock-backend",
            "mock-backend": {
                "name": "mock-backend",
                "model": "mock-model",
                "base_url": "http://localhost:9999",
                "temperature": 0.0,
                "max_tokens": 2048,
            },
        },
        "output": {
            "format": "markdown",
            "add_page_separators": True,
            "page_separator": "<!-- PAGE {page_num} -->\n\n",
        },
    }


@pytest.fixture
def benchmark_config(tmp_path: Path, benchmark_config_dict: dict) -> Config:
    """Create benchmark configuration."""
    import tomli_w

    reset_config()

    config_path = tmp_path / "benchmark_config.toml"

    # Flatten backends for TOML
    backends = benchmark_config_dict.pop("backends")
    benchmark_config_dict["backends"] = {
        "default": backends["default"],
        **{k: v for k, v in backends.items() if k != "default"}
    }

    with open(config_path, "wb") as f:
        tomli_w.dump(benchmark_config_dict, f)

    config = init_config(config_path)
    yield config
    reset_config()


# ============================================================================
# Mock Backend Fixtures
# ============================================================================

@pytest.fixture
async def fast_mock_backend() -> AsyncGenerator[OcrVlmBackend, None]:
    """Mock backend with fast, deterministic responses."""
    backend = AsyncMock(spec=OcrVlmBackend)
    backend.name = "fast-mock-backend"
    backend.config = OcrBackendConfig(
        name="fast-mock-backend",
        model="mock-model",
        base_url="http://localhost:9999",
        temperature=0.0,
        max_tokens=2048,
    )

    async def mock_page_to_markdown(
        image_bytes: bytes, page_num: int, doc_id: str
    ) -> str:
        """Simulate fast OCR processing."""
        await asyncio.sleep(0.01)  # 10ms latency
        return f"# Page {page_num}\n\nMock content for page {page_num}.\n\n"

    backend.page_to_markdown = mock_page_to_markdown
    backend.close = AsyncMock()
    backend.__aenter__ = AsyncMock(return_value=backend)
    backend.__aexit__ = AsyncMock()

    yield backend
    await backend.close()


@pytest.fixture
async def slow_mock_backend() -> AsyncGenerator[OcrVlmBackend, None]:
    """Mock backend with slower, realistic latency."""
    backend = AsyncMock(spec=OcrVlmBackend)
    backend.name = "slow-mock-backend"
    backend.config = OcrBackendConfig(
        name="slow-mock-backend",
        model="mock-model",
        base_url="http://localhost:9999",
        temperature=0.0,
        max_tokens=2048,
    )

    async def mock_page_to_markdown(
        image_bytes: bytes, page_num: int, doc_id: str
    ) -> str:
        """Simulate realistic API latency."""
        await asyncio.sleep(0.5)  # 500ms latency (realistic for VLM APIs)
        return f"# Page {page_num}\n\nMock content for page {page_num}.\n\n"

    backend.page_to_markdown = mock_page_to_markdown
    backend.close = AsyncMock()
    backend.__aenter__ = AsyncMock(return_value=backend)
    backend.__aexit__ = AsyncMock()

    yield backend
    await backend.close()


# ============================================================================
# PDF Fixture Generators
# ============================================================================

@pytest.fixture
def sample_pdf_1_page(tmp_path: Path) -> Path:
    """Generate a 1-page test PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "sample_1_page.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    c.drawString(100, 750, "Test Document - Page 1")
    c.drawString(100, 700, "This is a test document with one page.")
    c.drawString(100, 650, "Used for performance benchmarking.")

    c.showPage()
    c.save()

    return pdf_path


@pytest.fixture
def sample_pdf_10_pages(tmp_path: Path) -> Path:
    """Generate a 10-page test PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "sample_10_pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    for page_num in range(1, 11):
        c.drawString(100, 750, f"Test Document - Page {page_num}")
        c.drawString(100, 700, f"This is page {page_num} of 10.")
        c.drawString(100, 650, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
        c.drawString(100, 600, "Used for performance benchmarking.")

        # Add more text to make the page more realistic
        y = 550
        for i in range(10):
            c.drawString(100, y, f"Line {i+1}: Additional content for testing.")
            y -= 20

        c.showPage()

    c.save()
    return pdf_path


@pytest.fixture
def sample_pdf_50_pages(tmp_path: Path) -> Path:
    """Generate a 50-page test PDF for stress testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "sample_50_pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    for page_num in range(1, 51):
        c.drawString(100, 750, f"Test Document - Page {page_num}")
        c.drawString(100, 700, f"This is page {page_num} of 50.")
        c.drawString(100, 650, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")

        # Add varying content
        y = 600
        for i in range(15):
            c.drawString(100, y, f"Line {i+1}: Content for page {page_num}.")
            y -= 20

        c.showPage()

    c.save()
    return pdf_path


@pytest.fixture
def sample_pdf_100_pages(tmp_path: Path) -> Path:
    """Generate a 100-page test PDF for memory stress testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "sample_100_pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    for page_num in range(1, 101):
        c.drawString(100, 750, f"Test Document - Page {page_num}")
        c.drawString(100, 700, f"This is page {page_num} of 100.")

        # Minimal content to keep PDF size manageable
        y = 650
        for i in range(10):
            c.drawString(100, y, f"Line {i+1}: Test content.")
            y -= 30

        c.showPage()

    c.save()
    return pdf_path


# ============================================================================
# Pipeline Fixtures
# ============================================================================

@pytest.fixture
def benchmark_pipeline(benchmark_config: Config) -> HybridPipeline:
    """Create pipeline for benchmarking."""
    return HybridPipeline(benchmark_config)


# ============================================================================
# Resource Monitoring Utilities
# ============================================================================

class ResourceMonitor:
    """Monitor resource usage during tests."""

    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
        self.peak_memory: int = 0
        self.start_memory: int = 0

    def start(self):
        """Start monitoring."""
        import tracemalloc
        tracemalloc.start()
        self.start_time = time.time()
        self.start_memory = tracemalloc.get_traced_memory()[0]

    def stop(self) -> dict:
        """Stop monitoring and return stats."""
        import tracemalloc
        self.end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.peak_memory = peak

        return {
            "elapsed_seconds": self.end_time - self.start_time,
            "start_memory_mb": self.start_memory / (1024 * 1024),
            "peak_memory_mb": peak / (1024 * 1024),
            "delta_memory_mb": (peak - self.start_memory) / (1024 * 1024),
        }


@pytest.fixture
def resource_monitor() -> ResourceMonitor:
    """Provide resource monitoring for tests."""
    return ResourceMonitor()
