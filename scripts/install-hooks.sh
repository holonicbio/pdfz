#!/bin/bash
# Install git hooks for docling-hybrid-ocr
#
# Usage: ./scripts/install-hooks.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Create post-checkout hook
cat > "$HOOKS_DIR/post-checkout" << 'EOF'
#!/bin/bash
# Post-checkout hook: remind user to set up environment

# Only run on branch checkout (not file checkout)
if [ "$3" != "1" ]; then
    exit 0
fi

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
KEY_FILE="$PROJECT_ROOT/openrouter_key"

# Check if OPENROUTER_API_KEY is set
if [[ -z "$OPENROUTER_API_KEY" ]]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  OPENROUTER_API_KEY not set                                ║"
    echo "║                                                            ║"
    echo "║  To set up your environment, run:                          ║"
    echo "║    source ./scripts/setup_env.sh                           ║"
    echo "║                                                            ║"
    echo "║  Make sure 'openrouter_key' file exists with your API key  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
fi
EOF

chmod +x "$HOOKS_DIR/post-checkout"
echo "✓ Installed post-checkout hook"

echo ""
echo "Hooks installed. To set up your environment now, run:"
echo "  source ./scripts/setup_env.sh"
