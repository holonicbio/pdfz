# Team Quick Reference Card

## Developer Assignments

| ID | Name | Role | Primary Files | Contact Priority |
|----|------|------|--------------|-----------------|
| D01 | Tech Lead | Architecture | All (review) | Integration issues |
| D02 | Backend Lead | `backends/*` | Backend problems |
| D03 | Pipeline Lead | `orchestrator/*` | Pipeline issues |
| D04 | Infrastructure | `common/*`, CI | Config, retry, CI |
| D05 | Renderer | `renderer/*` | PDF rendering |
| D06 | CLI Lead | `cli/*` | CLI, user experience |
| D07 | Testing Lead | `tests/*` | Test infrastructure |
| D08 | Documentation | `docs/*` | Documentation |
| D09 | Block Processing | `blocks/*` | Block segmentation |
| D10 | Evaluation | `eval/*` | Metrics, benchmarks |

---

## Sprint 1 Tasks At a Glance

### P0 (Must Complete)
| Task ID | Owner | Task | Dependency |
|---------|-------|------|------------|
| S1-D04-01 | D04 | Retry utilities module | None |
| S1-D07-01 | D07 | HTTP mocking infrastructure | None |
| S1-D02-01 | D02 | Backend retry logic | S1-D04-01 |
| S1-D03-01 | D03 | Concurrent page processing | None |

### P1 (Should Complete)
| Task ID | Owner | Task |
|---------|-------|------|
| S1-D05-01 | D05 | Renderer memory optimization |
| S1-D06-01 | D06 | CLI error messages |
| S1-D07-02 | D07 | Backend integration tests |

### P2 (Nice to Have)
| Task ID | Owner | Task |
|---------|-------|------|
| S1-D08-01 | D08 | Update CLAUDE.md |
| S1-D09-01 | D09 | Block processing research |
| S1-D10-01 | D10 | Evaluation metrics research |

---

## Branch Naming Convention

```
feat/sN-description     # Feature: feat/s1-backend-retry
fix/sN-description      # Bug fix: fix/s2-memory-leak
refactor/sN-description # Refactor: refactor/s3-pipeline
docs/sN-description     # Docs: docs/s1-api-guide
test/sN-description     # Tests: test/s1-backend-mocks
```

---

## PR Checklist

```markdown
## PR Checklist
- [ ] CI passes
- [ ] Code reviewed by file owner or D01
- [ ] Tests added for new code
- [ ] Documentation updated (if applicable)
- [ ] No decrease in coverage
- [ ] Branch named correctly (feat/sN-xxx)
- [ ] No merge conflicts with develop
```

---

## Key File Locations

```
src/docling_hybrid/
├── __init__.py           # Package version
├── backends/
│   ├── base.py           # Backend ABC
│   ├── factory.py        # Backend factory
│   └── openrouter_nemotron.py  # Working backend
├── common/
│   ├── config.py         # Configuration
│   ├── errors.py         # Exception hierarchy
│   ├── ids.py            # ID generation
│   ├── logging.py        # Structured logging
│   └── models.py         # Pydantic models
├── renderer/
│   └── core.py           # PDF rendering
├── orchestrator/
│   ├── pipeline.py       # Main pipeline
│   └── models.py         # Pipeline models
└── cli/
    └── main.py           # CLI commands

configs/
├── default.toml          # Production defaults
└── local.toml            # Development config

tests/
├── conftest.py           # Shared fixtures
└── unit/                 # Unit tests
```

---

## Common Commands

```bash
# Development setup
source .venv/bin/activate
source .env.local

# Run tests
pytest tests/unit -v                    # Unit tests
pytest tests/unit --cov=src -v          # With coverage
pytest tests/unit -k "test_backend" -v  # Specific tests

# Code quality
ruff check src/                         # Linting
mypy src/docling_hybrid                 # Type checking

# CLI
docling-hybrid-ocr convert doc.pdf      # Basic conversion
docling-hybrid-ocr backends             # List backends
docling-hybrid-ocr info                 # System info

# Git workflow
git checkout -b feat/s1-your-feature
git push -u origin feat/s1-your-feature
```

---

## Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-xxx           # OpenRouter API key

# Optional overrides
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=DEBUG
DOCLING_HYBRID_MAX_WORKERS=2
```

---

## Integration Days Schedule

### Day 9
| Time | Activity | Participants |
|------|----------|-------------|
| 09:00 | Sprint Review | All |
| 11:00 | PR Status | D01 |
| 14:00 | Merge Session | D01 + owners |
| 18:00 | Status Check | D01, D07 |

### Day 10
| Time | Activity | Participants |
|------|----------|-------------|
| 09:00 | Full Tests | D07 |
| 11:00 | Docs Review | D08 |
| 14:00 | Retrospective | All |
| 15:30 | Next Sprint Plan | All |

---

## Escalation Path

```
1. DM the file owner (see assignments above)
2. Post in #team-channel with @owner
3. Escalate to D01 (Tech Lead)
4. Request emergency meeting
```

---

## Sprint 1 Dependencies Graph

```
S1-D04-01 (Retry Utils)
    │
    └──▶ S1-D02-01 (Backend Retry)
                │
                └──▶ S1-D07-02 (Integration Tests)

S1-D07-01 (HTTP Mocks)
    │
    └──▶ S1-D07-02 (Integration Tests)

S1-D03-01 (Concurrent Pages) [independent]

S1-D05-01 (Renderer) [independent]

S1-D06-01 (CLI) [independent]

S1-D08-01 (Docs) [independent]

S1-D09-01 (Block Research) [independent]

S1-D10-01 (Eval Research) [independent]
```

**Merge Order:**
1. S1-D04-01 (Retry Utils) - foundation
2. S1-D07-01 (HTTP Mocks) - foundation
3. S1-D02-01 (Backend Retry)
4. S1-D03-01 (Concurrent Pages)
5. S1-D05-01 (Renderer)
6. S1-D06-01 (CLI)
7. S1-D07-02 (Integration Tests)
8. S1-D08-01 (Docs)
9. S1-D09-01 (Block Research) - merge design doc
10. S1-D10-01 (Eval Research) - merge design doc
