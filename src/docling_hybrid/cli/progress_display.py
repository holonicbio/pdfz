"""Rich progress display for CLI.

This module provides Rich-based progress displays for:
- Individual file conversion with page-level progress
- Batch processing with file-level progress
- Real-time updates with ETA estimates

Usage:
    from rich.console import Console
    from docling_hybrid.cli.progress_display import BatchProgressDisplay

    console = Console()
    with BatchProgressDisplay(console, total_files=10) as progress:
        for i, pdf_path in enumerate(pdf_files):
            progress.start_file(i, pdf_path)
            # ... conversion ...
            progress.complete_file(i, success=True)
"""

from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


class BatchProgressDisplay:
    """Progress display for batch processing multiple files.

    Shows:
    - Overall progress (files completed/total)
    - Current file being processed
    - Per-file page progress
    - ETA for batch completion

    Attributes:
        console: Rich console for output
        total_files: Total number of files to process
        progress: Rich Progress instance
        batch_task: TaskID for batch progress
        file_tasks: Dict mapping file index to TaskID
    """

    def __init__(self, console: Console, total_files: int) -> None:
        """Initialize batch progress display.

        Args:
            console: Rich console for output
            total_files: Total number of files to process
        """
        self.console = console
        self.total_files = total_files
        self.file_tasks: Dict[int, TaskID] = {}

        # Create progress with batch-specific columns
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.completed}/{task.total} files"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
        )

        # Add batch-level task
        self.batch_task = self.progress.add_task(
            "Processing batch",
            total=total_files,
        )

    def __enter__(self) -> "BatchProgressDisplay":
        """Enter context manager."""
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.progress.__exit__(exc_type, exc_val, exc_tb)

    def start_file(self, file_index: int, pdf_path: Path, total_pages: int | None = None) -> None:
        """Mark a file as started.

        Args:
            file_index: Index of file (0-based)
            pdf_path: Path to PDF file
            total_pages: Total pages in PDF (if known)
        """
        # Create a task for this file
        desc = f"  └─ {pdf_path.name}"
        if total_pages:
            task_id = self.progress.add_task(
                desc,
                total=total_pages,
            )
        else:
            task_id = self.progress.add_task(
                desc,
                total=None,
            )

        self.file_tasks[file_index] = task_id

    def update_file_progress(self, file_index: int, completed_pages: int) -> None:
        """Update progress for a file.

        Args:
            file_index: Index of file (0-based)
            completed_pages: Number of pages completed so far
        """
        if file_index in self.file_tasks:
            task_id = self.file_tasks[file_index]
            self.progress.update(task_id, completed=completed_pages)

    def complete_file(self, file_index: int, success: bool = True, error: str | None = None) -> None:
        """Mark a file as completed.

        Args:
            file_index: Index of file (0-based)
            success: Whether conversion succeeded
            error: Error message if failed
        """
        # Update batch progress
        self.progress.update(self.batch_task, advance=1)

        # Complete file task if it exists
        if file_index in self.file_tasks:
            task_id = self.file_tasks[file_index]

            # Update description with result
            current_desc = self.progress.tasks[task_id].description
            if success:
                new_desc = f"[green]✓[/green] {current_desc}"
            else:
                new_desc = f"[red]✗[/red] {current_desc}"
                if error:
                    # Truncate long errors
                    error_short = error[:50]
                    if len(error) > 50:
                        error_short += "..."
                    new_desc += f" [dim]({error_short})[/dim]"

            self.progress.update(task_id, description=new_desc, completed=100)

            # Remove from tracking
            del self.file_tasks[file_index]


class SingleFileProgressDisplay:
    """Progress display for single file conversion.

    Shows:
    - File name
    - Page-level progress
    - Time elapsed
    - ETA

    Attributes:
        console: Rich console for output
        progress: Rich Progress instance
        file_task: TaskID for file progress
    """

    def __init__(
        self,
        console: Console,
        pdf_path: Path,
        total_pages: int | None = None,
    ) -> None:
        """Initialize single file progress display.

        Args:
            console: Rich console for output
            pdf_path: Path to PDF file
            total_pages: Total pages to process (if known)
        """
        self.console = console
        self.pdf_path = pdf_path

        # Create progress
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )

        # Add file task
        if total_pages:
            self.file_task = self.progress.add_task(
                f"Converting {pdf_path.name}",
                total=total_pages,
            )
        else:
            self.file_task = self.progress.add_task(
                f"Converting {pdf_path.name}",
                total=None,
            )

    def __enter__(self) -> "SingleFileProgressDisplay":
        """Enter context manager."""
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.progress.__exit__(exc_type, exc_val, exc_tb)

    def update(self, completed_pages: int) -> None:
        """Update progress.

        Args:
            completed_pages: Number of pages completed so far
        """
        self.progress.update(self.file_task, completed=completed_pages)

    def complete(self) -> None:
        """Mark conversion as complete."""
        self.progress.update(self.file_task, completed=100)


def print_batch_summary(console: Console, result) -> None:
    """Print a rich summary table for batch results.

    Args:
        console: Rich console for output
        result: BatchResult from convert_batch
    """
    # Create summary table
    table = Table(title="Batch Conversion Results", show_header=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Total Files", str(result.total_files))
    table.add_row("Successful", f"[green]{result.successful}[/green]")
    table.add_row("Failed", f"[red]{result.failed}[/red]" if result.failed > 0 else "0")
    table.add_row("Success Rate", f"{result.success_rate:.1f}%")
    table.add_row("Time Elapsed", f"{result.elapsed_seconds:.1f}s")

    console.print()
    console.print(table)

    # Show failed files if any
    if result.failed > 0:
        console.print("\n[bold red]Failed Files:[/bold red]")
        for file_result in result.file_results:
            if not file_result.success:
                console.print(f"  [red]✗[/red] {file_result.source_path.name}")
                if file_result.error:
                    # Truncate long errors
                    error = file_result.error[:100]
                    if len(file_result.error) > 100:
                        error += "..."
                    console.print(f"    [dim]{error}[/dim]")

    # Show successful files summary
    if result.successful > 0:
        console.print(f"\n[bold green]✓ {result.successful} files converted successfully[/bold green]")

        # Show total pages processed
        total_pages = sum(
            fr.result.processed_pages
            for fr in result.file_results
            if fr.success and fr.result
        )
        console.print(f"  Total pages processed: {total_pages}")


def print_file_result(console: Console, result) -> None:
    """Print a rich summary for single file conversion.

    Args:
        console: Rich console for output
        result: ConversionResult from convert_pdf
    """
    console.print()
    console.print("[bold green]✓ Conversion complete![/bold green]")

    # Create info table
    table = Table(show_header=False, box=None)
    table.add_column("", style="cyan", no_wrap=True)
    table.add_column("", style="white")

    table.add_row("Pages processed", f"{result.processed_pages}/{result.total_pages}")
    table.add_row("Backend", result.backend_name)
    table.add_row("Output", str(result.output_path))
    table.add_row("Time", f"{result.metadata.get('elapsed_seconds', 0):.1f}s")

    console.print(table)
