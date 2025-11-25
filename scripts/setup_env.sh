#!/bin/bash
# Setup environment variables for docling-hybrid-ocr
#
# Usage: source ./scripts/setup_env.sh
#
# This script reads the OpenRouter API key from the 'openrouter_key' file
# in the project root directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KEY_FILE="$PROJECT_ROOT/openrouter_key"

# Check if key file exists
if [[ -f "$KEY_FILE" ]]; then
    # Read the key (trim whitespace)
    OPENROUTER_API_KEY=$(cat "$KEY_FILE" | tr -d '[:space:]')

    if [[ -n "$OPENROUTER_API_KEY" ]]; then
        export OPENROUTER_API_KEY
        echo "✓ OPENROUTER_API_KEY set from openrouter_key file"
    else
        echo "⚠ openrouter_key file is empty"
    fi
else
    echo "⚠ openrouter_key file not found at: $KEY_FILE"
    echo "  Create it with: echo 'your-api-key' > openrouter_key"
fi

# Also source .env.local if it exists
if [[ -f "$PROJECT_ROOT/.env.local" ]]; then
    set -a
    source "$PROJECT_ROOT/.env.local"
    set +a
    echo "✓ Loaded .env.local"
fi
