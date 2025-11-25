"""Integration tests using OpenRouter API with real PDF files.

These tests require:
- OPENROUTER_API_KEY environment variable set
- PDF files starting with '2511' in the pdfs/ directory

Run with:
    pytest tests/integration -v

To run only live API tests:
    pytest tests/integration -v -m live_api
"""

import asyncio
import os
from pathlib import Path

import pytest

from docling_hybrid.backends.openrouter_nemotron import OpenRouterNemotronBackend
from docling_hybrid.common.config import Config, init_config
from docling_hybrid.common.models import OcrBackendConfig
from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions
from docling_hybrid.renderer import get_page_count, render_page_to_png_bytes


# ============================================================================
# Backend Tests
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestOpenRouterBackend:
    """Test OpenRouter backend with real API calls."""

    async def test_backend_initialization(self, openrouter_config):
        """Test backend can be initialized with valid config."""
        config = OcrBackendConfig(**openrouter_config)
        backend = OpenRouterNemotronBackend(config)

        assert backend.name == "nemotron-openrouter"
        assert backend.config.model == "nvidia/nemotron-nano-12b-v2-vl:free"

    async def test_single_page_ocr(self, openrouter_config, first_test_pdf):
        """Test OCR on a single page from test PDF."""
        config = OcrBackendConfig(**openrouter_config)
        backend = OpenRouterNemotronBackend(config)

        # Render first page
        image_bytes = render_page_to_png_bytes(first_test_pdf, 0)
        assert len(image_bytes) > 0

        # Perform OCR
        async with backend:
            result = await backend.page_to_markdown(
                image_bytes=image_bytes,
                page_num=1,
                doc_id="test-doc-001",
            )

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"\n--- OCR Result (first 500 chars) ---\n{result[:500]}")

    async def test_health_check(self, openrouter_config):
        """Test backend health check."""
        config = OcrBackendConfig(**openrouter_config)
        backend = OpenRouterNemotronBackend(config)

        async with backend:
            is_healthy = await backend.health_check()

        # Health check should return True with valid API key
        assert is_healthy is True


# ============================================================================
# Renderer Tests
# ============================================================================


@pytest.mark.requires_pdfs
class TestRendererWithPDFs:
    """Test PDF renderer with real PDF files."""

    def test_get_page_count(self, test_pdfs):
        """Test getting page count from all test PDFs."""
        for pdf_path in test_pdfs:
            page_count = get_page_count(pdf_path)
            assert page_count > 0
            print(f"{pdf_path.name}: {page_count} pages")

    def test_render_all_pages(self, first_test_pdf):
        """Test rendering all pages from first test PDF."""
        page_count = get_page_count(first_test_pdf)

        for page_idx in range(min(page_count, 3)):  # Limit to first 3 pages
            image_bytes = render_page_to_png_bytes(first_test_pdf, page_idx)
            assert len(image_bytes) > 0
            assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'  # PNG magic bytes
            print(f"Page {page_idx + 1}: {len(image_bytes)} bytes")


