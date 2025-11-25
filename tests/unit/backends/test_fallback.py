"""Unit tests for backend fallback chain.

Tests cover:
- Chain initialization
- Fallback triggering logic
- Error type handling
- Backend switching
- Health checking
- All OcrVlmBackend interface methods
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from docling_hybrid.backends.fallback import FallbackChain
from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendError,
    BackendResponseError,
    BackendTimeoutError,
)
from docling_hybrid.common.models import OcrBackendConfig


# ============================================================================
# Mock Backend
# ============================================================================


class MockBackend(OcrVlmBackend):
    """Mock backend for testing."""

    def __init__(self, name: str, should_fail: bool = False):
        """Initialize mock backend."""
        config = OcrBackendConfig(
            name=name,
            model="test-model",
            base_url="http://localhost:8000",
        )
        super().__init__(config)
        self.should_fail = should_fail
        self.call_count = 0
        self.close_called = False

    async def page_to_markdown(self, image_bytes: bytes, page_num: int, doc_id: str) -> str:
        """Mock page_to_markdown."""
        self.call_count += 1
        if self.should_fail:
            raise BackendConnectionError("Mock connection error", backend_name=self.name)
        return f"# Page {page_num} from {self.name}"

    async def table_to_markdown(self, image_bytes: bytes, meta: dict) -> str:
        """Mock table_to_markdown."""
        self.call_count += 1
        if self.should_fail:
            raise BackendTimeoutError("Mock timeout", backend_name=self.name)
        return f"| Table from {self.name} |"

    async def formula_to_latex(self, image_bytes: bytes, meta: dict) -> str:
        """Mock formula_to_latex."""
        self.call_count += 1
        if self.should_fail:
            raise BackendResponseError("Mock server error", backend_name=self.name, status_code=500)
        return f"formula_{self.name}"

    async def health_check(self) -> bool:
        """Mock health check."""
        return not self.should_fail

    async def close(self) -> None:
        """Mock close."""
        self.close_called = True


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_image():
    """Sample image bytes."""
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


@pytest.fixture
def primary_backend():
    """Create primary backend."""
    return MockBackend("primary")


@pytest.fixture
def fallback_backend():
    """Create fallback backend."""
    return MockBackend("fallback")


@pytest.fixture
def failing_primary():
    """Create failing primary backend."""
    return MockBackend("primary", should_fail=True)


@pytest.fixture
def simple_chain(primary_backend, fallback_backend):
    """Create simple fallback chain."""
    return FallbackChain(
        primary=primary_backend,
        fallbacks=[fallback_backend],
        max_attempts_per_backend=2,
    )


# ============================================================================
# Initialization Tests
# ============================================================================


def test_chain_initialization(primary_backend, fallback_backend):
    """Test chain initializes correctly."""
    chain = FallbackChain(
        primary=primary_backend,
        fallbacks=[fallback_backend],
        max_attempts_per_backend=2,
    )

    assert chain.primary == primary_backend
    assert chain.fallbacks == [fallback_backend]
    assert chain.max_attempts_per_backend == 2
    assert len(chain.all_backends) == 2
    assert chain.all_backends[0] == primary_backend
    assert chain.all_backends[1] == fallback_backend


def test_chain_initialization_no_fallbacks(primary_backend):
    """Test chain with no fallbacks."""
    chain = FallbackChain(primary=primary_backend)

    assert chain.primary == primary_backend
    assert chain.fallbacks == []
    assert len(chain.all_backends) == 1


def test_chain_initialization_multiple_fallbacks(primary_backend):
    """Test chain with multiple fallbacks."""
    fallback1 = MockBackend("fallback1")
    fallback2 = MockBackend("fallback2")

    chain = FallbackChain(
        primary=primary_backend,
        fallbacks=[fallback1, fallback2],
    )

    assert len(chain.all_backends) == 3
    assert chain.all_backends[1] == fallback1
    assert chain.all_backends[2] == fallback2


def test_chain_name(simple_chain):
    """Test chain name property."""
    assert simple_chain.name == "fallback_chain(primary)"


def test_chain_config(simple_chain, primary_backend):
    """Test chain config property."""
    assert simple_chain.config == primary_backend.config


# ============================================================================
# Fallback Decision Tests
# ============================================================================


def test_should_fallback_connection_error(simple_chain):
    """Test fallback on connection error."""
    error = BackendConnectionError("Connection failed", backend_name="test")
    assert simple_chain._should_fallback(error) is True


def test_should_fallback_timeout_error(simple_chain):
    """Test fallback on timeout error."""
    error = BackendTimeoutError("Timeout", backend_name="test")
    assert simple_chain._should_fallback(error) is True


def test_should_fallback_server_error(simple_chain):
    """Test fallback on 5xx server error."""
    error = BackendResponseError("Server error", backend_name="test", status_code=500)
    assert simple_chain._should_fallback(error) is True


def test_should_fallback_rate_limit(simple_chain):
    """Test fallback on rate limit (429)."""
    error = BackendResponseError("Rate limited", backend_name="test", status_code=429)
    assert simple_chain._should_fallback(error) is True


def test_should_not_fallback_auth_error(simple_chain):
    """Test no fallback on auth errors."""
    error_401 = BackendResponseError("Unauthorized", backend_name="test", status_code=401)
    assert simple_chain._should_fallback(error_401) is False

    error_403 = BackendResponseError("Forbidden", backend_name="test", status_code=403)
    assert simple_chain._should_fallback(error_403) is False


def test_should_not_fallback_client_error(simple_chain):
    """Test no fallback on 4xx client errors."""
    error = BackendResponseError("Bad request", backend_name="test", status_code=400)
    assert simple_chain._should_fallback(error) is False


def test_should_not_fallback_non_backend_error(simple_chain):
    """Test no fallback on non-backend errors."""
    error = ValueError("Invalid input")
    assert simple_chain._should_fallback(error) is False


# ============================================================================
# Page to Markdown Tests
# ============================================================================


@pytest.mark.asyncio
async def test_page_to_markdown_primary_succeeds(simple_chain, sample_image, primary_backend):
    """Test successful conversion with primary backend."""
    result = await simple_chain.page_to_markdown(sample_image, 1, "doc-123")

    assert result == "# Page 1 from primary"
    assert primary_backend.call_count == 1


@pytest.mark.asyncio
async def test_page_to_markdown_fallback_succeeds(failing_primary, fallback_backend, sample_image):
    """Test fallback to secondary backend."""
    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[fallback_backend],
        max_attempts_per_backend=1,
    )

    result = await chain.page_to_markdown(sample_image, 1, "doc-123")

    assert result == "# Page 1 from fallback"
    assert failing_primary.call_count == 1
    assert fallback_backend.call_count == 1


@pytest.mark.asyncio
async def test_page_to_markdown_all_fail(sample_image):
    """Test all backends failing."""
    failing_primary = MockBackend("primary", should_fail=True)
    failing_fallback = MockBackend("fallback", should_fail=True)

    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[failing_fallback],
        max_attempts_per_backend=1,
    )

    with pytest.raises(BackendConnectionError):
        await chain.page_to_markdown(sample_image, 1, "doc-123")


@pytest.mark.asyncio
async def test_page_to_markdown_multiple_attempts(sample_image):
    """Test multiple attempts per backend."""
    failing_primary = MockBackend("primary", should_fail=True)
    fallback = MockBackend("fallback")

    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[fallback],
        max_attempts_per_backend=3,
    )

    result = await chain.page_to_markdown(sample_image, 1, "doc-123")

    # Primary should be tried 3 times before fallback
    assert failing_primary.call_count == 3
    assert fallback.call_count == 1
    assert result == "# Page 1 from fallback"


# ============================================================================
# Table to Markdown Tests
# ============================================================================


@pytest.mark.asyncio
async def test_table_to_markdown_primary_succeeds(simple_chain, sample_image, primary_backend):
    """Test table conversion with primary backend."""
    result = await simple_chain.table_to_markdown(
        sample_image,
        {"doc_id": "doc-123", "page_num": 1}
    )

    assert result == "| Table from primary |"
    assert primary_backend.call_count == 1


@pytest.mark.asyncio
async def test_table_to_markdown_fallback(failing_primary, fallback_backend, sample_image):
    """Test table conversion with fallback."""
    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[fallback_backend],
        max_attempts_per_backend=1,
    )

    result = await chain.table_to_markdown(
        sample_image,
        {"doc_id": "doc-123", "page_num": 1}
    )

    assert result == "| Table from fallback |"
    assert fallback_backend.call_count == 1


# ============================================================================
# Formula to LaTeX Tests
# ============================================================================


@pytest.mark.asyncio
async def test_formula_to_latex_primary_succeeds(simple_chain, sample_image, primary_backend):
    """Test formula conversion with primary backend."""
    result = await simple_chain.formula_to_latex(
        sample_image,
        {"doc_id": "doc-123", "page_num": 1}
    )

    assert result == "formula_primary"
    assert primary_backend.call_count == 1


@pytest.mark.asyncio
async def test_formula_to_latex_fallback(failing_primary, fallback_backend, sample_image):
    """Test formula conversion with fallback."""
    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[fallback_backend],
        max_attempts_per_backend=1,
    )

    result = await chain.formula_to_latex(
        sample_image,
        {"doc_id": "doc-123", "page_num": 1}
    )

    assert result == "formula_fallback"
    assert fallback_backend.call_count == 1


# ============================================================================
# Health Check Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_healthy_backend_primary_healthy(simple_chain, primary_backend):
    """Test getting healthy backend when primary is healthy."""
    result = await simple_chain.get_healthy_backend()

    assert result == primary_backend


@pytest.mark.asyncio
async def test_get_healthy_backend_fallback_healthy(failing_primary, fallback_backend):
    """Test getting healthy backend when primary unhealthy."""
    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[fallback_backend],
    )

    result = await chain.get_healthy_backend()

    assert result == fallback_backend


@pytest.mark.asyncio
async def test_get_healthy_backend_all_unhealthy():
    """Test when all backends are unhealthy."""
    failing_primary = MockBackend("primary", should_fail=True)
    failing_fallback = MockBackend("fallback", should_fail=True)

    chain = FallbackChain(
        primary=failing_primary,
        fallbacks=[failing_fallback],
    )

    result = await chain.get_healthy_backend()

    assert result is None


@pytest.mark.asyncio
async def test_get_healthy_backend_no_health_check():
    """Test with backend that doesn't have health_check method."""
    # Create minimal backend without health_check
    class MinimalBackend(OcrVlmBackend):
        async def page_to_markdown(self, image_bytes, page_num, doc_id):
            return "test"
        async def table_to_markdown(self, image_bytes, meta):
            return "test"
        async def formula_to_latex(self, image_bytes, meta):
            return "test"

    config = OcrBackendConfig(
        name="minimal",
        model="test",
        base_url="http://localhost:8000",
    )
    minimal = MinimalBackend(config)

    chain = FallbackChain(primary=minimal)

    result = await chain.get_healthy_backend()

    # Should assume healthy if no health_check method
    assert result == minimal


