# Configuration Files

TOML configuration files for different environments.

## Overview

Layered configuration system with environment-specific overrides.

## Files

### `default.toml`
**Purpose:** Production defaults
**Use case:** Deployed systems, high-resource environments

```toml
[app]
name = "docling-hybrid-ocr"
version = "0.1.0"
environment = "production"

[logging]
level = "INFO"
format = "json"

[resources]
max_workers = 8              # High concurrency
max_memory_mb = 16384        # 16 GB
page_render_dpi = 200        # High quality
http_timeout_s = 120
http_retry_attempts = 3

[backends]
default = "nemotron-openrouter"

[[backends.candidates]]
name = "nemotron-openrouter"
model = "nvidia/nemotron-nano-12b-v2-vl:free"
base_url = "https://openrouter.ai/api/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
```

### `local.toml`
**Purpose:** Local development with resource constraints
**Use case:** 12GB RAM machines, local development, testing

```toml
[app]
environment = "development"

[logging]
level = "DEBUG"
format = "text"              # More readable for dev

[resources]
max_workers = 2              # Reduced concurrency
max_memory_mb = 4096         # 4 GB limit
page_render_dpi = 150        # Lower DPI for speed
http_timeout_s = 60
http_retry_attempts = 2

[backends]
default = "nemotron-openrouter"

# Same backend config as default
```

### `test.toml`
**Purpose:** Automated testing
**Use case:** CI/CD, test suite execution

```toml
[app]
environment = "test"

[logging]
level = "WARNING"            # Reduce test noise
format = "text"

[resources]
max_workers = 1              # Sequential processing
max_memory_mb = 2048         # Minimal resources
page_render_dpi = 72         # Fastest rendering
http_timeout_s = 30
http_retry_attempts = 1

[backends]
default = "mock-backend"     # Use mocks in tests
```

## Configuration Hierarchy

Configuration is loaded in priority order:

1. **Environment variables** (highest priority)
   ```bash
   DOCLING_HYBRID_LOG_LEVEL=DEBUG
   DOCLING_HYBRID_MAX_WORKERS=4
   ```

2. **User-specified config file**
   ```bash
   export DOCLING_HYBRID_CONFIG=configs/local.toml
   # OR
   docling-hybrid-ocr --config configs/local.toml convert ...
   ```

3. **Default config** (`configs/default.toml`)

## Usage

### Load config in code
```python
from pathlib import Path
from docling_hybrid.common.config import init_config

# Load specific config
config = init_config(Path("configs/local.toml"))

# Load default
config = init_config()  # Uses configs/default.toml
```

### Environment variable overrides

All config values can be overridden with environment variables using the prefix `DOCLING_HYBRID_`:

```bash
# Override log level
export DOCLING_HYBRID_LOG_LEVEL=DEBUG

# Override DPI
export DOCLING_HYBRID_PAGE_RENDER_DPI=150

# Override max workers
export DOCLING_HYBRID_MAX_WORKERS=2

# Override default backend
export DOCLING_HYBRID_DEFAULT_BACKEND=deepseek-vllm
```

## Environment-Specific Recommendations

### Production (default.toml)
- High resource limits
- JSON logging for parsing
- INFO level for important events only
- Multiple retry attempts
- Higher DPI for quality

### Local Development (local.toml)
- Lower resource limits (12GB RAM)
- Text logging for readability
- DEBUG level for detailed output
- Lower DPI for faster iteration
- Reduced concurrency

### Testing (test.toml)
- Minimal resources
- Minimal logging (WARNING only)
- Single worker (deterministic)
- Low DPI for speed
- Mock backends

## Adding Custom Configurations

Create a new TOML file in this directory:

```toml
# configs/my-custom.toml
[app]
environment = "custom"

[resources]
max_workers = 4
page_render_dpi = 175

# ... other settings
```

Load it:
```bash
export DOCLING_HYBRID_CONFIG=configs/my-custom.toml
docling-hybrid-ocr convert document.pdf
```

## Configuration Schema

See `src/docling_hybrid/common/config.py` for the complete schema and validation rules.

## See Also

- [../src/docling_hybrid/common/README.md](../src/docling_hybrid/common/README.md) - Configuration system
- [../CLAUDE.md](../CLAUDE.md) - Configuration patterns
- [../.env.example](../.env.example) - Environment variables
