#!/bin/bash
# Cleanup demo artifacts

echo "🧹 Cleaning up demo artifacts..."

# Remove generated files
rm -f .gitops/commit_message.txt
rm -f .gitops/commit_metadata.json
rm -f reports/commit-*.json
rm -f reports/incident-*.json
rm -f services/phi-service/internal/handlers/encryption.go

# Reset git state if in a git repo
if [ -d ".git" ]; then
    git checkout -- services/phi-service/internal/handlers/ 2>/dev/null || true
    git clean -fd services/phi-service/internal/handlers/ 2>/dev/null || true
fi

echo "✅ Demo cleanup complete"
echo ""
echo "You can run the demo again with:"
echo "  ./demo.sh"
