# Development Schedule - Quick Reference

## Visual Timeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         STAGE 1: MINIMAL SYSTEM (OpenRouter)                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  Week 1-2        Week 3-4        Week 5-6        Week 7-8                               │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                               │
│  │ Sprint 1│───▶│ Sprint 2│───▶│ Sprint 3│───▶│ Sprint 4│    ★ v0.1.0 Release          │
│  │Foundation│   │  Core   │    │ Pipeline│    │ Polish  │                               │
│  │Interfaces│   │  Impl   │    │  & CLI  │    │ Release │                               │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                               │
│       ↓              ↓              ↓              ↓                                    │
│  [Contracts]    [Renderer]     [Pipeline]    [Concurrent]                               │
│  [Config]       [Nemotron]     [CLI]         [Docker]                                   │
│  [CI/CD]        [Factory]      [E2E Tests]   [Real API]                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                         STAGE 2: FULL SYSTEM (DeepSeek + Extensions)                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  Week 9-10       Week 11-12      Week 13-14      Week 15-16                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                               │
│  │ Sprint 5│───▶│ Sprint 6│───▶│ Sprint 7│───▶│ Sprint 8│    ★ v1.0.0 Release          │
│  │DeepSeek │    │  Block  │    │  Multi  │    │  Eval   │                               │
│  │Backends │    │Processing│   │ Backend │    │ Release │                               │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                               │
│       ↓              ↓              ↓              ↓                                    │
│  [vLLM]         [Segment]      [Merge]        [Metrics]                                 │
│  [MLX]          [Routing]      [Arbitrate]    [Benchmark]                               │
│  [Compare]      [Region]       [Vote]         [Release]                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Team Assignment Matrix

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              DEVELOPER DOMAINS                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   D01 ─────────────────────────────────────────────────────────────▶ TECH LEAD │
│        Architecture • Integration • Code Review • Release                       │
│                                                                                 │
│   D02 ─────────────────────────────────────────────────────────────▶ BACKENDS  │
│        base.py • factory.py • openrouter.py • deepseek_*.py                    │
│                                                                                 │
│   D03 ─────────────────────────────────────────────────────────────▶ PIPELINE  │
│        interfaces.py • pipeline.py • routing.py • merging.py                   │
│                                                                                 │
│   D04 ─────────────────────────────────────────────────────────────▶ INFRA     │
│        config.py • logging.py • http.py • CI/CD • Docker                       │
│                                                                                 │
│   D05 ─────────────────────────────────────────────────────────────▶ RENDERER  │
│        base.py • pypdfium.py • region rendering                                │
│                                                                                 │
│   D06 ─────────────────────────────────────────────────────────────▶ CLI/UX    │
│        main.py • commands/* • help text • error messages                       │
│                                                                                 │
│   D07 ─────────────────────────────────────────────────────────────▶ TESTING   │
│        conftest.py • fixtures • mocks • integration tests                      │
│                                                                                 │
│   D08 ─────────────────────────────────────────────────────────────▶ DOCS      │
│        CLAUDE.md • guides/* • examples/* • API docs                            │
│                                                                                 │
│   D09 ─────────────────────────────────────────────────────────────▶ BLOCKS    │
│        base.py • types.py • segmenter.py • Docling integration                 │
│                                                                                 │
│   D10 ─────────────────────────────────────────────────────────────▶ EVAL      │
│        base.py • types.py • metrics.py • benchmarks                            │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Sprint-by-Sprint Goals

### STAGE 1: Minimal Functioning System

| Sprint | Theme | Key Deliverables | Success Criteria |
|--------|-------|------------------|------------------|
| **S1** | Foundation | Interfaces, Config, CI/CD | All interfaces frozen, CI green |
| **S2** | Core | Renderer, Nemotron Backend | Unit tests >85%, mocked integration works |
| **S3** | Pipeline | HybridPipeline, CLI | E2E flow works with mock |
| **S4** | Polish | Concurrency, Real API | v0.1.0 released |

### STAGE 2: Full Local System

| Sprint | Theme | Key Deliverables | Success Criteria |
|--------|-------|------------------|------------------|
| **S5** | DeepSeek | vLLM + MLX backends | Local inference works |
| **S6** | Blocks | Segmentation, Routing | Block-level OCR works |
| **S7** | Multi-Backend | Merging, Arbitration | Multiple backends per block |
| **S8** | Evaluation | Metrics, Benchmarks | v1.0.0 released |

## File Ownership Quick Reference

### Never Touch Without Owner Approval

| Owner | Protected Files |
|-------|----------------|
| D01 | `pyproject.toml`, `docs/ARCHITECTURE.md` |
| D02 | `backends/*` |
| D03 | `orchestrator/*` |
| D04 | `common/*`, `configs/*`, `.github/*` |
| D05 | `renderer/*` |
| D06 | `cli/*` |
| D07 | `tests/conftest.py`, `tests/mocks/*` |
| D08 | `CLAUDE.md`, `docs/guides/*` |
| D09 | `blocks/*` |
| D10 | `eval/*` |

## Integration Schedule

```
Sprint N Timeline:
├── Days 1-8: Development
│   ├── Day 1: Sprint kickoff
│   ├── Days 2-7: Implementation
│   └── Day 8: PR ready, review started
├── Days 9-10: Integration
│   ├── Day 9 AM: Demo & PR review
│   ├── Day 9 PM: Merge sequence
│   ├── Day 10 AM: Full test suite
│   └── Day 10 PM: Retrospective + next sprint planning
└── Weekend: Buffer / Spillover
```

## Merge Order (Each Sprint)

```
Priority Order for Merging:

1. Foundation (D04)
   └── common/*, configs/*

2. Interfaces (D02, D03, D05)
   └── */base.py, */types.py, */interfaces.py

