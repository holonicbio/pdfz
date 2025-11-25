"""Unit tests for the backends module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from docling_hybrid.backends import (
    make_backend,
    list_backends,
    OcrVlmBackend,
    OpenRouterNemotronBackend,
    DeepseekOcrVllmBackend,
    DeepseekOcrMlxBackend,
)
from docling_hybrid.backends.factory import register_backend
from docling_hybrid.common.errors import ConfigurationError
from docling_hybrid.common.models import OcrBackendConfig


class TestBackendFactory:
    """Tests for backend factory."""
    
    def test_list_backends(self):
        """Test listing available backends."""
        backends = list_backends()
        
        assert "nemotron-openrouter" in backends
        assert "deepseek-vllm" in backends
        assert "deepseek-mlx" in backends
    
    def test_make_backend_nemotron(self, with_api_key, backend_config):
        """Test creating Nemotron backend."""
        backend_config.name = "nemotron-openrouter"
        
        backend = make_backend(backend_config)
        
        assert isinstance(backend, OpenRouterNemotronBackend)
        assert backend.name == "nemotron-openrouter"
    
    def test_make_backend_deepseek_vllm(self, backend_config):
        """Test creating DeepSeek vLLM backend (stub)."""
        backend_config.name = "deepseek-vllm"
        
        backend = make_backend(backend_config)
        
        assert isinstance(backend, DeepseekOcrVllmBackend)
    
    def test_make_backend_deepseek_mlx(self, backend_config):
        """Test creating DeepSeek MLX backend (stub)."""
        backend_config.name = "deepseek-mlx"
        
        backend = make_backend(backend_config)
        
        assert isinstance(backend, DeepseekOcrMlxBackend)
    
    def test_make_backend_unknown(self, backend_config):
        """Test creating unknown backend raises error."""
        backend_config.name = "unknown-backend"
        
        with pytest.raises(ConfigurationError) as exc_info:
            make_backend(backend_config)
        
        assert "unknown-backend" in str(exc_info.value)
        assert "available" in str(exc_info.value).lower()
    
    def test_make_backend_case_insensitive(self, with_api_key, backend_config):
        """Test backend names are case-insensitive."""
        backend_config.name = "NEMOTRON-OPENROUTER"
        
        backend = make_backend(backend_config)
        
        assert isinstance(backend, OpenRouterNemotronBackend)


class TestOpenRouterNemotronBackend:
    """Tests for OpenRouter Nemotron backend."""
    
    def test_init_with_api_key_in_config(self, backend_config):
        """Test initialization with API key in config."""
        backend_config.name = "nemotron-openrouter"
        backend_config.api_key = "test-key"
        
        backend = OpenRouterNemotronBackend(backend_config)
        
        assert backend.api_key == "test-key"
    
    def test_init_with_api_key_from_env(self, backend_config, monkeypatch):
        """Test initialization with API key from environment."""
        backend_config.name = "nemotron-openrouter"
        backend_config.api_key = None
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-test-key")
        
        backend = OpenRouterNemotronBackend(backend_config)
        
        assert backend.api_key == "env-test-key"
    
    def test_init_missing_api_key(self, backend_config, clean_env):
        """Test initialization fails without API key."""
        backend_config.name = "nemotron-openrouter"
        backend_config.api_key = None
        
        with pytest.raises(ConfigurationError) as exc_info:
            OpenRouterNemotronBackend(backend_config)
        
        assert "API key" in str(exc_info.value)
    
    def test_encode_image(self, with_api_key, backend_config, sample_image_bytes):
        """Test image encoding to base64."""
        backend_config.name = "nemotron-openrouter"
        backend = OpenRouterNemotronBackend(backend_config)
        
        encoded = backend._encode_image(sample_image_bytes)
        
        assert encoded.startswith("data:image/png;base64,")
        assert len(encoded) > 50
    
    def test_build_messages(self, with_api_key, backend_config, sample_image_bytes):
        """Test message building for API."""
        backend_config.name = "nemotron-openrouter"
        backend = OpenRouterNemotronBackend(backend_config)
        
        messages = backend._build_messages("Test prompt", sample_image_bytes)
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert len(messages[0]["content"]) == 2
        assert messages[0]["content"][0]["type"] == "text"
        assert messages[0]["content"][1]["type"] == "image_url"
    
    def test_extract_content_string(self, with_api_key, backend_config):
        """Test extracting string content from response."""
        backend_config.name = "nemotron-openrouter"
        backend = OpenRouterNemotronBackend(backend_config)
        
        response = {
            "choices": [
                {"message": {"content": "Test content"}}
            ]
        }
        
        content = backend._extract_content(response)
        
        assert content == "Test content"
    
    def test_extract_content_list(self, with_api_key, backend_config):
        """Test extracting list content from response."""
        backend_config.name = "nemotron-openrouter"
        backend = OpenRouterNemotronBackend(backend_config)
        
        response = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"text": "Part 1"},
                            {"text": " Part 2"},
                        ]
                    }
                }
            ]
        }
        
        content = backend._extract_content(response)
        
        assert content == "Part 1 Part 2"
    
    def test_extract_content_no_choices(self, with_api_key, backend_config):
        """Test error when response has no choices."""
        from docling_hybrid.common.errors import BackendResponseError
        
        backend_config.name = "nemotron-openrouter"
        backend = OpenRouterNemotronBackend(backend_config)
        
        response = {"choices": []}
        
        with pytest.raises(BackendResponseError):
            backend._extract_content(response)


class TestDeepseekStubs:
    """Tests for DeepSeek backend stubs."""
    
    @pytest.mark.asyncio
    async def test_vllm_stub_raises(self, backend_config, sample_image_bytes):
        """Test vLLM stub raises NotImplementedError."""
        backend_config.name = "deepseek-vllm"
        backend = DeepseekOcrVllmBackend(backend_config)
        
        with pytest.raises(NotImplementedError):
            await backend.page_to_markdown(sample_image_bytes, 1, "doc-123")
        
        with pytest.raises(NotImplementedError):
            await backend.table_to_markdown(sample_image_bytes, {})
        
        with pytest.raises(NotImplementedError):
            await backend.formula_to_latex(sample_image_bytes, {})
    
    @pytest.mark.asyncio
    async def test_mlx_stub_raises(self, backend_config, sample_image_bytes):
        """Test MLX stub raises NotImplementedError."""
        backend_config.name = "deepseek-mlx"
        backend = DeepseekOcrMlxBackend(backend_config)
        
        with pytest.raises(NotImplementedError):
            await backend.page_to_markdown(sample_image_bytes, 1, "doc-123")


class TestBackendInterface:
    """Tests for backend interface contract."""
    
    def test_backend_is_abstract(self):
        """Test that OcrVlmBackend cannot be instantiated directly."""
        config = OcrBackendConfig(
            name="test",
            model="test",
            base_url="https://test.com",
        )
        
        with pytest.raises(TypeError):
            OcrVlmBackend(config)
    
    def test_backend_repr(self, with_api_key, backend_config):
        """Test backend string representation."""
        backend_config.name = "nemotron-openrouter"
        backend = OpenRouterNemotronBackend(backend_config)
        
        repr_str = repr(backend)
        
        assert "OpenRouterNemotronBackend" in repr_str
        assert "nemotron-openrouter" in repr_str
