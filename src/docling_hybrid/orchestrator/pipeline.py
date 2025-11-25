"""Hybrid conversion pipeline implementation.

This module provides the main pipeline for converting PDFs to Markdown
using Docling for structure and VLM backends for OCR.

The pipeline follows these steps:
1. Generate document ID
2. Load PDF via pypdfium2 (or Docling for extended features)
3. Render each page to PNG
4. Send to VLM backend for OCR
5. Concatenate results
6. Write output file

Usage:
    from pathlib import Path
    from docling_hybrid.orchestrator import HybridPipeline
    from docling_hybrid.common.config import init_config
    
    config = init_config(Path("configs/local.toml"))
    pipeline = HybridPipeline(config)
    
    result = await pipeline.convert_pdf(Path("document.pdf"))
    print(result.markdown)
"""

import asyncio
import time
from pathlib import Path
from typing import Any

from docling_hybrid.backends import make_backend
from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.config import Config
from docling_hybrid.common.errors import ValidationError
from docling_hybrid.common.ids import generate_doc_id
from docling_hybrid.common.logging import bind_context, clear_context, get_logger
from docling_hybrid.common.models import OcrBackendConfig, PageResult
from docling_hybrid.orchestrator.models import ConversionOptions, ConversionResult
from docling_hybrid.renderer import get_page_count, render_page_to_png_bytes

logger = get_logger(__name__)


