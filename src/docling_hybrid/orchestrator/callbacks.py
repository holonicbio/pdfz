"""Concrete implementations of progress callbacks.

This module provides ready-to-use implementations of the ProgressCallback
protocol for common use cases.

Implementations:
- ConsoleProgressCallback: Rich console progress display
- FileProgressCallback: Write progress to file for external monitoring
- CompositeProgressCallback: Combine multiple callbacks

Usage:
    from docling_hybrid.orchestrator.callbacks import (
        ConsoleProgressCallback,
        FileProgressCallback,
        CompositeProgressCallback,
    )

    # Console progress
    console = ConsoleProgressCallback(verbose=True)

    # File logging
    file_cb = FileProgressCallback(Path("progress.log"))

    # Combine multiple
    composite = CompositeProgressCallback([console, file_cb])

    result = await pipeline.convert_pdf(pdf_path, progress_callback=composite)
"""

import json
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from docling_hybrid.common.logging import get_logger
from docling_hybrid.common.models import PageResult
from docling_hybrid.orchestrator.models import ConversionResult

logger = get_logger(__name__)


class ConsoleProgressCallback:
    """Rich console progress display.

    Displays a progress bar with live updates during conversion.
    Uses the Rich library for beautiful terminal output.

    Attributes:
        console: Rich console instance
        verbose: Whether to show detailed per-page information
        progress: Rich Progress instance
        task: Current task ID

    Example:
        >>> callback = ConsoleProgressCallback(verbose=True)
        >>> result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)
        Converting document... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 10/10 100% 0:00:42
    """

    def __init__(
        self,
        console: Console | None = None,
        verbose: bool = False,
    ) -> None:
        """Initialize console progress callback.

        Args:
            console: Rich Console instance (creates new if None)
            verbose: Show detailed per-page information
        """
        self.console = console or Console()
        self.verbose = verbose
        self.progress: Progress | None = None
        self.task: TaskID | None = None
        self._start_time: float = 0.0

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        """Start progress bar."""
        self._start_time = time.time()

        # Create progress bar
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

        self.progress.start()
        self.task = self.progress.add_task(
            f"Converting document ({doc_id[:8]})",
            total=total_pages,
        )

        if self.verbose:
            self.console.print(
                f"[bold green]Starting conversion[/bold green] - {total_pages} pages"
            )

    def on_page_start(self, page_num: int, total: int) -> None:
        """Update progress bar for page start."""
        if self.verbose and self.progress:
            self.progress.console.print(
                f"  [cyan]Processing page {page_num}/{total}...[/cyan]"
            )

    def on_page_complete(
        self,
        page_num: int,
        total: int,
        result: PageResult,
    ) -> None:
        """Update progress bar for page completion."""
        if self.progress and self.task is not None:
            self.progress.update(self.task, advance=1)

        if self.verbose:
            chars = len(result.content)
            self.console.print(
                f"    [green]✓[/green] Page {page_num} complete "
                f"({chars} chars)"
            )

    def on_page_error(self, page_num: int, error: Exception) -> None:
        """Display page error."""
        if self.progress and self.task is not None:
            self.progress.update(self.task, advance=1)

        error_msg = str(error)
        if len(error_msg) > 60:
            error_msg = error_msg[:57] + "..."

        self.console.print(
            f"    [red]✗[/red] Page {page_num} failed: {error_msg}",
        )

    def on_conversion_complete(self, result: ConversionResult) -> None:
        """Stop progress bar and show summary."""
        if self.progress:
            self.progress.stop()

        elapsed = time.time() - self._start_time
        pages_per_sec = result.processed_pages / elapsed if elapsed > 0 else 0

        self.console.print()
        self.console.print(
            f"[bold green]✓ Conversion complete![/bold green]"
        )
        self.console.print(
            f"  Processed: {result.processed_pages}/{result.total_pages} pages"
        )
        self.console.print(f"  Time: {elapsed:.1f}s ({pages_per_sec:.2f} pages/s)")
        self.console.print(f"  Output: {result.output_path}")

    def on_conversion_error(self, error: Exception) -> None:
        """Display conversion error."""
        if self.progress:
            self.progress.stop()

        self.console.print()
        self.console.print(
            f"[bold red]✗ Conversion failed:[/bold red] {error}"
        )


