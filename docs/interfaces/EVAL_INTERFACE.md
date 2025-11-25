# Evaluation Framework Interface

## Overview

The Evaluation Framework provides interfaces for measuring the quality of OCR/VLM extraction results against ground truth data. This document defines the contracts that all evaluation components must follow.

**Owner:** D10 (Evaluation Lead)
**Status:** Sprint 1 - Interface Definition Complete
**Last Updated:** 2024-11-25

## Interface Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Metric Protocol                          │
│  (Compute similarity/accuracy for predictions)             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Ground Truth Loader Protocol                  │
│         (Load and validate ground truth data)              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Evaluation Runner Protocol                     │
│     (Coordinate evaluation and aggregate results)          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Report Generator Protocol                      │
│          (Format and output results)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Metric Protocol

### Purpose
Metrics compute similarity or accuracy scores between predicted and ground truth content.

### Interface

```python
from typing import Protocol, Optional, Dict, Any
from docling_hybrid.eval.types import MetricType

class MetricProtocol(Protocol):
    """Protocol for evaluation metrics."""

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

        Returns:
            Value between 0.0-1.0 where higher is better
        """
        ...
```

### Concrete Base Class

```python
from abc import ABC, abstractmethod

class Metric(ABC):
    """Abstract base class for metrics."""

    def __init__(self, name: str, metric_type: MetricType, config: Optional[Dict[str, Any]] = None):
        self._name = name
        self._metric_type = metric_type
        self._config = config or {}

    @abstractmethod
    def compute(self, predicted: str, ground_truth: str, metadata: Optional[Dict[str, Any]] = None) -> float:
        pass
```

### Specializations

#### TextSimilarityMetric
For general text comparison metrics:
- Character Error Rate (CER)
- Word Error Rate (WER)
- Token F1 Score
- BLEU Score

#### TableSimilarityMetric
For table structure and content metrics:
- TEDS (Tree Edit Distance-based Similarity)
- TEDS-S (TEDS Structure)
- Row/Column Accuracy

#### FormulaSimilarityMetric (Future)
For mathematical formula metrics:
- LaTeX Edit Distance
- Structural Equivalence

---

## 2. Ground Truth Loader Protocol

### Purpose
Loaders read and validate ground truth data from various formats.

### Interface

```python
from pathlib import Path
from typing import Protocol, List
from docling_hybrid.eval.types import GroundTruth

class GroundTruthLoaderProtocol(Protocol):
    """Protocol for ground truth loaders."""

    def load(self, path: Path) -> GroundTruth:
        """Load ground truth from a file.

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        ...

    def load_corpus(self, corpus_path: Path) -> List[GroundTruth]:
        """Load all ground truth files from a corpus directory."""
        ...
```

### Concrete Base Class

```python
from abc import ABC, abstractmethod

class GroundTruthLoader(ABC):
    """Abstract base class for ground truth loaders."""

    @abstractmethod
    def load(self, path: Path) -> GroundTruth:
        pass

    def load_corpus(self, corpus_path: Path) -> List[GroundTruth]:
        """Default implementation that iterates over directory."""
        # Base implementation provided
        pass
```

### Supported Formats

| Format | Extension | Loader Class (Future) |
|--------|-----------|----------------------|
| Markdown | `.md` | `MarkdownGroundTruthLoader` |
| JSON | `.json` | `JsonGroundTruthLoader` |
| Docling Export | `.json` | `DoclingGroundTruthLoader` |
| HTML | `.html` | `HtmlGroundTruthLoader` |

---

## 3. Evaluation Runner Protocol

### Purpose
Runners coordinate the evaluation process, applying metrics and aggregating results.

### Interface

