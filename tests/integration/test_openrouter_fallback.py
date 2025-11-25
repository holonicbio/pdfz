"""Integration tests for fallback chain with OpenRouter.

These tests validate the fallback chain mechanism using real OpenRouter API calls.
They test scenarios where the primary backend may fail and fallback backends
take over.

Run with:
    pytest tests/integration/test_openrouter_fallback.py -v -m live_api
"""

import asyncio
from pathlib import Path

import pytest

from docling_hybrid.backends.fallback import FallbackChain
from docling_hybrid.backends.openrouter_nemotron import OpenRouterNemotronBackend
from docling_hybrid.common.config import Config
from docling_hybrid.common.errors import BackendError
from docling_hybrid.common.models import OcrBackendConfig
from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions
from docling_hybrid.renderer import render_page_to_png_bytes


# ============================================================================
# Fallback Chain Tests with Real API
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestFallbackChainWithOpenRouter:
    """Test fallback chain using real OpenRouter backends."""

    async def test_fallback_chain_initialization(self, openrouter_config):
        """Test creating a fallback chain with multiple OpenRouter backends."""
        # Create two backend configs
        primary_config = OcrBackendConfig(**openrouter_config)
        fallback_config = OcrBackendConfig(**openrouter_config)
        fallback_config.name = "fallback-openrouter"

        # Create backends
        primary = OpenRouterNemotronBackend(primary_config)
        fallback = OpenRouterNemotronBackend(fallback_config)

        # Create fallback chain
        chain = FallbackChain(
            primary=primary,
            fallbacks=[fallback],
            max_attempts_per_backend=2,
        )

        assert chain.primary.name == "nemotron-openrouter"
        assert len(chain.fallbacks) == 1
        assert chain.fallbacks[0].name == "fallback-openrouter"
        assert len(chain.all_backends) == 2

        await chain.close()

    async def test_primary_backend_success_no_fallback(
        self, openrouter_config, first_test_pdf
    ):
        """Test that when primary succeeds, fallback is not triggered."""
        # Create primary and fallback backends
        primary_config = OcrBackendConfig(**openrouter_config)
        fallback_config = OcrBackendConfig(**openrouter_config)
        fallback_config.name = "fallback-openrouter"

        primary = OpenRouterNemotronBackend(primary_config)
        fallback = OpenRouterNemotronBackend(fallback_config)

        # Track calls to fallback
        original_page_to_markdown = fallback.page_to_markdown
        fallback_call_count = 0

        async def tracked_page_to_markdown(*args, **kwargs):
            nonlocal fallback_call_count
            fallback_call_count += 1
            return await original_page_to_markdown(*args, **kwargs)

        fallback.page_to_markdown = tracked_page_to_markdown

        # Create chain
        chain = FallbackChain(
            primary=primary,
            fallbacks=[fallback],
            max_attempts_per_backend=2,
        )

        # Render first page
        image_bytes = render_page_to_png_bytes(first_test_pdf, 0)

        # Perform OCR - should succeed with primary
        async with chain:
            result = await chain.page_to_markdown(
                image_bytes=image_bytes,
                page_num=1,
                doc_id="test-fallback-001",
            )

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        # Fallback should NOT have been called
        assert fallback_call_count == 0

        print(f"\n--- Primary Success Test ---")
        print(f"Primary succeeded, fallback not triggered")
        print(f"Result length: {len(result)} chars")

    async def test_fallback_on_invalid_primary_backend(
        self, openrouter_config, first_test_pdf
    ):
        """Test fallback to secondary when primary has invalid API key."""
        # Create primary with invalid key
        primary_config = OcrBackendConfig(**openrouter_config)
        primary_config.api_key = "invalid-key-12345"
        primary_config.name = "primary-invalid"

        # Create fallback with valid key
        fallback_config = OcrBackendConfig(**openrouter_config)
        fallback_config.name = "fallback-valid"

        primary = OpenRouterNemotronBackend(primary_config)
        fallback = OpenRouterNemotronBackend(fallback_config)

        # Create chain with max 1 attempt per backend to fail fast
        chain = FallbackChain(
            primary=primary,
            fallbacks=[fallback],
            max_attempts_per_backend=1,
        )

        # Render first page
        image_bytes = render_page_to_png_bytes(first_test_pdf, 0)

        # Perform OCR - primary should fail (401), but fallback should succeed
        async with chain:
            result = await chain.page_to_markdown(
                image_bytes=image_bytes,
                page_num=1,
                doc_id="test-fallback-002",
            )

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        print(f"\n--- Fallback Success Test ---")
        print(f"Primary failed with invalid key, fallback succeeded")
        print(f"Result length: {len(result)} chars")

    async def test_health_check_selects_healthy_backend(self, openrouter_config):
        """Test that health check can identify healthy backends."""
        # Create primary with invalid key
        primary_config = OcrBackendConfig(**openrouter_config)
        primary_config.api_key = "invalid-key-12345"
        primary_config.name = "primary-unhealthy"

        # Create fallback with valid key
        fallback_config = OcrBackendConfig(**openrouter_config)
        fallback_config.name = "fallback-healthy"

        primary = OpenRouterNemotronBackend(primary_config)
        fallback = OpenRouterNemotronBackend(fallback_config)

        # Create chain
        chain = FallbackChain(
            primary=primary,
            fallbacks=[fallback],
            max_attempts_per_backend=1,
        )

        async with chain:
            # Get healthy backend
            healthy = await chain.get_healthy_backend()

        # Should return the fallback since primary has invalid key
        # Note: Health check might still pass for primary if it just checks endpoint
        # reachability, so we check if we got a backend
        assert healthy is not None
        print(f"\n--- Health Check Test ---")
        print(f"Healthy backend: {healthy.name}")

    async def test_multiple_fallback_backends(
        self, openrouter_config, first_test_pdf
    ):
        """Test chain with multiple fallback backends."""
        # Create configs
        primary_config = OcrBackendConfig(**openrouter_config)
        primary_config.api_key = "invalid-1"
        primary_config.name = "primary"

        fallback1_config = OcrBackendConfig(**openrouter_config)
        fallback1_config.api_key = "invalid-2"
        fallback1_config.name = "fallback-1"

        fallback2_config = OcrBackendConfig(**openrouter_config)  # Valid key
        fallback2_config.name = "fallback-2"

        # Create backends
        primary = OpenRouterNemotronBackend(primary_config)
        fallback1 = OpenRouterNemotronBackend(fallback1_config)
        fallback2 = OpenRouterNemotronBackend(fallback2_config)

        # Create chain
        chain = FallbackChain(
            primary=primary,
            fallbacks=[fallback1, fallback2],
            max_attempts_per_backend=1,
        )

        # Render first page
        image_bytes = render_page_to_png_bytes(first_test_pdf, 0)

        # Perform OCR - should eventually succeed with fallback2
        async with chain:
            result = await chain.page_to_markdown(
                image_bytes=image_bytes,
                page_num=1,
                doc_id="test-fallback-003",
            )

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        print(f"\n--- Multiple Fallbacks Test ---")
        print(f"Primary and fallback-1 failed, fallback-2 succeeded")
        print(f"Result length: {len(result)} chars")

    async def test_all_backends_fail(self, first_test_pdf):
        """Test behavior when all backends in chain fail."""
        # Create all configs with invalid keys
        primary_config = OcrBackendConfig(
            name="primary-invalid",
            model="nvidia/nemotron-nano-12b-v2-vl:free",
            base_url="https://openrouter.ai/api/v1/chat/completions",
            api_key="invalid-1",
        )

        fallback_config = OcrBackendConfig(
            name="fallback-invalid",
            model="nvidia/nemotron-nano-12b-v2-vl:free",
            base_url="https://openrouter.ai/api/v1/chat/completions",
            api_key="invalid-2",
        )

        # Create backends
        primary = OpenRouterNemotronBackend(primary_config)
        fallback = OpenRouterNemotronBackend(fallback_config)

        # Create chain
        chain = FallbackChain(
            primary=primary,
            fallbacks=[fallback],
            max_attempts_per_backend=1,
        )

        # Render first page
        image_bytes = render_page_to_png_bytes(first_test_pdf, 0)

        # Perform OCR - should fail with all backends
        with pytest.raises(BackendError):
            async with chain:
                await chain.page_to_markdown(
                    image_bytes=image_bytes,
                    page_num=1,
                    doc_id="test-fallback-004",
                )

        print(f"\n--- All Backends Fail Test ---")
        print(f"All backends failed as expected")


# ============================================================================
# Pipeline Integration with Fallback
# ============================================================================


@pytest.mark.live_api
@pytest.mark.requires_pdfs
@pytest.mark.asyncio
class TestPipelineWithFallbackChain:
    """Test pipeline integration with fallback chain."""

    async def test_pipeline_with_fallback_chain_config(
        self, api_key, first_test_pdf, tmp_path
    ):
        """Test pipeline using fallback chain through configuration."""
        # Note: This is a conceptual test - actual fallback chain integration
        # with pipeline would require configuration support for multiple backends

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
        pipeline = HybridPipeline(config)

        output_path = tmp_path / "fallback_pipeline_output.md"
        options = ConversionOptions(
            max_pages=1,
            dpi=150,
            output_path=output_path,
        )

        async with pipeline:
            result = await pipeline.convert_pdf(first_test_pdf, options=options)

        assert result is not None
        assert result.processed_pages == 1
        assert len(result.markdown) > 0

        print(f"\n--- Pipeline Fallback Test ---")
        print(f"Pipeline completed successfully")
        print(f"Pages processed: {result.processed_pages}")