class FileProgressCallback:
    """Write progress to file for external monitoring.

    Writes JSON-formatted progress updates to a file. Each event is
    written as a single line with timestamp and event data.

    This is useful for:
    - Long-running batch jobs
    - External monitoring systems
    - Audit trails

    Attributes:
        file_path: Path to progress log file
        file_handle: Open file handle

    Example:
        >>> callback = FileProgressCallback(Path("progress.log"))
        >>> result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)

        # progress.log contents:
        # {"timestamp": "2024-01-15T10:30:00", "event": "conversion_start", ...}
        # {"timestamp": "2024-01-15T10:30:02", "event": "page_complete", ...}
        # ...
    """

    def __init__(self, file_path: Path, append: bool = True) -> None:
        """Initialize file progress callback.

        Args:
            file_path: Path to write progress events
            append: If True, append to existing file; if False, overwrite
        """
        self.file_path = file_path
        self.file_handle = open(
            file_path,
            "a" if append else "w",
            encoding="utf-8",
        )
        self._start_time: float = 0.0

    def _write_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Write an event to the log file.

        Args:
            event_type: Type of event (e.g., "conversion_start")
            data: Event data
        """
        event = {
            "timestamp": time.time(),
            "event": event_type,
            **data,
        }
        self.file_handle.write(json.dumps(event) + "\n")
        self.file_handle.flush()

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        """Log conversion start."""
        self._start_time = time.time()
        self._write_event(
            "conversion_start",
            {"doc_id": doc_id, "total_pages": total_pages},
        )

    def on_page_start(self, page_num: int, total: int) -> None:
        """Log page start."""
        self._write_event(
            "page_start",
            {"page_num": page_num, "total": total},
        )

    def on_page_complete(
        self,
        page_num: int,
        total: int,
        result: PageResult,
    ) -> None:
        """Log page completion."""
        self._write_event(
            "page_complete",
            {
                "page_num": page_num,
                "total": total,
                "content_length": len(result.content),
                "backend": result.backend_name,
            },
        )

    def on_page_error(self, page_num: int, error: Exception) -> None:
        """Log page error."""
        self._write_event(
            "page_error",
            {
                "page_num": page_num,
                "error": str(error),
                "error_type": type(error).__name__,
            },
        )

    def on_conversion_complete(self, result: ConversionResult) -> None:
        """Log conversion completion."""
        elapsed = time.time() - self._start_time
        self._write_event(
            "conversion_complete",
            {
                "doc_id": result.doc_id,
                "processed_pages": result.processed_pages,
                "total_pages": result.total_pages,
                "elapsed_seconds": round(elapsed, 2),
                "output_path": str(result.output_path),
            },
        )

    def on_conversion_error(self, error: Exception) -> None:
        """Log conversion error."""
        elapsed = time.time() - self._start_time
        self._write_event(
            "conversion_error",
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "elapsed_seconds": round(elapsed, 2),
            },
        )

    def close(self) -> None:
        """Close the file handle."""
        if self.file_handle:
            self.file_handle.close()

    def __del__(self) -> None:
        """Ensure file is closed on deletion."""
        try:
            self.close()
        except Exception:
            pass


class CompositeProgressCallback:
    """Combine multiple progress callbacks.

    Forwards all progress events to multiple callbacks. Useful for
    simultaneously displaying progress and logging to a file.

    Errors in individual callbacks are logged but don't stop other callbacks.

    Attributes:
        callbacks: List of callbacks to forward to

    Example:
        >>> console = ConsoleProgressCallback()
        >>> file = FileProgressCallback(Path("progress.log"))
        >>> composite = CompositeProgressCallback([console, file])
        >>> result = await pipeline.convert_pdf(pdf_path, progress_callback=composite)
    """

    def __init__(self, callbacks: list[Any]) -> None:
        """Initialize composite callback.

        Args:
            callbacks: List of callback instances to forward to
        """
        self.callbacks = callbacks

    def _call_all(self, method_name: str, *args, **kwargs) -> None:
        """Call a method on all callbacks.

        Args:
            method_name: Name of method to call
            *args: Positional arguments to pass
            **kwargs: Keyword arguments to pass
        """
        for callback in self.callbacks:
            try:
                method = getattr(callback, method_name, None)
                if method and callable(method):
                    method(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "callback_error",
                    callback=type(callback).__name__,
                    method=method_name,
                    error=str(e),
                )

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        """Forward to all callbacks."""
        self._call_all("on_conversion_start", doc_id, total_pages)

    def on_page_start(self, page_num: int, total: int) -> None:
        """Forward to all callbacks."""
        self._call_all("on_page_start", page_num, total)

    def on_page_complete(
        self,
        page_num: int,
        total: int,
        result: PageResult,
    ) -> None:
        """Forward to all callbacks."""
        self._call_all("on_page_complete", page_num, total, result)

    def on_page_error(self, page_num: int, error: Exception) -> None:
        """Forward to all callbacks."""
        self._call_all("on_page_error", page_num, error)

    def on_conversion_complete(self, result: ConversionResult) -> None:
        """Forward to all callbacks."""
        self._call_all("on_conversion_complete", result)

    def on_conversion_error(self, error: Exception) -> None:
        """Forward to all callbacks."""
        self._call_all("on_conversion_error", error)
