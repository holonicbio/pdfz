# Multi-stage Dockerfile for Docling Hybrid OCR
# Optimized for production deployment with minimal image size

# =============================================================================
# Stage 1: Builder
# Build Python wheels and dependencies
# =============================================================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only files needed for building
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel -o /wheels

# =============================================================================
# Stage 2: Runtime
# Minimal runtime environment
# =============================================================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="Docling Hybrid Team"
LABEL description="Docling Hybrid OCR - PDF to Markdown with VLM backends"
LABEL version="0.1.0"

# Set working directory
WORKDIR /app

# Install runtime dependencies (pypdfium2 requires libgcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheels from builder
COPY --from=builder /wheels /wheels

# Install the application
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# Copy configuration files
COPY configs/ /app/configs/

# Create directories for input/output
RUN mkdir -p /app/input /app/output

# Set environment variables
ENV DOCLING_HYBRID_CONFIG=/app/configs/default.toml
ENV PYTHONUNBUFFERED=1

# Expose port for potential API server (future use)
EXPOSE 8080

# Health check (for orchestration platforms like K8s)
# This will use the health command we'll create later
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD docling-hybrid-ocr health || exit 1

# Set entrypoint
ENTRYPOINT ["docling-hybrid-ocr"]

# Default command (can be overridden)
CMD ["--help"]