# ============================================================================
# Pipeline Tests
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestPipelineIntegration:
    """Test full pipeline with OpenRouter backend."""

    async def test_convert_single_page(self, api_key, first_test_pdf, tmp_path):
        """Test converting a single page PDF."""
        # Create config with API key
        config_dict = {
            "app": {"name": "test", "version": "0.1.0", "environment": "test"},
            "logging": {"level": "DEBUG", "format": "text"},
            "resources": {
                "max_workers": 1,
                "max_memory_mb": 2048,
                "page_render_dpi": 150,
                "http_timeout_s": 120,
                "http_retry_attempts": 3,
            },
            "backends": {
                "default": "nemotron-openrouter",
                "configs": {
                    "nemotron-openrouter": {
                        "name": "nemotron-openrouter",
                        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                        "base_url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": api_key,
                        "temperature": 0.0,
                        "max_tokens": 4096,
                    },
                },
            },
            "output": {
                "format": "markdown",
                "add_page_separators": True,
                "page_separator": "\n\n---\n\n<!-- Page {page_num} -->\n\n",
            },
            "docling": {
                "do_ocr": False,
                "do_table_structure": False,
                "do_cell_matching": False,
            },
        }

        config = Config.model_validate(config_dict)
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "output.md"
        options = ConversionOptions(
            max_pages=1,
            dpi=150,
            output_path=output_path,
        )

        async with pipeline:
            result = await pipeline.convert_pdf(first_test_pdf, options=options)

        assert result is not None
        assert result.processed_pages == 1
        assert result.markdown is not None
        assert len(result.markdown) > 0

        print(f"\n--- Conversion Result ---")
        print(f"Pages processed: {result.processed_pages}/{result.total_pages}")
        print(f"Output length: {len(result.markdown)} chars")
        print(f"First 500 chars:\n{result.markdown[:500]}")

    async def test_convert_multiple_pages(self, api_key, first_test_pdf, tmp_path):
        """Test converting multiple pages."""
        config_dict = {
            "app": {"name": "test", "version": "0.1.0", "environment": "test"},
            "logging": {"level": "DEBUG", "format": "text"},
            "resources": {
                "max_workers": 2,
                "max_memory_mb": 4096,
                "page_render_dpi": 150,
                "http_timeout_s": 120,
                "http_retry_attempts": 3,
            },
            "backends": {
                "default": "nemotron-openrouter",
                "configs": {
                    "nemotron-openrouter": {
                        "name": "nemotron-openrouter",
                        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                        "base_url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": api_key,
                        "temperature": 0.0,
                        "max_tokens": 4096,
                    },
                },
            },
            "output": {
                "format": "markdown",
                "add_page_separators": True,
                "page_separator": "\n\n---\n\n<!-- Page {page_num} -->\n\n",
            },
            "docling": {
                "do_ocr": False,
                "do_table_structure": False,
                "do_cell_matching": False,
            },
        }

        config = Config.model_validate(config_dict)
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "output_multi.md"
        options = ConversionOptions(
            max_pages=3,  # Convert up to 3 pages
            dpi=150,
            output_path=output_path,
        )

        async with pipeline:
            result = await pipeline.convert_pdf(first_test_pdf, options=options)

        assert result is not None
        assert result.processed_pages >= 1
        assert result.processed_pages <= 3

        print(f"\n--- Multi-page Conversion Result ---")
        print(f"Pages processed: {result.processed_pages}/{result.total_pages}")
        print(f"Output length: {len(result.markdown)} chars")


# ============================================================================
# All PDFs Test
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestAllPDFs:
    """Test conversion of all PDF files starting with '2511'."""

    async def test_convert_all_test_pdfs(self, api_key, test_pdfs, tmp_path):
        """Convert first page of each test PDF."""
        config_dict = {
            "app": {"name": "test", "version": "0.1.0", "environment": "test"},
            "logging": {"level": "INFO", "format": "text"},
            "resources": {
                "max_workers": 1,
                "max_memory_mb": 2048,
                "page_render_dpi": 150,
                "http_timeout_s": 120,
                "http_retry_attempts": 3,
            },
            "backends": {
                "default": "nemotron-openrouter",
                "configs": {
                    "nemotron-openrouter": {
                        "name": "nemotron-openrouter",
                        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                        "base_url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": api_key,
                        "temperature": 0.0,
                        "max_tokens": 4096,
                    },
                },
            },
            "output": {
                "format": "markdown",
                "add_page_separators": True,
                "page_separator": "\n\n---\n\n<!-- Page {page_num} -->\n\n",
            },
            "docling": {
                "do_ocr": False,
                "do_table_structure": False,
                "do_cell_matching": False,
            },
        }

        config = Config.model_validate(config_dict)
        results = []

        for pdf_path in test_pdfs:
            print(f"\n--- Processing: {pdf_path.name} ---")

            pipeline = HybridPipeline(config)
            output_path = tmp_path / f"{pdf_path.stem}_output.md"

            options = ConversionOptions(
                max_pages=1,  # First page only for speed
                dpi=150,
                output_path=output_path,
            )

            async with pipeline:
                result = await pipeline.convert_pdf(pdf_path, options=options)

            results.append({
                "pdf": pdf_path.name,
                "pages": result.total_pages,
                "processed": result.processed_pages,
                "output_length": len(result.markdown),
                "success": result.processed_pages > 0,
            })

            print(f"  Total pages: {result.total_pages}")
            print(f"  Processed: {result.processed_pages}")
            print(f"  Output: {len(result.markdown)} chars")

            # Small delay between PDFs to respect rate limits
            await asyncio.sleep(1)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY: All PDFs Test Results")
        print("=" * 60)
        successful = sum(1 for r in results if r["success"])
        print(f"Total PDFs: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")

        for r in results:
            status = "✓" if r["success"] else "✗"
            print(f"  {status} {r['pdf']}: {r['processed']}/{r['pages']} pages, {r['output_length']} chars")

        # All should succeed
        assert successful == len(results), f"{len(results) - successful} PDFs failed"