```python
from typing import Protocol, List
from docling_hybrid.eval.types import (
    PageEvaluationResult,
    DocumentEvaluationResult,
    CorpusEvaluationResult,
    GroundTruth,
)

class EvaluationRunnerProtocol(Protocol):
    """Protocol for evaluation runners."""

    def evaluate_page(
        self,
        predicted: str,
        ground_truth: str,
        page_num: int,
    ) -> PageEvaluationResult:
        """Evaluate a single page."""
        ...

    def evaluate_document(
        self,
        predicted_content: str,
        ground_truth: GroundTruth,
    ) -> DocumentEvaluationResult:
        """Evaluate a complete document."""
        ...

    def evaluate_corpus(
        self,
        predictions: List[tuple[str, str]],  # [(doc_id, content), ...]
        ground_truths: List[GroundTruth],
    ) -> CorpusEvaluationResult:
        """Evaluate a corpus of documents."""
        ...
```

### Concrete Base Class

```python
from abc import ABC, abstractmethod
from docling_hybrid.eval.types import EvaluationConfig

class EvaluationRunner(ABC):
    """Abstract base class for evaluation runners."""

    def __init__(self, config: EvaluationConfig, metrics: List[Metric]):
        self._config = config
        self._metrics = metrics

    @abstractmethod
    def evaluate_page(self, predicted: str, ground_truth: str, page_num: int) -> PageEvaluationResult:
        pass

    @abstractmethod
    def evaluate_document(self, predicted_content: str, ground_truth: GroundTruth) -> DocumentEvaluationResult:
        pass

    @abstractmethod
    def evaluate_corpus(self, predictions: List[tuple[str, str]], ground_truths: List[GroundTruth]) -> CorpusEvaluationResult:
        pass
```

---

## 4. Report Generator Protocol

### Purpose
Generators format evaluation results for output in various formats.

### Interface

```python
from typing import Protocol
from pathlib import Path
from docling_hybrid.eval.types import DocumentEvaluationResult, CorpusEvaluationResult

class ReportGeneratorProtocol(Protocol):
    """Protocol for report generators."""

    def generate_document_report(self, result: DocumentEvaluationResult) -> str:
        """Generate a report for a single document."""
        ...

    def generate_corpus_report(self, result: CorpusEvaluationResult) -> str:
        """Generate a report for a corpus."""
        ...

    def save_report(self, report: str, output_path: Path) -> None:
        """Save a report to a file."""
        ...
```

### Output Formats (Future)

| Format | Extension | Use Case |
|--------|-----------|----------|
| JSON | `.json` | Machine-readable, API integration |
| Markdown | `.md` | Human-readable reports |
| HTML | `.html` | Interactive dashboards |
| CSV | `.csv` | Spreadsheet analysis |

---

## Data Models

### MetricResult

```python
@dataclass
class MetricResult:
    """Result from a single metric computation."""
    metric_name: str
    metric_type: MetricType
    value: float  # 0.0-1.0, higher is better
    details: Dict[str, Any] = field(default_factory=dict)
    threshold: Optional[float] = None
    passes_threshold: Optional[bool] = None
```

### PageEvaluationResult

```python
@dataclass
class PageEvaluationResult:
    """Evaluation results for a single page."""
    page_num: int
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    processing_time_ms: Optional[float] = None

    @property
    def average_score(self) -> float:
        """Average metric score across all metrics."""
        ...
```

### DocumentEvaluationResult

```python
@dataclass
class DocumentEvaluationResult:
    """Evaluation results for a complete document."""
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
```

### CorpusEvaluationResult

```python
@dataclass
class CorpusEvaluationResult:
    """Evaluation results for a corpus of documents."""
    corpus_name: str
    document_results: List[DocumentEvaluationResult] = field(default_factory=list)
    aggregate_metrics: Dict[str, float] = field(default_factory=dict)
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    evaluation_time: datetime = field(default_factory=datetime.now)
    total_processing_time_ms: Optional[float] = None
    backend_name: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        """Percentage of documents that passed thresholds."""
        ...
```

---

## Usage Examples

### Example 1: Implementing a Custom Metric

```python
from docling_hybrid.eval.base import TextSimilarityMetric
from docling_hybrid.eval.types import MetricType

class CharacterErrorRate(TextSimilarityMetric):
    """Character Error Rate metric."""

    def __init__(self):
        super().__init__("character_error_rate")

    def compute(self, predicted: str, ground_truth: str, metadata=None) -> float:
        """Compute CER as 1 - (edit_distance / max_length)."""
        import Levenshtein

        distance = Levenshtein.distance(predicted, ground_truth)
        max_len = max(len(predicted), len(ground_truth))

        if max_len == 0:
            return 1.0  # Perfect match for empty strings

        # Return similarity (1 - error_rate)
        return 1.0 - (distance / max_len)
```

