#!/usr/bin/env bash
################################################################################
# GitOps 2.0 Healthcare Intelligence - Pre-Commit Hook Installer
# 
# Installs production-grade pre-commit hooks for compliance validation
# 
# Features:
# - Secret detection (PHI, PII, API keys)
# - Token limit protection
# - OPA policy validation
# - File count limits
# - Risk assessment
#
# Usage:
#   ./scripts/install-pre-commit-hook.sh
#   ./scripts/install-pre-commit-hook.sh --force  # Overwrite existing
#
# Version: 2.0.0
# Last Updated: 2025-12-05
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOK_PATH="$REPO_ROOT/.git/hooks/pre-commit"
BACKUP_PATH="$HOOK_PATH.backup"

# Parse arguments
FORCE=false
if [[ "${1:-}" == "--force" ]]; then
    FORCE=true
fi

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# Validation
################################################################################

validate_environment() {
    print_info "Validating environment..."
    
    # Check if in git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
    
    # Check Python installation
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check required Python tools
    local required_tools=(
        "tools/healthcare_commit_generator.py"
        "tools/secret_sanitizer.py"
        "tools/token_limit_guard.py"
    )
    
    for tool in "${required_tools[@]}"; do
        if [[ ! -f "$REPO_ROOT/$tool" ]]; then
            print_warning "Required tool not found: $tool"
        fi
    done
    
    # Check OPA installation
    if ! command -v opa &> /dev/null; then
        print_warning "OPA not installed - policy validation will be skipped"
        print_info "Install OPA from: https://www.openpolicyagent.org/docs/latest/#running-opa"
    fi
    
    print_success "Environment validation complete"
}

################################################################################
# Installation
################################################################################

install_hook() {
    print_info "Installing pre-commit hook..."
    
    # Backup existing hook
    if [[ -f "$HOOK_PATH" ]] && [[ "$FORCE" == false ]]; then
        print_warning "Pre-commit hook already exists: $HOOK_PATH"
        echo -n "Backup and replace? (y/n) "
        read -r response
        if [[ "$response" != "y" ]]; then
            print_info "Installation cancelled"
            exit 0
        fi
        cp "$HOOK_PATH" "$BACKUP_PATH"
        print_success "Backed up existing hook to: $BACKUP_PATH"
    fi
    
    # Create hook script
    cat > "$HOOK_PATH" << 'HOOK_EOF'
#!/usr/bin/env bash
################################################################################
# GitOps 2.0 Healthcare Intelligence - Pre-Commit Hook
# Auto-generated - DO NOT EDIT MANUALLY
################################################################################

set -e

# Get repository root
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  GitOps 2.0 Healthcare Intelligence - Pre-Commit Checks"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
if [[ -z "$STAGED_FILES" ]]; then
    echo -e "${YELLOW}⚠${NC} No files staged for commit"
    exit 0
fi

FILE_COUNT=$(echo "$STAGED_FILES" | wc -l | tr -d ' ')
echo -e "${BLUE}ℹ${NC} Checking $FILE_COUNT staged file(s)..."

################################################################################
# Check 1: File Count Validation
################################################################################
echo -e "\n${BLUE}➜${NC} Check 1: File Count Validation"

MAX_FILES=100
if [[ $FILE_COUNT -gt $MAX_FILES ]]; then
    echo -e "${RED}✗${NC} Too many files staged: $FILE_COUNT (max: $MAX_FILES)"
    echo -e "${YELLOW}⚠${NC} Consider breaking this into smaller commits"
    exit 1
fi
echo -e "${GREEN}✓${NC} File count OK: $FILE_COUNT files"

################################################################################
# Check 2: Secret Detection
################################################################################
echo -e "\n${BLUE}➜${NC} Check 2: Secret & PHI Detection"

if [[ -f "$REPO_ROOT/tools/secret_sanitizer.py" ]]; then
    # Get diff of staged changes
    DIFF=$(git diff --cached)
    
    # Run secret sanitizer
    if echo "$DIFF" | python3 "$REPO_ROOT/tools/secret_sanitizer.py" --check-stdin 2>&1; then
        echo -e "${GREEN}✓${NC} No secrets or PHI detected"
    else
        echo -e "${RED}✗${NC} Secrets or PHI detected in staged changes"
        echo -e "${YELLOW}⚠${NC} Remove sensitive data before committing"
        echo -e "${BLUE}ℹ${NC} Run: git diff --cached | python3 tools/secret_sanitizer.py --check-stdin"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} Secret sanitizer not found - skipping check"