3. Implementations (D02, D05, D03, D06)
   └── */core implementations

4. Tests (D07)
   └── tests/*

5. Documentation (D08)
   └── docs/*, CLAUDE.md, etc.
```

## Dependency Flow

```
                    ┌─────────────┐
                    │   common    │  Layer 0
                    │  (D04)      │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │ backends │     │ renderer │     │  blocks  │  Layer 1
   │  (D02)   │     │  (D05)   │     │  (D09)   │
   └────┬─────┘     └────┬─────┘     └────┬─────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  ┌──────────────┐
                  │ orchestrator │  Layer 2
                  │    (D03)     │
                  └──────┬───────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        ┌──────────┐          ┌──────────┐
        │   CLI    │          │   eval   │  Layer 3
        │  (D06)   │          │  (D10)   │
        └──────────┘          └──────────┘
```

## Communication Protocol

### Daily
- **09:00** Async standup in Slack/Teams
- **Format**: "Yesterday: X | Today: Y | Blockers: Z"

### Weekly
- **Monday 10:00**: Sprint sync (30 min)
- **Friday 15:00**: Demo prep (30 min)

### Integration Period (Days 9-10)
- **Day 9 09:00**: Demo meeting (2 hours)
- **Day 9 14:00**: Merge session (4 hours)
- **Day 10 09:00**: Test & verify (3 hours)
- **Day 10 14:00**: Retro + planning (3 hours)

## PR Requirements

```yaml
Required for PR Approval:
  - CI passes (all checks green)
  - At least 1 approval from:
    - Owner of dependent module, OR
    - Tech Lead (D01)
  - No merge conflicts
  - Documentation updated (if applicable)
  - Tests included for new code
  - Coverage not decreased

PR Naming: feat/sN-description (e.g., feat/s2-nemotron-backend)
Branch from: develop
Merge to: develop
```

## Emergency Escalation

```
Level 1: DM the file owner
Level 2: Post in team channel with @owner
Level 3: Escalate to D01 (Tech Lead)
Level 4: Emergency meeting (schedule immediately)

Blocking Issues:
- File ownership conflicts → D01 arbitrates
- Interface changes needed → All affected owners + D01
- CI/CD broken → D04 + D01 immediately
- Security issue → D01 + all hands immediately
```

## Key Milestones

| Week | Milestone | Gate Criteria |
|------|-----------|---------------|
| 2 | Interfaces Frozen | All interfaces approved, documented |
| 4 | Core Complete | Renderer + Backend work together |
| 6 | E2E Working | CLI converts PDF with mock backend |
| 8 | **Stage 1 Release** | v0.1.0 with OpenRouter working |
| 10 | Local Backends | DeepSeek vLLM + MLX working |
| 12 | Block Processing | Block-level OCR functional |
| 14 | Multi-Backend | Merging strategies working |
| 16 | **Stage 2 Release** | v1.0.0 with full feature set |

---

## Quick Commands

```bash
# Development
pip install -e ".[dev]"        # Install in dev mode
pytest tests/unit -v           # Run unit tests
pytest tests/integration -v    # Run integration tests
ruff check src/                # Linting
mypy src/                      # Type checking

# CLI
docling-hybrid-ocr convert doc.pdf        # Basic conversion
docling-hybrid-ocr convert doc.pdf -v     # Verbose
docling-hybrid-ocr backends               # List backends
docling-hybrid-ocr info                   # System info

# Git workflow
git checkout develop
git pull origin develop
git checkout -b feat/sN-description
# ... make changes ...
git push -u origin feat/sN-description
# Create PR to develop
```

## Contact Matrix

| Area | Primary | Backup |
|------|---------|--------|
| Architecture | D01 | D03 |
| Backends | D02 | D03 |
| Pipeline | D03 | D02 |
| Infrastructure | D04 | D01 |
| Renderer | D05 | D04 |
| CLI | D06 | D08 |
| Testing | D07 | D04 |
| Documentation | D08 | D06 |
| Blocks | D09 | D03 |
| Evaluation | D10 | D09 |