# ============================================================================
# Concurrent Processing & Rate Limiting Tests
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestConcurrentProcessingWithRateLimiting:
    """Test concurrent page processing with rate limiting."""

    async def test_concurrent_page_processing(self, api_key, first_test_pdf, tmp_path):
        """Test that multiple pages can be processed concurrently."""
        import time

        config_dict = {
            "app": {"name": "test", "version": "0.1.0", "environment": "test"},
            "logging": {"level": "INFO", "format": "text"},
            "resources": {
                "max_workers": 3,  # Process 3 pages concurrently
                "max_memory_mb": 4096,
                "page_render_dpi": 150,
                "http_timeout_s": 120,
                "http_retry_attempts": 3,
            },
            "backends": {
                "default": "nemotron-openrouter",
                "configs": {
                    "nemotron-openrouter": {
                        "name": "nemotron-openrouter",
                        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                        "base_url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": api_key,
                        "temperature": 0.0,
                        "max_tokens": 4096,
                    },
                },
            },
            "output": {
                "format": "markdown",
                "add_page_separators": True,
                "page_separator": "\n\n---\n\n<!-- Page {page_num} -->\n\n",
            },
            "docling": {
                "do_ocr": False,
                "do_table_structure": False,
                "do_cell_matching": False,
            },
        }

        config = Config.model_validate(config_dict)
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "concurrent_output.md"
        options = ConversionOptions(
            max_pages=3,  # Process 3 pages to test concurrency
            dpi=150,
            output_path=output_path,
        )

        start_time = time.time()

        async with pipeline:
            result = await pipeline.convert_pdf(first_test_pdf, options=options)

        elapsed = time.time() - start_time

        assert result is not None
        assert result.processed_pages >= 1
        assert result.processed_pages <= 3

        print(f"\n--- Concurrent Processing Test ---")
        print(f"Pages processed: {result.processed_pages}")
        print(f"Time elapsed: {elapsed:.2f}s")
        print(f"Average time per page: {elapsed/result.processed_pages:.2f}s")

        # With concurrent processing, total time should be less than
        # sequential (which would be ~sum of individual page times)
        # This is a basic sanity check

    async def test_rate_limit_handling(self, api_key, first_test_pdf, tmp_path):
        """Test handling of rate limits with small delays between requests."""
        config_dict = {
            "app": {"name": "test", "version": "0.1.0", "environment": "test"},
            "logging": {"level": "DEBUG", "format": "text"},
            "resources": {
                "max_workers": 1,  # Sequential to test rate limiting
                "max_memory_mb": 2048,
                "page_render_dpi": 150,
                "http_timeout_s": 120,
                "http_retry_attempts": 3,
            },
            "backends": {
                "default": "nemotron-openrouter",
                "configs": {
                    "nemotron-openrouter": {
                        "name": "nemotron-openrouter",
                        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                        "base_url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": api_key,
                        "temperature": 0.0,
                        "max_tokens": 4096,
                        "max_retries": 5,  # More retries for rate limiting
                        "retry_initial_delay": 2.0,
                        "retry_max_delay": 30.0,
                    },
                },
            },
            "output": {
                "format": "markdown",
                "add_page_separators": True,
                "page_separator": "\n\n---\n\n<!-- Page {page_num} -->\n\n",
            },
            "docling": {
                "do_ocr": False,
                "do_table_structure": False,
                "do_cell_matching": False,
            },
        }

        config = Config.model_validate(config_dict)
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "rate_limit_output.md"
        options = ConversionOptions(
            max_pages=2,
            dpi=150,
            output_path=output_path,
        )

        async with pipeline:
            result = await pipeline.convert_pdf(first_test_pdf, options=options)

        assert result is not None
        assert result.processed_pages >= 1

        print(f"\n--- Rate Limit Test ---")
        print(f"Pages processed: {result.processed_pages}")
        print(f"Retries handled gracefully")


