#!/bin/bash
# GitOps 2.0 Pre-Commit Hook Installer
# Automatically installs compliance validation for commit messages

set -e

HOOK_DIR=".git/hooks"
HOOK_FILE="$HOOK_DIR/commit-msg"
VALIDATOR_SCRIPT="scripts/validate_commit_msg.py"

echo "🔧 Installing GitOps 2.0 Compliance Pre-Commit Hook..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "   Run this script from the root of your git repository"
    exit 1
fi

# Check if validator script exists
if [ ! -f "$VALIDATOR_SCRIPT" ]; then
    echo "❌ Error: Validator script not found at $VALIDATOR_SCRIPT"
    exit 1
fi

# Make validator script executable
chmod +x "$VALIDATOR_SCRIPT"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOK_DIR"

# Create the commit-msg hook
cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# GitOps 2.0 Commit Message Validator Hook
# Enforces healthcare compliance metadata in all commits

VALIDATOR="scripts/validate_commit_msg.py"

# Check if in training mode
TRAINING_MODE=$(git config --get copilot.compliance.training || echo "false")

if [ "$TRAINING_MODE" = "true" ]; then
    echo "ℹ️  Running in Training Mode (warnings only)"
    python3 "$VALIDATOR" "$1" || {
        echo ""
        echo "⚠️  This commit would be rejected in production mode"
        echo "💡 Fix the issues above before pushing to main/develop"
        echo ""
        echo "To disable training mode:"
        echo "  git config copilot.compliance.training false"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
else
    # Strict mode - block non-compliant commits
    python3 "$VALIDATOR" "$1" || {
        echo ""
        echo "💡 Quick fixes:"
        echo "   1. Use GitHub Copilot: '@workspace Generate a commit message for my staged changes'"
        echo "   2. View schema: .github/gitops-copilot-instructions.md"
        echo "   3. Enable training mode: git config copilot.compliance.training true"
        echo ""
        exit 1
    }
fi

exit 0
EOF

# Make hook executable
chmod +x "$HOOK_FILE"

echo "✅ Pre-commit hook installed successfully!"
echo ""
echo "📋 What happens now:"
echo "   • All commits will be validated for compliance metadata"
echo "   • Non-compliant commits will be rejected"
echo "   • Use GitHub Copilot to auto-generate compliant messages"
echo ""
echo "🎓 New to the team? Enable Training Mode:"
echo "   git config copilot.compliance.training true"
echo ""
echo "📖 Learn more:"
echo "   • Schema: .github/gitops-copilot-instructions.md"
echo "   • Guide: docs/GETTING_STARTED.md"
echo ""
echo "🧪 Test it:"
echo "   1. Make a change: echo 'test' > test.txt"
echo "   2. Stage it: git add test.txt"
echo "   3. Try a non-compliant commit: git commit -m 'test'"
echo "   4. Watch it get blocked! ✋"
echo ""
