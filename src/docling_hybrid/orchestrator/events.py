"""Typed event classes for progress tracking.

This module defines structured event classes for progress tracking.
These events can be serialized for external monitoring systems or
stored for audit trails.

Events provide a type-safe alternative to the callback protocol,
useful for queuing, logging, or network transmission.

Usage:
    from docling_hybrid.orchestrator.events import (
        ConversionStartEvent,
        PageCompleteEvent,
        to_dict,
    )

    # Create events
    start_event = ConversionStartEvent(doc_id="doc-123", total_pages=10)
    page_event = PageCompleteEvent(page_num=1, total=10, ...)

    # Serialize to dict
    event_dict = to_dict(start_event)

    # Can be sent over network, logged, etc.
    import json
    json.dumps(event_dict)
"""

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from docling_hybrid.common.models import PageResult
from docling_hybrid.orchestrator.models import ConversionResult


class ProgressEventType(str, Enum):
    """Types of progress events."""

    CONVERSION_START = "conversion_start"
    PAGE_START = "page_start"
    PAGE_COMPLETE = "page_complete"
    PAGE_ERROR = "page_error"
    CONVERSION_COMPLETE = "conversion_complete"
    CONVERSION_ERROR = "conversion_error"


class ProgressEvent(BaseModel):
    """Base class for all progress events.

    Attributes:
        event_type: Type of event
        timestamp: Unix timestamp when event occurred
    """

    event_type: ProgressEventType = Field(
        description="Type of progress event"
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp when event occurred",
    )

    class Config:
        use_enum_values = True


class ConversionStartEvent(ProgressEvent):
    """Event fired when conversion begins.

    Attributes:
        doc_id: Document identifier
        total_pages: Total number of pages to process
    """

    event_type: ProgressEventType = Field(
        default=ProgressEventType.CONVERSION_START,
        description="Event type",
    )
    doc_id: str = Field(description="Document identifier")
    total_pages: int = Field(ge=1, description="Total pages to process")


class PageStartEvent(ProgressEvent):
    """Event fired when a page starts processing.

    Attributes:
        page_num: Page number (1-indexed)
        total: Total number of pages
    """

    event_type: ProgressEventType = Field(
        default=ProgressEventType.PAGE_START,
        description="Event type",
    )
    page_num: int = Field(ge=1, description="Page number (1-indexed)")
    total: int = Field(ge=1, description="Total pages")


class PageCompleteEvent(ProgressEvent):
    """Event fired when a page completes successfully.

    Attributes:
        page_num: Page number (1-indexed)
        total: Total number of pages
        page_result: The page result
    """

    event_type: ProgressEventType = Field(
        default=ProgressEventType.PAGE_COMPLETE,
        description="Event type",
    )
    page_num: int = Field(ge=1, description="Page number (1-indexed)")
    total: int = Field(ge=1, description="Total pages")
    page_result: PageResult = Field(description="Page processing result")


class PageErrorEvent(ProgressEvent):
    """Event fired when page processing fails.

    Attributes:
        page_num: Page number (1-indexed)
        error_message: Error message
        error_type: Exception type name
    """

    event_type: ProgressEventType = Field(
        default=ProgressEventType.PAGE_ERROR,
        description="Event type",
    )
    page_num: int = Field(ge=1, description="Page number (1-indexed)")
    error_message: str = Field(description="Error message")
    error_type: str = Field(description="Exception type name")


class ConversionCompleteEvent(ProgressEvent):
    """Event fired when conversion completes successfully.

    Attributes:
        result: The complete conversion result
    """

    event_type: ProgressEventType = Field(
        default=ProgressEventType.CONVERSION_COMPLETE,
        description="Event type",
    )
    result: ConversionResult = Field(description="Conversion result")


class ConversionErrorEvent(ProgressEvent):
    """Event fired when conversion fails.

    Attributes:
        error_message: Error message
        error_type: Exception type name
    """

    event_type: ProgressEventType = Field(
        default=ProgressEventType.CONVERSION_ERROR,
        description="Event type",
    )
    error_message: str = Field(description="Error message")
    error_type: str = Field(description="Exception type name")


