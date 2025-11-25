"""Data types and models for evaluation framework.

This module defines the data models used throughout the evaluation framework,
including ground truth formats, metric results, and evaluation outputs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class GroundTruthFormat(Enum):
    """Supported ground truth formats."""

    MARKDOWN = "markdown"  # Plain markdown text
    JSON = "json"  # Structured JSON with metadata
    DOCLING = "docling"  # Docling JSON export format
    HTML = "html"  # HTML with structure preserved


class MetricType(Enum):
    """Types of evaluation metrics."""

    TEXT_SIMILARITY = "text_similarity"  # General text comparison
    TABLE_SIMILARITY = "table_similarity"  # Table structure and content
    FORMULA_SIMILARITY = "formula_similarity"  # Formula/equation accuracy
    STRUCTURE_SIMILARITY = "structure_similarity"  # Document structure
    READ_ORDER = "read_order"  # Reading order accuracy


@dataclass
class GroundTruth:
    """Ground truth data for a single document.

    Attributes:
        doc_id: Unique identifier for the document
        source_path: Path to source PDF file
        content: Ground truth content (format-dependent)
        format: Format of the ground truth data
        metadata: Additional metadata about the ground truth
        created_at: When this ground truth was created
        annotator: Who created/verified this ground truth
        blocks: Optional block-level ground truth (for block evaluation)
    """

    doc_id: str
    source_path: Path
    content: str
    format: GroundTruthFormat
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    annotator: Optional[str] = None
    blocks: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MetricResult:
    """Result from a single metric computation.

    Attributes:
        metric_name: Name of the metric (e.g., "character_error_rate")
        metric_type: Type/category of the metric
        value: Computed metric value (0.0-1.0 for similarity, higher is better)
        details: Additional metric-specific details
        threshold: Optional quality threshold for this metric
        passes_threshold: Whether the value passes the threshold
    """

    metric_name: str
    metric_type: MetricType
    value: float
    details: Dict[str, Any] = field(default_factory=dict)
    threshold: Optional[float] = None
    passes_threshold: Optional[bool] = None

    def __post_init__(self):
        if self.threshold is not None and self.passes_threshold is None:
            self.passes_threshold = self.value >= self.threshold


@dataclass
class PageEvaluationResult:
    """Evaluation results for a single page.

    Attributes:
        page_num: Page number (1-indexed)
        metrics: Dictionary of metric results by metric name
        errors: Any errors encountered during evaluation
        processing_time_ms: Time taken to evaluate this page
    """

    page_num: int
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: Optional[float] = None

    @property
    def has_errors(self) -> bool:
        """Check if this page has any errors."""
        return len(self.errors) > 0

    @property
    def average_score(self) -> float:
        """Compute average metric score across all metrics."""
        if not self.metrics:
            return 0.0
        return sum(m.value for m in self.metrics.values()) / len(self.metrics)


@dataclass
class DocumentEvaluationResult:
    """Evaluation results for a complete document.

    Attributes:
        doc_id: Document identifier
        source_path: Path to source PDF
        ground_truth_path: Path to ground truth file
        predicted_content: Predicted/extracted content
        ground_truth: Ground truth data
        page_results: Per-page evaluation results
        document_metrics: Document-level metrics
        overall_score: Overall quality score (0.0-1.0)
        passed: Whether document passes quality thresholds
        evaluation_time: When evaluation was performed
        processing_time_ms: Total evaluation time
        backend_name: Backend used for extraction
    """

    doc_id: str
    source_path: Path
    ground_truth_path: Path
    predicted_content: str
    ground_truth: GroundTruth
    page_results: List[PageEvaluationResult] = field(default_factory=list)
    document_metrics: Dict[str, MetricResult] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = False
    evaluation_time: datetime = field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = None
    backend_name: Optional[str] = None

    @property
    def total_pages(self) -> int:
        """Total number of pages evaluated."""
        return len(self.page_results)

    @property
    def pages_with_errors(self) -> int:
        """Number of pages with errors."""
        return sum(1 for p in self.page_results if p.has_errors)

    @property
    def average_page_score(self) -> float:
        """Average score across all pages."""
        if not self.page_results:
            return 0.0
        return sum(p.average_score for p in self.page_results) / len(self.page_results)


@dataclass
class CorpusEvaluationResult:
    """Evaluation results for a corpus of documents.

    Attributes:
        corpus_name: Name of the evaluation corpus
        document_results: Results for each document
        aggregate_metrics: Aggregated metrics across all documents
        summary_statistics: Summary statistics
        evaluation_time: When evaluation was performed
        total_processing_time_ms: Total time for all documents
        backend_name: Backend used for extraction
        config: Configuration used for evaluation
    """

    corpus_name: str
    document_results: List[DocumentEvaluationResult] = field(default_factory=list)
    aggregate_metrics: Dict[str, float] = field(default_factory=dict)
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    evaluation_time: datetime = field(default_factory=datetime.now)
    total_processing_time_ms: Optional[float] = None
    backend_name: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_documents(self) -> int:
        """Total number of documents evaluated."""
        return len(self.document_results)

    @property
    def passed_documents(self) -> int:
        """Number of documents that passed thresholds."""
        return sum(1 for d in self.document_results if d.passed)

    @property
    def pass_rate(self) -> float:
        """Percentage of documents that passed."""
        if not self.document_results:
            return 0.0
        return self.passed_documents / self.total_documents

    @property
    def average_overall_score(self) -> float:
        """Average overall score across all documents."""
        if not self.document_results:
            return 0.0
        return sum(d.overall_score for d in self.document_results) / len(self.document_results)


@dataclass
class MetricConfig:
    """Configuration for a single metric.

    Attributes:
        name: Metric name
        metric_type: Type of metric
        enabled: Whether this metric is enabled
        threshold: Optional quality threshold
        weight: Weight for computing aggregate scores
        config: Metric-specific configuration
    """

    name: str
    metric_type: MetricType
    enabled: bool = True
    threshold: Optional[float] = None
    weight: float = 1.0
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationConfig:
    """Configuration for evaluation framework.

    Attributes:
        metrics: List of metric configurations
        ground_truth_format: Expected ground truth format
        page_level: Whether to compute page-level metrics
        require_all_metrics: Whether all metrics must pass thresholds
        output_format: Format for evaluation reports
        output_path: Where to save evaluation reports
        cache_predictions: Whether to cache predictions
    """

    metrics: List[MetricConfig] = field(default_factory=list)
    ground_truth_format: GroundTruthFormat = GroundTruthFormat.MARKDOWN
    page_level: bool = True
    require_all_metrics: bool = False
    output_format: str = "json"
    output_path: Optional[Path] = None
    cache_predictions: bool = True
