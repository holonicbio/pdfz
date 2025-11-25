"""Integration test configuration and fixtures.

These tests require:
- OPENROUTER_API_KEY environment variable
- PDF files in pdfs/ directory (files starting with '2511')
"""

import os
from pathlib import Path

import pytest

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# PDF test files directory
PDFS_DIR = PROJECT_ROOT / "pdfs"


def get_test_pdfs() -> list[Path]:
    """Get all PDF files starting with '2511' from pdfs directory."""
    if not PDFS_DIR.exists():
        return []
    return sorted(PDFS_DIR.glob("2511*.pdf"))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "live_api: mark test as requiring live OpenRouter API"
    )
    config.addinivalue_line(
        "markers", "requires_pdfs: mark test as requiring PDF test files"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests if requirements not met."""
    # Check for API key
    has_api_key = bool(os.environ.get("OPENROUTER_API_KEY"))

    # Check for PDF files
    test_pdfs = get_test_pdfs()
    has_pdfs = len(test_pdfs) > 0

    skip_no_api = pytest.mark.skip(reason="OPENROUTER_API_KEY not set")
    skip_no_pdfs = pytest.mark.skip(
        reason=f"No PDF files starting with '2511' found in {PDFS_DIR}"
    )

    for item in items:
        if "live_api" in item.keywords and not has_api_key:
            item.add_marker(skip_no_api)
        if "requires_pdfs" in item.keywords and not has_pdfs:
            item.add_marker(skip_no_pdfs)


@pytest.fixture
def api_key() -> str:
    """Get OpenRouter API key from environment."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set")
    return key


@pytest.fixture
def pdfs_dir() -> Path:
    """Get path to PDFs directory."""
    if not PDFS_DIR.exists():
        pytest.skip(f"PDFs directory not found: {PDFS_DIR}")
    return PDFS_DIR


@pytest.fixture
def test_pdfs() -> list[Path]:
    """Get list of test PDF files (starting with '2511')."""
    pdfs = get_test_pdfs()
    if not pdfs:
        pytest.skip(f"No PDF files starting with '2511' found in {PDFS_DIR}")
    return pdfs


@pytest.fixture
def first_test_pdf(test_pdfs) -> Path:
    """Get first test PDF file."""
    return test_pdfs[0]


@pytest.fixture
def openrouter_config() -> dict:
    """OpenRouter backend configuration for testing."""
    return {
        "name": "nemotron-openrouter",
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "temperature": 0.0,
        "max_tokens": 4096,
    }