def to_dict(event: ProgressEvent) -> dict[str, Any]:
    """Convert event to dictionary.

    Args:
        event: Progress event to serialize

    Returns:
        Dictionary representation of event

    Example:
        >>> event = ConversionStartEvent(doc_id="doc-123", total_pages=10)
        >>> event_dict = to_dict(event)
        >>> event_dict["event_type"]
        'conversion_start'
    """
    return event.model_dump(mode="json")


def from_dict(data: dict[str, Any]) -> ProgressEvent:
    """Create event from dictionary.

    Args:
        data: Dictionary with event data

    Returns:
        Progress event instance

    Raises:
        ValueError: If event_type is unknown

    Example:
        >>> data = {"event_type": "conversion_start", "doc_id": "doc-123", "total_pages": 10}
        >>> event = from_dict(data)
        >>> isinstance(event, ConversionStartEvent)
        True
    """
    event_type = data.get("event_type")

    event_map = {
        ProgressEventType.CONVERSION_START: ConversionStartEvent,
        ProgressEventType.PAGE_START: PageStartEvent,
        ProgressEventType.PAGE_COMPLETE: PageCompleteEvent,
        ProgressEventType.PAGE_ERROR: PageErrorEvent,
        ProgressEventType.CONVERSION_COMPLETE: ConversionCompleteEvent,
        ProgressEventType.CONVERSION_ERROR: ConversionErrorEvent,
    }

    # Handle string event_type
    if isinstance(event_type, str):
        event_type = ProgressEventType(event_type)

    event_class = event_map.get(event_type)
    if event_class is None:
        raise ValueError(f"Unknown event type: {event_type}")

    return event_class.model_validate(data)


class EventQueueCallback:
    """Progress callback that queues events for external processing.

    This callback converts progress updates into typed events and
    adds them to a queue. Useful for:
    - Async processing of progress updates
    - Network transmission
    - Event logging
    - External monitoring

    Attributes:
        events: List of queued events

    Example:
        >>> callback = EventQueueCallback()
        >>> result = await pipeline.convert_pdf(pdf_path, progress_callback=callback)
        >>> for event in callback.events:
        ...     print(f"{event.event_type}: {event.timestamp}")
    """

    def __init__(self) -> None:
        """Initialize event queue callback."""
        self.events: list[ProgressEvent] = []

    def on_conversion_start(self, doc_id: str, total_pages: int) -> None:
        """Queue conversion start event."""
        event = ConversionStartEvent(doc_id=doc_id, total_pages=total_pages)
        self.events.append(event)

    def on_page_start(self, page_num: int, total: int) -> None:
        """Queue page start event."""
        event = PageStartEvent(page_num=page_num, total=total)
        self.events.append(event)

    def on_page_complete(
        self,
        page_num: int,
        total: int,
        result: PageResult,
    ) -> None:
        """Queue page complete event."""
        event = PageCompleteEvent(
            page_num=page_num,
            total=total,
            page_result=result,
        )
        self.events.append(event)

    def on_page_error(self, page_num: int, error: Exception) -> None:
        """Queue page error event."""
        event = PageErrorEvent(
            page_num=page_num,
            error_message=str(error),
            error_type=type(error).__name__,
        )
        self.events.append(event)

    def on_conversion_complete(self, result: ConversionResult) -> None:
        """Queue conversion complete event."""
        event = ConversionCompleteEvent(result=result)
        self.events.append(event)

    def on_conversion_error(self, error: Exception) -> None:
        """Queue conversion error event."""
        event = ConversionErrorEvent(
            error_message=str(error),
            error_type=type(error).__name__,
        )
        self.events.append(event)

    def clear(self) -> None:
        """Clear all queued events."""
        self.events.clear()

    def get_events(self, event_type: ProgressEventType | None = None) -> list[ProgressEvent]:
        """Get queued events, optionally filtered by type.

        Args:
            event_type: Filter by event type (None = all events)

        Returns:
            List of events

        Example:
            >>> callback = EventQueueCallback()
            >>> # ... after conversion ...
            >>> errors = callback.get_events(ProgressEventType.PAGE_ERROR)
        """
        if event_type is None:
            return self.events.copy()

        return [e for e in self.events if e.event_type == event_type]
