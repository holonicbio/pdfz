#!/bin/bash
# Setup script for Docling Hybrid OCR
# Run this script after cloning the repository

set -e

echo "=========================================="
echo "Docling Hybrid OCR - Setup"
echo "=========================================="
echo

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
python_major=$(echo "$python_version" | cut -d'.' -f1)
python_minor=$(echo "$python_version" | cut -d'.' -f2)

echo "Python version: $python_version"

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
    echo "Error: Python 3.11+ is required"
    exit 1
fi
echo "✓ Python version OK"
echo

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo

# Install package in development mode
echo "Installing docling-hybrid-ocr in development mode..."
pip install -e ".[dev]" --quiet
echo "✓ Package installed"
echo

# Create local config if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local from template..."
    cp .env.example .env.local
    echo "✓ .env.local created"
    echo
    echo "⚠️  IMPORTANT: Edit .env.local and add your OPENROUTER_API_KEY"
else
    echo "✓ .env.local already exists"
fi
echo

# Check for API key
if [ -f ".env.local" ]; then
    source .env.local 2>/dev/null || true
fi

if [ -z "$OPENROUTER_API_KEY" ] || [ "$OPENROUTER_API_KEY" = "your-openrouter-api-key-here" ]; then
    echo "⚠️  Warning: OPENROUTER_API_KEY not set"
    echo "   Get your API key from: https://openrouter.ai/keys"
    echo "   Then add it to .env.local"
else
    echo "✓ OPENROUTER_API_KEY is set"
fi
echo

# Run quick verification
echo "Running verification tests..."
if python -c "from docling_hybrid import __version__; print(f'Version: {__version__}')" 2>/dev/null; then
    echo "✓ Package imports correctly"
else
    echo "✗ Package import failed"
    exit 1
fi
echo

# Run unit tests
echo "Running unit tests..."
if pytest tests/unit -v --tb=short 2>/dev/null; then
    echo "✓ Unit tests passed"
else
    echo "⚠️  Some tests failed (this may be expected if dependencies are missing)"
fi
echo

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo
echo "  2. Set your API key in .env.local:"
echo "     OPENROUTER_API_KEY=your-key-here"
echo
echo "  3. Load environment variables:"
echo "     source .env.local"
echo
echo "  4. Test the CLI:"
echo "     docling-hybrid-ocr --help"
echo
echo "  5. Convert a PDF:"
echo "     docling-hybrid-ocr convert your-document.pdf"
echo
echo "For development documentation, see:"
echo "  - CLAUDE.md (master context)"
echo "  - LOCAL_DEV.md (local development guide)"
echo "  - CONTINUATION.md (development handoff)"
