"""Evaluation framework for hybrid OCR quality assessment.

This module provides comprehensive evaluation capabilities for assessing
OCR/VLM extraction quality against ground truth data.

STATUS: Sprint 1 Complete - Interfaces Defined

Key Components:
    - Metrics: Various similarity metrics (CER, WER, TEDS, etc.)
    - Ground Truth Loaders: Load ground truth from various formats
    - Evaluation Runners: Coordinate evaluation and aggregate results
    - Report Generators: Format results for output

Usage:
    from docling_hybrid.eval import (
        Metric,
        EvaluationRunner,
        GroundTruthLoader,
        EvaluationConfig,
        MetricConfig,
    )

    # Configure evaluation
    config = EvaluationConfig(
        metrics=[
            MetricConfig(
                name="character_error_rate",
                metric_type=MetricType.TEXT_SIMILARITY,
                threshold=0.95,
            ),
        ]
    )

    # Run evaluation (implementations in Sprint 5+)
    metrics = [CharacterErrorRate()]
    runner = BasicEvaluationRunner(config, metrics)
    result = runner.evaluate_document(predicted, ground_truth)

Sprint Implementation Status:
    - Sprint 1: ✅ Interfaces and data models defined
    - Sprint 5: ○ Basic metrics implementation (CER, WER, Token F1)
    - Sprint 6: ○ Ground truth loaders and runners
    - Sprint 7: ○ Table metrics (TEDS)
    - Sprint 8: ○ Report generators and polish

For detailed information:
    - Interface docs: docs/interfaces/EVAL_INTERFACE.md
    - Design docs: docs/design/EVALUATION.md
"""

# Import base classes and protocols
from docling_hybrid.eval.base import (
    EvaluationRunner,
    EvaluationRunnerProtocol,
    GroundTruthLoader,
    GroundTruthLoaderProtocol,
    Metric,
    MetricProtocol,
    ReportGeneratorProtocol,
    TableSimilarityMetric,
    TextSimilarityMetric,
)

# Import data types
from docling_hybrid.eval.types import (
    CorpusEvaluationResult,
    DocumentEvaluationResult,
    EvaluationConfig,
    GroundTruth,
    GroundTruthFormat,
    MetricConfig,
    MetricResult,
    MetricType,
    PageEvaluationResult,
)

__all__ = [
    # Base classes and protocols
    "Metric",
    "MetricProtocol",
    "TextSimilarityMetric",
    "TableSimilarityMetric",
    "GroundTruthLoader",
    "GroundTruthLoaderProtocol",
    "EvaluationRunner",
    "EvaluationRunnerProtocol",
    "ReportGeneratorProtocol",
    # Data types
    "GroundTruth",
    "GroundTruthFormat",
    "MetricType",
    "MetricResult",
    "MetricConfig",
    "PageEvaluationResult",
    "DocumentEvaluationResult",
    "CorpusEvaluationResult",
    "EvaluationConfig",
]

# Version will be set by package __init__.py
__version__ = "0.1.0"
