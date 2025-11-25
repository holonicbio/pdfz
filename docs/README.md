# Documentation

Comprehensive documentation for Docling Hybrid OCR.

## Overview

This directory contains all project documentation including architecture specs, user guides, API references, and development guides.

## Directory Structure

```
docs/
├── README.md                            # This file
├── ARCHITECTURE.md                      # System architecture overview
├── API.md                               # Python API documentation
├── API_REFERENCE.md                     # Detailed API reference
├── QUICK_START.md                       # Getting started guide
├── CLI_GUIDE.md                         # Command-line interface guide
├── TROUBLESHOOTING.md                   # Common issues and solutions
├── OPENROUTER_SETUP.md                  # OpenRouter API setup
├── OPENROUTER_TESTING.md                # Testing with OpenRouter
├── DEPLOYMENT.md                        # Deployment guide
├── DOCKER.md                            # Docker usage
├── FUTURE_EXTENSIONS.md                 # Planned features
├── DEVELOPMENT_SCHEDULE.md              # Development timeline
├── SCHEDULE_QUICK_REFERENCE.md          # Quick schedule overview
├── SPRINT_PLAN.md                       # Sprint planning
├── SPRINT1_INTEGRATION_CHECKLIST.md     # Sprint 1 tasks
├── SPRINT1_CONCURRENT_PROCESSING_STRATEGY.md
├── PARALLEL_DEVELOPMENT_PLAN.md         # Parallel development strategy
├── components/                          # Component specifications
│   └── BACKENDS.md                      # Backend implementation details
├── design/                              # Design documents
│   ├── BLOCK_PROCESSING.md              # Block-level processing design
│   └── EVALUATION.md                    # Evaluation framework design
└── interfaces/                          # API interface specifications
```

## Documentation Categories

### User Documentation

**Getting Started**
- [QUICK_START.md](./QUICK_START.md) - Quick start guide
- [CLI_GUIDE.md](./CLI_GUIDE.md) - Command-line usage
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common problems and solutions

**Setup and Configuration**
- [OPENROUTER_SETUP.md](./OPENROUTER_SETUP.md) - Setting up OpenRouter API
- [OPENROUTER_TESTING.md](./OPENROUTER_TESTING.md) - Testing your setup
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deploying the system
- [DOCKER.md](./DOCKER.md) - Using Docker

### Developer Documentation

**Architecture and Design**
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview
- [components/BACKENDS.md](./components/BACKENDS.md) - Backend implementations
- [design/BLOCK_PROCESSING.md](./design/BLOCK_PROCESSING.md) - Block processing design
- [design/EVALUATION.md](./design/EVALUATION.md) - Evaluation framework

**API Documentation**
- [API.md](./API.md) - Python API guide
- [API_REFERENCE.md](./API_REFERENCE.md) - Detailed API reference
- `interfaces/` - Interface specifications

**Development Planning**
- [DEVELOPMENT_SCHEDULE.md](./DEVELOPMENT_SCHEDULE.md) - Development timeline
- [SPRINT_PLAN.md](./SPRINT_PLAN.md) - Sprint planning
- [SPRINT1_INTEGRATION_CHECKLIST.md](./SPRINT1_INTEGRATION_CHECKLIST.md) - Sprint 1 tasks
- [PARALLEL_DEVELOPMENT_PLAN.md](./PARALLEL_DEVELOPMENT_PLAN.md) - Parallel dev strategy
- [FUTURE_EXTENSIONS.md](./FUTURE_EXTENSIONS.md) - Planned features

## Key Documents

### ARCHITECTURE.md
Complete system architecture including:
- Component overview
- Data flow diagrams
- Backend architecture
- Pipeline design
- Extension points

### API.md
Python API documentation:
- Installation
- Basic usage
- Advanced patterns
- Configuration
- Error handling

### TROUBLESHOOTING.md
Comprehensive troubleshooting guide:
- Installation issues
- Configuration problems
- API errors
- Performance issues
- Common mistakes

### CLI_GUIDE.md
Command-line interface guide:
- All commands
- Options and flags
- Examples
- Tips and tricks

### DEPLOYMENT.md
Deployment instructions:
- System requirements
- Installation steps
- Configuration
- Monitoring
- Scaling

## Documentation Standards

### File Organization
- Use `.md` extension for all docs
- Use `UPPERCASE_WITH_UNDERSCORES.md` for top-level docs
- Use subdirectories for categorization

### Writing Style
- Clear, concise language
- Code examples for concepts
- Use headings for navigation
- Include table of contents for long docs

### Code Examples
```python
# Good: Complete, runnable example
from pathlib import Path
from docling_hybrid import init_config, HybridPipeline

config = init_config(Path("configs/local.toml"))
pipeline = HybridPipeline(config)
result = await pipeline.convert_pdf(Path("document.pdf"))
print(result.markdown)
```

### Internal Links
```markdown
See [ARCHITECTURE.md](./ARCHITECTURE.md) for details.
See [Backend README](../src/docling_hybrid/backends/README.md)
```

## Contributing to Documentation

### Adding New Documentation

1. **Determine category:**
   - User guide → Root level
   - Component spec → `components/`
   - Design doc → `design/`
   - Interface spec → `interfaces/`

2. **Create file:**
   ```bash
   touch docs/MY_NEW_DOC.md
   ```

3. **Add to README:**
   Update this file with link to new doc

4. **Follow template:**
   ```markdown
   # Document Title

   Brief description.

   ## Overview
   ...

   ## Details
   ...

   ## Examples
   ...

   ## See Also
   - [Related Doc](./RELATED.md)
   ```

### Updating Existing Documentation

1. Check if information is outdated
2. Update relevant sections
3. Update "Last Updated" date if present
4. Cross-reference with code changes

### Documentation Review

Before committing documentation changes:
- [ ] Spelling and grammar checked
- [ ] Code examples tested
- [ ] Links verified
- [ ] Cross-references updated
- [ ] README index updated if needed

## Documentation Tools

### Markdown Linting
```bash
# Install markdownlint
npm install -g markdownlint-cli

# Lint docs
markdownlint docs/**/*.md
```

### Link Checking
```bash
# Install markdown-link-check
npm install -g markdown-link-check

# Check links
find docs -name "*.md" -exec markdown-link-check {} \;
```

### Documentation Preview
```bash
# Using grip (GitHub-flavored markdown preview)
pip install grip
grip docs/ARCHITECTURE.md
# Opens in browser at http://localhost:6419
```

## See Also

- [../CLAUDE.md](../CLAUDE.md) - Master development context
- [../README.md](../README.md) - Project README
- [../src/docling_hybrid/README.md](../src/docling_hybrid/README.md) - Source code overview
