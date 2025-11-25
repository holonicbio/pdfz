#!/bin/bash
# Cleanup script for Docling Hybrid OCR
# Use this to free disk space during development

set -e

echo "=========================================="
echo "Docling Hybrid OCR - Cleanup"
echo "=========================================="
echo

# Show current disk usage
echo "Current project size:"
du -sh . 2>/dev/null || echo "Unable to calculate"
echo

# Clean Python bytecode
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
echo "✓ Python cache cleaned"

# Clean test cache
echo "Cleaning test cache..."
rm -rf .pytest_cache 2>/dev/null || true
rm -rf .mypy_cache 2>/dev/null || true
rm -rf .ruff_cache 2>/dev/null || true
echo "✓ Test cache cleaned"

# Clean coverage
echo "Cleaning coverage reports..."
rm -rf htmlcov 2>/dev/null || true
rm -f .coverage 2>/dev/null || true
rm -f coverage.xml 2>/dev/null || true
echo "✓ Coverage reports cleaned"

# Clean build artifacts
echo "Cleaning build artifacts..."
rm -rf build 2>/dev/null || true
rm -rf dist 2>/dev/null || true
rm -rf *.egg-info 2>/dev/null || true
rm -rf src/*.egg-info 2>/dev/null || true
echo "✓ Build artifacts cleaned"

# Clean output files (optional)
read -p "Clean output .md files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find . -name "*.nemotron.md" -delete 2>/dev/null || true
    find . -name "*.deepseek.md" -delete 2>/dev/null || true
    echo "✓ Output files cleaned"
else
    echo "- Output files kept"
fi

# Show final disk usage
echo
echo "Final project size:"
du -sh . 2>/dev/null || echo "Unable to calculate"
echo

echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
