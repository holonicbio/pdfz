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
from rich.table import Table

from docling_hybrid import __version__
from docling_hybrid.backends import list_backends
from docling_hybrid.common.config import init_config
from docling_hybrid.common.errors import DoclingHybridError
from docling_hybrid.common.logging import setup_logging
from docling_hybrid.orchestrator import ConversionOptions, HybridPipeline

# Create Typer app
app = typer.Typer(
    name="docling-hybrid-ocr",
    help="Convert PDFs to Markdown using hybrid Docling + VLM OCR",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


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
        
        # Show what we're doing
        console.print(f"[bold blue]Converting:[/bold blue] {pdf_path}")
        
        # Build options
        options = ConversionOptions(
            backend_name=backend,
            dpi=dpi,
            add_page_separators=not no_page_separators,
            max_pages=max_pages,
            start_page=start_page,
        )
        
        # Run conversion
        result = asyncio.run(_run_conversion(config, pdf_path, output, options))
        
        # Show results
        console.print()
        console.print(f"[bold green]✓ Conversion complete![/bold green]")
        console.print(f"  Pages processed: {result.processed_pages}/{result.total_pages}")
        console.print(f"  Backend: {result.backend_name}")
        console.print(f"  Output: {result.output_path}")
        console.print(f"  Time: {result.metadata.get('elapsed_seconds', 0):.1f}s")
        
    except DoclingHybridError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if e.details:
            for key, value in e.details.items():
                console.print(f"  {key}: {value}")
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


if __name__ == "__main__":
    app()
