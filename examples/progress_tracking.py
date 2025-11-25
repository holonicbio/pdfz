#!/usr/bin/env python3
"""
Progress Tracking Example

This example demonstrates various ways to track conversion progress:
1. Simple progress bar with Rich
2. Real-time page-by-page updates
3. Writing progress to a log file
4. Multiple progress displays (console + file)

Note: Full progress callback support (ProgressCallback protocol) will be
available in Sprint 2. This example shows the current approaches and future API.

Usage:
    python examples/progress_tracking.py document.pdf

Requirements:
    - OPENROUTER_API_KEY environment variable must be set
    - Config file at configs/local.toml (or configs/default.toml)
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import TextIO

from rich.console import Console
from rich.live import Live
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.common.errors import DoclingHybridError
from docling_hybrid.renderer import get_page_count


console = Console()


# =============================================================================
# Example 1: Simple Progress Bar
# =============================================================================

async def example_simple_progress(pdf_path: Path) -> None:
    """
    Simple progress bar showing overall conversion progress.

    Args:
        pdf_path: Path to PDF file
    """
    console.print("\n[bold blue]Example 1: Simple Progress Bar[/bold blue]\n")

    # Initialize
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)

    # Get page count
    total_pages = get_page_count(pdf_path)
    console.print(f"Converting {pdf_path.name} ({total_pages} pages)...\n")

    # Create progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Converting...",
            total=total_pages
        )

        # Convert PDF
        result = await pipeline.convert_pdf(pdf_path)

        # Complete progress
        progress.update(task, completed=total_pages)

    console.print(f"\n✅ Done! Processed {result.processed_pages} pages")


# =============================================================================
# Example 2: Detailed Progress with Statistics
# =============================================================================

async def example_detailed_progress(pdf_path: Path) -> None:
    """
    Show detailed progress with per-page statistics.

    Args:
        pdf_path: Path to PDF file
    """
    console.print("\n[bold blue]Example 2: Detailed Progress with Statistics[/bold blue]\n")

    # Initialize
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)

    # Get page count
    total_pages = get_page_count(pdf_path)

    # Track statistics
    start_time = time.time()
    page_times = []

    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Converting {pdf_path.name}",
            total=total_pages
        )

        # Convert PDF
        result = await pipeline.convert_pdf(pdf_path)

        # Update progress
        progress.update(task, completed=total_pages)

    # Calculate statistics
    elapsed = time.time() - start_time
    pages_per_sec = result.processed_pages / elapsed if elapsed > 0 else 0

    # Display results
    console.print("\n[bold green]Conversion Complete![/bold green]\n")

    # Create statistics table
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total pages", str(result.total_pages))
    table.add_row("Processed pages", str(result.processed_pages))
    table.add_row("Total time", f"{elapsed:.1f}s")
    table.add_row("Pages per second", f"{pages_per_sec:.2f}")
    table.add_row("Avg time per page", f"{elapsed/result.processed_pages:.1f}s")
    table.add_row("Backend", result.backend_name)
    table.add_row("Output size", f"{len(result.markdown)} chars")

    console.print(table)


# =============================================================================
# Example 3: Progress to Log File
# =============================================================================

class FileProgressWriter:
    """Write progress updates to a log file."""

    def __init__(self, log_path: Path):
        """
        Initialize file progress writer.

        Args:
            log_path: Path to log file
        """
        self.log_path = log_path
        self.file: TextIO | None = None
        self.start_time = time.time()

    def __enter__(self) -> "FileProgressWriter":
        """Open log file."""
        self.file = open(self.log_path, "w")
        self.log("Progress log started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close log file."""
        if self.file:
            self.log("Progress log ended")
            self.file.close()

    def log(self, message: str) -> None:
        """Write a log message with timestamp."""
        if self.file:
            elapsed = time.time() - self.start_time
            self.file.write(f"[{elapsed:7.2f}s] {message}\n")
            self.file.flush()

    def log_conversion_start(self, pdf_path: Path, total_pages: int) -> None:
        """Log conversion start."""
        self.log(f"Starting conversion: {pdf_path.name}")
        self.log(f"Total pages: {total_pages}")

    def log_page_complete(self, page_num: int, total: int, chars: int) -> None:
        """Log page completion."""
        progress_pct = (page_num / total) * 100
        self.log(f"Page {page_num}/{total} complete ({progress_pct:.1f}%) - {chars} chars")

    def log_conversion_complete(self, pages: int, total_time: float) -> None:
        """Log conversion completion."""
        self.log(f"Conversion complete: {pages} pages in {total_time:.1f}s")


async def example_file_progress(pdf_path: Path, log_path: Path) -> None:
    """
    Write progress updates to a log file.

    Args:
        pdf_path: Path to PDF file
        log_path: Path to log file
    """
    console.print("\n[bold blue]Example 3: Progress to Log File[/bold blue]\n")
    console.print(f"Log file: {log_path}\n")

    # Initialize
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)

    # Get page count
    total_pages = get_page_count(pdf_path)

    # Open log file
    with FileProgressWriter(log_path) as logger:
        logger.log_conversion_start(pdf_path, total_pages)

        # Show progress in console too
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Converting...", total=total_pages)

            # Convert PDF
            start_time = time.time()
            result = await pipeline.convert_pdf(pdf_path)
            elapsed = time.time() - start_time

            # Log each page result
            for page_result in result.page_results:
                logger.log_page_complete(
                    page_result.page_num,
                    total_pages,
                    len(page_result.content)
                )

            # Complete
            progress.update(task, completed=total_pages)
            logger.log_conversion_complete(result.processed_pages, elapsed)

    console.print(f"\n✅ Done! Check log file: {log_path}")


# =============================================================================
# Example 4: Live Status Display
# =============================================================================

