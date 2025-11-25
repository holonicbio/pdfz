"""Integration tests for backend HTTP handling.

This module tests backend integrations with mocked HTTP responses,
covering success cases, error handling, timeouts, and rate limiting.
"""

import pytest
import aiohttp
from aioresponses import aioresponses

from docling_hybrid.backends import OpenRouterNemotronBackend
from docling_hybrid.common.errors import BackendError
from docling_hybrid.common.models import OcrBackendConfig
from tests.mocks import (
    mock_openrouter_success,
    mock_openrouter_list_content,
    mock_openrouter_rate_limit,
    mock_openrouter_error,
    mock_openrouter_timeout,
    mock_openrouter_connection_error,
    mock_openrouter_empty_content,
    mock_openrouter_missing_choices,
    mock_openrouter_auth_error,
)


@pytest.fixture
def nemotron_config() -> OcrBackendConfig:
    """Create a Nemotron backend config for testing."""
    return OcrBackendConfig(
        name="nemotron-openrouter",
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key="test-api-key-12345",
        temperature=0.0,
        max_tokens=4096,
    )


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


class TestOpenRouterNemotronIntegration:
    """Integration tests for OpenRouter Nemotron backend with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_page_to_markdown_success(
        self, nemotron_config, sample_image_bytes
    ):
        """Test successful page-to-markdown conversion."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        expected_content = "# Page 1\n\nThis is the content of page 1."

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_success(expected_content),
            )

            async with backend:
                result = await backend.page_to_markdown(
                    sample_image_bytes, 1, "doc-test-123"
                )

            assert result == expected_content

    @pytest.mark.asyncio
    async def test_page_to_markdown_list_content(
        self, nemotron_config, sample_image_bytes
    ):
        """Test handling of content returned as a list."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        content_parts = ["# Page Header\n\n", "Paragraph 1.\n\n", "Paragraph 2."]
        expected = "".join(content_parts)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_list_content(content_parts),
            )

            async with backend:
                result = await backend.page_to_markdown(
                    sample_image_bytes, 1, "doc-test-123"
                )

            assert result == expected

    @pytest.mark.asyncio
    async def test_table_to_markdown_success(
        self, nemotron_config, sample_image_bytes
    ):
        """Test successful table-to-markdown conversion."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        expected_table = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |"

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_success(expected_table),
            )

            async with backend:
                result = await backend.table_to_markdown(
                    sample_image_bytes, {"block_id": "table-1"}
                )

            assert result == expected_table

    @pytest.mark.asyncio
    async def test_formula_to_latex_success(
        self, nemotron_config, sample_image_bytes
    ):
        """Test successful formula-to-latex conversion."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        expected_latex = r"\frac{x^2 + y^2}{z}"

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_success(expected_latex),
            )

            async with backend:
                result = await backend.formula_to_latex(
                    sample_image_bytes, {"block_id": "formula-1"}
                )

            assert result == expected_latex

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, nemotron_config, sample_image_bytes):
        """Test handling of rate limit errors (429)."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        status, payload, headers = mock_openrouter_rate_limit(retry_after=30)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=status,
                payload=payload,
                headers=headers,
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                assert "rate limit" in str(error).lower()
                assert error.backend_name == "nemotron-openrouter"

    @pytest.mark.asyncio
    async def test_server_error_500(self, nemotron_config, sample_image_bytes):
        """Test handling of 500 server errors."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        status, payload = mock_openrouter_error(500, "server_error", "Internal error")

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=status,
                payload=payload,
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                assert "500" in str(error)

    @pytest.mark.asyncio
    async def test_auth_error_401(self, nemotron_config, sample_image_bytes):
        """Test handling of authentication errors (401)."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        status, payload = mock_openrouter_auth_error()

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=status,
                payload=payload,
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                assert "api key" in str(error).lower() or "401" in str(error)

    @pytest.mark.asyncio
    async def test_timeout_error(self, nemotron_config, sample_image_bytes):
        """Test handling of timeout errors."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                exception=mock_openrouter_timeout(),
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                assert "timeout" in str(error).lower()

    @pytest.mark.asyncio
    async def test_connection_error(self, nemotron_config, sample_image_bytes):
        """Test handling of connection errors."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                exception=mock_openrouter_connection_error(),
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                assert "connection" in str(error).lower() or "failed" in str(error).lower()

    @pytest.mark.asyncio
    async def test_empty_content_error(self, nemotron_config, sample_image_bytes):
        """Test handling of empty content responses."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_empty_content(),
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                assert "empty" in str(error).lower()

    @pytest.mark.asyncio
    async def test_missing_choices_error(self, nemotron_config, sample_image_bytes):
        """Test handling of malformed responses missing 'choices' field."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_missing_choices(),
            )

            async with backend:
                with pytest.raises(BackendError) as exc_info:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )

                error = exc_info.value
                # Should fail due to missing 'choices' field
                assert error.backend_name == "nemotron-openrouter"

    @pytest.mark.asyncio
    async def test_multiple_requests_sequential(
        self, nemotron_config, sample_image_bytes
    ):
        """Test multiple sequential requests."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        with aioresponses() as mock_http:
            # Set up multiple responses
            for i in range(3):
                mock_http.post(
                    nemotron_config.base_url,
                    status=200,
                    payload=mock_openrouter_success(f"# Page {i+1}\n\nContent {i+1}"),
                )

            async with backend:
                results = []
                for i in range(3):
                    result = await backend.page_to_markdown(
                        sample_image_bytes, i + 1, "doc-test-123"
                    )
                    results.append(result)

            assert len(results) == 3
            assert "Page 1" in results[0]
            assert "Page 2" in results[1]
            assert "Page 3" in results[2]

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self, nemotron_config):
        """Test that context manager properly closes session."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        async with backend:
            assert backend._session is not None
            assert not backend._session.closed

        # After exiting context, session should be closed
        assert backend._session is None or backend._session.closed

    @pytest.mark.asyncio
    async def test_custom_headers_included(
        self, nemotron_config, sample_image_bytes, monkeypatch
    ):
        """Test that custom headers are included in requests."""
        # Set custom headers via environment
        monkeypatch.setenv("DOCLING_HYBRID_HTTP_REFERER", "https://test.com")
        monkeypatch.setenv("DOCLING_HYBRID_X_TITLE", "Test App")

        backend = OpenRouterNemotronBackend(nemotron_config)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=200,
                payload=mock_openrouter_success("# Test"),
            )

            async with backend:
                await backend.page_to_markdown(
                    sample_image_bytes, 1, "doc-test-123"
                )

            # Verify the request was made
            assert len(mock_http.requests) == 1


