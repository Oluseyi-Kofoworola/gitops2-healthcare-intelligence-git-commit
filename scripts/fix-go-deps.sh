#!/usr/bin/env bash
# Fix missing go.sum entries across all services
# WHY: CI fails with "missing go.sum entry" errors (21 occurrences)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔧 Fixing Go dependencies..."

for service in services/auth-service services/payment-gateway services/phi-service services/medical-device cmd/gitops-health; do
    if [[ -f "$service/go.mod" ]]; then
        echo "  → $service"
        cd "$REPO_ROOT/$service"
        go mod download 2>&1 | head -5 || true
        go mod tidy
        cd "$REPO_ROOT"
    fi
done

if [[ -f "go.work" ]]; then
    echo "  → Syncing workspace"
    go work sync
fi

echo "✅ Dependencies fixed"