async def example_live_status(pdf_path: Path) -> None:
    """
    Show a live status display that updates in real-time.

    Args:
        pdf_path: Path to PDF file
    """
    console.print("\n[bold blue]Example 4: Live Status Display[/bold blue]\n")

    # Initialize
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)

    # Get page count
    total_pages = get_page_count(pdf_path)

    def create_status_table(
        current_page: int,
        total: int,
        elapsed: float,
        status: str
    ) -> Table:
        """Create a status table."""
        table = Table(title="Conversion Status", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        progress_pct = (current_page / total) * 100 if total > 0 else 0
        pages_per_sec = current_page / elapsed if elapsed > 0 else 0
        eta = (total - current_page) / pages_per_sec if pages_per_sec > 0 else 0

        table.add_row("Status", f"[bold]{status}[/bold]")
        table.add_row("File", pdf_path.name)
        table.add_row("Progress", f"{current_page}/{total} pages ({progress_pct:.1f}%)")
        table.add_row("Elapsed", f"{elapsed:.1f}s")
        table.add_row("Speed", f"{pages_per_sec:.2f} pages/s")
        table.add_row("ETA", f"{eta:.1f}s")

        return table

    # Start conversion with live display
    start_time = time.time()

    with Live(
        create_status_table(0, total_pages, 0, "Starting..."),
        console=console,
        refresh_per_second=4
    ) as live:
        # Simulate progress updates (in real Sprint 2, this will use ProgressCallback)
        live.update(
            create_status_table(0, total_pages, 0, "Converting...")
        )

        # Convert PDF
        result = await pipeline.convert_pdf(pdf_path)

        # Final update
        elapsed = time.time() - start_time
        live.update(
            create_status_table(total_pages, total_pages, elapsed, "Complete")
        )

    console.print(f"\n✅ Done! Processed {result.processed_pages} pages")


# =============================================================================
# Example 5: Future API (Sprint 2 Progress Callbacks)
# =============================================================================

def show_future_api_example() -> None:
    """
    Show what the future progress callback API will look like (Sprint 2).

    This is documentation only - the actual implementation is not yet available.
    """
    console.print("\n[bold blue]Example 5: Future API (Sprint 2)[/bold blue]\n")

    example_code = '''
# This API will be available in Sprint 2 after Dev-03 completes progress callbacks

from docling_hybrid.orchestrator.progress import ProgressCallback
from docling_hybrid.orchestrator.callbacks import ConsoleProgressCallback

class MyProgressCallback(ProgressCallback):
    """Custom progress callback."""

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        print(f"Starting conversion: {doc_id} ({total_pages} pages)")

    def on_page_start(self, page_num: int, total: int) -> None:
        print(f"Processing page {page_num}/{total}...")

    def on_page_complete(self, page_num: int, total: int, result: PageResult) -> None:
        print(f"✓ Page {page_num}/{total} complete")

    def on_page_error(self, page_num: int, error: Exception) -> None:
        print(f"✗ Page {page_num} failed: {error}")

    def on_conversion_complete(self, result: ConversionResult) -> None:
        print(f"Conversion complete: {result.processed_pages} pages")

    def on_conversion_error(self, error: Exception) -> None:
        print(f"Conversion failed: {error}")

# Use the callback
callback = MyProgressCallback()
result = await pipeline.convert_pdf(
    pdf_path,
    progress_callback=callback
)

# Or use built-in callback
from docling_hybrid.orchestrator.callbacks import ConsoleProgressCallback
callback = ConsoleProgressCallback()
result = await pipeline.convert_pdf(
    pdf_path,
    progress_callback=callback
)
'''

    console.print("[yellow]Future API (Sprint 2):[/yellow]")
    console.print(example_code)
    console.print("\n[cyan]This API is not yet implemented. Use Examples 1-4 for current progress tracking.[/cyan]")


# =============================================================================
# Main
# =============================================================================

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[red]Usage: python examples/progress_tracking.py <pdf_file> [example_num][/red]")
        console.print("\nExamples:")
        console.print("  1. Simple progress bar")
        console.print("  2. Detailed progress with statistics")
        console.print("  3. Progress to log file")
        console.print("  4. Live status display")
        console.print("  5. Future API documentation")
        console.print("\nRun all:")
        console.print("  python examples/progress_tracking.py <pdf_file>")
        console.print("\nRun specific example:")
        console.print("  python examples/progress_tracking.py <pdf_file> 2")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    # Check if file exists
    if not pdf_path.exists():
        console.print(f"[red]❌ Error: File not found: {pdf_path}[/red]")
        sys.exit(1)

    # Get example number if provided
    example_num = int(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        if example_num == 1:
            asyncio.run(example_simple_progress(pdf_path))
        elif example_num == 2:
            asyncio.run(example_detailed_progress(pdf_path))
        elif example_num == 3:
            log_path = Path("conversion_progress.log")
            asyncio.run(example_file_progress(pdf_path, log_path))
        elif example_num == 4:
            asyncio.run(example_live_status(pdf_path))
        elif example_num == 5:
            show_future_api_example()
        else:
            # Run all examples
            console.print("[bold]Running all examples...[/bold]")

            asyncio.run(example_simple_progress(pdf_path))
            console.print("\n" + "="*60 + "\n")

            asyncio.run(example_detailed_progress(pdf_path))
            console.print("\n" + "="*60 + "\n")

            log_path = Path("conversion_progress.log")
            asyncio.run(example_file_progress(pdf_path, log_path))
            console.print("\n" + "="*60 + "\n")

            asyncio.run(example_live_status(pdf_path))
            console.print("\n" + "="*60 + "\n")

            show_future_api_example()

    except DoclingHybridError as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(130)

    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
