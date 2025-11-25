"""Base classes and protocols for evaluation framework.

This module defines the abstract interfaces for metrics, ground truth loaders,
and evaluation runners. All concrete implementations should inherit from these.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from docling_hybrid.eval.types import (
    CorpusEvaluationResult,
    DocumentEvaluationResult,
    EvaluationConfig,
    GroundTruth,
    MetricResult,
    MetricType,
    PageEvaluationResult,
)


class MetricProtocol(Protocol):
    """Protocol for evaluation metrics.

    All metrics must implement this protocol to be used in the evaluation
    framework. Metrics should be stateless and thread-safe.
    """

    @property
    def name(self) -> str:
        """Unique name of the metric (e.g., 'character_error_rate')."""
        ...

    @property
    def metric_type(self) -> MetricType:
        """Type/category of this metric."""
        ...

    def compute(
        self,
        predicted: str,
        ground_truth: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute the metric value.

        Args:
            predicted: Predicted/extracted text
            ground_truth: Ground truth text
            metadata: Optional metadata for context

        Returns:
            Metric value (0.0-1.0 for similarity, higher is better)
        """
        ...


class Metric(ABC):
    """Abstract base class for evaluation metrics.

    Provides a concrete base implementation that can be extended.
    Subclasses must implement the compute method.
    """

    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize metric.

        Args:
            name: Unique metric name
            metric_type: Type/category of metric
            config: Optional metric-specific configuration
        """
        self._name = name
        self._metric_type = metric_type
        self._config = config or {}

    @property
    def name(self) -> str:
        """Unique name of the metric."""
        return self._name

    @property
    def metric_type(self) -> MetricType:
        """Type/category of this metric."""
        return self._metric_type

    @property
    def config(self) -> Dict[str, Any]:
        """Metric-specific configuration."""
        return self._config

    @abstractmethod
    def compute(
        self,
        predicted: str,
        ground_truth: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute the metric value.

        Args:
            predicted: Predicted/extracted text
            ground_truth: Ground truth text
            metadata: Optional metadata for context

        Returns:
            Metric value (0.0-1.0 for similarity, higher is better)

        Raises:
            ValueError: If inputs are invalid
        """
        pass

    def compute_with_details(
        self,
        predicted: str,
        ground_truth: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MetricResult:
        """Compute metric with full details.

        Args:
            predicted: Predicted/extracted text
            ground_truth: Ground truth text
            metadata: Optional metadata for context

        Returns:
            MetricResult with value and details
        """
        value = self.compute(predicted, ground_truth, metadata)
        return MetricResult(
            metric_name=self.name,
            metric_type=self.metric_type,
            value=value,
            details=metadata or {},
        )


class GroundTruthLoaderProtocol(Protocol):
    """Protocol for ground truth loaders.

    Loaders are responsible for reading ground truth data from various formats.
    """

    def load(self, path: Path) -> GroundTruth:
        """Load ground truth from a file.

        Args:
            path: Path to ground truth file

        Returns:
            GroundTruth object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        ...

    def load_corpus(self, corpus_path: Path) -> List[GroundTruth]:
        """Load all ground truth files from a corpus directory.

        Args:
            corpus_path: Path to corpus directory

        Returns:
            List of GroundTruth objects

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        ...


class GroundTruthLoader(ABC):
    """Abstract base class for ground truth loaders."""

    @abstractmethod
    def load(self, path: Path) -> GroundTruth:
        """Load ground truth from a file.

        Args:
            path: Path to ground truth file

        Returns:
            GroundTruth object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        pass

    def load_corpus(self, corpus_path: Path) -> List[GroundTruth]:
        """Load all ground truth files from a corpus directory.

        Default implementation that looks for matching files.
        Can be overridden for custom corpus structures.

        Args:
            corpus_path: Path to corpus directory

        Returns:
            List of GroundTruth objects

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if not corpus_path.exists():
            raise FileNotFoundError(f"Corpus directory not found: {corpus_path}")

        if not corpus_path.is_dir():
            raise ValueError(f"Path is not a directory: {corpus_path}")

        ground_truths = []
        for file_path in sorted(corpus_path.iterdir()):
            if file_path.is_file() and self._is_valid_file(file_path):
                try:
                    gt = self.load(file_path)
                    ground_truths.append(gt)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Warning: Failed to load {file_path}: {e}")

        return ground_truths

    def _is_valid_file(self, path: Path) -> bool:
        """Check if file is valid for this loader.

        Override this to filter files by extension or other criteria.

        Args:
            path: File path to check

        Returns:
            True if file should be loaded
        """
        return True


class EvaluationRunnerProtocol(Protocol):
    """Protocol for evaluation runners.

    Runners coordinate the evaluation of predictions against ground truth,
    applying all configured metrics and aggregating results.
    """

    def evaluate_page(
        self,
        predicted: str,
        ground_truth: str,
        page_num: int,
    ) -> PageEvaluationResult:
        """Evaluate a single page.

        Args:
            predicted: Predicted page content
            ground_truth: Ground truth page content
            page_num: Page number (1-indexed)

        Returns:
            PageEvaluationResult
        """
        ...

    def evaluate_document(
        self,
        predicted_content: str,
        ground_truth: GroundTruth,
    ) -> DocumentEvaluationResult:
        """Evaluate a complete document.

        Args:
            predicted_content: Predicted document content
            ground_truth: Ground truth data

        Returns:
            DocumentEvaluationResult
        """
        ...

    def evaluate_corpus(
        self,
        predictions: List[tuple[str, str]],  # [(doc_id, content), ...]
        ground_truths: List[GroundTruth],
    ) -> CorpusEvaluationResult:
        """Evaluate a corpus of documents.

        Args:
            predictions: List of (doc_id, content) tuples
            ground_truths: List of ground truth objects

        Returns:
            CorpusEvaluationResult
        """
        ...


class EvaluationRunner(ABC):
    """Abstract base class for evaluation runners."""

    def __init__(
        self,
        config: EvaluationConfig,
        metrics: List[Metric],
    ):
        """Initialize evaluation runner.

        Args:
            config: Evaluation configuration
            metrics: List of metrics to compute
        """
        self._config = config
        self._metrics = metrics

    @property
    def config(self) -> EvaluationConfig:
        """Evaluation configuration."""
        return self._config

    @property
    def metrics(self) -> List[Metric]:
        """List of metrics to compute."""
        return self._metrics

    @abstractmethod
    def evaluate_page(
        self,
        predicted: str,
        ground_truth: str,
        page_num: int,
    ) -> PageEvaluationResult:
        """Evaluate a single page.

        Args:
            predicted: Predicted page content
            ground_truth: Ground truth page content
            page_num: Page number (1-indexed)

        Returns:
            PageEvaluationResult
        """
        pass

    @abstractmethod
    def evaluate_document(
        self,
        predicted_content: str,
        ground_truth: GroundTruth,
    ) -> DocumentEvaluationResult:
        """Evaluate a complete document.

        Args:
            predicted_content: Predicted document content
            ground_truth: Ground truth data

        Returns:
            DocumentEvaluationResult
        """
        pass

    @abstractmethod
    def evaluate_corpus(
        self,
        predictions: List[tuple[str, str]],  # [(doc_id, content), ...]
        ground_truths: List[GroundTruth],
    ) -> CorpusEvaluationResult:
        """Evaluate a corpus of documents.

        Args:
            predictions: List of (doc_id, content) tuples
            ground_truths: List of ground truth objects

        Returns:
            CorpusEvaluationResult
        """
        pass


class ReportGeneratorProtocol(Protocol):
    """Protocol for evaluation report generators.

    Generators format evaluation results for output in various formats.
    """

    def generate_document_report(
        self,
        result: DocumentEvaluationResult,
    ) -> str:
        """Generate a report for a single document.

        Args:
            result: Document evaluation result

        Returns:
            Formatted report as string
        """
        ...

    def generate_corpus_report(
        self,
        result: CorpusEvaluationResult,
    ) -> str:
        """Generate a report for a corpus.

        Args:
            result: Corpus evaluation result

        Returns:
            Formatted report as string
        """
        ...

    def save_report(
        self,
        report: str,
        output_path: Path,
    ) -> None:
        """Save a report to a file.

        Args:
            report: Report content
            output_path: Where to save the report
        """
        ...


# Utility base class for common metric computations
class TextSimilarityMetric(Metric):
    """Base class for text similarity metrics.

    Provides common utilities for text-based metrics.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, MetricType.TEXT_SIMILARITY, config)

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison.

        Default implementation removes extra whitespace.
        Override for custom normalization.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Remove extra whitespace
        normalized = " ".join(text.split())
        # Optionally apply case normalization
        if self.config.get("case_insensitive", False):
            normalized = normalized.lower()
        return normalized


class TableSimilarityMetric(Metric):
    """Base class for table similarity metrics.

    Provides common utilities for table-based metrics.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, MetricType.TABLE_SIMILARITY, config)

    def parse_markdown_table(self, markdown: str) -> List[List[str]]:
        """Parse a Markdown table into a 2D list.

        Args:
            markdown: Markdown table string

        Returns:
            2D list of cell values

        Raises:
            ValueError: If not a valid Markdown table
        """
        # Simple parser - can be enhanced
        lines = [line.strip() for line in markdown.split("\n") if line.strip()]
        if not lines:
            raise ValueError("Empty table")

        rows = []
        for line in lines:
            # Skip separator lines (e.g., |---|---|)
            if line.startswith("|") and all(c in "|-: " for c in line):
                continue
            # Parse data rows
            if line.startswith("|"):
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                rows.append(cells)

        return rows