class HybridPipeline:
    """Main pipeline for PDF to Markdown conversion.
    
    Coordinates the full conversion process:
    - PDF rendering
    - OCR/VLM processing
    - Result aggregation
    - Output writing
    
    Attributes:
        config: Application configuration
        backend: OCR/VLM backend instance (lazily created)
    
    Example:
        >>> pipeline = HybridPipeline(config)
        >>> result = await pipeline.convert_pdf(Path("document.pdf"))
        >>> print(result.markdown[:100])
        # Title
        
        First paragraph of the document...
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize the pipeline.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._backend: OcrVlmBackend | None = None
        self._backend_name: str | None = None
        
        logger.info(
            "pipeline_initialized",
            default_backend=config.backends.default,
            max_workers=config.resources.max_workers,
            dpi=config.resources.page_render_dpi,
        )
    
    def _get_backend(self, backend_name: str | None = None) -> OcrVlmBackend:
        """Get or create backend instance.
        
        Args:
            backend_name: Backend name (None = use default)
            
        Returns:
            Backend instance
        """
        name = backend_name or self.config.backends.default
        
        # Reuse existing backend if same name
        if self._backend is not None and self._backend_name == name:
            return self._backend
        
        # Get backend config and create instance
        backend_config = self.config.backends.get_backend_config(name)
        self._backend = make_backend(backend_config)
        self._backend_name = name
        
        return self._backend

    async def _process_single_page(
        self,
        pdf_path: Path,
        page_idx: int,
        dpi: int,
        backend: OcrVlmBackend,
        backend_name: str,
        doc_id: str,
        total_pages: int,
    ) -> PageResult | None:
        """Process a single page: render and OCR.

        Args:
            pdf_path: Path to PDF file
            page_idx: Zero-indexed page index
            dpi: Rendering DPI
            backend: OCR backend instance
            backend_name: Backend name for metadata
            doc_id: Document ID
            total_pages: Total pages in document

        Returns:
            PageResult if successful, None if error
        """
        page_num = page_idx + 1  # 1-indexed for display

        try:
            # Render page
            image_bytes = render_page_to_png_bytes(
                pdf_path=pdf_path,
                page_index=page_idx,
                dpi=dpi,
            )

            # OCR
            markdown = await backend.page_to_markdown(
                image_bytes=image_bytes,
                page_num=page_num,
                doc_id=doc_id,
            )

            # Create page result
            page_result = PageResult(
                page_num=page_num,
                doc_id=doc_id,
                content=markdown,
                backend_name=backend_name,
                metadata={
                    "image_size_kb": len(image_bytes) // 1024,
                    "dpi": dpi,
                },
            )

            logger.info(
                "page_completed",
                page_num=page_num,
                total=total_pages,
                markdown_chars=len(markdown),
            )

            return page_result

        except Exception as e:
            logger.error(
                "page_failed",
                page_num=page_num,
                error=str(e),
            )
            return None

    async def convert_pdf(
        self,
        pdf_path: Path,
        output_path: Path | None = None,
        options: ConversionOptions | None = None,
    ) -> ConversionResult:
        """Convert a PDF to Markdown.
        
        This is the main entry point for conversion. It:
        1. Validates the input PDF
        2. Generates a document ID
        3. Renders and processes each page
        4. Concatenates results
        5. Optionally writes to output file
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Path for output Markdown (optional)
                If not provided, defaults to <pdf_name>.nemotron.md
            options: Conversion options (optional)
        
        Returns:
            ConversionResult with full Markdown and per-page results
            
        Raises:
            ValidationError: If PDF file doesn't exist or is invalid
            BackendError: If OCR processing fails
            
        Example:
            >>> result = await pipeline.convert_pdf(
            ...     pdf_path=Path("document.pdf"),
            ...     output_path=Path("output.md"),
            ...     options=ConversionOptions(max_pages=10),
            ... )
            >>> print(f"Converted {result.processed_pages} pages")
        """
        options = options or ConversionOptions()
        start_time = time.time()
        
        # Validate input
        if not pdf_path.exists():
            raise ValidationError(
                f"PDF file not found: {pdf_path}",
                details={"path": str(pdf_path)}
            )
        
        # Generate document ID
        doc_id = generate_doc_id(pdf_path.name)
        
        # Bind logging context
        bind_context(doc_id=doc_id, pdf=str(pdf_path))
        
        try:
            logger.info("conversion_started", pdf=str(pdf_path))
            
            # Get page count
            total_pages = get_page_count(pdf_path)
            logger.info("pdf_loaded", total_pages=total_pages)
            
            # Calculate page range
            start_idx = options.start_page - 1  # Convert to 0-indexed
            end_idx = total_pages
            
            if options.max_pages is not None:
                end_idx = min(start_idx + options.max_pages, total_pages)
            
            # Get backend
            backend = self._get_backend(options.backend_name)
            backend_name = backend.name
            
            # Get DPI
            dpi = options.dpi or self.config.resources.page_render_dpi

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.config.resources.max_workers)

            logger.info(
                "starting_concurrent_processing",
                num_pages=end_idx - start_idx,
                max_workers=self.config.resources.max_workers,
            )

            # Process pages concurrently with semaphore
            async def process_with_semaphore(page_idx: int):
                """Process a single page with semaphore control."""
                async with semaphore:
                    return await self._process_single_page(
                        pdf_path=pdf_path,
                        page_idx=page_idx,
                        dpi=dpi,
                        backend=backend,
                        backend_name=backend_name,
                        doc_id=doc_id,
                        total_pages=total_pages,
                    )

            # Create tasks for all pages
            tasks = [
                process_with_semaphore(page_idx)
                for page_idx in range(start_idx, end_idx)
            ]

            # Execute concurrently and gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Separate successful results from errors, maintaining page order
            page_results: list[PageResult] = []
            page_markdowns: list[str] = []

            for result in results:
                if isinstance(result, Exception):
                    # Exception raised during processing
                    logger.error(
                        "page_processing_exception",
                        error=str(result),
                        error_type=type(result).__name__,
                    )
                    # Continue with other pages, skip failed ones
                    continue
                elif result is None:
                    # Page processing returned None (error already logged)
                    continue
                else:
                    # Successful result
                    page_results.append(result)
                    page_markdowns.append(result.content)
            
            # Concatenate results
            if options.add_page_separators:
                parts = []
                for page_result in page_results:
                    separator = options.page_separator_format.format(
                        page_num=page_result.page_num
                    )
                    parts.append(separator + page_result.content)
                full_markdown = "\n\n".join(parts)
            else:
                full_markdown = "\n\n".join(page_markdowns)
            
            # Determine output path
            if output_path is None:
                output_path = pdf_path.with_suffix(f".{backend_name.split('-')[0]}.md")
            
            # Write output
            output_path.write_text(full_markdown, encoding="utf-8")
            logger.info("output_written", path=str(output_path))
            
            # Calculate timing
            elapsed = time.time() - start_time
            
            # Build result
            result = ConversionResult(
                doc_id=doc_id,
                source_path=pdf_path,
                output_path=output_path,
                markdown=full_markdown,
                page_results=page_results,
                total_pages=total_pages,
                processed_pages=len(page_results),
                backend_name=backend_name,
                metadata={
                    "elapsed_seconds": round(elapsed, 2),
                    "dpi": dpi,
                    "start_page": options.start_page,
                    "pages_requested": end_idx - start_idx,
                },
            )
            
            logger.info(
                "conversion_completed",
                processed_pages=len(page_results),
                elapsed_seconds=round(elapsed, 2),
            )
            
            return result
            
        finally:
            clear_context()
    
    async def close(self) -> None:
        """Close backend connections."""
        if self._backend is not None:
            await self._backend.close()
            self._backend = None
            self._backend_name = None
    
    async def __aenter__(self) -> "HybridPipeline":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
