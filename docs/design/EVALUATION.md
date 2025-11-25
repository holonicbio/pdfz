# Evaluation Framework Design

## Document Information

**Version:** 1.0
**Author:** D10 (Evaluation Lead)
**Status:** Sprint 1 - Design Complete
**Last Updated:** 2024-11-25
**Review Status:** Pending Tech Lead Approval

---

## Table of Contents

1. [Overview](#overview)
2. [Motivation](#motivation)
3. [Requirements](#requirements)
4. [Architecture](#architecture)
5. [Metrics](#metrics)
6. [Ground Truth Format](#ground-truth-format)
7. [Evaluation Workflow](#evaluation-workflow)
8. [Implementation Plan](#implementation-plan)
9. [Testing Strategy](#testing-strategy)
10. [Future Extensions](#future-extensions)

---

## 1. Overview

The Evaluation Framework provides comprehensive quality assessment for OCR/VLM extraction results. It enables:

- **Quantitative measurement** of extraction quality against ground truth
- **Multi-metric evaluation** covering text, tables, formulas, and structure
- **Corpus-level analysis** for benchmarking and model comparison
- **Automated regression testing** for quality assurance

### Key Features

- 📊 **Multiple Metrics**: CER, WER, TEDS, Token F1, Formula Accuracy
- 📁 **Flexible Ground Truth**: Markdown, JSON, HTML, Docling formats
- 🔄 **Batch Processing**: Evaluate entire document corpora
- 📈 **Rich Reports**: JSON, Markdown, HTML, CSV outputs
- 🎯 **Threshold-Based QA**: Pass/fail based on configurable thresholds

---

## 2. Motivation

### Problem Statement

Without systematic evaluation:
- Quality regressions go unnoticed
- Backend/model comparisons are subjective
- Optimization efforts lack quantitative guidance
- Production deployment confidence is low

### Goals

1. **Measure Quality**: Quantify extraction accuracy objectively
2. **Enable Comparison**: Compare backends, models, configurations
3. **Support Development**: Guide optimization and debugging
4. **Ensure Quality**: Prevent regressions via automated testing

### Non-Goals (Phase 1)

- ❌ Online/real-time evaluation (batch only)
- ❌ Active learning or model training
- ❌ Automatic ground truth generation
- ❌ Visual similarity metrics (text-based only for now)

---

## 3. Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Support text similarity metrics (CER, WER) | P0 |
| FR-02 | Support table structure metrics (TEDS) | P1 |
| FR-03 | Support formula accuracy metrics | P2 |
| FR-04 | Load ground truth from Markdown files | P0 |
| FR-05 | Load ground truth from JSON files | P1 |
| FR-06 | Evaluate individual documents | P0 |
| FR-07 | Evaluate document corpora | P0 |
| FR-08 | Generate JSON evaluation reports | P0 |
| FR-09 | Generate Markdown evaluation reports | P1 |
| FR-10 | Support page-level metrics | P1 |
| FR-11 | Support configurable quality thresholds | P1 |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | Process 100-page document in <5 minutes | P1 |
| NFR-02 | Memory usage <2GB for typical corpus | P1 |
| NFR-03 | Metrics are deterministic and reproducible | P0 |
| NFR-04 | Support concurrent evaluation | P2 |
| NFR-05 | Extensible for new metrics | P0 |

---

## 4. Architecture

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Evaluation Framework                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Metrics    │     │ Ground Truth │     │   Runners    │   │
│  │              │     │   Loaders    │     │              │   │
│  ├──────────────┤     ├──────────────┤     ├──────────────┤   │
│  │ • CER        │     │ • Markdown   │     │ • Basic      │   │
│  │ • WER        │     │ • JSON       │     │ • Async      │   │
│  │ • Token F1   │     │ • Docling    │     │ • Parallel   │   │
│  │ • TEDS       │     │ • HTML       │     │              │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Report Generators                           │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • JSON  • Markdown  • HTML  • CSV                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

```
┌─────────────┐
│  PDF Files  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  OCR Pipeline       │
│  (Extraction)       │
└──────┬──────────────┘
       │
       │ Predicted
       │ Content
       ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Evaluation Runner   │────▶│  Ground Truth       │
│                     │     │  Loader             │
└──────┬──────────────┘     └─────────────────────┘
       │
       │ Apply Metrics
       ▼
┌─────────────────────┐
│  Metric Results     │
│  (CER, WER, etc.)   │
└──────┬──────────────┘
       │
       │ Aggregate
       ▼
┌─────────────────────┐
│  Evaluation Report  │
│  (JSON/MD/HTML)     │
└─────────────────────┘
```

### 4.3 Class Structure

```python
# Core hierarchy
MetricProtocol
  └── Metric (ABC)
       ├── TextSimilarityMetric (ABC)
       │    ├── CharacterErrorRate
       │    ├── WordErrorRate
       │    └── TokenF1Score
       ├── TableSimilarityMetric (ABC)
       │    ├── TEDS
       │    └── TEDSStructure
       └── FormulaSimilarityMetric (ABC)
            └── LaTeXEditDistance

GroundTruthLoaderProtocol
  └── GroundTruthLoader (ABC)
       ├── MarkdownGroundTruthLoader
       ├── JsonGroundTruthLoader
       └── DoclingGroundTruthLoader

EvaluationRunnerProtocol
  └── EvaluationRunner (ABC)
       ├── BasicEvaluationRunner
       └── ParallelEvaluationRunner

ReportGeneratorProtocol
  ├── JsonReportGenerator
  ├── MarkdownReportGenerator
  └── HtmlReportGenerator
```

---

## 5. Metrics

### 5.1 Text Similarity Metrics

#### Character Error Rate (CER)

**Definition:**
```
CER = edit_distance(predicted, ground_truth) / len(ground_truth)
Similarity = 1 - CER
```

**Properties:**
- **Range:** 0.0 (worst) to 1.0 (perfect)
- **Granularity:** Character-level
- **Use Case:** General text accuracy, sensitive to minor errors

**Implementation:**
```python
import Levenshtein

class CharacterErrorRate(TextSimilarityMetric):
    def compute(self, predicted: str, ground_truth: str, metadata=None) -> float:
        distance = Levenshtein.distance(predicted, ground_truth)
        max_len = max(len(predicted), len(ground_truth), 1)
        return 1.0 - (distance / max_len)
```

**Advantages:**
- Simple and well-understood
- Sensitive to all types of errors

**Disadvantages:**
- Can be overly harsh for minor formatting differences
- Doesn't account for semantic equivalence

---

#### Word Error Rate (WER)

**Definition:**
```
WER = edit_distance(pred_words, gt_words) / len(gt_words)
Similarity = 1 - WER
```

**Properties:**
- **Range:** 0.0 (worst) to 1.0 (perfect)
- **Granularity:** Word-level
- **Use Case:** Less sensitive to whitespace/punctuation

**Implementation:**
```python
class WordErrorRate(TextSimilarityMetric):
    def compute(self, predicted: str, ground_truth: str, metadata=None) -> float:
        pred_words = predicted.split()
        gt_words = ground_truth.split()
        distance = Levenshtein.distance(pred_words, gt_words)
        max_len = max(len(pred_words), len(gt_words), 1)
        return 1.0 - (distance / max_len)
```

**Advantages:**
- More forgiving of whitespace issues
- Better for document-level quality

**Disadvantages:**
- Misses character-level errors within words

---

#### Token F1 Score

**Definition:**
```
Precision = |predicted ∩ ground_truth| / |predicted|
Recall = |predicted ∩ ground_truth| / |ground_truth|
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Properties:**
- **Range:** 0.0 (worst) to 1.0 (perfect)
- **Granularity:** Token-level (words or n-grams)
- **Use Case:** Balanced precision/recall assessment

**Advantages:**
- Order-independent
- Balances precision and recall

**Disadvantages:**
- Ignores word order completely

---

### 5.2 Table Similarity Metrics

#### TEDS (Tree Edit Distance-based Similarity)

**Definition:**
Tree edit distance between HTML table representations

**Properties:**
- **Range:** 0.0 (worst) to 1.0 (perfect)
- **Granularity:** Table structure + content
- **Use Case:** Comprehensive table quality

**Reference:**
Zhong et al. "Image-based table recognition: data, model, and evaluation" (ECCV 2020)

**Implementation Strategy:**
1. Parse Markdown table to HTML tree
2. Compute tree edit distance
3. Normalize by max tree size

**Components:**
- Node insertions/deletions
- Node substitutions
- Cell content comparison

---

#### TEDS-S (TEDS Structure Only)

**Definition:**
TEDS computed only on table structure (ignoring cell content)

**Properties:**
- **Range:** 0.0 (worst) to 1.0 (perfect)
- **Granularity:** Table structure only
- **Use Case:** Assessing table detection and parsing

**Advantages:**
- Isolates structure quality
- Useful for debugging table extraction

---

### 5.3 Formula Similarity Metrics

#### LaTeX Edit Distance

**Definition:**
Normalized edit distance between LaTeX strings

**Properties:**
- **Range:** 0.0 (worst) to 1.0 (perfect)
- **Granularity:** Character-level LaTeX
- **Use Case:** Formula extraction accuracy

**Implementation:**
```python
class LaTeXEditDistance(FormulaSimilarityMetric):
    def compute(self, predicted: str, ground_truth: str, metadata=None) -> float:
        # Normalize LaTeX (remove whitespace, standardize commands)
        pred_norm = self._normalize_latex(predicted)
        gt_norm = self._normalize_latex(ground_truth)

        # Compute edit distance
        distance = Levenshtein.distance(pred_norm, gt_norm)
        max_len = max(len(pred_norm), len(gt_norm), 1)
        return 1.0 - (distance / max_len)

    def _normalize_latex(self, latex: str) -> str:
        # Remove whitespace
        normalized = "".join(latex.split())
        # Standardize \frac vs \dfrac, etc.
        # ...
        return normalized
```

---

### 5.4 Metric Selection Guidelines

| Document Type | Primary Metrics | Secondary Metrics |
|---------------|----------------|-------------------|
| Plain Text | WER, CER | Token F1 |
| Tables | TEDS, TEDS-S | CER (on cells) |
| Formulas | LaTeX Edit Distance | - |
| Mixed | CER, WER, TEDS | Token F1 |

---

## 6. Ground Truth Format

### 6.1 Format Options

#### Option 1: Markdown (Recommended for Phase 1)

**File Structure:**
```
corpus/
├── doc-001/
│   ├── source.pdf
│   └── ground_truth.md
├── doc-002/
│   ├── source.pdf
│   └── ground_truth.md
└── ...
```

**Advantages:**
- Human-readable
- Easy to create manually
- Standard format
- Tables supported natively

**Disadvantages:**
- No metadata storage
- Limited structure annotation

**Example:**
```markdown
# Document Title

This is the first paragraph with some **bold** text.

## Section 1

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

The formula is: $E = mc^2$
```

---

#### Option 2: JSON (Recommended for Phase 2)

**File Structure:**
```json
{
  "doc_id": "doc-001",
  "source_pdf": "doc-001.pdf",
  "format": "json",
  "metadata": {
    "created_at": "2024-11-25T10:00:00Z",
    "annotator": "human-01",
    "total_pages": 5
  },
  "content": "Full markdown content...",
  "pages": [
    {
      "page_num": 1,
      "content": "Page 1 content..."
    }
  ],
  "blocks": [
    {
      "block_type": "paragraph",
      "page_num": 1,
      "bbox": [100, 200, 500, 250],
      "content": "Block content..."
    }
  ]
}
```

**Advantages:**
- Rich metadata
- Block-level annotations
- Page-level ground truth
- Machine-readable

**Disadvantages:**
- Not human-friendly for manual creation
- Requires tooling

---

#### Option 3: Docling Export (Future)

**Description:**
Use Docling's native export format as ground truth

**Advantages:**
- Automatic generation
- Full structure preserved
- Block-level annotations

**Disadvantages:**
- Requires Docling for ground truth creation
- May include extraction errors

---

### 6.2 Ground Truth Creation Workflow

```
┌─────────────────┐
│  Source PDF     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Manual         │
│  Transcription  │  ← Human annotator
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Markdown File  │
│  (Ground Truth) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validation     │  ← Check formatting
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Corpus         │
└─────────────────┘
```

**Best Practices:**
1. Use consistent Markdown formatting
2. Preserve original structure
3. Annotate ambiguous cases
4. Version control ground truth
5. Peer review for quality

---

## 7. Evaluation Workflow

### 7.1 Document-Level Evaluation

```python
# Pseudocode
async def evaluate_document(
    predicted_content: str,
    ground_truth: GroundTruth,
    config: EvaluationConfig,
) -> DocumentEvaluationResult:

    # 1. Initialize metrics
    metrics = [create_metric(m) for m in config.metrics]

    # 2. Compute document-level metrics
    doc_metrics = {}
    for metric in metrics:
        value = metric.compute(predicted_content, ground_truth.content)
        doc_metrics[metric.name] = MetricResult(
            metric_name=metric.name,
            metric_type=metric.metric_type,
            value=value,
        )

    # 3. Compute page-level metrics (if enabled)
    page_results = []
    if config.page_level:
        predicted_pages = split_into_pages(predicted_content)
        gt_pages = split_into_pages(ground_truth.content)

        for page_num, (pred_page, gt_page) in enumerate(zip(predicted_pages, gt_pages), 1):
            page_result = evaluate_page(pred_page, gt_page, page_num, metrics)
            page_results.append(page_result)

    # 4. Compute overall score
    overall_score = compute_weighted_average(doc_metrics, config)

    # 5. Check pass/fail
    passed = check_thresholds(doc_metrics, config)

    return DocumentEvaluationResult(
        doc_id=ground_truth.doc_id,
        document_metrics=doc_metrics,
        page_results=page_results,
        overall_score=overall_score,
        passed=passed,
        ...
    )
```

### 7.2 Corpus-Level Evaluation

```python
# Pseudocode
async def evaluate_corpus(
    predictions: List[tuple[str, str]],  # [(doc_id, content), ...]
    ground_truths: List[GroundTruth],
    config: EvaluationConfig,
) -> CorpusEvaluationResult:

    # 1. Match predictions to ground truths
    matched = match_by_doc_id(predictions, ground_truths)

    # 2. Evaluate each document
    doc_results = []
    for pred_content, gt in matched:
        doc_result = await evaluate_document(pred_content, gt, config)
        doc_results.append(doc_result)

    # 3. Aggregate metrics across corpus
    aggregate_metrics = {}
    for metric_name in config.metrics:
        values = [d.document_metrics[metric_name].value for d in doc_results]
        aggregate_metrics[metric_name] = {
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "min": min(values),
            "max": max(values),
        }

    # 4. Compute summary statistics
    summary_stats = {
        "total_documents": len(doc_results),
        "passed_documents": sum(d.passed for d in doc_results),
        "pass_rate": sum(d.passed for d in doc_results) / len(doc_results),
        "average_score": sum(d.overall_score for d in doc_results) / len(doc_results),
    }

    return CorpusEvaluationResult(
        document_results=doc_results,
        aggregate_metrics=aggregate_metrics,
        summary_statistics=summary_stats,
        ...
    )
```

---

## 8. Implementation Plan

### Sprint 1 (Current): Interface Definition ✅
- [x] Define all protocols and ABCs
- [x] Define data models
- [x] Write interface documentation
- [x] Write design document
- [x] Tech Lead approval

### Sprint 5: Basic Metrics
**Duration:** Weeks 9-10
**Owner:** D10

**Tasks:**
1. Implement CharacterErrorRate
2. Implement WordErrorRate
3. Implement TokenF1Score
4. Write comprehensive unit tests
5. Benchmark performance

**Deliverables:**
- `src/docling_hybrid/eval/metrics/text.py`
- `tests/unit/eval/test_text_metrics.py`
- Performance benchmarks

---

### Sprint 6: Ground Truth & Runner
**Duration:** Weeks 11-12
**Owner:** D10

**Tasks:**
1. Implement MarkdownGroundTruthLoader
2. Implement BasicEvaluationRunner
3. Implement JsonReportGenerator
4. Create test corpus (10-20 documents)
5. Integration tests

**Deliverables:**
- `src/docling_hybrid/eval/loaders/markdown.py`
- `src/docling_hybrid/eval/runners/basic.py`
- `src/docling_hybrid/eval/reporters/json_reporter.py`
- `tests/fixtures/eval_corpus/`
- `tests/integration/eval/test_evaluation_flow.py`

---

### Sprint 7: Table Metrics
**Duration:** Weeks 13-14
**Owner:** D10

**Tasks:**
1. Implement TEDS metric
2. Implement TEDS-S metric
3. Create table-specific test corpus
4. Benchmark against reference implementation

**Deliverables:**
- `src/docling_hybrid/eval/metrics/tables.py`
- `tests/unit/eval/test_table_metrics.py`
- `tests/fixtures/table_corpus/`

---

### Sprint 8: Polish & Documentation
**Duration:** Weeks 15-16
**Owner:** D10

**Tasks:**
1. Implement MarkdownReportGenerator
2. Implement HtmlReportGenerator
3. Create comprehensive user guide
4. Run full corpus evaluation
5. Document benchmark results

**Deliverables:**
- `src/docling_hybrid/eval/reporters/markdown_reporter.py`
- `src/docling_hybrid/eval/reporters/html_reporter.py`
- `docs/guides/EVALUATION_GUIDE.md`
- Benchmark report

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Coverage Target:** >95%

**Test Categories:**
1. Metric computation correctness
2. Ground truth loading/validation
3. Result aggregation logic
4. Report generation formatting

**Example:**
```python
def test_character_error_rate_perfect_match():
    metric = CharacterErrorRate()
    result = metric.compute("hello world", "hello world")
    assert result == 1.0

def test_character_error_rate_no_match():
    metric = CharacterErrorRate()
    result = metric.compute("abc", "xyz")
    assert result < 0.5

def test_word_error_rate_single_substitution():
    metric = WordErrorRate()
    result = metric.compute("hello world", "hello earth")
    expected = 1.0 - (1.0 / 2.0)  # 1 error in 2 words
    assert abs(result - expected) < 0.01
```

---

### 9.2 Integration Tests

**Test Scenarios:**
1. Full document evaluation
2. Corpus evaluation
3. Multi-metric evaluation
4. Report generation

**Example:**
```python
@pytest.mark.integration
async def test_full_document_evaluation():
    # Setup
    config = EvaluationConfig(
        metrics=[
            MetricConfig("character_error_rate", MetricType.TEXT_SIMILARITY, threshold=0.95),
            MetricConfig("word_error_rate", MetricType.TEXT_SIMILARITY, threshold=0.90),
        ]
    )

    metrics = [CharacterErrorRate(), WordErrorRate()]
    runner = BasicEvaluationRunner(config, metrics)

    predicted = "This is a test document."
    ground_truth = GroundTruth(
        doc_id="test-001",
        source_path=Path("test.pdf"),
        content="This is a test document.",
        format=GroundTruthFormat.MARKDOWN,
    )

    # Execute
    result = runner.evaluate_document(predicted, ground_truth)

    # Assert
    assert result.overall_score > 0.95
    assert result.passed is True
    assert len(result.document_metrics) == 2
```

---

### 9.3 Benchmark Tests

**Performance Targets:**
- 100-page document: <5 minutes
- 1000-document corpus: <2 hours
- Memory: <2GB peak

**Benchmark Suite:**
```python
@pytest.mark.benchmark
def test_cer_performance(benchmark):
    metric = CharacterErrorRate()
    long_text = "hello world " * 10000  # ~120KB text

    def evaluate():
        return metric.compute(long_text, long_text)

    result = benchmark(evaluate)
    assert result == 1.0
```

---

## 10. Future Extensions

### Phase 3: Advanced Metrics

**Structural Similarity:**
- Heading hierarchy accuracy
- Reading order correctness
- Block boundary detection

**Semantic Similarity:**
- BERT embeddings distance
- Sentence similarity
- Meaning preservation

---

### Phase 4: Active Learning

**Confidence-Based Selection:**
- Identify low-confidence predictions
- Suggest samples for annotation
- Iterative corpus improvement

---

### Phase 5: Continuous Evaluation

**CI/CD Integration:**
- Automatic evaluation on PR
- Regression detection
- Quality gates for merging

---

### Phase 6: Visualization Dashboard

**Features:**
- Interactive metric trends
- Per-document drill-down
- Backend comparison charts
- Quality heatmaps

---

## Appendix A: Metric Comparison

| Metric | Speed | Sensitivity | Use Case |
|--------|-------|-------------|----------|
| CER | Fast | High | Character accuracy |
| WER | Fast | Medium | Word accuracy |
| Token F1 | Fast | Medium | Bag-of-words quality |
| TEDS | Slow | High | Table structure+content |
| TEDS-S | Slow | High | Table structure only |
| LaTeX ED | Fast | High | Formula accuracy |

---

## Appendix B: References

1. **TEDS Metric:**
   - Zhong et al. "Image-based table recognition: data, model, and evaluation" ECCV 2020
   - https://github.com/ibm-aur-nlp/PubTabNet

2. **Edit Distance:**
   - Levenshtein distance: python-Levenshtein library
   - https://github.com/maxbachmann/Levenshtein

3. **OCR Evaluation:**
   - Nayef et al. "ICDAR2017 Robust Reading Challenge on Multi-Lingual Scene Text Detection and Script Identification"
   - CER/WER standard definitions

---

## Appendix C: Acceptance Criteria

**Sprint 1 Checklist:**
- [x] All interfaces defined
- [x] All data models defined
- [x] Interface documentation complete
- [x] Design document complete
- [x] Examples provided
- [ ] Tech Lead approval (D01)

**Sprint 5+ Checklist:**
- [ ] CER, WER, Token F1 implemented
- [ ] Ground truth loader working
- [ ] Evaluation runner working
- [ ] JSON report generator working
- [ ] Test corpus created (10+ documents)
- [ ] Unit tests >95% coverage
- [ ] Integration tests passing
- [ ] Performance benchmarks documented

---

**Document Status:** Ready for Review
**Next Action:** Submit to Tech Lead (D01) for approval
