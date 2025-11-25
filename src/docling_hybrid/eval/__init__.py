"""Evaluation framework for hybrid OCR quality.

STATUS: STUB - Extended scope (Phase 3)

This module will provide:
- Ground truth loading and validation
- Metric computation (edit distance, TEDS, etc.)
- Evaluation harness for batch testing
- Report generation

Planned Metrics:
- Text: Normalized edit distance, token F1
- Tables: TEDS, TEDS-S, row/column accuracy
- Formulas: LaTeX edit distance, structural equivalence
- Read order: Block sequence accuracy

Planned Usage:
    from docling_hybrid.eval import Evaluator, EvalConfig
    
    evaluator = Evaluator(eval_config, pipeline_config)
    report = await evaluator.evaluate_corpus(
        corpus_path=Path("test_corpus/"),
        ground_truth_path=Path("ground_truth/"),
    )
    
    print(f"Text edit distance: {report.metrics['text_edit_distance']:.3f}")

CLI:
    docling-hybrid-eval --corpus test_corpus/ --ground-truth ground_truth/
"""

# Placeholder for future implementation
__all__ = []
