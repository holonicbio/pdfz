"""Unit tests for CLI functionality.

Tests the command-line interface including:
- Error handling and hints
- Command argument parsing
- Output formatting
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from docling_hybrid.cli.main import (
    _get_error_hint,
    _handle_docling_error,
    app,
)
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendResponseError,
    BackendTimeoutError,
    ConfigurationError,
    RenderingError,
    ValidationError,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_console():
    """Create a mock Rich console."""
    return MagicMock(spec=Console)


# ============================================================================
# Error Hint Tests
# ============================================================================

class TestErrorHints:
    """Tests for _get_error_hint function."""

    def test_configuration_error_api_key(self):
        """Test hint for missing API key."""
        error = ConfigurationError(
            "Missing OPENROUTER_API_KEY",
            details={"env_var": "OPENROUTER_API_KEY"}
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "API key" in hint
        assert "export OPENROUTER_API_KEY" in hint
        assert "openrouter.ai/keys" in hint

    def test_configuration_error_config_file(self):
        """Test hint for config file errors."""
        error = ConfigurationError("Config file not found")
        hint = _get_error_hint(error)
        assert hint is not None
        assert "config" in hint.lower()
        assert "--config" in hint

    def test_configuration_error_backend(self):
        """Test hint for unknown backend."""
        error = ConfigurationError("Unknown backend: foo")
        hint = _get_error_hint(error)
        assert hint is not None
        assert "backend" in hint.lower()
        assert "docling-hybrid-ocr backends" in hint

    def test_backend_connection_error(self):
        """Test hint for connection errors."""
        error = BackendConnectionError(
            "Cannot connect to API",
            backend_name="nemotron-openrouter"
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "connection" in hint.lower()
        assert "localhost:8000" in hint

    def test_backend_timeout_error(self):
        """Test hint for timeout errors."""
        error = BackendTimeoutError(
            "Request timed out",
            backend_name="nemotron-openrouter"
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "timeout" in hint.lower() or "too long" in hint.lower()
        assert "--dpi" in hint
        assert "--max-pages" in hint

    def test_backend_response_error_rate_limit(self):
        """Test hint for rate limit (429) errors."""
        error = BackendResponseError(
            "Rate limit exceeded",
            backend_name="nemotron-openrouter",
            status_code=429
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "rate limit" in hint.lower()
        assert "wait" in hint.lower()

    def test_backend_response_error_auth(self):
        """Test hint for auth (401/403) errors."""
        for status in [401, 403]:
            error = BackendResponseError(
                "Authentication failed",
                backend_name="nemotron-openrouter",
                status_code=status
            )
            hint = _get_error_hint(error)
            assert hint is not None
            assert "auth" in hint.lower() or "key" in hint.lower()
            assert "OPENROUTER_API_KEY" in hint

    def test_backend_response_error_server(self):
        """Test hint for server (5xx) errors."""
        error = BackendResponseError(
            "Internal server error",
            backend_name="nemotron-openrouter",
            status_code=500
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "server error" in hint.lower()
        assert "wait" in hint.lower()
        assert "status.openrouter.ai" in hint

    def test_rendering_error(self):
        """Test hint for rendering errors."""
        error = RenderingError(
            "Failed to render page",
            details={"page": 1}
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "rendering" in hint.lower() or "PDF" in hint
        assert "--dpi" in hint

    def test_validation_error_file_not_found(self):
        """Test hint for file not found errors."""
        error = ValidationError(
            "File not found: test.pdf",
            details={"path": "test.pdf"}
        )
        hint = _get_error_hint(error)
        assert hint is not None
        assert "not found" in hint.lower()
        assert "ls" in hint

    def test_generic_error_no_hint(self):
        """Test that generic errors return None."""
        from docling_hybrid.common.errors import DoclingHybridError
        error = DoclingHybridError("Generic error")
        hint = _get_error_hint(error)
        assert hint is None


# ============================================================================
# Error Handler Tests
# ============================================================================

class TestErrorHandler:
    """Tests for _handle_docling_error function."""

    def test_handles_error_with_hint(self, mock_console):
        """Test error handling with actionable hint."""
        error = ConfigurationError(
            "Missing API key",
            details={"env_var": "OPENROUTER_API_KEY"}
        )
        _handle_docling_error(error, mock_console, verbose=False)

        # Check that error message was printed
        assert mock_console.print.called
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)

        # Should contain error message
        assert "Missing API key" in output

        # Should contain hint
        assert "💡" in output or "Hint" in output

    def test_handles_error_with_details(self, mock_console):
        """Test error handling with details."""
        error = BackendResponseError(
            "API error",
            backend_name="nemotron-openrouter",
            status_code=500,
            details={"url": "https://api.example.com"}
        )
        _handle_docling_error(error, mock_console, verbose=False)

        assert mock_console.print.called
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)

        # Should contain details
        assert "Details" in output or "url" in output

    def test_handles_error_verbose(self, mock_console):
        """Test error handling in verbose mode."""
        error = ConfigurationError("Test error")
        _handle_docling_error(error, mock_console, verbose=True)

        assert mock_console.print.called
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)

        # Should contain verbose details
        assert "ConfigurationError" in output or "Full error" in output


# ============================================================================
# CLI Command Tests
# ============================================================================

class TestCLICommands:
    """Tests for CLI commands."""

    def test_version_flag(self, cli_runner):
        """Test --version flag."""
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "docling-hybrid-ocr version" in result.stdout

    def test_backends_command(self, cli_runner):
        """Test backends command."""
        result = cli_runner.invoke(app, ["backends"])
        assert result.exit_code == 0
        assert "nemotron-openrouter" in result.stdout
        assert "deepseek-vllm" in result.stdout
        assert "deepseek-mlx" in result.stdout

    def test_info_command(self, cli_runner):
        """Test info command."""
        result = cli_runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "Docling Hybrid OCR" in result.stdout
        assert "Version" in result.stdout
        assert "OPENROUTER_API_KEY" in result.stdout

    def test_info_command_with_api_key(self, cli_runner, monkeypatch):
        """Test info command shows API key status."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        result = cli_runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "✓ Set" in result.stdout or "Set" in result.stdout

    def test_info_command_without_api_key(self, cli_runner, monkeypatch):
        """Test info command shows missing API key."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        result = cli_runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "✗" in result.stdout or "Not set" in result.stdout

    def test_convert_missing_pdf(self, cli_runner):
        """Test convert command with non-existent PDF."""
        result = cli_runner.invoke(app, ["convert", "nonexistent.pdf"])
        assert result.exit_code != 0
        # Typer validates file existence before our code runs
        assert "does not exist" in result.stdout.lower() or "error" in result.stdout.lower()

    @patch("docling_hybrid.cli.main.init_config")
    @patch("docling_hybrid.cli.main.setup_logging")
    @patch("docling_hybrid.cli.main.get_page_count")
    @patch("docling_hybrid.cli.main.asyncio.run")
    def test_convert_basic(
        self,
        mock_run,
        mock_get_page_count,
        mock_setup_logging,
        mock_init_config,
        cli_runner,
        tmp_path,
    ):
        """Test basic convert command."""
        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%")

        # Mock the result
        mock_result = MagicMock()
        mock_result.processed_pages = 3
        mock_result.total_pages = 3
        mock_result.backend_name = "nemotron-openrouter"
        mock_result.output_path = tmp_path / "output.md"
        mock_result.metadata = {"elapsed_seconds": 1.5}
        mock_run.return_value = mock_result

        # Mock page count
        mock_get_page_count.return_value = 3

        # Mock config
        mock_config = MagicMock()
        mock_config.logging.level = "INFO"
        mock_config.resources.page_render_dpi = 200
        mock_init_config.return_value = mock_config

        # Run command
        result = cli_runner.invoke(app, ["convert", str(pdf_file)])

        # Check success
        assert result.exit_code == 0
        assert "Converting" in result.stdout
        assert "complete" in result.stdout.lower()

    @patch("docling_hybrid.cli.main.init_config")
    def test_convert_config_error(self, mock_init_config, cli_runner, tmp_path):
        """Test convert command with configuration error."""
        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%")

        # Make init_config raise ConfigurationError
        mock_init_config.side_effect = ConfigurationError(
            "Missing OPENROUTER_API_KEY",
            details={"env_var": "OPENROUTER_API_KEY"}
        )

        # Run command
        result = cli_runner.invoke(app, ["convert", str(pdf_file)])

        # Check failure with helpful error
        assert result.exit_code != 0
        assert "Error" in result.stdout
        assert "API key" in result.stdout or "OPENROUTER_API_KEY" in result.stdout


# ============================================================================
# Integration-style Tests
# ============================================================================

class TestCLIIntegration:
    """Integration-style tests for CLI."""

    def test_convert_with_options(self, cli_runner, tmp_path, monkeypatch):
        """Test convert command with various options."""
        # Set dummy API key
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%")

        # This will fail (no real backend), but we can check option parsing
        result = cli_runner.invoke(app, [
            "convert",
            str(pdf_file),
            "--output", str(tmp_path / "output.md"),
            "--dpi", "150",
            "--max-pages", "5",
            "--start-page", "2",
            "--verbose",
        ])

        # Will fail due to no backend, but options should be parsed
        # The important thing is we tested the option parsing code path
        assert "--output" not in result.stdout  # Options were consumed
        assert "--dpi" not in result.stdout

    def test_help_text(self, cli_runner):
        """Test help text is displayed."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "convert" in result.stdout
        assert "backends" in result.stdout
        assert "info" in result.stdout

    def test_convert_help(self, cli_runner):
        """Test convert command help."""
        result = cli_runner.invoke(app, ["convert", "--help"])
        assert result.exit_code == 0
        assert "PDF" in result.stdout
        assert "Markdown" in result.stdout
        assert "--output" in result.stdout
        assert "--dpi" in result.stdout
        assert "--max-pages" in result.stdout
