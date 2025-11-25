#!/usr/bin/env python3
"""
Batch PDF to Markdown Conversion Example

This example demonstrates how to convert multiple PDF files in batch mode,
with parallel processing and comprehensive error handling.

Usage:
    # Convert all PDFs in a directory
    python examples/batch_conversion.py pdfs/

    # Convert specific files
    python examples/batch_conversion.py file1.pdf file2.pdf file3.pdf

    # Recursive directory scan
    python examples/batch_conversion.py pdfs/ --recursive

    # Control parallelism
    python examples/batch_conversion.py pdfs/ --parallel 4

Requirements:
    - OPENROUTER_API_KEY environment variable must be set
    - Config file at configs/local.toml (or configs/default.toml)
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import List, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

from docling_hybrid import init_config, HybridPipeline
from docling_hybrid.common.errors import DoclingHybridError
from docling_hybrid.orchestrator import ConversionResult


console = Console()


async def convert_single_pdf(
    pipeline: HybridPipeline,
    pdf_path: Path,
    output_dir: Path | None = None
) -> Tuple[Path, ConversionResult | None, str | None]:
    """
    Convert a single PDF file.

    Args:
        pipeline: Initialized HybridPipeline
        pdf_path: Path to PDF file
        output_dir: Optional output directory. If None, saves next to PDF.

    Returns:
        Tuple of (pdf_path, result or None, error_message or None)
    """
    try:
        # Determine output path
        if output_dir:
            output_path = output_dir / pdf_path.with_suffix(".md").name
        else:
            output_path = pdf_path.with_suffix(".md")

        # Convert
        result = await pipeline.convert_pdf(
            pdf_path=pdf_path,
            output_path=output_path
        )

        return (pdf_path, result, None)

    except DoclingHybridError as e:
        return (pdf_path, None, str(e))

    except Exception as e:
        return (pdf_path, None, f"Unexpected error: {e}")


async def batch_convert(
    pdf_paths: List[Path],
    output_dir: Path | None = None,
    parallel: int = 4
) -> List[Tuple[Path, ConversionResult | None, str | None]]:
    """
    Convert multiple PDFs in batch mode with parallel processing.

    Args:
        pdf_paths: List of PDF file paths
        output_dir: Optional output directory
        parallel: Number of files to process in parallel

    Returns:
        List of (pdf_path, result or None, error_message or None) tuples
    """
    console.print(f"\n[bold blue]🚀 Starting batch conversion[/bold blue]")
    console.print(f"   Files: {len(pdf_paths)}")
    console.print(f"   Parallel: {parallel}")
    console.print(f"   Output: {output_dir or 'Same as input files'}\n")

    # Initialize pipeline once for all conversions
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)

    # Create output directory if specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Track results
    results = []

    # Process in batches
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            f"Converting {len(pdf_paths)} PDFs...",
            total=len(pdf_paths)
        )

        # Process files in batches for parallel execution
        for i in range(0, len(pdf_paths), parallel):
            batch = pdf_paths[i:i + parallel]

            # Create tasks for this batch
            tasks = [
                convert_single_pdf(pipeline, pdf_path, output_dir)
                for pdf_path in batch
            ]

            # Run batch in parallel
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Update progress
            progress.update(task, advance=len(batch))

    return results


def collect_pdf_files(
    paths: List[Path],
    recursive: bool = False
) -> List[Path]:
    """
    Collect all PDF files from the given paths.

    Args:
        paths: List of file or directory paths
        recursive: Whether to search directories recursively

    Returns:
        List of PDF file paths
    """
    pdf_files = []

    for path in paths:
        if path.is_file() and path.suffix.lower() == ".pdf":
            pdf_files.append(path)

        elif path.is_dir():
            if recursive:
                pdf_files.extend(path.rglob("*.pdf"))
            else:
                pdf_files.extend(path.glob("*.pdf"))

    # Remove duplicates and sort
    pdf_files = sorted(set(pdf_files))

    return pdf_files


def print_summary(
    results: List[Tuple[Path, ConversionResult | None, str | None]],
    elapsed: float
) -> None:
    """
    Print a summary table of conversion results.

    Args:
        results: List of conversion results
        elapsed: Total elapsed time in seconds
    """
    console.print("\n[bold green]📊 Conversion Summary[/bold green]\n")

    # Create summary table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Status", justify="center")
    table.add_column("Pages", justify="right")
    table.add_column("Output", no_wrap=False)

    # Count successes and failures
    successes = 0
    failures = 0
    total_pages = 0

    for pdf_path, result, error in results:
        if result:
            successes += 1
            total_pages += result.processed_pages
            table.add_row(
                pdf_path.name,
                "✅ Success",
                str(result.processed_pages),
                str(result.output_path.name) if result.output_path else "-"
            )
        else:
            failures += 1
            table.add_row(
                pdf_path.name,
                "❌ Failed",
                "-",
                error or "Unknown error"
            )

    console.print(table)

    # Print statistics
    console.print(f"\n[bold]Statistics:[/bold]")
    console.print(f"  Total files: {len(results)}")
    console.print(f"  Successful: {successes} ({successes/len(results)*100:.1f}%)")
    console.print(f"  Failed: {failures} ({failures/len(results)*100:.1f}%)")
    console.print(f"  Total pages: {total_pages}")
    console.print(f"  Total time: {elapsed:.1f}s")
    console.print(f"  Avg time per file: {elapsed/len(results):.1f}s")
    if total_pages > 0:
        console.print(f"  Avg time per page: {elapsed/total_pages:.1f}s")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert multiple PDF files to Markdown in batch mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all PDFs in a directory
  python examples/batch_conversion.py pdfs/

  # Convert specific files
  python examples/batch_conversion.py file1.pdf file2.pdf file3.pdf

  # Recursive directory scan
  python examples/batch_conversion.py pdfs/ --recursive

  # Custom output directory
  python examples/batch_conversion.py pdfs/ --output-dir output/

  # Control parallelism (default: 4)
  python examples/batch_conversion.py pdfs/ --parallel 8
        """
    )

    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="PDF files or directories to convert"
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        help="Output directory (default: same as input files)"
    )

    parser.add_argument(
        "-p", "--parallel",
        type=int,
        default=4,
        help="Number of files to process in parallel (default: 4)"
    )

    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Search directories recursively"
    )

    args = parser.parse_args()

    # Collect PDF files
    console.print("[bold]🔍 Collecting PDF files...[/bold]")
    pdf_files = collect_pdf_files(args.paths, args.recursive)

    if not pdf_files:
        console.print("[red]❌ No PDF files found![/red]")
        sys.exit(1)

    console.print(f"[green]✓ Found {len(pdf_files)} PDF files[/green]")

    # Validate parallel parameter
    if args.parallel < 1 or args.parallel > 16:
        console.print("[red]❌ Parallel must be between 1 and 16[/red]")
        sys.exit(1)

    # Run batch conversion
    start_time = time.time()

    try:
        results = asyncio.run(
            batch_convert(pdf_files, args.output_dir, args.parallel)
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    elapsed = time.time() - start_time

    # Print summary
    print_summary(results, elapsed)

    # Exit with error code if any failures
    failures = sum(1 for _, result, _ in results if result is None)
    if failures > 0:
        console.print(f"\n[yellow]⚠️  {failures} file(s) failed to convert[/yellow]")
        sys.exit(1)
    else:
        console.print("\n[bold green]✅ All files converted successfully![/bold green]")


if __name__ == "__main__":
    main()
