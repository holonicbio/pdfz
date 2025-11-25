# DeepSeek Integration Plan (Sprint 4)

## Document Information

**Version:** 1.0
**Date:** November 25, 2025
**Author:** Dev-01
**Sprint:** Sprint 4 (Planning Document for Sprint 3)
**Status:** Planning - No Implementation

---

## Executive Summary

This document provides a comprehensive plan for integrating DeepSeek-OCR with vLLM as a backend for the Docling Hybrid OCR system. The integration will enable high-performance local GPU inference as an alternative to the OpenRouter cloud API, reducing costs and latency for production deployments.

**Key Benefits:**
- **Cost Reduction:** Eliminate per-request API costs with local inference
- **Performance:** Achieve ~2500 tokens/s on A100 GPUs
- **Privacy:** Keep document processing fully on-premise
- **Flexibility:** Support both cloud (OpenRouter) and local (vLLM) backends

**Target Timeline:** Sprint 4 (1 week implementation + testing)

---

## Table of Contents

1. [Model Overview](#model-overview)
2. [Hardware Requirements](#hardware-requirements)
3. [vLLM Deployment Options](#vllm-deployment-options)
4. [Architecture Integration](#architecture-integration)
5. [API Compatibility](#api-compatibility)
6. [Integration Points](#integration-points)
7. [Test Strategy](#test-strategy)
8. [Implementation Plan](#implementation-plan)
9. [Rollback Strategy](#rollback-strategy)
10. [Cost Analysis](#cost-analysis)
11. [Risk Assessment](#risk-assessment)
12. [Success Criteria](#success-criteria)
13. [References](#references)

---

## Model Overview

### DeepSeek-OCR Specifications

**Model:** deepseek-ai/DeepSeek-OCR
**Type:** Vision-Language Model optimized for OCR and document understanding
**Architecture:** DeepEncoder (380M params) + DeepSeek-3B-MoE decoder (570M active params)
**Total Parameters:** ~3 billion
**Model Size:** 6.7 GB (BF16 precision)
**Framework:** vLLM + Transformers 4.46+

### Performance Characteristics

- **Throughput:** ~2500 tokens/s on A100 GPU (vLLM mode)
- **Precision:** BF16 (recommended), FP16, INT8, INT4 (quantized)
- **Context Window:** Up to 8192 tokens (configurable)
- **Image Processing:** Supports large document images with optimal quality

### Supported Features

- Full page OCR to Markdown
- Table structure extraction
- Mathematical formula recognition (LaTeX output)
- Multi-language support
- Complex layout understanding

---

## Hardware Requirements

### GPU Requirements

#### Minimum Configuration (Testing)
- **GPU:** NVIDIA T4 (16GB VRAM)
- **Use Case:** Single-image testing, development
- **Configuration:** 4-bit quantization required
- **Limitation:** Slower throughput, limited batch size

#### Recommended Configuration (Production)
- **GPU:** NVIDIA L4 or A100 (24GB+ VRAM)
- **Use Case:** Production deployment, batch processing
- **Configuration:** BF16 precision for optimal quality
- **Expected Performance:** 2500 tokens/s

#### Optimal Configuration (High-Volume Production)
- **GPU:** NVIDIA A100 (40GB VRAM)
- **Use Case:** High-volume processing, large batches
- **Configuration:** BF16 with maximized KVCache (--gpu-memory-utilization=0.95)
- **Expected Performance:** Maximum throughput with large context windows

### VRAM Requirements by Use Case

| Use Case | VRAM Requirement | Configuration |
|----------|-----------------|---------------|
| Single-image testing | 8-12 GB | 4-bit or 8-bit quantization |
| Development | 16 GB | FP16 or INT8 |
| Small batches | 16-24 GB | BF16, limited batch size |
| Production batches | 24-32 GB | BF16, standard batch size |
| Large PDFs | 32-40 GB | BF16, large context windows |

### System Requirements

#### CPU & RAM
- **CPU:** 8+ cores recommended (for concurrent preprocessing)
- **RAM:** 32GB+ (16GB minimum for development)
- **Storage:** 50GB+ for model weights and cache

#### Software Stack
- **OS:** Linux (Ubuntu 22.04+ recommended)
- **CUDA:** 11.8+ (12.1+ recommended for latest optimizations)
- **Python:** 3.11 or 3.12
- **PyTorch:** 2.6.0+
- **vLLM:** 0.8.4+ (latest stable)
- **Transformers:** 4.46+
- **Flash-Attn:** 2.7.3+ (for performance)

---

## vLLM Deployment Options

### Option 1: Docker Deployment (Recommended)

**Pros:**
- Isolated environment
- Easy to deploy and scale
- Consistent across environments
- Built-in GPU passthrough

**Cons:**
- Slightly higher memory overhead
- Requires Docker expertise

#### Docker Deployment Command

```bash
docker run --runtime nvidia --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HF_TOKEN=$HF_TOKEN" \
  -p 8000:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  vllm serve deepseek-ai/DeepSeek-OCR \
  --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --gpu-memory-utilization 0.95
```

**Key Parameters:**
- `--runtime nvidia --gpus all`: Enable GPU passthrough
- `--ipc=host`: Share host IPC namespace for PyTorch shared memory
- `-p 8000:8000`: Expose OpenAI-compatible API on port 8000
- `--logits_processors`: Use custom NGram processor for DeepSeek-OCR
- `--no-enable-prefix-caching`: Disable prefix caching for OCR workloads
- `--mm-processor-cache-gb 0`: Optimize memory for vision models
- `--gpu-memory-utilization 0.95`: Use 95% of GPU memory (default is 90%)

#### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  vllm-deepseek:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    environment:
      - HF_TOKEN=${HF_TOKEN}
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - ./logs:/logs
    ports:
      - "8000:8000"
    ipc: host
    command: >
      vllm serve deepseek-ai/DeepSeek-OCR
      --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor
      --no-enable-prefix-caching
      --mm-processor-cache-gb 0
      --gpu-memory-utilization 0.95
      --max-model-len 8192
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### Option 2: Bare Metal Deployment

**Pros:**
- Maximum performance (no containerization overhead)
- Direct access to GPU
- Easier debugging

**Cons:**
- Requires manual dependency management
- Potential environment conflicts
- Less portable

#### Installation Steps

```bash
# 1. Create virtual environment
python3.11 -m venv venv-vllm
source venv-vllm/bin/activate

# 2. Install CUDA-compatible PyTorch
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu121

# 3. Install vLLM with CUDA support
pip install vllm>=0.8.4

# 4. Install Flash-Attention for performance
pip install flash-attn==2.7.3 --no-build-isolation

# 5. Start vLLM server
vllm serve deepseek-ai/DeepSeek-OCR \
  --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --gpu-memory-utilization 0.95 \
  --port 8000
```

### Option 3: Cloud Deployment

**Supported Platforms:**
- **RunPod:** GPU pods with vLLM templates
- **Vast.ai:** Cost-effective GPU rental
- **AWS EC2:** G5/P4 instances
- **Google Cloud:** A2 instances
- **Azure:** NC-series VMs

**Pros:**
- No hardware investment
- Elastic scaling
- Pay-per-use

**Cons:**
- Ongoing costs
- Network latency
- Data privacy considerations

#### Example: AWS EC2 Deployment

```bash
# Launch g5.xlarge instance (A10G GPU, 24GB VRAM)
# Ubuntu 22.04 Deep Learning AMI

# Instance will have CUDA pre-installed
# Follow Docker deployment steps above
```

---

## Architecture Integration

### Current Architecture (Sprint 3)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI / Python API                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Orchestrator                                │
│                     (HybridPipeline)                                │
└─────────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────┐     ┌────────────────────────────────────┐
│   Renderer (pypdfium2)    │     │       Backend Factory              │
└───────────────────────────┘     └────────────────────────────────────┘
                                              │
                                              ▼
                              ┌───────────────────────────┐
                              │ OpenRouter Nemotron       │
                              │ (Cloud API)               │
                              └───────────────────────────┘
```

### Proposed Architecture (Sprint 4)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI / Python API                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Orchestrator                                │
│              (HybridPipeline with fallback chain)                   │
└─────────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────┐     ┌────────────────────────────────────┐
│   Renderer (pypdfium2)    │     │       Backend Factory              │
└───────────────────────────┘     └────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼──────────────────────┐
                    ▼                         ▼                      ▼
        ┌───────────────────┐   ┌───────────────────┐   ┌──────────────────┐
        │ DeepSeek vLLM     │   │ OpenRouter        │   │ DeepSeek MLX     │
        │ (Local GPU)       │   │ Nemotron          │   │ (macOS - stub)   │
        │ PRIMARY           │   │ (Cloud API)       │   │ (Phase 3)        │
        │                   │   │ FALLBACK          │   │                  │
        └───────────────────┘   └───────────────────┘   └──────────────────┘
                    │                         │
                    ▼                         ▼
        ┌───────────────────┐   ┌───────────────────┐
        │ Local vLLM Server │   │   OpenRouter API  │
        │ localhost:8000    │   │   (External)      │
        └───────────────────┘   └───────────────────┘
```

### Component Changes

#### New Component: DeepseekOcrVllmBackend
- **File:** `src/docling_hybrid/backends/deepseek_vllm.py` (currently stub)
- **Base Class:** `OcrVlmBackend`
- **HTTP Client:** `aiohttp` (reuse from OpenRouter backend)
- **API Format:** OpenAI-compatible chat completion

#### Modified Component: Backend Factory
- **File:** `src/docling_hybrid/backends/factory.py`
- **Change:** Update to instantiate `DeepseekOcrVllmBackend` instead of stub

#### Modified Component: Configuration
- **File:** `configs/default.toml`
- **Change:** Set `default = "deepseek-vllm"` for production

#### New Component: Fallback Chain (Sprint 2 - Already Implemented)
- **File:** `src/docling_hybrid/orchestrator/pipeline.py`
- **Feature:** Automatic fallback from DeepSeek to OpenRouter on failures

---

## API Compatibility

### OpenAI-Compatible API

vLLM serves an OpenAI-compatible API by default, which means:

**Endpoint:** `http://localhost:8000/v1/chat/completions`
**Protocol:** HTTP POST with JSON payload
**Authentication:** Optional (can add API key for security)

### Request Format

The request format matches OpenRouter/OpenAI:

```json
{
  "model": "deepseek-ai/DeepSeek-OCR",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Convert this page to Markdown..."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,iVBORw0KGg..."
          }
        }
      ]
    }
  ],
  "temperature": 0.0,
  "max_tokens": 8192
}
```

### Response Format

```json
{
  "id": "cmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-ai/DeepSeek-OCR",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "# Document Title\n\nMarkdown content..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801
  }
}
```

### Code Reusability

Since vLLM uses OpenAI-compatible API:
- **95% code reuse** from `OpenRouterNemotronBackend`
- **Same prompts:** PAGE_TO_MARKDOWN_PROMPT, TABLE_TO_MARKDOWN_PROMPT, FORMULA_TO_LATEX_PROMPT
- **Same image encoding:** Base64 data URLs
- **Same response parsing:** Extract content from choices[0].message.content

**Key Differences:**
1. **base_url:** `http://localhost:8000` instead of `https://openrouter.ai`
2. **api_key:** Optional (can omit for local deployment)
3. **Headers:** No HTTP-Referer or X-Title headers needed
4. **Retry logic:** Different error handling (connection errors vs rate limits)

---

## Integration Points

### 1. Backend Implementation

**File:** `src/docling_hybrid/backends/deepseek_vllm.py`

**Current State:** Stub with NotImplementedError
**Target State:** Full implementation

**Implementation Strategy:**

```python
# src/docling_hybrid/backends/deepseek_vllm.py

# REUSE from OpenRouterNemotronBackend:
# - Base64 image encoding logic
# - HTTP request building
# - Response parsing
# - Retry logic (modify for local server)

# MODIFY:
# - Remove OpenRouter-specific headers
# - Make api_key optional
# - Add connection health check
# - Adjust timeout (local should be faster)
# - Different error messages for local deployment

# NEW:
# - Health check method: is_server_available()
# - Local server connection validation
```

**Estimated Lines of Code:** 200-250 lines (vs 300 for OpenRouter - simpler due to no API key management)

### 2. Configuration Updates

**File:** `configs/default.toml`

**Changes:**

```toml
[backends]
# For production with local GPU
default = "deepseek-vllm"

# Fallback chain (Sprint 2 feature)
fallback_chain = ["deepseek-vllm", "nemotron-openrouter"]

[backends.deepseek-vllm]
name = "deepseek-vllm"
model = "deepseek-ai/DeepSeek-OCR"
base_url = "http://localhost:8000/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
# Local server, so we can use higher timeout for large images
timeout_s = 180
```

### 3. Health Monitoring

**New Utility:** `src/docling_hybrid/backends/health.py`

```python
async def check_vllm_health(base_url: str) -> bool:
    """Check if vLLM server is healthy and ready."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health", timeout=5) as resp:
                return resp.status == 200
    except Exception:
        return False
```

### 4. CLI Enhancements

**File:** `src/docling_hybrid/cli/main.py`

**New Command:** `docling-hybrid-ocr check-server`

```bash
# Check if vLLM server is running
docling-hybrid-ocr check-server --backend deepseek-vllm

# Output:
# ✓ DeepSeek vLLM server is healthy at http://localhost:8000
# Model: deepseek-ai/DeepSeek-OCR
# Status: Ready
```

### 5. Documentation Updates

**Files to Update:**
- `docs/QUICK_START.md` - Add DeepSeek setup section
- `docs/components/BACKENDS.md` - Document DeepSeek backend
- `README.md` - Update architecture diagram
- `docs/DEPLOYMENT.md` - Add vLLM deployment guide

---

## Test Strategy

### Test Pyramid

```
         /\
        /E2E\         10% - Real vLLM server + real PDFs
       /------\
      / Integ \       30% - Mocked HTTP (aioresponses)
     /----------\
    /   Unit     \    60% - Pure logic tests
   /--------------\
```

### Unit Tests (60%)

**File:** `tests/unit/backends/test_deepseek_vllm.py`

**Test Cases:**
1. Backend initialization
2. Image encoding to base64
3. Request payload building
4. Response parsing (string content)
5. Response parsing (list content)
6. Error handling (connection errors)
7. Error handling (timeout)
8. Error handling (invalid JSON response)
9. Health check logic

**Mocking Strategy:**
- Use `aioresponses` to mock HTTP calls
- Mock successful responses
- Mock error responses (404, 500, timeout)
- Mock connection errors

**Example Test:**

```python
@pytest.mark.asyncio
async def test_page_to_markdown_success(deepseek_backend, mock_aiohttp):
    """Test successful page OCR."""
    mock_aiohttp.post(
        "http://localhost:8000/v1/chat/completions",
        payload={
            "choices": [{"message": {"content": "# Title\n\nContent"}}]
        },
        status=200,
    )

    result = await deepseek_backend.page_to_markdown(
        image_bytes=b"fake_png_data",
        page_num=1,
        doc_id="test-123",
    )

    assert result == "# Title\n\nContent"
```

### Integration Tests (30%)

**File:** `tests/integration/test_deepseek_vllm_integration.py`

**Test Cases:**
1. Full pipeline with mocked vLLM responses
2. Concurrent page processing (multiple requests)
3. Fallback from DeepSeek to OpenRouter (on failure)
4. Health check before processing
5. Large image handling
6. Multiple pages from PDF

**Mocking Strategy:**
- Mock vLLM HTTP responses with realistic payloads
- Test concurrent requests (asyncio.gather)
- Test rate limiting (though less relevant for local)

### E2E Tests (10%)

**File:** `tests/e2e/test_deepseek_e2e.py`

**Prerequisites:**
- vLLM server must be running on localhost:8000
- DeepSeek-OCR model must be loaded
- Mark tests with `@pytest.mark.e2e` and `@pytest.mark.requires_vllm`

**Test Cases:**
1. Convert single-page PDF
2. Convert multi-page PDF (5 pages)
3. Test table extraction
4. Test formula extraction
5. Compare output quality with OpenRouter

**Running E2E Tests:**

```bash
# Start vLLM server first
docker-compose -f docker-compose.vllm.yml up -d

# Wait for model to load (can take 1-2 minutes)
sleep 120

# Run E2E tests
pytest tests/e2e/test_deepseek_e2e.py -v --run-e2e

# Cleanup
docker-compose -f docker-compose.vllm.yml down
```

### Test Environment Setup

**File:** `tests/conftest.py`

```python
@pytest.fixture
def deepseek_backend():
    """Create DeepSeek vLLM backend for testing."""
    config = OcrBackendConfig(
        name="deepseek-vllm",
        model="deepseek-ai/DeepSeek-OCR",
        base_url="http://localhost:8000/v1/chat/completions",
        temperature=0.0,
        max_tokens=8192,
    )
    return DeepseekOcrVllmBackend(config)

@pytest.fixture
def mock_vllm_response():
    """Standard successful vLLM response."""
    return {
        "id": "cmpl-123",
        "choices": [
            {
                "message": {
                    "content": "# Test Page\n\nTest content"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {"total_tokens": 100}
    }
```

### Performance Testing

**File:** `tests/performance/test_deepseek_performance.py`

**Metrics to Track:**
1. Throughput (pages/second)
2. Latency per page (mean, p50, p95, p99)
3. GPU memory usage
4. CPU usage
5. Comparison with OpenRouter

**Benchmark Command:**

```bash
# Benchmark 100 pages
docling-hybrid-ocr benchmark \
  --input tests/fixtures/benchmark.pdf \
  --backend deepseek-vllm \
  --iterations 100 \
  --report benchmark-deepseek.json
```

---

## Implementation Plan

### Sprint 4 Implementation Timeline

**Duration:** 5 days
**Team:** 2-3 developers

### Day 1: Environment Setup and Backend Implementation

**Tasks:**
1. Set up vLLM Docker environment
2. Download DeepSeek-OCR model (1-2 hours)
3. Verify vLLM server starts successfully
4. Implement `DeepseekOcrVllmBackend` class
   - Copy HTTP logic from OpenRouter backend
   - Remove OpenRouter-specific code
   - Add local server health checks
   - Update error messages
5. Add unit tests for new backend

**Deliverables:**
- Working vLLM server (Docker)
- `src/docling_hybrid/backends/deepseek_vllm.py` (full implementation)
- Unit tests passing

**Estimated Effort:** 6-8 hours

### Day 2: Integration and Testing

**Tasks:**
1. Update backend factory to use DeepSeek backend
2. Update configuration files
3. Test full pipeline with DeepSeek backend
4. Implement health check CLI command
5. Add integration tests
6. Test fallback chain (DeepSeek → OpenRouter)

**Deliverables:**
- Pipeline working with DeepSeek backend
- Integration tests passing
- Fallback chain validated

**Estimated Effort:** 6-8 hours

### Day 3: E2E Testing and Performance

**Tasks:**
1. Create E2E test suite
2. Run full document conversions
3. Benchmark performance (throughput, latency)
4. Compare quality with OpenRouter
5. Optimize parameters (DPI, max_tokens, etc.)
6. Test concurrent processing

**Deliverables:**
- E2E tests passing
- Performance benchmarks documented
- Quality comparison report

**Estimated Effort:** 6-8 hours

### Day 4: Documentation and Deployment

**Tasks:**
1. Update QUICK_START.md with DeepSeek setup
2. Create DEPLOYMENT_VLLM.md guide
3. Update architecture diagrams
4. Create docker-compose.yml for production
5. Test deployment on clean machine
6. Create troubleshooting guide

**Deliverables:**
- Complete documentation
- Production-ready deployment guide
- Docker Compose configuration

**Estimated Effort:** 4-6 hours

### Day 5: Review and Refinement

**Tasks:**
1. Code review
2. Address feedback
3. Fix any bugs found in testing
4. Final documentation review
5. Prepare Sprint 4 completion report

**Deliverables:**
- Production-ready code
- Complete documentation
- Sprint 4 completion report

**Estimated Effort:** 4-6 hours

### Total Effort Estimate

**Development:** 26-36 hours (3.5-4.5 days)
**Buffer:** 10% for unexpected issues
**Total:** ~30-40 hours

---

## Rollback Strategy

### Rollback Scenarios

#### Scenario 1: vLLM Server Instability
**Issue:** vLLM server crashes or hangs
**Detection:** Health check failures, timeout errors
**Rollback:**
1. Set `default = "nemotron-openrouter"` in config
2. Fallback chain automatically handles transition
3. No code changes needed

#### Scenario 2: Quality Issues
**Issue:** DeepSeek output quality lower than OpenRouter
**Detection:** User reports, quality metrics
**Rollback:**
1. Keep DeepSeek backend in codebase
2. Change default to OpenRouter
3. Use DeepSeek for specific document types only
4. Add quality comparison in docs

#### Scenario 3: Performance Issues
**Issue:** DeepSeek slower than expected
**Detection:** Benchmarks show poor throughput
**Rollback:**
1. Optimize vLLM parameters (--gpu-memory-utilization, --max-model-len)
2. If still slow, revert to OpenRouter for high-volume processing
3. Use DeepSeek for sensitive documents only

#### Scenario 4: GPU Resource Constraints
**Issue:** Insufficient GPU memory or availability
**Detection:** Out of memory errors, GPU not available
**Rollback:**
1. Use quantization (INT8 or INT4) to reduce VRAM
2. If still insufficient, fallback to OpenRouter
3. Document minimum GPU requirements clearly

### Graceful Degradation

The system will gracefully degrade in the following order:

1. **Primary:** DeepSeek vLLM (local GPU)
2. **Fallback 1:** OpenRouter Nemotron (cloud API)
3. **Fallback 2:** Manual fallback to CPU-based Docling OCR (low quality)

**Fallback Triggers:**
- Connection errors (vLLM server not reachable)
- Timeout errors (>180s response time)
- GPU out of memory errors
- Health check failures

**Implementation:**
```python
# Fallback chain in config
[backends]
fallback_chain = ["deepseek-vllm", "nemotron-openrouter"]

# Automatic retry in pipeline
try:
    result = await deepseek_backend.page_to_markdown(...)
except (BackendConnectionError, BackendTimeoutError):
    logger.warning("DeepSeek failed, falling back to OpenRouter")
    result = await openrouter_backend.page_to_markdown(...)
```

---

## Cost Analysis

### Cloud API Costs (OpenRouter - Baseline)

**Model:** nvidia/nemotron-nano-12b-v2-vl:free
**Cost:** FREE tier with rate limits

**Paid Alternatives:**
- gpt-4o: $2.50/1M input tokens, $10/1M output tokens
- claude-3.5-sonnet: $3/1M input tokens, $15/1M output tokens

**Estimated Cost for 1000 Pages:**
- Input: ~1-2M tokens (with images)
- Output: ~500K tokens (Markdown)
- Total: $20-50 for paid models

### Local GPU Costs (DeepSeek vLLM)

#### Option A: On-Premise GPU

**Hardware Investment:**
- NVIDIA A100 (40GB): $10,000-15,000
- L4 (24GB): $5,000-7,000
- Workstation: $3,000-5,000
- Total: $8,000-20,000

**Operating Costs:**
- Electricity: ~$50-100/month (24/7 operation)
- Maintenance: Minimal

**Break-Even:**
- For 1000 pages/month @ $30/batch: 13-27 months
- For 10000 pages/month: 2-3 months

#### Option B: Cloud GPU Rental

**AWS g5.xlarge (A10G, 24GB VRAM):**
- On-demand: $1.006/hour
- Reserved (1yr): $0.60/hour
- Spot: $0.30-0.50/hour

**Cost for 1000 pages:**
- Processing time: ~2 hours (with batch processing)
- Cost: $0.60-2.00 (spot/reserved)

**Monthly (10,000 pages):**
- Cost: $6-20 (vs $200-500 with paid APIs)

#### Option C: RunPod/Vast.ai

**RunPod (A100 80GB):**
- On-demand: $1.89/hour
- Reserved: $1.09/hour

**Vast.ai (A100 40GB):**
- Spot: $0.50-0.90/hour

### Cost Comparison Summary

| Deployment | Setup Cost | Monthly (10K pages) | Break-Even |
|------------|------------|---------------------|------------|
| OpenRouter Free | $0 | $0 (rate limited) | N/A |
| OpenRouter Paid | $0 | $200-500 | N/A |
| Cloud GPU (Spot) | $0 | $10-20 | Immediate |
| Cloud GPU (Reserved) | $0 | $15-30 | Immediate |
| On-Premise GPU | $10,000-20,000 | $50-100 | 2-27 months |

**Recommendation:**
- **Low Volume (<1K pages/month):** OpenRouter Free
- **Medium Volume (1-10K pages/month):** Cloud GPU (Spot)
- **High Volume (>10K pages/month):** On-premise GPU or Reserved Cloud GPU
- **Privacy Requirements:** On-premise GPU (mandatory)

---

## Risk Assessment

### Technical Risks

#### Risk 1: vLLM Version Compatibility
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Pin vLLM version in requirements (e.g., vllm==0.8.4)
- Test with specific vLLM versions
- Document tested versions
- Monitor vLLM releases

#### Risk 2: DeepSeek Model Availability
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Cache model locally in Docker volume
- Document alternative model sources
- Test with model mirrors
- Keep OpenRouter fallback

#### Risk 3: GPU Memory Issues
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Document minimum VRAM requirements clearly
- Test with different GPU configurations
- Support quantization (INT8/INT4)
- Provide memory optimization tips

#### Risk 4: Performance Not Meeting Expectations
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Benchmark early in Sprint 4
- Optimize vLLM parameters
- Use Flash-Attention 2
- Consider model quantization if needed

### Operational Risks

#### Risk 5: vLLM Server Management
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Use Docker for consistent deployment
- Implement health checks
- Auto-restart on failure (Docker restart policy)
- Monitor server logs

#### Risk 6: Concurrent Request Handling
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Test concurrent processing early
- Use vLLM's batching features
- Implement request queuing if needed
- Monitor GPU utilization

### Integration Risks

#### Risk 7: API Compatibility Issues
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Test OpenAI compatibility thoroughly
- Document any differences
- Add API version checks
- Maintain compatibility layer

#### Risk 8: Quality Regression
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Compare outputs with OpenRouter
- Use same prompts across backends
- Implement quality metrics
- Run regression tests

---

## Success Criteria

### Functional Requirements

- [ ] DeepSeek vLLM backend fully implemented
- [ ] All unit tests passing (>95% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing with real vLLM server
- [ ] Fallback chain working correctly
- [ ] Health check command functional
- [ ] Docker deployment tested

### Performance Requirements

- [ ] Throughput: >10 pages/minute on A100 GPU
- [ ] Latency: <30s per page (p95)
- [ ] GPU utilization: >70%
- [ ] No memory leaks over 24-hour run

### Quality Requirements

- [ ] Output quality comparable to OpenRouter (subjective)
- [ ] Table extraction accuracy >90%
- [ ] Formula extraction accuracy >85%
- [ ] No hallucinations or invented content

### Documentation Requirements

- [ ] DeepSeek setup guide complete
- [ ] vLLM deployment guide complete
- [ ] Troubleshooting guide complete
- [ ] API documentation updated
- [ ] Architecture diagrams updated

### Operational Requirements

- [ ] Docker image builds successfully
- [ ] Docker Compose configuration works
- [ ] Health monitoring functional
- [ ] Log aggregation working
- [ ] Deployment tested on clean machine

---

## References

### Official Documentation

1. [vLLM Documentation](https://docs.vllm.ai/)
2. [vLLM Docker Deployment Guide](https://docs.vllm.ai/en/latest/deployment/docker/)
3. [vLLM OpenAI Compatible Server](https://docs.vllm.ai/en/v0.6.0/serving/openai_compatible_server.html)
4. [DeepSeek-OCR Usage Guide - vLLM](https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-OCR.html)
5. [DeepSeek-OCR Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-OCR)

### Community Resources

6. [DeepSeek-OCR Google Colab Discussion](https://huggingface.co/deepseek-ai/DeepSeek-OCR/discussions/27)
7. [GPU Requirements Guide for DeepSeek Models](https://apxml.com/posts/system-requirements-deepseek-models)
8. [DeepSeek OCR GPU Requirements Guide](https://sparkco.ai/blog/deepseek-ocr-gpu-requirements-a-comprehensive-guide)
9. [How to Access and Use DeepSeek OCR](https://www.analyticsvidhya.com/blog/2025/10/deepseeks-ocr/)
10. [Deploy vLLM with Docker Guide](https://medium.com/@kimdoil1211/effortless-vllm-deployment-with-docker-a-comprehensive-guide-2a23119839e2)

### Docker Resources

11. [vLLM Docker Hub](https://hub.docker.com/r/vllm/vllm-openai/tags)
12. [Getting Started with vLLM Docker](https://www.remio.ai/post/getting-started-with-vllm-docker-gpu-powered-inference-using-the-official-vllm-vllm-openai-image)
13. [vLLM Dockerfile Documentation](https://docs.vllm.ai/en/stable/contributing/dockerfile/dockerfile.html)

### Deployment Guides

14. [DeepSeek R1 Deployment - Northflank](https://northflank.com/guides/deploy-deepseek-r1-vllm-northflank-ai-llm)
15. [DeepSeek R1 with vLLM V1 - AMD ROCm](https://rocm.docs.amd.com/projects/ai-developer-hub/en/latest/notebooks/inference/vllm_v1_DSR1.html)
16. [DeepSeek-R1 Model Deployment - Apolo](https://docs.apolo.us/index/examples-use-cases/llms/deepseek-r1-model-deployment)

### Performance and Optimization

17. [DeepSeek Hardware Guide](https://www.bardeen.ai/answers/what-hardware-does-deepseek-use)
18. [DeepSeek System Requirements](https://www.oneclickitsolution.com/centerofexcellence/aiml/deepseek-models-minimum-system-requirements)
19. [GPU Hardware Requirements 2025](https://www.proxpc.com/blogs/gpu-hardware-requirements-guide-for-deepseek-models-in-2025)
20. [DeepSeek R1 Hardware Requirements](https://www.geeky-gadgets.com/hardware-requirements-for-deepseek-r1-ai-models/)

---

## Appendix A: vLLM Server Startup Script

```bash
#!/bin/bash
# scripts/start_vllm_deepseek.sh

set -e

echo "Starting DeepSeek-OCR vLLM server..."

# Configuration
MODEL="deepseek-ai/DeepSeek-OCR"
PORT=8000
GPU_MEMORY_UTIL=0.95
MAX_MODEL_LEN=8192

# Check GPU availability
if ! command -v nvidia-smi &> /dev/null; then
    echo "Error: nvidia-smi not found. Is CUDA installed?"
    exit 1
fi

# Check GPU memory
GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
if [ "$GPU_MEM" -lt 16000 ]; then
    echo "Warning: GPU has less than 16GB VRAM. Consider using quantization."
fi

# Start vLLM server
echo "Starting vLLM server on port $PORT..."
vllm serve "$MODEL" \
  --port "$PORT" \
  --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
  --max-model-len "$MAX_MODEL_LEN" \
  --trust-remote-code
```

---

## Appendix B: Health Check Script

```bash
#!/bin/bash
# scripts/check_vllm_health.sh

VLLM_URL="${VLLM_URL:-http://localhost:8000}"

echo "Checking vLLM server health at $VLLM_URL..."

# Check if server is reachable
if ! curl -s -f "$VLLM_URL/health" > /dev/null; then
    echo "❌ vLLM server is not healthy or not reachable"
    exit 1
fi

echo "✅ vLLM server is healthy"

# Get model info
echo "Fetching model information..."
curl -s "$VLLM_URL/v1/models" | python3 -m json.tool

exit 0
```

---

## Appendix C: Docker Compose Full Configuration

```yaml
# docker-compose.vllm.yml
version: '3.8'

services:
  vllm-deepseek:
    image: vllm/vllm-openai:latest
    container_name: deepseek-ocr-vllm
    runtime: nvidia
    restart: unless-stopped

    environment:
      - HF_TOKEN=${HF_TOKEN}
      - CUDA_VISIBLE_DEVICES=0
      - VLLM_LOGGING_LEVEL=INFO

    volumes:
      # Model cache
      - ~/.cache/huggingface:/root/.cache/huggingface
      # Logs
      - ./logs/vllm:/logs

    ports:
      - "8000:8000"

    ipc: host

    command: >
      vllm serve deepseek-ai/DeepSeek-OCR
      --port 8000
      --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor
      --no-enable-prefix-caching
      --mm-processor-cache-gb 0
      --gpu-memory-utilization 0.95
      --max-model-len 8192
      --trust-remote-code

    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  # Optional: Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  prometheus_data:
```

---

**End of Document**

**Next Steps for Sprint 4:**
1. Review this planning document with the team
2. Approve hardware/cloud resources
3. Assign developers to implementation tasks
4. Begin Day 1 implementation
5. Track progress against timeline
6. Report blockers daily

**Questions or Concerns:**
Contact: Dev-01 (Sprint 3 Planning Lead)