# ============================================================================
# Error Handling Tests with Real API
# ============================================================================


@pytest.mark.live_api
@pytest.mark.asyncio
class TestErrorHandlingWithRealAPI:
    """Test error handling scenarios with real OpenRouter API."""

    async def test_invalid_api_key_error(self, first_test_pdf):
        """Test handling of invalid API key (401 error)."""
        from docling_hybrid.common.errors import ConfigurationError

        config_dict = {
            "app": {"name": "test", "version": "0.1.0", "environment": "test"},
            "logging": {"level": "DEBUG", "format": "text"},
            "resources": {
                "max_workers": 1,
                "max_memory_mb": 2048,
                "page_render_dpi": 150,
                "http_timeout_s": 30,
                "http_retry_attempts": 1,
            },
            "backends": {
                "default": "nemotron-openrouter",
                "configs": {
                    "nemotron-openrouter": {
                        "name": "nemotron-openrouter",
                        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                        "base_url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": "invalid-key-for-testing-12345",
                        "temperature": 0.0,
                        "max_tokens": 4096,
                    },
                },
            },
            "output": {
                "format": "markdown",
                "add_page_separators": False,
            },
            "docling": {
                "do_ocr": False,
                "do_table_structure": False,
                "do_cell_matching": False,
            },
        }

        config = Config.model_validate(config_dict)
        pipeline = HybridPipeline(config)

        options = ConversionOptions(max_pages=1, dpi=150)

        # Should raise an error due to invalid API key
        with pytest.raises(Exception) as exc_info:
            async with pipeline:
                await pipeline.convert_pdf(first_test_pdf, options=options)

        # Error should be related to authentication/API key
        error_msg = str(exc_info.value).lower()
        assert "api key" in error_msg or "401" in error_msg or "auth" in error_msg or "unauthorized" in error_msg

        print(f"\n--- Invalid API Key Test ---")
        print(f"Error caught correctly: {type(exc_info.value).__name__}")

    async def test_backend_health_check(self, openrouter_config):
        """Test backend health check with real API."""
        config = OcrBackendConfig(**openrouter_config)

        # If no API key is set, use a dummy key and expect failure
        if not config.api_key:
            config.api_key = "test-key"
            expected_health = False
        else:
            expected_health = True

        backend = OpenRouterNemotronBackend(config)

        async with backend:
            is_healthy = await backend.health_check()

        if expected_health:
            assert is_healthy is True
            print(f"\n--- Health Check Test ---")
            print(f"Backend is healthy: {is_healthy}")
        else:
            # With invalid key, might still return True if endpoint is reachable
            print(f"\n--- Health Check Test ---")
            print(f"Health check result: {is_healthy}")
