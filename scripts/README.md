# Utility Scripts

Bash scripts and utilities for development, setup, and maintenance.

## Scripts

### `setup.sh`
**Purpose:** Initial project setup

```bash
./scripts/setup.sh
```

**What it does:**
1. Creates Python virtual environment
2. Installs dependencies from `pyproject.toml`
3. Sets up development tools (ruff, mypy, pytest)
4. Creates necessary directories
5. Verifies installation

**Usage:**
```bash
# First time setup
cd docling-hybrid-ocr
./scripts/setup.sh

# Activate environment
source .venv/bin/activate
```

### `setup_env.sh`
**Purpose:** Load environment variables and API keys

```bash
source ./scripts/setup_env.sh
```

**What it does:**
1. Reads API key from `openrouter_key` file
2. Exports `OPENROUTER_API_KEY` environment variable
3. Sources `.env.local` if it exists
4. Verifies key is set

**Usage:**
```bash
# Create key file
echo 'sk-or-v1-your-key-here' > openrouter_key

# Load environment
source ./scripts/setup_env.sh

# Verify
echo $OPENROUTER_API_KEY
```

### `cleanup.sh`
**Purpose:** Clean build artifacts and temporary files

```bash
./scripts/cleanup.sh
```

**What it cleans:**
- Python cache (`__pycache__`, `*.pyc`)
- Build directories (`build/`, `dist/`, `*.egg-info`)
- Test cache (`.pytest_cache/`)
- Coverage reports (`.coverage`, `htmlcov/`)
- Temporary files

**Usage:**
```bash
# Before committing
./scripts/cleanup.sh
```

### `install-hooks.sh`
**Purpose:** Install git hooks for environment setup

```bash
./scripts/install-hooks.sh
```

**What it does:**
1. Installs post-checkout hook
2. Reminds to run `source ./scripts/setup_env.sh` after checkout
3. Helps prevent "missing API key" errors

**Usage:**
```bash
# One-time setup
./scripts/install-hooks.sh

# Now git will remind you to source environment
git checkout main
# → Reminder: source ./scripts/setup_env.sh
```

### `docker-build.sh`
**Purpose:** Build Docker image for the application

```bash
./scripts/docker-build.sh
```

**What it does:**
1. Builds Docker image with all dependencies
2. Tags image as `docling-hybrid-ocr:latest`
3. Runs basic smoke tests

**Usage:**
```bash
# Build image
./scripts/docker-build.sh

# Run container
docker run -v $(pwd):/work -it docling-hybrid-ocr:latest convert /work/document.pdf
```

### `generate_test_pdfs.py`
**Purpose:** Generate sample PDF files for testing

```bash
python scripts/generate_test_pdfs.py
```

**What it generates:**
- `simple.pdf` - Single page with text
- `multi_page.pdf` - Multiple pages
- `with_tables.pdf` - PDF with table content
- `complex.pdf` - Complex layouts

**Usage:**
```bash
# Generate test PDFs
python scripts/generate_test_pdfs.py --output-dir tests/fixtures/sample_pdfs

# Use in tests
pytest tests/integration/test_pipeline_e2e.py
```

### Shell Completion Scripts

**`completion.bash`** - Bash completion
**`completion.zsh`** - Zsh completion

Install completion for your shell:

```bash
# Bash
source scripts/completion.bash

# Zsh
source scripts/completion.zsh

# Permanent install (Bash)
echo 'source ~/docling-hybrid-ocr/scripts/completion.bash' >> ~/.bashrc

# Permanent install (Zsh)
echo 'source ~/docling-hybrid-ocr/scripts/completion.zsh' >> ~/.zshrc
```

See `COMPLETIONS.md` for detailed instructions.

## Common Workflows

### First-Time Setup
```bash
# 1. Run setup
./scripts/setup.sh

# 2. Create API key file
echo 'sk-or-v1-...' > openrouter_key

# 3. Load environment
source ./scripts/setup_env.sh

# 4. Install hooks (optional)
./scripts/install-hooks.sh

# 5. Run tests
pytest tests/unit -v
```

### Daily Development
```bash
# Activate environment
source .venv/bin/activate

# Load API key
source ./scripts/setup_env.sh

# Do work...

# Clean up before commit
./scripts/cleanup.sh
git add .
git commit -m "..."
```

### CI/CD Pipeline
```bash
# Setup
./scripts/setup.sh

# Run tests (no API key needed for unit tests)
pytest tests/unit -v

# Run linting
ruff check src/

# Type checking
mypy src/docling_hybrid
```

## Environment Files

### `.env.local` (create from `.env.example`)
```bash
# Copy example
cp .env.example .env.local

# Edit with your settings
OPENROUTER_API_KEY=sk-or-v1-...
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=DEBUG
```

### `openrouter_key` (gitignored)
```bash
# Simple file containing just your API key
echo 'sk-or-v1-your-key-here' > openrouter_key

# Load with setup_env.sh
source ./scripts/setup_env.sh
```

## See Also

- [../CLAUDE.md](../CLAUDE.md) - Development workflow
- [../LOCAL_DEV.md](../LOCAL_DEV.md) - Local development guide
- [COMPLETIONS.md](./COMPLETIONS.md) - Shell completion guide
