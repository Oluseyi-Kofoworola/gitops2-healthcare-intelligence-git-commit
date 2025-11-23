#!/usr/bin/env bash
# GitOps 2.0 - Git Aliases Setup
# This script configures git aliases to match the GitOps 2.0 manifesto vision

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Setting up GitOps 2.0 git aliases..."
echo ""

# Configure git intent alias
git config --global alias.intent '!python3 '"$REPO_ROOT"'/tools/intent_commit.py'
echo "✅ Configured: git intent"
echo "   Usage: git intent --type feat --scope payment --subject 'add SOX controls' --goal 'improve audit readiness'"

# Configure git copilot alias (same as intent for consistency)
git config --global alias.copilot '!python3 '"$REPO_ROOT"'/tools/intent_commit.py'
echo "✅ Configured: git copilot"
echo "   Usage: git copilot commit --type feat --scope auth --risk high --json"

# Configure git healthcare alias for healthcare-specific commits
git config --global alias.healthcare '!python3 '"$REPO_ROOT"'/tools/healthcare_commit_generator.py'
echo "✅ Configured: git healthcare"
echo "   Usage: git healthcare --type security --scope phi --description 'implement encryption'"

# Configure git risk alias for risk scoring
git config --global alias.risk '!python3 '"$REPO_ROOT"'/tools/git_intel/risk_scorer.py'
echo "✅ Configured: git risk"
echo "   Usage: git risk --max-commits 20 --json"

# Configure git bisect-ai alias for intelligent regression detection
git config --global alias.bisect-ai '!python3 '"$REPO_ROOT"'/tools/intelligent_bisect.py'
echo "✅ Configured: git bisect-ai"
echo "   Usage: git bisect-ai --baseline HEAD~10 --target HEAD --threshold-ms 200"

# Configure git comply alias for compliance framework
git config --global alias.comply '!python3 '"$REPO_ROOT"'/tools/ai_compliance_framework.py'
echo "✅ Configured: git comply"
echo "   Usage: git comply analyze-commit HEAD --json"

# Configure git monitor alias for compliance monitoring
git config --global alias.monitor '!python3 '"$REPO_ROOT"'/tools/compliance_monitor.py'
echo "✅ Configured: git monitor"
echo "   Usage: git monitor dashboard --json"

echo ""
echo "🎉 GitOps 2.0 aliases configured successfully!"
echo ""
echo "📚 Available Commands:"
echo "   git intent       - Intent-driven commit generation"
echo "   git copilot      - AI-powered commit assistant (alias for intent)"
echo "   git healthcare   - Healthcare-compliant commit templates"
echo "   git risk         - AI-driven risk assessment"
echo "   git bisect-ai    - Intelligent regression detection"
echo "   git comply       - Healthcare compliance framework"
echo "   git monitor      - Real-time compliance monitoring"
echo ""
echo "💡 Example Workflow:"
echo "   1. Make your changes"
echo "   2. git add -p"
echo "   3. git copilot commit --type feat --scope payment --risk medium --json"
echo "   4. git risk --max-commits 5"
echo "   5. git push"
echo ""
echo "📖 For more info, see README.md"
