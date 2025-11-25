"""Pytest configuration and shared fixtures.

This module provides fixtures for testing docling-hybrid-ocr components.
"""

import asyncio
import os
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from docling_hybrid.common.config import Config, reset_config
from docling_hybrid.common.models import OcrBackendConfig

# Import fixtures from utils module
pytest_plugins = ["tests.utils.async_fixtures"]


# ============================================================================
# Event Loop
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config_dict() -> dict:
    """Raw config dictionary for testing."""
    return {
        "app": {
            "name": "docling-hybrid-ocr",
            "version": "0.1.0",
            "environment": "test",
        },
        "logging": {
            "level": "DEBUG",
            "format": "text",
        },
        "resources": {
            "max_workers": 1,
            "max_memory_mb": 2048,
            "page_render_dpi": 72,
            "http_timeout_s": 10,
            "http_retry_attempts": 1,
        },
        "backends": {
            "default": "nemotron-openrouter",
            "configs": {
                "nemotron-openrouter": {
                    "name": "nemotron-openrouter",
                    "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                    "base_url": "https://openrouter.ai/api/v1/chat/completions",
                    "api_key": "test-api-key",
                    "temperature": 0.0,
                    "max_tokens": 1024,
                },
            },
        },
        "output": {
            "format": "markdown",
            "add_page_separators": False,
            "page_separator": "\n\n---\n\n<!-- Page {page_num} -->\n\n",
        },
        "docling": {
            "do_ocr": False,
            "do_table_structure": False,
            "do_cell_matching": False,
        },
    }


@pytest.fixture
def test_config_path(tmp_path: Path, test_config_dict: dict) -> Path:
    """Create a temporary test config file."""
    import tomli_w
    
    config_path = tmp_path / "test_config.toml"
    
    # Flatten backends for TOML
    backends = test_config_dict.pop("backends")
    test_config_dict["backends"] = {
        "default": backends["default"],
        **{k: v for k, v in backends.items() if k != "default"}
    }
    
    with open(config_path, "wb") as f:
        tomli_w.dump(test_config_dict, f)
    
    return config_path


@pytest.fixture
def backend_config() -> OcrBackendConfig:
    """Create a backend config for testing."""
    return OcrBackendConfig(
        name="test-backend",
        model="test-model",
        base_url="https://api.test.com/v1/chat/completions",
        api_key="test-api-key",
        temperature=0.0,
        max_tokens=1024,
    )


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global config before each test."""
    reset_config()
    yield
    reset_config()


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession."""
    session = MagicMock()
    session.post = AsyncMock()
    session.close = AsyncMock()
    session.closed = False
    return session


@pytest.fixture
def mock_api_response():
    """Create a mock API response with valid content."""
    return {
        "choices": [
            {
                "message": {
                    "content": "# Test Heading\n\nThis is test content."
                }
            }
        ]
    }


@pytest.fixture
def mock_backend():
    """Create a mock OCR backend."""
    backend = AsyncMock()
    backend.name = "mock-backend"
    backend.config = MagicMock()
    backend.page_to_markdown = AsyncMock(return_value="# Mock Page\n\nContent here.")
    backend.table_to_markdown = AsyncMock(return_value="| A | B |\n|---|---|\n| 1 | 2 |")
    backend.formula_to_latex = AsyncMock(return_value="\\frac{1}{2}")
    backend.close = AsyncMock()
    return backend


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create minimal valid PNG bytes for testing."""
    # Minimal 1x1 white PNG
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02'
        b'\xfe\r\x8a\x8f\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_env(monkeypatch):
    """Remove OCR-related environment variables."""
    env_vars = [
        "OPENROUTER_API_KEY",
        "DOCLING_HYBRID_CONFIG",
        "DOCLING_HYBRID_LOG_LEVEL",
        "DOCLING_HYBRID_MAX_WORKERS",
        "DOCLING_HYBRID_HTTP_REFERER",
        "DOCLING_HYBRID_X_TITLE",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def with_api_key(monkeypatch):
    """Set a test API key."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key-12345")