### Example 2: Using the Evaluation Framework

```python
from docling_hybrid.eval import EvaluationRunner, GroundTruthLoader
from docling_hybrid.eval.types import EvaluationConfig, MetricConfig, MetricType

# Configure evaluation
config = EvaluationConfig(
    metrics=[
        MetricConfig(
            name="character_error_rate",
            metric_type=MetricType.TEXT_SIMILARITY,
            threshold=0.95,
            weight=1.0,
        ),
        MetricConfig(
            name="word_error_rate",
            metric_type=MetricType.TEXT_SIMILARITY,
            threshold=0.90,
            weight=1.0,
        ),
    ],
    page_level=True,
    require_all_metrics=False,
)

# Initialize components (implementations in Sprint 5+)
metrics = [CharacterErrorRate(), WordErrorRate()]
runner = BasicEvaluationRunner(config, metrics)
loader = MarkdownGroundTruthLoader()

# Load ground truth
ground_truths = loader.load_corpus(Path("ground_truth/"))

# Evaluate predictions
predictions = [("doc-1", "Predicted content..."), ...]
result = runner.evaluate_corpus(predictions, ground_truths)

# Check results
print(f"Pass rate: {result.pass_rate:.2%}")
print(f"Average score: {result.average_overall_score:.3f}")
```

---

## Design Decisions

### Decision 1: Protocol + ABC Pattern

**Rationale:**
- Protocols allow duck typing for maximum flexibility
- ABCs provide base implementations to reduce boilerplate
- Developers can choose which to use

**Trade-off:**
More complex type system, but better DX

### Decision 2: Metric Values are Similarities (0.0-1.0)

**Rationale:**
- Consistent interpretation: higher is always better
- Easy to aggregate and compare
- Standard range simplifies thresholds

**Note:**
Traditional error rates (CER, WER) are inverted: `similarity = 1 - error_rate`

### Decision 3: Page-Level + Document-Level Metrics

**Rationale:**
- Page-level helps identify problematic pages
- Document-level provides overall quality assessment
- Both useful for different analysis needs

---

## Future Extensions

### Sprint 5: Metric Implementations
- CharacterErrorRate
- WordErrorRate
- TokenF1Score

### Sprint 6: Table Metrics
- TEDS (Tree Edit Distance-based Similarity)
- RowColumnAccuracy

### Sprint 7: Advanced Features
- Confidence-weighted metrics
- Multi-backend metric fusion
- Custom aggregation strategies

### Sprint 8: Reporting
- HTML dashboard generation
- CSV export for analysis
- Metric trending over time

---

## Acceptance Criteria

**Sprint 1 (Interface Definition):**
- [x] All protocols defined with complete type hints
- [x] All abstract base classes implemented
- [x] All data models defined with Pydantic/dataclasses
- [x] Interface documentation complete
- [x] Examples provided for each interface
- [x] Tech Lead approval (D01)

**Sprint 5+ (Implementation):**
- [ ] At least 3 metrics implemented (CER, WER, Token F1)
- [ ] Ground truth loader for Markdown format
- [ ] Basic evaluation runner
- [ ] JSON report generator
- [ ] Unit tests >90% coverage
- [ ] Integration tests with real data

---

## Dependencies

### Required
- **Common**: Error types, logging
- **Standard Library**: abc, typing, dataclasses
- **External (Future)**: python-Levenshtein, pandas (for TEDS)

### Optional
- **Orchestrator**: For end-to-end evaluation integration
- **CLI**: For evaluation command integration

---

## Contact

**Owner:** D10 (Evaluation Lead)
**Reviewers:** D01 (Tech Lead), D09 (Block Processing)
**Status:** Interface Complete - Ready for Sprint 5 Implementation
