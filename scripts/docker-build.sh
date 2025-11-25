#!/usr/bin/env bash
# docker-build.sh - Build and manage Docling Hybrid OCR Docker images
#
# Usage:
#   ./scripts/docker-build.sh [OPTIONS] [COMMAND]
#
# Commands:
#   build       Build the Docker image (default)
#   test        Build and run tests
#   push        Build and push to registry
#   clean       Remove local images
#   run         Build and run interactive shell
#
# Options:
#   --tag TAG   Specify custom tag (default: latest)
#   --no-cache  Build without using cache
#   --help      Show this help message

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="docling-hybrid-ocr"
IMAGE_TAG="latest"
USE_CACHE=true
COMMAND="build"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Docling Hybrid OCR Docker Build Script

Usage:
  $0 [OPTIONS] [COMMAND]

Commands:
  build       Build the Docker image (default)
  test        Build and run tests inside container
  push        Build and push to registry
  clean       Remove local images
  run         Build and run interactive shell
  size        Show image size

Options:
  --tag TAG       Specify custom tag (default: latest)
  --no-cache      Build without using cache
  --platform PLAT Build for specific platform (e.g., linux/amd64)
  --help, -h      Show this help message

Examples:
  # Build with default settings
  $0

  # Build with custom tag
  $0 --tag v0.1.0 build

  # Build without cache
  $0 --no-cache build

  # Test the image
  $0 test

  # Show image size
  $0 size
EOF
}

build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

    # Build arguments
    BUILD_ARGS=()
    if [[ "$USE_CACHE" == "false" ]]; then
        BUILD_ARGS+=("--no-cache")
    fi

    if [[ -n "${PLATFORM:-}" ]]; then
        BUILD_ARGS+=("--platform" "$PLATFORM")
    fi

    # Build the image
    docker build \
        "${BUILD_ARGS[@]}" \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -f Dockerfile \
        .

    log_success "Image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"

    # Show image size
    SIZE=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    log_info "Image size: $SIZE"

    # Check if image is under 500MB (requirement)
    SIZE_MB=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}" | sed 's/MB//' | awk '{print int($1)}')
    if [[ "$SIZE_MB" -gt 500 ]]; then
        log_warning "Image size exceeds 500MB requirement (actual: ${SIZE_MB}MB)"
    else
        log_success "Image size meets 500MB requirement (actual: ${SIZE_MB}MB)"
    fi
}

test_image() {
    log_info "Testing Docker image..."

    # Build first
    build_image

    # Test 1: Can run help
    log_info "Test 1: Running --help"
    docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" --help

    # Test 2: Can list backends
    log_info "Test 2: Listing backends"
    docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" backends

    # Test 3: Can show info
    log_info "Test 3: Showing info"
    docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" info

    log_success "All tests passed!"
}

push_image() {
    log_info "Pushing image to registry..."

    # Build first
    build_image

    # Ask for confirmation
    read -p "Push ${IMAGE_NAME}:${IMAGE_TAG} to registry? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker push "${IMAGE_NAME}:${IMAGE_TAG}"
        log_success "Image pushed successfully"
    else
        log_warning "Push cancelled"
    fi
}

clean_images() {
    log_info "Cleaning up Docker images..."

    # Remove the image
    if docker images -q "${IMAGE_NAME}:${IMAGE_TAG}" 2> /dev/null; then
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}"
        log_success "Image removed: ${IMAGE_NAME}:${IMAGE_TAG}"
    else
        log_warning "No image found to remove: ${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    # Clean up dangling images
    DANGLING=$(docker images -f "dangling=true" -q)
    if [[ -n "$DANGLING" ]]; then
        log_info "Removing dangling images..."
        docker rmi $DANGLING || true
    fi

    log_success "Cleanup complete"
}

run_interactive() {
    log_info "Running interactive shell..."

    # Build first
    build_image

    # Run with shell
    docker run -it --rm \
        -v "$(pwd)/input:/app/input:ro" \
        -v "$(pwd)/output:/app/output" \
        -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
        --entrypoint /bin/bash \
        "${IMAGE_NAME}:${IMAGE_TAG}"
}

show_size() {
    if docker images -q "${IMAGE_NAME}:${IMAGE_TAG}" 2> /dev/null; then
        log_info "Image details for ${IMAGE_NAME}:${IMAGE_TAG}:"
        docker images "${IMAGE_NAME}:${IMAGE_TAG}"

        # Show layer sizes
        log_info "\nLayer breakdown:"
        docker history "${IMAGE_NAME}:${IMAGE_TAG}" --human=true --no-trunc
    else
        log_error "Image not found: ${IMAGE_NAME}:${IMAGE_TAG}"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --no-cache)
            USE_CACHE=false
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        build|test|push|clean|run|size)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    build)
        build_image
        ;;
    test)
        test_image
        ;;
    push)
        push_image
        ;;
    clean)
        clean_images
        ;;
    run)
        run_interactive
        ;;
    size)
        show_size
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
