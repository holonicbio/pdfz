"""Main CLI implementation using Typer.

This module implements the command-line interface for docling-hybrid-ocr.

Commands:
    convert: Convert a PDF to Markdown
    backends: List available backends
    version: Show version information
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from docling_hybrid import __version__
from docling_hybrid.backends import list_backends
from docling_hybrid.common.config import init_config
from docling_hybrid.common.errors import (
    BackendConnectionError,
    BackendError,
    BackendResponseError,
    BackendTimeoutError,
    ConfigurationError,
    DoclingHybridError,
    RenderingError,
    ValidationError,
)
from docling_hybrid.common.logging import setup_logging
from docling_hybrid.orchestrator import ConversionOptions, HybridPipeline

# Import batch processing
from docling_hybrid.cli.batch import convert_batch, find_pdf_files
from docling_hybrid.cli.progress_display import BatchProgressDisplay, print_batch_summary

# Create Typer app
app = typer.Typer(
    name="docling-hybrid-ocr",
    help="Convert PDFs to Markdown using hybrid Docling + VLM OCR",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


def _get_error_hint(error: DoclingHybridError) -> str | None:
    """Get actionable hint for an error.

    Args:
        error: The error to get hint for

    Returns:
        Hint string or None if no specific hint
    """
    # Configuration errors
    if isinstance(error, ConfigurationError):
        if "api_key" in error.message.lower() or "openrouter_api_key" in str(error.details).lower():
            return (
                "💡 Hint: Set your OpenRouter API key:\n"
                "   export OPENROUTER_API_KEY=your-key-here\n"
                "   Or add it to .env.local and run: source .env.local\n"
                "   Get a free key at: https://openrouter.ai/keys"
            )
        elif "config" in error.message.lower():
            return (
                "💡 Hint: Check your configuration file path:\n"
                "   --config configs/local.toml\n"
                "   Or use the default config (configs/default.toml)"
            )
        elif "backend" in error.message.lower():
            return (
                "💡 Hint: Check available backends with:\n"
                "   docling-hybrid-ocr backends\n"
                "   Then use: --backend <name>"
            )

    # Backend connection errors
    elif isinstance(error, BackendConnectionError):
        return (
            "💡 Hint: Check your internet connection and try again.\n"
            "   If using a local backend (vLLM/MLX), ensure the server is running:\n"
            "   - vLLM: http://localhost:8000\n"
            "   - Check firewall settings"
        )

    # Backend timeout errors
    elif isinstance(error, BackendTimeoutError):
        return (
            "💡 Hint: The backend is taking too long. Try:\n"
            "   - Using a lower DPI: --dpi 100\n"
            "   - Processing fewer pages: --max-pages 3\n"
            "   - Waiting and trying again (API may be busy)"
        )

    # Backend response errors
    elif isinstance(error, BackendResponseError):
        status = error.details.get("status_code")
        if status == 429:
            return (
                "💡 Hint: Rate limit exceeded. Try:\n"
                "   - Wait a few minutes and try again\n"
                "   - Process fewer pages at once: --max-pages 5\n"
                "   - Check your API usage at OpenRouter dashboard"
            )
        elif status == 401 or status == 403:
            return (
                "💡 Hint: Authentication failed. Check:\n"
                "   - Your API key is correct: echo $OPENROUTER_API_KEY\n"
                "   - The key hasn't expired\n"
                "   - You have permission to use the model"
            )
        elif status and 500 <= status < 600:
            return (
                "💡 Hint: Backend server error. Try:\n"
                "   - Waiting a few minutes and trying again\n"
                "   - Using a different backend: --backend <name>\n"
                "   - Check OpenRouter status: https://status.openrouter.ai"
            )

    # Rendering errors
    elif isinstance(error, RenderingError):
        return (
            "💡 Hint: PDF rendering failed. Try:\n"
            "   - Verify the PDF opens in a PDF viewer\n"
            "   - Use a lower DPI: --dpi 100\n"
            "   - Try a different PDF file\n"
            "   - Check file permissions"
        )

    # Validation errors
    elif isinstance(error, ValidationError):
        if "not found" in error.message.lower() or "does not exist" in error.message.lower():
            return (
                "💡 Hint: File not found. Check:\n"
                "   - The file path is correct\n"
                "   - The file exists: ls <path>\n"
                "   - You have read permissions"
            )

    return None


def _handle_docling_error(error: DoclingHybridError, console: Console, verbose: bool) -> None:
    """Handle and display a Docling error with hints.

    Args:
        error: The error to handle
        console: Rich console for output
        verbose: Whether verbose output is enabled
    """
    # Show error message
    console.print(f"\n[bold red]Error:[/bold red] {error.message}")

    # Show details if present
    if error.details:
        console.print("\n[yellow]Details:[/yellow]")
        for key, value in error.details.items():
            # Skip internal keys
            if key in ("backend",):
                continue
            console.print(f"  {key}: {value}")

    # Show actionable hint
    hint = _get_error_hint(error)
    if hint:
        console.print(f"\n{hint}")

    # In verbose mode, show full exception
    if verbose:
        console.print("\n[dim]Full error details:[/dim]")
        console.print(f"[dim]{repr(error)}[/dim]")


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"docling-hybrid-ocr version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Docling Hybrid OCR - Convert PDFs to Markdown using VLM backends."""
    pass


