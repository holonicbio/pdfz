"""Unit tests for progress callback protocol.

Tests the ProgressCallback protocol and helper functions.
"""

import pytest

from docling_hybrid.common.models import PageResult
from docling_hybrid.orchestrator.models import ConversionResult
from docling_hybrid.orchestrator.progress import (
    ProgressCallback,
    is_progress_callback,
)
from pathlib import Path


class TestProgressCallbackProtocol:
    """Test the ProgressCallback protocol."""

    def test_protocol_exists(self):
        """Test that protocol is defined."""
        assert ProgressCallback is not None

    def test_complete_implementation(self):
        """Test that a complete implementation is recognized."""

        class CompleteCallback:
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(
                self, page_num: int, total: int, result: PageResult
            ) -> None:
                pass

            def on_page_error(self, page_num: int, error: Exception) -> None:
                pass

            def on_conversion_complete(self, result: ConversionResult) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = CompleteCallback()
        assert is_progress_callback(callback)

    def test_partial_implementation(self):
        """Test that partial implementations are recognized."""

        class PartialCallback:
            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_complete(
                self, page_num: int, total: int, result: PageResult
            ) -> None:
                pass

            def on_conversion_complete(self, result: ConversionResult) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_error(self, page_num: int, error: Exception) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = PartialCallback()
        assert is_progress_callback(callback)

    def test_non_implementation(self):
        """Test that non-implementations are not recognized."""

        class NotACallback:
            def some_method(self):
                pass

        obj = NotACallback()
        assert not is_progress_callback(obj)

    def test_with_tracking_implementation(self):
        """Test implementation that tracks calls."""

        class TrackingCallback:
            def __init__(self):
                self.events = []

            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                self.events.append(("start", doc_id, total_pages))

            def on_page_start(self, page_num: int, total: int) -> None:
                self.events.append(("page_start", page_num, total))

            def on_page_complete(
                self, page_num: int, total: int, result: PageResult
            ) -> None:
                self.events.append(("page_complete", page_num, total))

            def on_page_error(self, page_num: int, error: Exception) -> None:
                self.events.append(("page_error", page_num, str(error)))

            def on_conversion_complete(self, result: ConversionResult) -> None:
                self.events.append(("complete", result.doc_id))

            def on_conversion_error(self, error: Exception) -> None:
                self.events.append(("error", str(error)))

        callback = TrackingCallback()
        assert is_progress_callback(callback)

        # Test event tracking
        callback.on_conversion_start("doc-123", 10)
        callback.on_page_start(1, 10)

        page_result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Test",
            backend_name="test-backend",
        )
        callback.on_page_complete(1, 10, page_result)

        callback.on_page_error(2, ValueError("Test error"))

        result = ConversionResult(
            doc_id="doc-123",
            source_path=Path("/test.pdf"),
            output_path=Path("/test.md"),
            markdown="# Test",
            total_pages=10,
            processed_pages=9,
            backend_name="test-backend",
        )
        callback.on_conversion_complete(result)

        callback.on_conversion_error(RuntimeError("Test error"))

        # Verify events
        assert len(callback.events) == 6
        assert callback.events[0] == ("start", "doc-123", 10)
        assert callback.events[1] == ("page_start", 1, 10)
        assert callback.events[2] == ("page_complete", 1, 10)
        assert callback.events[3] == ("page_error", 2, "Test error")
        assert callback.events[4] == ("complete", "doc-123")
        assert callback.events[5] == ("error", "Test error")


class TestIsProgressCallback:
    """Test the is_progress_callback helper function."""

    def test_with_none(self):
        """Test that None is not a callback."""
        assert not is_progress_callback(None)

    def test_with_int(self):
        """Test that primitive types are not callbacks."""
        assert not is_progress_callback(42)

    def test_with_string(self):
        """Test that strings are not callbacks."""
        assert not is_progress_callback("not a callback")

    def test_with_dict(self):
        """Test that dicts are not callbacks."""
        assert not is_progress_callback({"key": "value"})

    def test_with_lambda(self):
        """Test that lambdas are not callbacks."""
        assert not is_progress_callback(lambda x: x)


class TestCallbackSignatures:
    """Test that callback methods have correct signatures."""

    def test_on_conversion_start_signature(self):
        """Test on_conversion_start accepts correct arguments."""

        class TestCallback:
            called = False

            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                TestCallback.called = True
                assert isinstance(doc_id, str)
                assert isinstance(total_pages, int)

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(
                self, page_num: int, total: int, result: PageResult
            ) -> None:
                pass

            def on_page_error(self, page_num: int, error: Exception) -> None:
                pass

            def on_conversion_complete(self, result: ConversionResult) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = TestCallback()
        callback.on_conversion_start("doc-123", 10)
        assert TestCallback.called

    def test_on_page_complete_signature(self):
        """Test on_page_complete accepts correct arguments."""

        class TestCallback:
            called = False

            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(
                self, page_num: int, total: int, result: PageResult
            ) -> None:
                TestCallback.called = True
                assert isinstance(page_num, int)
                assert isinstance(total, int)
                assert isinstance(result, PageResult)

            def on_page_error(self, page_num: int, error: Exception) -> None:
                pass

            def on_conversion_complete(self, result: ConversionResult) -> None:
                pass

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = TestCallback()
        page_result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Test",
            backend_name="test-backend",
        )
        callback.on_page_complete(1, 10, page_result)
        assert TestCallback.called

    def test_on_conversion_complete_signature(self):
        """Test on_conversion_complete accepts correct arguments."""

        class TestCallback:
            called = False

            def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
                pass

            def on_page_start(self, page_num: int, total: int) -> None:
                pass

            def on_page_complete(
                self, page_num: int, total: int, result: PageResult
            ) -> None:
                pass

            def on_page_error(self, page_num: int, error: Exception) -> None:
                pass

            def on_conversion_complete(self, result: ConversionResult) -> None:
                TestCallback.called = True
                assert isinstance(result, ConversionResult)

            def on_conversion_error(self, error: Exception) -> None:
                pass

        callback = TestCallback()
        result = ConversionResult(
            doc_id="doc-123",
            source_path=Path("/test.pdf"),
            output_path=Path("/test.md"),
            markdown="# Test",
            total_pages=10,
            processed_pages=10,
            backend_name="test-backend",
        )
        callback.on_conversion_complete(result)
        assert TestCallback.called