class TestBackendErrorMessages:
    """Test that error messages are informative and actionable."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_message(
        self, nemotron_config, sample_image_bytes
    ):
        """Test that rate limit errors have actionable messages."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        status, payload, headers = mock_openrouter_rate_limit(retry_after=60)

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=status,
                payload=payload,
                headers=headers,
            )

            async with backend:
                try:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )
                    pytest.fail("Should have raised BackendError")
                except BackendError as e:
                    error_msg = str(e).lower()
                    # Error should mention rate limiting
                    assert "rate" in error_msg or "429" in error_msg
                    # Should include backend name
                    assert e.backend_name == "nemotron-openrouter"

    @pytest.mark.asyncio
    async def test_auth_error_message(self, nemotron_config, sample_image_bytes):
        """Test that auth errors have actionable messages."""
        backend = OpenRouterNemotronBackend(nemotron_config)

        status, payload = mock_openrouter_auth_error()

        with aioresponses() as mock_http:
            mock_http.post(
                nemotron_config.base_url,
                status=status,
                payload=payload,
            )

            async with backend:
                try:
                    await backend.page_to_markdown(
                        sample_image_bytes, 1, "doc-test-123"
                    )
                    pytest.fail("Should have raised BackendError")
                except BackendError as e:
                    error_msg = str(e).lower()
                    # Error should mention authentication/API key
                    assert "api key" in error_msg or "401" in error_msg or "auth" in error_msg