@app.command()
def convert(
    pdf_path: Path = typer.Argument(
        ...,
        help="Path to the PDF file to convert",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output Markdown file path (default: <input>.nemotron.md)",
    ),
    backend: Optional[str] = typer.Option(
        None,
        "--backend",
        "-b",
        help="Backend to use (default: from config)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
    dpi: Optional[int] = typer.Option(
        None,
        "--dpi",
        help="Page rendering DPI (default: from config)",
        min=72,
        max=600,
    ),
    max_pages: Optional[int] = typer.Option(
        None,
        "--max-pages",
        "-n",
        help="Maximum pages to process (default: all)",
        min=1,
    ),
    start_page: int = typer.Option(
        1,
        "--start-page",
        "-s",
        help="First page to process (1-indexed)",
        min=1,
    ),
    no_page_separators: bool = typer.Option(
        False,
        "--no-separators",
        help="Don't add page separator comments",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging",
    ),
) -> None:
    """Convert a PDF file to Markdown.
    
    Uses the configured VLM backend to perform OCR on each page
    and concatenates the results into a single Markdown file.
    
    Examples:
    
        # Basic conversion
        docling-hybrid-ocr convert document.pdf
        
        # Specify output file
        docling-hybrid-ocr convert document.pdf -o output.md
        
        # Use specific backend
        docling-hybrid-ocr convert document.pdf --backend nemotron-openrouter
        
        # Process only first 5 pages
        docling-hybrid-ocr convert document.pdf --max-pages 5
        
        # Use custom config
        docling-hybrid-ocr convert document.pdf --config configs/local.toml
    """
    try:
        # Initialize configuration
        config = init_config(config_file)
        
        # Setup logging
        log_level = "DEBUG" if verbose else config.logging.level
        log_format = "text"  # Always use text for CLI
        setup_logging(level=log_level, format=log_format)
        
        # Build options
        options = ConversionOptions(
            backend_name=backend,
            dpi=dpi,
            add_page_separators=not no_page_separators,
            max_pages=max_pages,
            start_page=start_page,
        )

        # Show what we're doing
        console.print(f"\n[bold blue]Converting:[/bold blue] {pdf_path}")

        # Get page count to show progress
        from docling_hybrid.renderer import get_page_count
        try:
            total_pages = get_page_count(pdf_path)
            pages_to_process = min(
                total_pages - start_page + 1,
                max_pages if max_pages else total_pages
            )
            console.print(f"[dim]Total pages: {total_pages}, Processing: {pages_to_process}[/dim]")
        except Exception:
            # If we can't get page count, just show generic message
            console.print(f"[dim]Processing pages...[/dim]")
            pages_to_process = None

        # Run conversion with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            if pages_to_process:
                task = progress.add_task(
                    f"Processing {pages_to_process} pages...",
                    total=100
                )
            else:
                task = progress.add_task(
                    "Converting PDF...",
                    total=None
                )

            # Run conversion in the background
            result = asyncio.run(_run_conversion_with_progress(
                config, pdf_path, output, options, progress, task
            ))

        # Show results
        console.print()
        console.print(f"[bold green]✓ Conversion complete![/bold green]")
        console.print(f"  Pages processed: {result.processed_pages}/{result.total_pages}")
        console.print(f"  Backend: {result.backend_name}")
        console.print(f"  Output: {result.output_path}")
        console.print(f"  Time: {result.metadata.get('elapsed_seconds', 0):.1f}s")
        
    except DoclingHybridError as e:
        _handle_docling_error(e, console, verbose)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


async def _run_conversion(config, pdf_path, output, options):
    """Run the conversion pipeline."""
    async with HybridPipeline(config) as pipeline:
        return await pipeline.convert_pdf(
            pdf_path=pdf_path,
            output_path=output,
            options=options,
        )


async def _run_conversion_with_progress(config, pdf_path, output, options, progress, task_id):
    """Run the conversion pipeline and update progress.

    Args:
        config: Application config
        pdf_path: Path to PDF file
        output: Output path
        options: Conversion options
        progress: Rich Progress instance
        task_id: Task ID for progress updates

    Returns:
        ConversionResult
    """
    import asyncio

    # Start the conversion
    async def run_conversion():
        async with HybridPipeline(config) as pipeline:
            return await pipeline.convert_pdf(
                pdf_path=pdf_path,
                output_path=output,
                options=options,
            )

    # Create the conversion task
    conversion_task = asyncio.create_task(run_conversion())

    # Update progress periodically while conversion runs
    completed = False
    current_progress = 0

    while not completed:
        # Check if conversion is done
        if conversion_task.done():
            completed = True
            progress.update(task_id, completed=100)
            break

        # Simulate progress (since we don't have real progress hooks yet)
        # This gives user feedback that something is happening
        if current_progress < 95:  # Never reach 100 until actually done
            current_progress += 5
            progress.update(task_id, completed=current_progress)

        # Wait a bit before checking again
        await asyncio.sleep(1)

    # Get the result
    return await conversion_task


@app.command()
def backends() -> None:
    """List available OCR/VLM backends.
    
    Shows all registered backends and their implementation status.
    """
    available = list_backends()
    
    # Create table
    table = Table(title="Available Backends")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")
    
    # Backend info
    backend_info = {
        "nemotron-openrouter": ("✓ Implemented", "OpenRouter API with Nemotron-nano-12b-v2-vl"),
        "deepseek-vllm": ("○ Stub", "DeepSeek-OCR via vLLM (CUDA Linux)"),
        "deepseek-mlx": ("○ Stub", "DeepSeek-OCR via MLX (macOS)"),
    }
    
    for name in available:
        status, desc = backend_info.get(name, ("?", "Unknown backend"))
        table.add_row(name, status, desc)
    
    console.print(table)
    console.print()
    console.print("[dim]Use --backend <name> with the convert command to select a backend.[/dim]")


@app.command()
def info() -> None:
    """Show system information and configuration.

    Displays version, configuration paths, and environment status.
    """
    import os

    console.print("[bold]Docling Hybrid OCR[/bold]")
    console.print(f"Version: {__version__}")
    console.print()

    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    key_status = "[green]✓ Set[/green]" if api_key else "[red]✗ Not set[/red]"
    console.print(f"OPENROUTER_API_KEY: {key_status}")

    # Check config file
    config_env = os.environ.get("DOCLING_HYBRID_CONFIG")
    if config_env:
        console.print(f"Config file: {config_env}")
    else:
        console.print("Config file: [dim]Using defaults[/dim]")

    console.print()
    console.print("[dim]Set OPENROUTER_API_KEY environment variable to use the Nemotron backend.[/dim]")


@app.command(name="convert-batch")
def convert_batch_command(
    input_dir: Path = typer.Argument(
        ...,
        help="Directory containing PDF files",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        "./output",
        "--output-dir",
        "-o",
        help="Output directory for converted files",
    ),
    backend: Optional[str] = typer.Option(
        None,
        "--backend",
        "-b",
        help="Backend to use (default: from config)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
    parallel: int = typer.Option(
        4,
        "--parallel",
        "-p",
        help="Number of files to process in parallel",
        min=1,
        max=16,
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Search for PDFs recursively in subdirectories",
    ),
    pattern: str = typer.Option(
        "*.pdf",
        "--pattern",
        help="Glob pattern for matching PDF files",
    ),
    dpi: Optional[int] = typer.Option(
        None,
        "--dpi",
        help="Page rendering DPI (default: from config)",
        min=72,
        max=600,
    ),
    max_pages: Optional[int] = typer.Option(
        None,
        "--max-pages",
        "-n",
        help="Maximum pages to process per file (default: all)",
        min=1,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging",
    ),
) -> None:
    """Convert multiple PDF files in batch mode.

    Scans a directory for PDF files and converts them in parallel.
    Each PDF is converted to a separate Markdown file in the output directory.

    Examples:

        # Convert all PDFs in a directory
        docling-hybrid-ocr convert-batch ./pdfs/ --output-dir ./output/

        # Recursive search with custom pattern
        docling-hybrid-ocr convert-batch ./docs/ -r --pattern "report_*.pdf"

        # Control parallelism
        docling-hybrid-ocr convert-batch ./pdfs/ --parallel 8

        # Limit pages per file
        docling-hybrid-ocr convert-batch ./pdfs/ --max-pages 5
    """
    try:
        # Initialize configuration
        config = init_config(config_file)

        # Setup logging
        log_level = "DEBUG" if verbose else config.logging.level
        log_format = "text"  # Always use text for CLI
        setup_logging(level=log_level, format=log_format)

        # Find PDF files
        console.print(f"\n[bold blue]Scanning:[/bold blue] {input_dir}")
        console.print(f"[dim]Pattern: {pattern}, Recursive: {recursive}[/dim]")

        try:
            pdf_files = find_pdf_files(input_dir, pattern=pattern, recursive=recursive)
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)

        if not pdf_files:
            console.print(f"[yellow]No PDF files found matching pattern '{pattern}'[/yellow]")
            raise typer.Exit(0)

        console.print(f"[green]Found {len(pdf_files)} PDF file(s)[/green]\n")

        # Build conversion options
        options = ConversionOptions(
            backend_name=backend,
            dpi=dpi,
            max_pages=max_pages,
        )

        # Show what we're doing
        console.print(f"[bold blue]Converting {len(pdf_files)} files...[/bold blue]")
        console.print(f"[dim]Output directory: {output_dir}[/dim]")
        console.print(f"[dim]Parallel workers: {parallel}[/dim]\n")

        # Run batch conversion with progress display
        with BatchProgressDisplay(console, total_files=len(pdf_files)) as progress:
            # Wrap the async conversion to update progress
            async def run_batch_with_progress():
                # Start batch conversion
                result = await convert_batch(
                    input_paths=pdf_files,
                    output_dir=output_dir,
                    config=config,
                    parallel=parallel,
                    options=options,
                )
                return result

            result = asyncio.run(run_batch_with_progress())

        # Print summary
        print_batch_summary(console, result)

        # Exit with appropriate code
        if result.failed > 0:
            raise typer.Exit(1)
        else:
            raise typer.Exit(0)

    except DoclingHybridError as e:
        _handle_docling_error(e, console, verbose)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def health(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
    skip_backends: bool = typer.Option(
        False,
        "--skip-backends",
        help="Skip backend connectivity checks",
    ),
    timeout: int = typer.Option(
        10,
        "--timeout",
        "-t",
        help="Backend check timeout in seconds",
        min=1,
        max=60,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed health information",
    ),
) -> None:
    """Check system health and backend connectivity.

    Performs comprehensive health checks including:
    - Python version compatibility
    - Configuration validation
    - Backend connectivity (optional)
    - System resource availability

    Exit codes:
    - 0: All checks passed (healthy)
    - 1: Some checks degraded but operational
    - 2: Critical checks failed (unhealthy)

    Examples:

        # Basic health check
        docling-hybrid-ocr health

        # Skip backend connectivity checks
        docling-hybrid-ocr health --skip-backends

        # Verbose output with details
        docling-hybrid-ocr health --verbose

        # Custom timeout for backend checks
        docling-hybrid-ocr health --timeout 5
    """
    try:
        # Initialize configuration
        config = init_config(config_file)

        # Setup minimal logging
        from docling_hybrid.common.logging import setup_logging
        setup_logging(level="WARNING", format="text")

        # Run health checks
        from docling_hybrid.common.health import check_system_health, format_health_report

        health_result = asyncio.run(check_system_health(
            config=config,
            check_backends=not skip_backends,
            backend_timeout=timeout,
        ))

        # Format and display report
        report = format_health_report(health_result, verbose=verbose)
        console.print(report)

        # Exit with appropriate code
        from docling_hybrid.common.health import HealthStatus
        if health_result.overall_status == HealthStatus.HEALTHY:
            raise typer.Exit(0)
        elif health_result.overall_status == HealthStatus.DEGRADED:
            raise typer.Exit(1)
        else:
            raise typer.Exit(2)

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e.message}")
        if e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
        raise typer.Exit(2)
    except Exception as e:
        console.print(f"[bold red]Health check failed:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(2)


@app.command()
def validate_config(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file to validate",
        exists=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation information",
    ),
) -> None:
    """Validate configuration file.

    Checks configuration file for:
    - Valid TOML syntax
    - Required sections and fields
    - Value types and constraints
    - Backend configurations
    - API key availability

    Exit codes:
    - 0: Configuration is valid
    - 1: Configuration has errors

    Examples:

        # Validate default configuration
        docling-hybrid-ocr validate-config

        # Validate specific config file
        docling-hybrid-ocr validate-config --config configs/local.toml

        # Verbose validation with details
        docling-hybrid-ocr validate-config --verbose
    """
    try:
        from docling_hybrid.common.health import check_config_health

        console.print(f"\n[bold blue]Validating configuration...[/bold blue]")
        if config_file:
            console.print(f"[dim]Config file: {config_file}[/dim]\n")
        else:
            console.print(f"[dim]Config file: default[/dim]\n")

        # Check config health
        result = asyncio.run(check_config_health(config_file))

        # Display result
        from docling_hybrid.common.health import HealthStatus

        if result.status == HealthStatus.HEALTHY:
            console.print("[bold green]✓ Configuration is valid[/bold green]")
            console.print(f"  {result.message}")

            if verbose and result.details:
                console.print("\n[bold]Configuration Details:[/bold]")
                for key, value in result.details.items():
                    console.print(f"  {key}: {value}")

            raise typer.Exit(0)

        elif result.status == HealthStatus.DEGRADED:
            console.print("[bold yellow]⚠ Configuration has warnings[/bold yellow]")
            console.print(f"  {result.message}")

            if "issues" in result.details:
                console.print("\n[bold]Issues:[/bold]")
                for issue in result.details["issues"]:
                    console.print(f"  • {issue}")

            if verbose and result.details:
                console.print("\n[bold]Details:[/bold]")
                for key, value in result.details.items():
                    if key != "issues":
                        console.print(f"  {key}: {value}")

            console.print("\n[dim]Configuration can be used but may not work optimally.[/dim]")
            raise typer.Exit(0)

        else:  # UNHEALTHY
            console.print("[bold red]✗ Configuration is invalid[/bold red]")
            console.print(f"  {result.message}")

            if result.details:
                console.print("\n[bold]Error Details:[/bold]")
                for key, value in result.details.items():
                    console.print(f"  {key}: {value}")

            console.print("\n[dim]Fix the errors above and try again.[/dim]")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Validation failed:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
