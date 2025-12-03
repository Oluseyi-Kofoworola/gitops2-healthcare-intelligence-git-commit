#!/bin/bash
# Maximum Cleanup and Optimization Script
# Removes all unnecessary files and optimizes the repository

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "🧹 Starting Maximum Cleanup and Optimization..."
echo ""

# Step 1: Remove all progress/status markdown files (keep only essential docs)
echo "📋 Step 1: Removing progress/status documentation files..."
rm -f ALL_GAPS_CLOSED.md \
      CLEANUP_PLAN.md \
      CLEANUP_SUMMARY.txt \
      CODE_REVIEW_FEEDBACK_COMPLETE.md \
      CODEQL_V4_UPGRADE_SUCCESS.md \
      COMPLETION_SUMMARY.md \
      COMPLIANCE_AND_SECURITY_JOURNAL.md \
      CONSOLIDATION_SUCCESS.md \
      DEPENDABOT_FIX_SUMMARY.md \
      ENGINEERING_JOURNAL.md \
      ENTERPRISE_READINESS_COMPLETE.md \
      FINAL_SUMMARY.md \
      GAPS_CLOSURE_REPORT.md \
      GITHUB_ACTIONS_FIX.md \
      GITHUB_ACTIONS_UPGRADE.md \
      IMPLEMENTATION_STATUS.md \
      PHASE_2_COMPLETE.md \
      PROGRESS_UPDATE.md \
      PROJECT_PROGRESS_REPORT.md \
      PUBLICATION_SUCCESS.md \
      PUSH_SUCCESS.md \
      QUICK_STATUS.md \
      README.new.md \
      REFACTORING_PROGRESS.md \
      REFINEMENT_COMPLETION_REPORT.md \
      RESOLUTION_COMPLETE.md \
      SECTION_B_COMPLETE.md \
      SECTION_D_COMPLETE.md \
      SECTION_E_100PCT_COMPLETE.md \
      SECTION_E_COMPLETE_40PCT.md \
      SECTION_E_FINAL_STATUS.md \
      SECTION_E_PROGRESS.md \
      SECTION_E_SESSION_COMPLETE.md \
      SECTION_E_STATUS_UPDATED.md \
      SECTION_E_STATUS.md \
      SECTION_F_COMPLETION_REPORT.md \
      SECTION_F_PLAN.md \
      SECTION_F_SESSION_1_COMPLETE.md \
      SECTION_F_SESSION_COMPLETE.md \
      SECTIONS_ABC_COMPLETE.md \
      SECTIONS_ABCD_COMPLETE.md \
      SESSION_AUTH_SERVICE_COMPLETE.md \
      SESSION_PAYMENT_GATEWAY_COMPLETE.md \
      SESSION_SECTION_E_COMPLETE.md \
      STATUS.md \
      TESTING_SUITE_VISUAL_SUMMARY.md \
      UPGRADE_PROGRESS_REPORT.md \
      VALIDATION_COMPLETE.md \
      WORKFLOW_CONSOLIDATION.md \
      WORKFLOW_FIXES_COMPLETE.md \
      WORKFLOW_FIXES.md \
      WORLD_CLASS_COMPLETE.md \
      WORLD_CLASS_PLATFORM_COMPLETE.md

echo "   ✅ Removed 53 progress/status files"

# Step 2: Remove duplicate/legacy scripts
echo "📋 Step 2: Removing duplicate and legacy scripts..."
rm -f healthcare-demo-new.sh \
      healthcare-demo.sh \
      setup-healthcare-enterprise.sh \
      final-validation.sh \
      security-audit-complete.sh \
      security-validation.sh \
      setup-git-aliases.sh \
      validate-code-quality.sh \
      generate_upgrade_scaffolding.py

echo "   ✅ Removed 9 duplicate scripts"

# Step 3: Remove legacy and executive directories
echo "📋 Step 3: Removing legacy and temporary directories..."
rm -rf legacy/ executive/

echo "   ✅ Removed legacy/ and executive/ directories"

# Step 4: Clean up test files - remove redundant test files
echo "📋 Step 4: Cleaning up redundant test files..."
if [ -f "services/auth-service/main_test_new.go" ]; then
    rm -f services/auth-service/main_test_new.go
    echo "   ✅ Removed main_test_new.go (use main_test.go instead)"
fi

# Step 5: Remove compiled binaries and build artifacts
echo "📋 Step 5: Removing build artifacts..."
find . -type f -name "*.exe" -delete
find . -type f -name "*.dll" -delete
find . -type f -name "*.so" -delete
find . -type f -name "*.dylib" -delete
find . -type d -name "bin" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true

# Remove service binaries
rm -f services/*/auth-service \
      services/*/payment-gateway \
      services/*/phi-service \
      services/*/medical-device \
      services/*/synthetic-phi-service

echo "   ✅ Removed build artifacts and binaries"

# Step 6: Remove Python cache and temporary files
echo "📋 Step 6: Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

echo "   ✅ Removed Python cache files"

# Step 7: Remove Go build cache and test cache
echo "📋 Step 7: Removing Go cache files..."
find . -type f -name "go.sum" -delete
rm -f go.work.sum

echo "   ✅ Removed Go sum files (will regenerate on build)"

# Step 8: Remove macOS specific files
echo "📋 Step 8: Removing macOS system files..."
find . -name ".DS_Store" -delete

echo "   ✅ Removed .DS_Store files"

# Step 9: Remove empty directories
echo "📋 Step 9: Removing empty directories..."
find . -type d -empty -delete 2>/dev/null || true

echo "   ✅ Removed empty directories"

# Step 10: Remove documentation examples if they exist
echo "📋 Step 10: Cleaning up docs directory..."
if [ -d "docs/examples" ]; then
    rm -rf docs/examples
    echo "   ✅ Removed docs/examples"
fi

# Step 11: Remove cmd/gitops-health if not needed
echo "📋 Step 11: Checking cmd/gitops-health..."
if [ -d "cmd/gitops-health" ]; then
    echo "   ⚠️  cmd/gitops-health exists but may not be needed"
fi

# Step 12: Optimize .gitignore
echo "📋 Step 12: Creating optimized .gitignore..."
cat > .gitignore << 'EOF'
# Binaries
*.exe
*.dll
*.so
*.dylib
bin/
dist/

# Go
go.sum
go.work.sum
*.test
*.out
coverage.html
coverage.out

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.pytest_cache/
*.egg-info/
.mypy_cache/
.venv/
venv/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
*.tmp

# Node
node_modules/
package-lock.json

# Reports
reports/
*.json.bak

# Secrets
*.key
*.pem
*.env
.env.local
EOF

echo "   ✅ Created optimized .gitignore"

# Final summary
echo ""
echo "✅ Maximum Cleanup Complete!"
echo ""
echo "📊 Summary:"
du -sh . | awk '{print "   Repository size: " $1}'
find . -type f | wc -l | awk '{print "   Total files: " $1}'
find . -type f -name "*.md" | wc -l | awk '{print "   Markdown files: " $1}'
find . -type f -name "*.go" | wc -l | awk '{print "   Go files: " $1}'
find . -type f -name "*.py" | wc -l | awk '{print "   Python files: " $1}'
echo ""
echo "🎯 Next steps:"
echo "   1. Run: git status"
echo "   2. Run: ./setup.sh  (to rebuild services)"
echo "   3. Run: git add -A && git commit -m 'chore: maximum cleanup and optimization'"
echo ""
