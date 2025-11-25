"""Progress callback protocols for conversion pipeline.

This module defines the protocols and interfaces for progress tracking
during PDF conversion. Callbacks allow external monitoring of conversion
progress in real-time.

The ProgressCallback protocol defines a standard interface that can be
implemented by various progress reporters (console, file, network, etc.).

Usage:
    from docling_hybrid.orchestrator.progress import ProgressCallback
    from docling_hybrid.orchestrator import HybridPipeline

    class MyProgressCallback:
        def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
            print(f"Starting conversion of {total_pages} pages")

        def on_page_complete(self, page_num: int, total: int, result) -> None:
            print(f"Completed page {page_num}/{total}")

        # ... implement other methods

    callback = MyProgressCallback()
    pipeline = HybridPipeline(config)
    result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)
"""

from typing import Protocol, runtime_checkable

from docling_hybrid.common.models import PageResult
from docling_hybrid.orchestrator.models import ConversionResult


@runtime_checkable
class ProgressCallback(Protocol):
    """Protocol for progress callbacks during PDF conversion.

    Implementations of this protocol can track conversion progress
    and provide feedback to users or external systems.

    All methods are optional - implementations can choose to implement
    only the events they care about. Methods should not raise exceptions.

    Example:
        >>> class SimpleCallback:
        ...     def on_conversion_start(self, doc_id: str, total_pages: int):
        ...         print(f"Starting: {total_pages} pages")
        ...
        ...     def on_page_complete(self, page_num: int, total: int, result):
        ...         print(f"Page {page_num}/{total} done")
        ...
        ...     def on_conversion_complete(self, result):
        ...         print(f"Finished: {result.processed_pages} pages")
        ...
        ...     def on_conversion_error(self, error: Exception):
        ...         print(f"Error: {error}")
        ...
        ...     def on_page_start(self, page_num: int, total: int):
        ...         pass
        ...
        ...     def on_page_error(self, page_num: int, error: Exception):
        ...         pass
    """

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        """Called when conversion begins.

        Args:
            doc_id: Unique identifier for this conversion
            total_pages: Total number of pages to process
        """
        ...

    def on_page_start(self, page_num: int, total: int) -> None:
        """Called when a page starts processing.

        Args:
            page_num: Page number being processed (1-indexed)
            total: Total number of pages
        """
        ...

    def on_page_complete(
        self,
        page_num: int,
        total: int,
        result: PageResult,
    ) -> None:
        """Called when a page completes successfully.

        Args:
            page_num: Page number that was processed (1-indexed)
            total: Total number of pages
            result: The page result with extracted content
        """
        ...

    def on_page_error(self, page_num: int, error: Exception) -> None:
        """Called when a page processing fails.

        Args:
            page_num: Page number that failed (1-indexed)
            error: The exception that occurred
        """
        ...

    def on_conversion_complete(self, result: ConversionResult) -> None:
        """Called when conversion completes successfully.

        Args:
            result: The complete conversion result
        """
        ...

    def on_conversion_error(self, error: Exception) -> None:
        """Called when the entire conversion fails.

        Args:
            error: The exception that occurred
        """
        ...


def is_progress_callback(obj: object) -> bool:
    """Check if an object implements the ProgressCallback protocol.

    Args:
        obj: Object to check

    Returns:
        True if object implements ProgressCallback protocol

    Example:
        >>> class MyCallback:
        ...     def on_conversion_start(self, doc_id, total_pages): pass
        ...     def on_page_start(self, page_num, total): pass
        ...     def on_page_complete(self, page_num, total, result): pass
        ...     def on_page_error(self, page_num, error): pass
        ...     def on_conversion_complete(self, result): pass
        ...     def on_conversion_error(self, error): pass
        ...
        >>> is_progress_callback(MyCallback())
        True
    """
    return isinstance(obj, ProgressCallback)
