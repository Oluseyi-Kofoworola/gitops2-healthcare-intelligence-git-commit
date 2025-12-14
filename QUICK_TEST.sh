#!/bin/bash
# Quick feature test - no interaction required
set -e

echo "🚀 GitOps 2.0 - Quick Feature Test"
echo "=================================="
echo ""

cd "$(dirname "$0")"
source .venv-mac/bin/activate 2>/dev/null || true

echo "✅ Test 1: Configuration System"
python tools/config.py
echo ""

echo "✅ Test 2: AI Commit Generator (with real changes)"
python tools/git_copilot_commit.py --analyze 2>&1 | head -30
echo ""

echo "✅ Test 3: Intelligent Bisect (help)"
python tools/git_intelligent_bisect.py --help | head -15
echo ""

echo "✅ Test 4: Available GitOps Health Modules"
echo "Modules:"
ls -1 tools/gitops_health/*.py | grep -v __pycache__ | sed 's|tools/gitops_health/||' | sed 's|.py||' | sed 's|^|  - |'
echo ""

echo "✅ Test 5: Repository Stats"
echo "Python files: $(find tools -name '*.py' | wc -l | tr -d ' ')"
echo "Go services: $(find services -maxdepth 1 -type d | grep -v '^services$' | wc -l | tr -d ' ')"
echo "Tests: $(find tests -name 'test_*.py' | wc -l | tr -d ' ')"
echo "Commits: $(git rev-list --count HEAD 2>/dev/null || echo 'N/A')"
echo ""

echo "🎉 All tests complete!"
echo ""
echo "Next steps:"
echo "  • Run full demo: ./LIVE_DEMO.sh"
echo "  • Check docs: ls docs/*.md"
echo "  • View config: python tools/config.py"
