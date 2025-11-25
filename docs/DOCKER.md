# Docker Deployment Guide

This guide covers deploying Docling Hybrid OCR using Docker for both development and production environments.

## Table of Contents
- [Quick Start](#quick-start)
- [Building the Image](#building-the-image)
- [Running with Docker](#running-with-docker)
- [Running with Docker Compose](#running-with-docker-compose)
- [Configuration](#configuration)
- [Volume Mounts](#volume-mounts)
- [Environment Variables](#environment-variables)
- [Resource Limits](#resource-limits)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Build the Image

```bash
# Using the build script (recommended)
./scripts/docker-build.sh

# Or using Docker directly
docker build -t docling-hybrid-ocr:latest .
```

### 2. Set Your API Key

```bash
# Create .env file in project root
echo "OPENROUTER_API_KEY=your-key-here" > .env
```

### 3. Convert a PDF

```bash
# Place your PDF in the input directory
mkdir -p input output
cp your-document.pdf input/

# Run conversion using Docker Compose
docker-compose run docling-hybrid convert /app/input/your-document.pdf -o /app/output/result.md

# Or using Docker directly
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /app/input/your-document.pdf -o /app/output/result.md
```

---

## Building the Image

### Using the Build Script

The `scripts/docker-build.sh` script provides a convenient interface:

```bash
# Basic build
./scripts/docker-build.sh build

# Build with custom tag
./scripts/docker-build.sh --tag v0.1.0 build

# Build without cache (fresh build)
./scripts/docker-build.sh --no-cache build

# Build for specific platform
./scripts/docker-build.sh --platform linux/amd64 build

# Test the image
./scripts/docker-build.sh test

# Show image size
./scripts/docker-build.sh size
```

### Using Docker Directly

```bash
# Basic build
docker build -t docling-hybrid-ocr:latest .

# Build without cache
docker build --no-cache -t docling-hybrid-ocr:latest .

# Build for specific platform
docker build --platform linux/amd64 -t docling-hybrid-ocr:latest .

# Multi-platform build (requires buildx)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t docling-hybrid-ocr:latest \
  .
```

### Image Size Optimization

The image uses a multi-stage build to minimize size:

- **Target size:** <500MB
- **Base:** python:3.11-slim (~150MB)
- **Application:** ~100-200MB with dependencies
- **Total:** Typically 250-350MB

To check image size:

```bash
docker images docling-hybrid-ocr:latest
```

---

## Running with Docker

### Basic Conversion

```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /app/input/document.pdf
```

### With Options

```bash
# Custom output path
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /app/input/document.pdf -o /app/output/custom-name.md

# Limit pages and set DPI
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /app/input/document.pdf --max-pages 5 --dpi 150

# Use custom config
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/configs:/app/configs:ro \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  -e DOCLING_HYBRID_CONFIG=/app/configs/local.toml \
  docling-hybrid-ocr:latest \
  convert /app/input/document.pdf
```

### CLI Commands

```bash
# Show help
docker run --rm docling-hybrid-ocr:latest --help

# List backends
docker run --rm docling-hybrid-ocr:latest backends

# Show info
docker run --rm docling-hybrid-ocr:latest info

# Health check
docker run --rm \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  health

# Validate config
docker run --rm \
  -v $(pwd)/configs:/app/configs:ro \
  docling-hybrid-ocr:latest \
  validate-config --config /app/configs/local.toml
```

### Interactive Shell

For debugging or exploration:

```bash
# Run interactive bash shell
docker run -it --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  --entrypoint /bin/bash \
  docling-hybrid-ocr:latest

# Inside container, you can run commands directly:
# docling-hybrid-ocr backends
# docling-hybrid-ocr convert /app/input/test.pdf
```

---

## Running with Docker Compose

Docker Compose simplifies running containers with persistent configurations.

### Basic Usage

```bash
# Start and run conversion (one-time)
docker-compose run docling-hybrid convert /app/input/document.pdf

# Start service in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Required
OPENROUTER_API_KEY=your-key-here

# Optional overrides
DOCLING_HYBRID_CONFIG=/app/configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=DEBUG
DOCLING_HYBRID_MAX_WORKERS=4
```

### Custom docker-compose.override.yml

For local development, create `docker-compose.override.yml`:

```yaml
version: "3.8"

services:
  docling-hybrid:
    # Override command for development
    command: ["info"]

    # Add development volumes
    volumes:
      - ./src:/app/src:ro
      - ./tests:/app/tests:ro

    # Development environment variables
    environment:
      - DOCLING_HYBRID_LOG_LEVEL=DEBUG
      - PYTHONUNBUFFERED=1
```

---

## Configuration

### Configuration Files

The container includes default configs at `/app/configs/`:

- `default.toml` - Production defaults
- `local.toml` - Development settings (12GB RAM)
- `test.toml` - Test configuration

### Overriding Configuration

**Method 1: Environment Variable**

```bash
docker run --rm \
  -e DOCLING_HYBRID_CONFIG=/app/configs/local.toml \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest convert input.pdf
```

**Method 2: Mount Custom Config**

```bash
# Create custom config
cp configs/default.toml my-config.toml
# Edit my-config.toml...

# Mount and use it
docker run --rm \
  -v $(pwd)/my-config.toml:/app/my-config.toml:ro \
  -e DOCLING_HYBRID_CONFIG=/app/my-config.toml \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest convert input.pdf
```

**Method 3: Mount Entire Configs Directory**

```bash
docker run --rm \
  -v $(pwd)/configs:/app/configs:ro \
  -e DOCLING_HYBRID_CONFIG=/app/configs/custom.toml \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest convert input.pdf
```

---

## Volume Mounts

### Input Directory (Read-Only)

```bash
-v $(pwd)/input:/app/input:ro
```

Mount your PDF files here. Read-only (`:ro`) prevents accidental modification.

### Output Directory (Read-Write)

```bash
-v $(pwd)/output:/app/output
```

Converted Markdown files are written here.

### Configs Directory (Read-Only)

```bash
-v $(pwd)/configs:/app/configs:ro
```

Optional: Mount custom configuration files.

### Complete Example

```bash
mkdir -p input output

docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/configs:/app/configs:ro \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /app/input/document.pdf -o /app/output/result.md
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes* | - | OpenRouter API key (required for nemotron backend) |
| `DOCLING_HYBRID_CONFIG` | No | `/app/configs/default.toml` | Path to config file |
| `DOCLING_HYBRID_LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DOCLING_HYBRID_MAX_WORKERS` | No | From config | Maximum concurrent workers |

*Required when using OpenRouter backends (default)

### Setting Environment Variables

**Docker CLI:**

```bash
docker run -e VAR_NAME=value ...
```

**Docker Compose (.env file):**

```bash
# .env
OPENROUTER_API_KEY=sk-...
DOCLING_HYBRID_LOG_LEVEL=DEBUG
```

**Docker Compose (inline):**

```yaml
services:
  docling-hybrid:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DOCLING_HYBRID_LOG_LEVEL=DEBUG
```

---

## Resource Limits

### Memory Limits

**Docker CLI:**

```bash
docker run --rm \
  --memory=4g \
  --memory-swap=4g \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest convert input.pdf
```

**Docker Compose:**

```yaml
services:
  docling-hybrid:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### CPU Limits

**Docker CLI:**

```bash
docker run --rm \
  --cpus=2 \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest convert input.pdf
```

**Docker Compose:**

```yaml
services:
  docling-hybrid:
    deploy:
      resources:
        limits:
          cpus: '2'
        reservations:
          cpus: '1'
```

### Recommended Limits

| Workload | Memory | CPUs | Workers |
|----------|--------|------|---------|
| Light (1-10 pages) | 2GB | 1-2 | 2 |
| Medium (10-50 pages) | 4GB | 2-4 | 4 |
| Heavy (50+ pages) | 8GB+ | 4-8 | 8 |

---

## Production Deployment

### Docker Swarm

```yaml
version: "3.8"

services:
  docling-hybrid:
    image: docling-hybrid-ocr:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - /data/input:/app/input:ro
      - /data/output:/app/output
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docling-hybrid-ocr
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docling-hybrid-ocr
  template:
    metadata:
      labels:
        app: docling-hybrid-ocr
    spec:
      containers:
      - name: docling-hybrid
        image: docling-hybrid-ocr:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: docling-secrets
              key: openrouter-api-key
        volumeMounts:
        - name: input
          mountPath: /app/input
          readOnly: true
        - name: output
          mountPath: /app/output
      volumes:
      - name: input
        persistentVolumeClaim:
          claimName: docling-input-pvc
      - name: output
        persistentVolumeClaim:
          claimName: docling-output-pvc
```

### Health Checks

The container includes a health check that runs every 30 seconds:

```bash
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD docling-hybrid-ocr health || exit 1
```

To check health manually:

```bash
docker exec <container-id> docling-hybrid-ocr health
```

---

## Troubleshooting

### Image Build Fails

**Problem:** Build fails during wheel creation

```bash
# Solution: Clear Docker cache and rebuild
docker builder prune
./scripts/docker-build.sh --no-cache build
```

**Problem:** Image size exceeds 500MB

```bash
# Check layer sizes
docker history docling-hybrid-ocr:latest

# Identify large layers and optimize Dockerfile
./scripts/docker-build.sh size
```

### Container Fails to Start

**Problem:** Missing API key

```bash
# Error: "Missing OPENROUTER_API_KEY"
# Solution: Set environment variable
docker run -e OPENROUTER_API_KEY=your-key ...
```

**Problem:** Permission denied on volumes

```bash
# Solution: Check directory permissions
chmod 755 input output
```

### Conversion Errors

**Problem:** Out of memory

```bash
# Solution: Increase memory limit
docker run --memory=8g ...

# Or reduce workers in config
-e DOCLING_HYBRID_MAX_WORKERS=2
```

**Problem:** Backend timeout

```bash
# Solution: Use local config with lower DPI
docker run \
  -e DOCLING_HYBRID_CONFIG=/app/configs/local.toml \
  docling-hybrid-ocr:latest convert input.pdf --dpi 100
```

### Debugging

**Enable verbose logging:**

```bash
docker run \
  -e DOCLING_HYBRID_LOG_LEVEL=DEBUG \
  docling-hybrid-ocr:latest convert input.pdf --verbose
```

**Run interactive shell:**

```bash
docker run -it --rm \
  -v $(pwd)/input:/app/input:ro \
  --entrypoint /bin/bash \
  docling-hybrid-ocr:latest

# Inside container:
ls -la /app
docling-hybrid-ocr info
python -c "import docling_hybrid; print(docling_hybrid.__version__)"
```

**Check logs:**

```bash
# Docker Compose
docker-compose logs -f docling-hybrid

# Docker (running container)
docker logs <container-id> -f
```

---

## Advanced Usage

### Running with vLLM Backend

If you have a local vLLM server, uncomment the vLLM service in `docker-compose.yml`:

```yaml
services:
  vllm-backend:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    command: [
      "--model", "deepseek-ai/DeepSeek-OCR",
      "--host", "0.0.0.0",
      "--port", "8000"
    ]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Then use the `deepseek-vllm` backend:

```bash
docker-compose run docling-hybrid \
  convert /app/input/document.pdf --backend deepseek-vllm
```

### Batch Processing

Process multiple PDFs:

```bash
# Place multiple PDFs in input/
docker-compose run docling-hybrid \
  convert-batch /app/input --output-dir /app/output --parallel 4
```

---

## Best Practices

1. **Always use read-only mounts** for input files (`:ro`)
2. **Set resource limits** to prevent container from consuming all system resources
3. **Use .env files** for sensitive data (API keys)
4. **Tag images** with versions for production deployments
5. **Monitor health checks** in production environments
6. **Use multi-stage builds** to keep images small
7. **Enable logging** at appropriate levels (INFO for prod, DEBUG for dev)

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Project README](../README.md)
- [Configuration Guide](../CLAUDE.md#configuration)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

**Document Version:** 1.0
**Last Updated:** 2024-11-25
**Maintainer:** Dev-04 (DevOps)