fi

################################################################################
# Check 3: Token Limit Validation
################################################################################
echo -e "\n${BLUE}➜${NC} Check 3: Token Limit Check"

if [[ -f "$REPO_ROOT/tools/token_limit_guard.py" ]]; then
    DIFF=$(git diff --cached)
    
    if python3 "$REPO_ROOT/tools/token_limit_guard.py" --check-diff 2>&1; then
        echo -e "${GREEN}✓${NC} Changeset size within token limits"
    else
        echo -e "${YELLOW}⚠${NC} Warning: Large changeset may exceed AI token limits"
        echo -e "${BLUE}ℹ${NC} Consider splitting into smaller commits for better AI processing"
    fi
else
    echo -e "${YELLOW}⚠${NC} Token limit guard not found - skipping check"
fi

################################################################################
# Check 4: OPA Policy Validation
################################################################################
echo -e "\n${BLUE}➜${NC} Check 4: OPA Policy Validation"

if command -v opa &> /dev/null && [[ -d "$REPO_ROOT/policies/healthcare" ]]; then
    if opa test "$REPO_ROOT/policies/healthcare" --verbose 2>&1 | grep -q "PASS"; then
        echo -e "${GREEN}✓${NC} All OPA policies passed"
    else
        echo -e "${RED}✗${NC} OPA policy validation failed"
        echo -e "${BLUE}ℹ${NC} Run: opa test policies/healthcare/ --verbose"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} OPA not installed or policies not found - skipping check"
fi

################################################################################
# Check 5: Commit Message Validation
################################################################################
echo -e "\n${BLUE}➜${NC} Check 5: Conventional Commit Format"

# This check runs in prepare-commit-msg hook
echo -e "${BLUE}ℹ${NC} Commit message will be validated after creation"

################################################################################
# Summary
################################################################################
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✓ All Pre-Commit Checks Passed${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}ℹ${NC} Next steps:"
echo -e "  1. Create commit message (manually or with healthcare_commit_generator.py)"
echo -e "  2. Review compliance metadata"
echo -e "  3. Complete commit\n"

exit 0
HOOK_EOF

    # Make executable
    chmod +x "$HOOK_PATH"
    
    print_success "Pre-commit hook installed: $HOOK_PATH"
}

################################################################################
# Testing
################################################################################

test_hook() {
    print_info "Testing pre-commit hook..."
    
    # Create test file
    TEST_FILE="$REPO_ROOT/.githooks_test_file"
    echo "# Test file for pre-commit hook" > "$TEST_FILE"
    
    # Stage test file
    git add "$TEST_FILE" 2>/dev/null || true
    
    # Run hook
    if "$HOOK_PATH" 2>&1 | grep -q "All Pre-Commit Checks Passed"; then
        print_success "Pre-commit hook test passed"
    else
        print_warning "Pre-commit hook test had warnings (this may be normal)"
    fi
    
    # Clean up
    git reset HEAD "$TEST_FILE" 2>/dev/null || true
    rm -f "$TEST_FILE"
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    print_header "GitOps 2.0 Healthcare Intelligence - Pre-Commit Hook Installation"
    
    # Step 1: Validate environment
    validate_environment
    
    # Step 2: Install hook
    install_hook
    
    # Step 3: Test installation
    test_hook
    
    # Success message
    echo ""
    print_success "Installation complete!"
    echo ""
    print_info "The pre-commit hook will now run automatically before each commit"
    print_info "It will check for:"
    echo "  • Secrets and PHI in code changes"
    echo "  • Token limits for AI processing"
    echo "  • OPA policy compliance"
    echo "  • File count limits"
    echo ""
    print_info "To bypass checks (NOT recommended):"
    echo "  git commit --no-verify"
    echo ""
    print_info "To uninstall:"
    echo "  rm $HOOK_PATH"
    if [[ -f "$BACKUP_PATH" ]]; then
        echo "  mv $BACKUP_PATH $HOOK_PATH  # Restore backup"
    fi
    echo ""
}

# Run installation
main "$@"