# ============================================================================
# Context Manager Tests
# ============================================================================


@pytest.mark.asyncio
async def test_context_manager(primary_backend, fallback_backend):
    """Test chain as async context manager."""
    chain = FallbackChain(
        primary=primary_backend,
        fallbacks=[fallback_backend],
    )

    async with chain as c:
        assert c == chain

    # All backends should be closed
    assert primary_backend.close_called is True
    assert fallback_backend.close_called is True


@pytest.mark.asyncio
async def test_close(primary_backend, fallback_backend):
    """Test closing the chain."""
    chain = FallbackChain(
        primary=primary_backend,
        fallbacks=[fallback_backend],
    )

    await chain.close()

    assert primary_backend.close_called is True
    assert fallback_backend.close_called is True


@pytest.mark.asyncio
async def test_close_with_error():
    """Test closing when a backend raises error."""
    class ErrorBackend(OcrVlmBackend):
        async def page_to_markdown(self, image_bytes, page_num, doc_id):
            return "test"
        async def table_to_markdown(self, image_bytes, meta):
            return "test"
        async def formula_to_latex(self, image_bytes, meta):
            return "test"
        async def close(self):
            raise RuntimeError("Close error")

    config = OcrBackendConfig(
        name="error",
        model="test",
        base_url="http://localhost:8000",
    )
    error_backend = ErrorBackend(config)
    normal_backend = MockBackend("normal")

    chain = FallbackChain(
        primary=error_backend,
        fallbacks=[normal_backend],
    )

    # Should not raise, but log warning
    await chain.close()

    # Normal backend should still be closed
    assert normal_backend.close_called is True


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_chain_with_three_backends(sample_image):
    """Test chain with three backends."""
    failing1 = MockBackend("backend1", should_fail=True)
    failing2 = MockBackend("backend2", should_fail=True)
    working3 = MockBackend("backend3")

    chain = FallbackChain(
        primary=failing1,
        fallbacks=[failing2, working3],
        max_attempts_per_backend=1,
    )

    result = await chain.page_to_markdown(sample_image, 1, "doc-123")

    assert result == "# Page 1 from backend3"
    assert failing1.call_count == 1
    assert failing2.call_count == 1
    assert working3.call_count == 1


@pytest.mark.asyncio
async def test_chain_auth_error_no_fallback(sample_image):
    """Test that auth errors don't trigger fallback."""
    class AuthErrorBackend(MockBackend):
        async def page_to_markdown(self, image_bytes, page_num, doc_id):
            self.call_count += 1
            raise BackendResponseError(
                "Unauthorized",
                backend_name=self.name,
                status_code=401
            )

    primary = AuthErrorBackend("primary")
    fallback = MockBackend("fallback")

    chain = FallbackChain(
        primary=primary,
        fallbacks=[fallback],
        max_attempts_per_backend=1,
    )

    # Should fail immediately without trying fallback
    with pytest.raises(BackendResponseError) as exc_info:
        await chain.page_to_markdown(sample_image, 1, "doc-123")

    assert exc_info.value.status_code == 401
    assert primary.call_count == 1
    assert fallback.call_count == 0  # Should not be called
