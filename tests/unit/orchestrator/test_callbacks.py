"""Unit tests for progress callback implementations.

Tests the concrete callback implementations:
- ConsoleProgressCallback
- FileProgressCallback
- CompositeProgressCallback
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from docling_hybrid.common.models import PageResult
from docling_hybrid.orchestrator.callbacks import (
    CompositeProgressCallback,
    ConsoleProgressCallback,
    FileProgressCallback,
)
from docling_hybrid.orchestrator.models import ConversionResult


class TestConsoleProgressCallback:
    """Test ConsoleProgressCallback."""

    def test_initialization(self):
        """Test callback initializes correctly."""
        callback = ConsoleProgressCallback()
        assert callback.console is not None
        assert callback.verbose is False
        assert callback.progress is None
        assert callback.task is None

    def test_initialization_with_custom_console(self):
        """Test initialization with custom console."""
        custom_console = Console()
        callback = ConsoleProgressCallback(console=custom_console)
        assert callback.console is custom_console

    def test_initialization_verbose(self):
        """Test initialization with verbose mode."""
        callback = ConsoleProgressCallback(verbose=True)
        assert callback.verbose is True

    def test_conversion_start(self):
        """Test on_conversion_start creates progress bar."""
        callback = ConsoleProgressCallback()
        callback.on_conversion_start("doc-123", 10)

        assert callback.progress is not None
        assert callback.task is not None

    def test_page_complete_updates_progress(self):
        """Test on_page_complete updates progress bar."""
        callback = ConsoleProgressCallback()
        callback.on_conversion_start("doc-123", 10)

        page_result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Test Content",
            backend_name="test-backend",
        )

        # Should not raise
        callback.on_page_complete(1, 10, page_result)

    def test_page_error_handles_gracefully(self):
        """Test on_page_error handles errors gracefully."""
        callback = ConsoleProgressCallback()
        callback.on_conversion_start("doc-123", 10)

        # Should not raise
        callback.on_page_error(1, ValueError("Test error"))

    def test_conversion_complete_stops_progress(self):
        """Test on_conversion_complete stops progress bar."""
        callback = ConsoleProgressCallback()
        callback.on_conversion_start("doc-123", 10)

        result = ConversionResult(
            doc_id="doc-123",
            source_path=Path("/test.pdf"),
            output_path=Path("/test.md"),
            markdown="# Test",
            total_pages=10,
            processed_pages=10,
            backend_name="test-backend",
        )

        # Should not raise
        callback.on_conversion_complete(result)

    def test_conversion_error_stops_progress(self):
        """Test on_conversion_error stops progress bar."""
        callback = ConsoleProgressCallback()
        callback.on_conversion_start("doc-123", 10)

        # Should not raise
        callback.on_conversion_error(RuntimeError("Test error"))

    def test_verbose_mode_shows_details(self):
        """Test verbose mode shows detailed output."""
        with patch.object(Console, "print") as mock_print:
            callback = ConsoleProgressCallback(verbose=True)
            callback.on_conversion_start("doc-123", 10)

            # Should have printed start message
            assert mock_print.called


class TestFileProgressCallback:
    """Test FileProgressCallback."""

    def test_initialization(self, tmp_path):
        """Test callback initializes and creates file."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)

        assert callback.file_path == log_file
        assert callback.file_handle is not None

        callback.close()

    def test_conversion_start_writes_event(self, tmp_path):
        """Test on_conversion_start writes to file."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)

        callback.on_conversion_start("doc-123", 10)
        callback.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 1

        event = json.loads(lines[0])
        assert event["event"] == "conversion_start"
        assert event["doc_id"] == "doc-123"
        assert event["total_pages"] == 10
        assert "timestamp" in event

    def test_page_complete_writes_event(self, tmp_path):
        """Test on_page_complete writes to file."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)

        callback.on_conversion_start("doc-123", 10)

        page_result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Test Content",
            backend_name="test-backend",
        )
        callback.on_page_complete(1, 10, page_result)
        callback.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

        event = json.loads(lines[1])
        assert event["event"] == "page_complete"
        assert event["page_num"] == 1
        assert event["total"] == 10
        assert event["content_length"] == len("# Test Content")
        assert event["backend"] == "test-backend"

    def test_page_error_writes_event(self, tmp_path):
        """Test on_page_error writes to file."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)

        callback.on_page_error(1, ValueError("Test error"))
        callback.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 1

        event = json.loads(lines[0])
        assert event["event"] == "page_error"
        assert event["page_num"] == 1
        assert event["error"] == "Test error"
        assert event["error_type"] == "ValueError"

    def test_conversion_complete_writes_event(self, tmp_path):
        """Test on_conversion_complete writes to file."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)

        callback.on_conversion_start("doc-123", 10)

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
        callback.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

        event = json.loads(lines[1])
        assert event["event"] == "conversion_complete"
        assert event["doc_id"] == "doc-123"
        assert event["processed_pages"] == 10
        assert event["total_pages"] == 10

    def test_conversion_error_writes_event(self, tmp_path):
        """Test on_conversion_error writes to file."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)

        callback.on_conversion_start("doc-123", 10)
        callback.on_conversion_error(RuntimeError("Test error"))
        callback.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

        event = json.loads(lines[1])
        assert event["event"] == "conversion_error"
        assert event["error"] == "Test error"
        assert event["error_type"] == "RuntimeError"

    def test_append_mode(self, tmp_path):
        """Test append mode preserves existing content."""
        log_file = tmp_path / "progress.log"

        # First callback
        callback1 = FileProgressCallback(log_file, append=False)
        callback1.on_conversion_start("doc-123", 10)
        callback1.close()

        # Second callback in append mode
        callback2 = FileProgressCallback(log_file, append=True)
        callback2.on_conversion_start("doc-456", 5)
        callback2.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

    def test_overwrite_mode(self, tmp_path):
        """Test overwrite mode replaces existing content."""
        log_file = tmp_path / "progress.log"

        # First callback
        callback1 = FileProgressCallback(log_file, append=False)
        callback1.on_conversion_start("doc-123", 10)
        callback1.close()

        # Second callback in overwrite mode
        callback2 = FileProgressCallback(log_file, append=False)
        callback2.on_conversion_start("doc-456", 5)
        callback2.close()

        # Read and verify
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["doc_id"] == "doc-456"


class TestCompositeProgressCallback:
    """Test CompositeProgressCallback."""

    def test_initialization(self):
        """Test callback initializes with empty list."""
        callback = CompositeProgressCallback([])
        assert callback.callbacks == []

    def test_forwards_to_single_callback(self, tmp_path):
        """Test forwarding to a single callback."""
        log_file = tmp_path / "progress.log"
        file_callback = FileProgressCallback(log_file)

        composite = CompositeProgressCallback([file_callback])
        composite.on_conversion_start("doc-123", 10)

        file_callback.close()

        # Verify event was forwarded
        content = log_file.read_text()
        assert "conversion_start" in content

    def test_forwards_to_multiple_callbacks(self, tmp_path):
        """Test forwarding to multiple callbacks."""
        log_file1 = tmp_path / "progress1.log"
        log_file2 = tmp_path / "progress2.log"

        callback1 = FileProgressCallback(log_file1)
        callback2 = FileProgressCallback(log_file2)

        composite = CompositeProgressCallback([callback1, callback2])
        composite.on_conversion_start("doc-123", 10)

        callback1.close()
        callback2.close()

        # Verify both received the event
        assert "conversion_start" in log_file1.read_text()
        assert "conversion_start" in log_file2.read_text()

    def test_handles_callback_errors(self, tmp_path):
        """Test that errors in one callback don't stop others."""

        class ErrorCallback:
            def on_conversion_start(self, doc_id, total_pages):
                raise ValueError("Intentional error")

            def on_page_start(self, page_num, total):
                pass

            def on_page_complete(self, page_num, total, result):
                pass

            def on_page_error(self, page_num, error):
                pass

            def on_conversion_complete(self, result):
                pass

            def on_conversion_error(self, error):
                pass

        log_file = tmp_path / "progress.log"
        good_callback = FileProgressCallback(log_file)
        bad_callback = ErrorCallback()

        composite = CompositeProgressCallback([bad_callback, good_callback])

        # Should not raise, even though bad_callback raises
        composite.on_conversion_start("doc-123", 10)

        good_callback.close()

        # Verify good callback still received the event
        assert "conversion_start" in log_file.read_text()

    def test_forwards_all_events(self, tmp_path):
        """Test that all event types are forwarded."""
        log_file = tmp_path / "progress.log"
        callback = FileProgressCallback(log_file)
        composite = CompositeProgressCallback([callback])

        # Send all events
        composite.on_conversion_start("doc-123", 10)
        composite.on_page_start(1, 10)

        page_result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Test",
            backend_name="test-backend",
        )
        composite.on_page_complete(1, 10, page_result)
        composite.on_page_error(2, ValueError("Test error"))

        result = ConversionResult(
            doc_id="doc-123",
            source_path=Path("/test.pdf"),
            output_path=Path("/test.md"),
            markdown="# Test",
            total_pages=10,
            processed_pages=9,
            backend_name="test-backend",
        )
        composite.on_conversion_complete(result)
        composite.on_conversion_error(RuntimeError("Test error"))

        callback.close()

        # Verify all events were logged
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 6

        events = [json.loads(line) for line in lines]
        event_types = [event["event"] for event in events]

        assert "conversion_start" in event_types
        assert "page_start" in event_types
        assert "page_complete" in event_types
        assert "page_error" in event_types
        assert "conversion_complete" in event_types
        assert "conversion_error" in event_types

    def test_with_console_and_file_callbacks(self, tmp_path):
        """Test combining console and file callbacks."""
        log_file = tmp_path / "progress.log"

        console_callback = ConsoleProgressCallback()
        file_callback = FileProgressCallback(log_file)

        composite = CompositeProgressCallback([console_callback, file_callback])

        # Should not raise
        composite.on_conversion_start("doc-123", 10)

        page_result = PageResult(
            page_num=1,
            doc_id="doc-123",
            content="# Test",
            backend_name="test-backend",
        )
        composite.on_page_complete(1, 10, page_result)

        result = ConversionResult(
            doc_id="doc-123",
            source_path=Path("/test.pdf"),
            output_path=Path("/test.md"),
            markdown="# Test",
            total_pages=10,
            processed_pages=10,
            backend_name="test-backend",
        )
        composite.on_conversion_complete(result)

        file_callback.close()

        # Verify file callback received events
        content = log_file.read_text()
        assert "conversion_start" in content
        assert "page_complete" in content
        assert "conversion_complete" in content
