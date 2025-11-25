# Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Local Installation](#local-installation)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Production Best Practices](#production-best-practices)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

---

## Overview

Docling Hybrid OCR can be deployed in several ways:
- **Docker Container** - Recommended for production (simplest, most portable)
- **Local Installation** - For development and testing
- **Cloud Platforms** - AWS, GCP, Azure, or other cloud providers
- **Kubernetes** - For large-scale deployments

This guide covers all deployment methods with step-by-step instructions.

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 12GB
- Disk: 2GB free space
- Python: 3.11 or higher
- Internet connection (for API backends)

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 16GB+
- Disk: 10GB free space
- SSD storage for better I/O performance

### Required Accounts

- **OpenRouter API Key** - Sign up at [openrouter.ai](https://openrouter.ai) (free tier available)
- Optional: Cloud provider account (AWS/GCP/Azure) for cloud deployment

---

## Quick Start with Docker

Docker provides the easiest and most reliable deployment method.

### 1. Build the Docker Image

```bash
# Clone the repository
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr

# Build the image
docker build -t docling-hybrid-ocr:latest .
```

**Expected build time:** 3-5 minutes

### 2. Run a Conversion

```bash
# Single file conversion
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /app/input/document.pdf -o /app/output/result.md
```

### 3. Using Docker Compose

For easier management, use Docker Compose:

```bash
# Create .env file with your API key
echo "OPENROUTER_API_KEY=your-key-here" > .env

# Run with docker-compose
docker-compose up
```

**docker-compose.yml example:**
```yaml
version: "3.8"

services:
  docling-hybrid:
    build: .
    image: docling-hybrid-ocr:latest
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DOCLING_HYBRID_CONFIG=/app/configs/default.toml
      - DOCLING_HYBRID_LOG_LEVEL=INFO
    volumes:
      - ./input:/app/input
      - ./output:/app/output
      - ./configs:/app/configs:ro
    command: ["convert", "/app/input/document.pdf", "-o", "/app/output/result.md"]
```

### 4. Interactive Shell

To run multiple commands interactively:

```bash
docker run -it --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  bash
```

Then inside the container:
```bash
docling-hybrid-ocr convert /app/input/doc1.pdf
docling-hybrid-ocr convert /app/input/doc2.pdf
docling-hybrid-ocr backends
```

---

## Local Installation

### 1. System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev git
```

**macOS:**
```bash
brew install python@3.11 git
```

**Windows:**
- Install Python 3.11+ from [python.org](https://python.org)
- Install Git from [git-scm.com](https://git-scm.com)

### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr

# Run setup script (creates venv, installs dependencies)
./scripts/setup.sh

# Or manual setup:
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Configuration

```bash
# Copy example environment file
cp .env.example .env.local

# Edit .env.local with your API key
nano .env.local  # or use your preferred editor
```

Add your API key to `.env.local`:
```bash
OPENROUTER_API_KEY=sk-your-key-here
DOCLING_HYBRID_CONFIG=configs/local.toml
DOCLING_HYBRID_LOG_LEVEL=INFO
```

### 4. Activate and Use

```bash
# Activate environment
source .venv/bin/activate
source .env.local

# Verify installation
docling-hybrid-ocr --version
docling-hybrid-ocr backends

# Convert a PDF
docling-hybrid-ocr convert document.pdf
```

### 5. Running Tests

```bash
# Unit tests
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=src/docling_hybrid --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: AWS EC2

**1. Launch EC2 Instance:**
```bash
# Recommended instance: t3.xlarge or larger
# AMI: Ubuntu 22.04 LTS
# Storage: 20GB EBS
# Security group: Allow SSH (22) and optionally HTTP (80)
```

**2. Connect and Install:**
```bash
ssh ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Logout and login again to apply group changes
exit
ssh ubuntu@your-instance-ip

# Clone and build
git clone https://github.com/your-org/docling-hybrid-ocr.git
cd docling-hybrid-ocr
docker build -t docling-hybrid-ocr .
```

**3. Run Conversion:**
```bash
docker run --rm \
  -v $(pwd)/data:/data \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docling-hybrid-ocr:latest \
  convert /data/input.pdf -o /data/output.md
```

#### Option 2: AWS ECS (Fargate)

**1. Create ECR Repository:**
```bash
aws ecr create-repository --repository-name docling-hybrid-ocr
```

**2. Build and Push Image:**
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t docling-hybrid-ocr .
docker tag docling-hybrid-ocr:latest \
  YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/docling-hybrid-ocr:latest

# Push
docker push YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/docling-hybrid-ocr:latest
```

**3. Create ECS Task Definition:**
```json
{
  "family": "docling-hybrid-ocr",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "16384",
  "containerDefinitions": [
    {
      "name": "docling-hybrid-ocr",
      "image": "YOUR_AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/docling-hybrid-ocr:latest",
      "essential": true,
      "environment": [
        {
          "name": "OPENROUTER_API_KEY",
          "value": "your-key-here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/docling-hybrid-ocr",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Option 3: AWS Lambda

For smaller documents (< 10 pages), AWS Lambda can be cost-effective:

**Limitations:**
- 15-minute execution timeout
- 10GB memory maximum
- Ephemeral storage limited to 10GB

**Setup:**
```bash
# Package application with dependencies
pip install -t package/ .
cd package
zip -r ../deployment-package.zip .
cd ..
zip -g deployment-package.zip lambda_handler.py

# Create Lambda function
aws lambda create-function \
  --function-name docling-hybrid-ocr \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --handler lambda_handler.handler \
  --zip-file fileb://deployment-package.zip \
  --timeout 900 \
  --memory-size 10240
```

### Google Cloud Platform (GCP)

#### Option 1: GCP Compute Engine

Similar to AWS EC2, create a VM instance and follow local installation steps.

#### Option 2: GCP Cloud Run

**1. Build and Push to GCR:**
```bash
# Authenticate
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/YOUR_PROJECT/docling-hybrid-ocr .
docker push gcr.io/YOUR_PROJECT/docling-hybrid-ocr
```

**2. Deploy to Cloud Run:**
```bash
gcloud run deploy docling-hybrid-ocr \
  --image gcr.io/YOUR_PROJECT/docling-hybrid-ocr \
  --platform managed \
  --region us-central1 \
  --memory 16Gi \
  --cpu 4 \
  --timeout 3600 \
  --set-env-vars OPENROUTER_API_KEY=your-key-here
```

### Azure Deployment

#### Azure Container Instances

```bash
# Create resource group
az group create --name docling-rg --location eastus

# Create container instance
az container create \
  --resource-group docling-rg \
  --name docling-hybrid-ocr \
  --image YOUR_REGISTRY/docling-hybrid-ocr:latest \
  --cpu 4 \
  --memory 16 \
  --environment-variables \
    OPENROUTER_API_KEY=your-key-here \
    DOCLING_HYBRID_CONFIG=/app/configs/default.toml
```

### Kubernetes Deployment

**deployment.yaml:**
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
      - name: docling-hybrid-ocr
        image: docling-hybrid-ocr:latest
        resources:
          requests:
            memory: "12Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "4"
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: docling-secrets
              key: openrouter-api-key
        - name: DOCLING_HYBRID_CONFIG
          value: "/app/configs/default.toml"
        volumeMounts:
        - name: config
          mountPath: /app/configs
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: docling-config
```

**Create secret:**
```bash
kubectl create secret generic docling-secrets \
  --from-literal=openrouter-api-key=your-key-here
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml
```

---

## Configuration

### Environment Variables

All configuration can be overridden via environment variables:

```bash
# Core settings
export DOCLING_HYBRID_CONFIG=/path/to/config.toml
export DOCLING_HYBRID_LOG_LEVEL=INFO
export DOCLING_HYBRID_LOG_FORMAT=json

# Backend settings
export OPENROUTER_API_KEY=your-key-here
export DOCLING_HYBRID_DEFAULT_BACKEND=nemotron-openrouter

# Resource limits
export DOCLING_HYBRID_MAX_WORKERS=4
export DOCLING_HYBRID_MAX_MEMORY_MB=16384
export DOCLING_HYBRID_PAGE_RENDER_DPI=200
export DOCLING_HYBRID_HTTP_TIMEOUT_S=120
```

### Configuration Files

**Production (configs/default.toml):**
- 8 concurrent workers
- 16GB memory limit
- 200 DPI rendering
- JSON structured logs

**Local Development (configs/local.toml):**
- 2 concurrent workers
- 4GB memory limit
- 150 DPI rendering
- Human-readable logs

**Custom Configuration:**
```toml
# configs/production.toml
[app]
name = "docling-hybrid-ocr"
version = "0.1.0"
environment = "production"

[logging]
level = "INFO"
format = "json"

[resources]
max_workers = 8
max_memory_mb = 16384
page_render_dpi = 200
http_timeout_s = 120
http_retry_attempts = 3

[backends]
default = "nemotron-openrouter"

[backends.nemotron-openrouter]
name = "nemotron-openrouter"
model = "nvidia/nemotron-nano-12b-v2-vl:free"
base_url = "https://openrouter.ai/api/v1/chat/completions"
temperature = 0.0
max_tokens = 8192
```

---

## Production Best Practices

### 1. Security

**API Key Management:**
```bash
# NEVER commit API keys to version control
# Use environment variables or secrets management

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name /docling/openrouter-api-key \
  --secret-string "your-key-here"

# GCP Secret Manager
gcloud secrets create openrouter-api-key \
  --data-file=-

# Azure Key Vault
az keyvault secret set \
  --vault-name docling-vault \
  --name openrouter-api-key \
  --value "your-key-here"
```

**Network Security:**
- Use HTTPS for all API communication
- Restrict container/VM access with security groups
- Use VPC/private networks when possible
- Implement rate limiting for API endpoints

### 2. Resource Management

**Memory Limits:**
```bash
# Docker memory limit
docker run --memory=16g docling-hybrid-ocr

# Kubernetes resource limits (see deployment.yaml above)
```

**CPU Limits:**
```bash
# Docker CPU limit
docker run --cpus=4 docling-hybrid-ocr
```

### 3. Error Handling

**Retry Logic:**
- Configured in `http_retry_attempts` (default: 3)
- Exponential backoff between retries
- Handles transient network errors

**Fallback Backends:**
```toml
# In config file
[backends]
default = "deepseek-vllm"
fallback = ["nemotron-openrouter"]
fallback_on_errors = ["connection", "timeout", "server_error"]
max_fallback_attempts = 2
```

### 4. Performance Optimization

**Concurrent Workers:**
```bash
# Adjust based on available CPU cores and memory
export DOCLING_HYBRID_MAX_WORKERS=8
```

**DPI Settings:**
```bash
# Higher DPI = better quality, more memory/time
# Lower DPI = faster processing, less memory
export DOCLING_HYBRID_PAGE_RENDER_DPI=150  # For faster processing
```

**Batch Processing:**
```bash
# Process multiple files efficiently
docling-hybrid-ocr convert-batch ./pdfs/ --parallel 4
```

---

## Monitoring and Logging

### Logging Configuration

**Structured JSON Logging (Production):**
```bash
export DOCLING_HYBRID_LOG_LEVEL=INFO
export DOCLING_HYBRID_LOG_FORMAT=json
```

**Example log output:**
```json
{
  "event": "conversion_started",
  "timestamp": "2024-11-25T10:30:00Z",
  "level": "info",
  "doc_id": "doc-abc123",
  "pdf_path": "/data/document.pdf",
  "total_pages": 10,
  "backend": "nemotron-openrouter"
}
```

### Health Checks

**Docker health check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD docling-hybrid-ocr health || exit 1
```

**Kubernetes liveness probe:**
```yaml
livenessProbe:
  exec:
    command:
    - docling-hybrid-ocr
    - health
  initialDelaySeconds: 30
  periodSeconds: 30
```

**Manual health check:**
```bash
docling-hybrid-ocr health

# Output:
# ✓ Configuration: Valid
# ✓ OpenRouter Backend: Connected (latency: 120ms)
# Overall: HEALTHY
```

### Metrics Collection

**Application Metrics:**
- Pages processed per minute
- API latency (p50, p95, p99)
- Memory usage
- Error rates
- Backend availability

**CloudWatch (AWS):**
```bash
# Install CloudWatch agent
# Logs automatically sent to CloudWatch Logs
# Custom metrics can be sent via boto3
```

**Prometheus (Kubernetes):**
```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: docling-hybrid-ocr
spec:
  selector:
    matchLabels:
      app: docling-hybrid-ocr
  endpoints:
  - port: metrics
    path: /metrics
```

---

## Troubleshooting

### Common Issues

#### 1. Out of Memory

**Symptoms:**
- Process killed unexpectedly
- "MemoryError" exceptions
- Container restarts

**Solutions:**
```bash
# Reduce concurrent workers
export DOCLING_HYBRID_MAX_WORKERS=2

# Reduce DPI
export DOCLING_HYBRID_PAGE_RENDER_DPI=100

# Increase memory limit
docker run --memory=20g docling-hybrid-ocr

# Process fewer pages at once
docling-hybrid-ocr convert doc.pdf --max-pages 5
```

#### 2. API Connection Errors

**Symptoms:**
- "ConnectionError" or "Timeout" exceptions
- Slow processing

**Solutions:**
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Increase timeout
export DOCLING_HYBRID_HTTP_TIMEOUT_S=300

# Check network connectivity
curl -I https://openrouter.ai

# Use health check
docling-hybrid-ocr health
```

#### 3. Docker Build Failures

**Symptoms:**
- Build errors during `docker build`

**Solutions:**
```bash
# Clean Docker cache
docker system prune -a

# Use BuildKit
export DOCKER_BUILDKIT=1
docker build -t docling-hybrid-ocr .

# Check disk space
df -h
```

#### 4. Permission Errors

**Symptoms:**
- "Permission denied" when accessing files

**Solutions:**
```bash
# Ensure proper volume permissions
chmod 755 input/ output/

# Run Docker with user mapping
docker run --user $(id -u):$(id -g) docling-hybrid-ocr
```

### Getting Help

For more detailed troubleshooting:
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive troubleshooting guide
- **[CLAUDE.md](../CLAUDE.md)** - Development context and architecture
- **[API.md](API.md)** - Complete API documentation
- **GitHub Issues** - Report bugs or request features

### Debug Mode

Enable debug logging for detailed diagnostics:

```bash
export DOCLING_HYBRID_LOG_LEVEL=DEBUG
docling-hybrid-ocr convert document.pdf --verbose
```

### Support Channels

- **GitHub Issues:** https://github.com/your-org/docling-hybrid-ocr/issues
- **Documentation:** https://github.com/your-org/docling-hybrid-ocr#readme
- **Email:** support@your-org.com (if available)

---

## Next Steps

After deployment:
1. **Run Health Checks** - Verify all backends are accessible
2. **Test Conversion** - Convert a sample PDF
3. **Monitor Logs** - Check for errors or warnings
4. **Set Up Monitoring** - Configure metrics collection
5. **Backup Configuration** - Save working config files
6. **Document Custom Settings** - Note any environment-specific changes

For advanced usage and customization:
- **[API.md](API.md)** - Programmatic usage
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture

---

*Last Updated: 2024-11-25*
*Version: Sprint 2*
