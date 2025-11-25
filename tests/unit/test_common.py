"""Unit tests for the common module."""

import pytest

from docling_hybrid.common.ids import (
    generate_id,
    generate_timestamp_id,
    generate_doc_id,
    generate_page_id,
)
from docling_hybrid.common.errors import (
    DoclingHybridError,
    ConfigurationError,
    ValidationError,
    BackendError,
    BackendResponseError,
)
from docling_hybrid.common.models import (
    OcrBackendConfig,
    BackendCandidate,
    PageResult,
    ContentType,
)


class TestIdGeneration:
    """Tests for ID generation utilities."""
    
    def test_generate_id_format(self):
        """Test that generated IDs have correct format."""
        id = generate_id("test")
        
        assert id.startswith("test-")
        parts = id.split("-")
        assert len(parts) == 2
        assert len(parts[1]) == 8  # Default length
    
    def test_generate_id_unique(self):
        """Test that generated IDs are unique."""
        ids = [generate_id("test") for _ in range(100)]
        assert len(set(ids)) == 100
    
    def test_generate_id_custom_length(self):
        """Test custom ID length."""
        id = generate_id("test", length=16)
        parts = id.split("-")
        assert len(parts[1]) == 16
    
    def test_generate_timestamp_id_format(self):
        """Test timestamp ID format."""
        id = generate_timestamp_id("run")
        
        parts = id.split("-")
        assert len(parts) == 3
        assert parts[0] == "run"
        assert parts[1].isdigit()  # Timestamp
        assert len(parts[2]) == 4  # Default random length
    
    def test_generate_doc_id_without_filename(self):
        """Test doc ID generation without filename."""
        id = generate_doc_id()
        assert id.startswith("doc-")
    
    def test_generate_doc_id_with_filename(self):
        """Test doc ID generation with filename."""
        id = generate_doc_id("my_paper.pdf")
        assert id.startswith("doc-my_paper-")
    
    def test_generate_page_id(self):
        """Test page ID generation."""
        page_id = generate_page_id("doc-abc123", 5)
        assert page_id == "doc-abc123:p5"


class TestErrors:
    """Tests for error types."""
    
    def test_docling_hybrid_error_message(self):
        """Test base error message."""
        error = DoclingHybridError("Test error")
        assert str(error) == "Test error"
    
    def test_docling_hybrid_error_with_details(self):
        """Test error with details."""
        error = DoclingHybridError("Test error", details={"key": "value"})
        assert "key=value" in str(error)
        assert error.details == {"key": "value"}
    
    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("Missing config", details={"path": "/test"})
        assert isinstance(error, DoclingHybridError)
        assert "Missing config" in str(error)
    
    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid input")
        assert isinstance(error, DoclingHybridError)
    
    def test_backend_error_with_name(self):
        """Test backend error with name."""
        error = BackendError("Connection failed", backend_name="test-backend")
        assert error.backend_name == "test-backend"
        assert "backend=test-backend" in str(error)
    
    def test_backend_response_error(self):
        """Test backend response error."""
        error = BackendResponseError(
            "Bad response",
            backend_name="test",
            status_code=500,
            response_body="Internal Server Error",
        )
        assert error.status_code == 500
        assert "status_code=500" in str(error)


class TestModels:
    """Tests for data models."""
    
    def test_ocr_backend_config_valid(self):
        """Test valid backend config."""
        config = OcrBackendConfig(
            name="test",
            model="test-model",
            base_url="https://api.test.com/v1",
        )
        
        assert config.name == "test"
        assert config.model == "test-model"
        assert config.temperature == 0.0  # Default
        assert config.max_tokens == 8192  # Default
    
    def test_ocr_backend_config_url_validation(self):
        """Test URL validation."""
        # Valid URLs
        config = OcrBackendConfig(
            name="test",
            model="test",
            base_url="https://api.test.com/v1/",
        )
        # Trailing slash should be removed
        assert config.base_url == "https://api.test.com/v1"
        
        # Invalid URL
        with pytest.raises(ValueError):
            OcrBackendConfig(
                name="test",
                model="test",
                base_url="not-a-url",
            )
    
    def test_ocr_backend_config_temperature_range(self):
        """Test temperature validation."""
        # Valid
        config = OcrBackendConfig(
            name="test",
            model="test",
            base_url="https://api.test.com",
            temperature=1.5,
        )
        assert config.temperature == 1.5
        
        # Invalid (too high)
        with pytest.raises(ValueError):
            OcrBackendConfig(
                name="test",
                model="test",
                base_url="https://api.test.com",
                temperature=3.0,
            )
    
    def test_backend_candidate(self):
        """Test backend candidate model."""
        candidate = BackendCandidate(
            backend_name="test",
            content="# Heading",
            content_type=ContentType.MARKDOWN,
            score=0.95,
        )
        
        assert candidate.backend_name == "test"
        assert candidate.score == 0.95
        assert candidate.content_type == ContentType.MARKDOWN
    
    def test_page_result(self):
        """Test page result model."""
        result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Page 1",
            backend_name="test",
        )
        
        assert result.page_num == 1
        assert result.doc_id == "doc-123"
        assert result.candidates == []  # Default
    
    def test_page_result_validation(self):
        """Test page result validation."""
        # Page number must be >= 1
        with pytest.raises(ValueError):
            PageResult(
                page_num=0,
                doc_id="doc-123",
                content="test",
                backend_name="test",
            )
