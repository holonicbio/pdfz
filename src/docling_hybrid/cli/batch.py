"""Batch processing command implementation.

This module provides batch PDF conversion functionality with:
- Directory scanning with glob patterns
- Parallel file processing
- Progress tracking for multiple files
- Summary report generation
- Graceful error handling per file

Usage:
    # Convert all PDFs in a directory
    docling-hybrid-ocr convert-batch ./pdfs/ --output-dir ./output/

    # Recursive with pattern
    docling-hybrid-ocr convert-batch ./docs/ -r --pattern "*.pdf"

    # Control parallelism
    docling-hybrid-ocr convert-batch ./pdfs/ --parallel 8
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from docling_hybrid.common.config import Config
from docling_hybrid.common.errors import DoclingHybridError
from docling_hybrid.common.logging import get_logger
from docling_hybrid.orchestrator import ConversionOptions, ConversionResult, HybridPipeline

logger = get_logger(__name__)


@dataclass
class BatchFileResult:
    """Result of converting a single file in batch mode.

    Attributes:
        source_path: Path to source PDF
        success: Whether conversion succeeded
        result: ConversionResult if successful
        error: Error message if failed
    """
    source_path: Path
    success: bool
    result: ConversionResult | None = None
    error: str | None = None


@dataclass
class BatchResult:
    """Result of batch conversion.

    Attributes:
        total_files: Total number of files to process
        successful: Number of successful conversions
        failed: Number of failed conversions
        file_results: Per-file results
        elapsed_seconds: Total time elapsed
    """
    total_files: int
    successful: int
    failed: int
    file_results: List[BatchFileResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100


def find_pdf_files(
    input_dir: Path,
    pattern: str = "*.pdf",
    recursive: bool = False,
) -> List[Path]:
    """Find PDF files matching pattern.

    Args:
        input_dir: Directory to search
        pattern: Glob pattern (default: "*.pdf")
        recursive: Whether to search recursively

    Returns:
        List of PDF file paths sorted by name

    Raises:
        ValueError: If input_dir doesn't exist or is not a directory
    """
    if not input_dir.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    if not input_dir.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")

    # Use rglob for recursive, glob for non-recursive
    glob_func = input_dir.rglob if recursive else input_dir.glob

    # Find all matching files
    pdf_files = [p for p in glob_func(pattern) if p.is_file()]

    # Sort by name for consistent ordering
    pdf_files.sort()

    logger.info(
        "pdf_files_found",
        count=len(pdf_files),
        pattern=pattern,
        recursive=recursive,
        directory=str(input_dir),
    )

    return pdf_files


async def convert_single_file(
    pdf_path: Path,
    output_dir: Path,
    pipeline: HybridPipeline,
    options: ConversionOptions,
) -> BatchFileResult:
    """Convert a single PDF file.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory
        pipeline: Pipeline instance to use
        options: Conversion options

    Returns:
        BatchFileResult with conversion outcome
    """
    try:
        logger.info("batch_file_started", pdf=str(pdf_path))

        # Determine output path (preserve subdirectory structure)
        output_path = output_dir / f"{pdf_path.stem}.md"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert
        result = await pipeline.convert_pdf(
            pdf_path=pdf_path,
            output_path=output_path,
            options=options,
        )

        logger.info(
            "batch_file_completed",
            pdf=str(pdf_path),
            pages=result.processed_pages,
        )

        return BatchFileResult(
            source_path=pdf_path,
            success=True,
            result=result,
        )

    except DoclingHybridError as e:
        logger.error(
            "batch_file_failed",
            pdf=str(pdf_path),
            error=str(e),
        )
        return BatchFileResult(
            source_path=pdf_path,
            success=False,
            error=str(e),
        )
    except Exception as e:
        logger.error(
            "batch_file_exception",
            pdf=str(pdf_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        return BatchFileResult(
            source_path=pdf_path,
            success=False,
            error=f"{type(e).__name__}: {str(e)}",
        )


async def convert_batch(
    input_paths: List[Path],
    output_dir: Path,
    config: Config,
    parallel: int = 4,
    options: ConversionOptions | None = None,
) -> BatchResult:
    """Convert multiple PDFs in parallel.

    Args:
        input_paths: List of PDF paths to convert
        output_dir: Output directory for converted files
        config: Application configuration
        parallel: Maximum number of files to process in parallel
        options: Conversion options for each file

    Returns:
        BatchResult with summary and per-file results

    Raises:
        ValueError: If input_paths is empty or output_dir is invalid
    """
    import time

    if not input_paths:
        raise ValueError("No input files provided")

    if not output_dir:
        raise ValueError("Output directory not specified")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use default options if not provided
    options = options or ConversionOptions()

    logger.info(
        "batch_started",
        total_files=len(input_paths),
        parallel=parallel,
        output_dir=str(output_dir),
    )

    start_time = time.time()

    # Create pipeline (shared across all files for efficiency)
    async with HybridPipeline(config) as pipeline:
        # Create semaphore to limit parallelism
        semaphore = asyncio.Semaphore(parallel)

        async def convert_with_semaphore(pdf_path: Path) -> BatchFileResult:
            """Convert a file with semaphore control."""
            async with semaphore:
                return await convert_single_file(
                    pdf_path=pdf_path,
                    output_dir=output_dir,
                    pipeline=pipeline,
                    options=options,
                )

        # Process all files concurrently (with semaphore limit)
        tasks = [convert_with_semaphore(pdf) for pdf in input_paths]
        file_results = await asyncio.gather(*tasks, return_exceptions=False)

    # Calculate summary statistics
    successful = sum(1 for r in file_results if r.success)
    failed = len(file_results) - successful
    elapsed = time.time() - start_time

    result = BatchResult(
        total_files=len(input_paths),
        successful=successful,
        failed=failed,
        file_results=file_results,
        elapsed_seconds=round(elapsed, 2),
    )

    logger.info(
        "batch_completed",
        total_files=result.total_files,
        successful=result.successful,
        failed=result.failed,
        elapsed_seconds=result.elapsed_seconds,
    )

    return result


def format_batch_summary(result: BatchResult) -> str:
    """Format batch result as a human-readable summary.

    Args:
        result: BatchResult to format

    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("\n=== Batch Conversion Summary ===\n")
    lines.append(f"Total files: {result.total_files}")
    lines.append(f"Successful: {result.successful}")
    lines.append(f"Failed: {result.failed}")
    lines.append(f"Success rate: {result.success_rate:.1f}%")
    lines.append(f"Time elapsed: {result.elapsed_seconds:.1f}s")

    if result.failed > 0:
        lines.append("\n--- Failed Files ---")
        for file_result in result.file_results:
            if not file_result.success:
                lines.append(f"  ✗ {file_result.source_path.name}")
                if file_result.error:
                    # Truncate long errors
                    error = file_result.error[:100]
                    if len(file_result.error) > 100:
                        error += "..."
                    lines.append(f"    {error}")

    if result.successful > 0:
        lines.append("\n--- Successful Files ---")
        for file_result in result.file_results:
            if file_result.success and file_result.result:
                pages = file_result.result.processed_pages
                lines.append(f"  ✓ {file_result.source_path.name} ({pages} pages)")

    return "\n".join(lines)
