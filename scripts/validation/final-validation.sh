#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}GitOps 2.0 Healthcare Intelligence - Final Validation${NC}"
echo "================================================================"
echo ""

VALIDATION_PASSED=0
VALIDATION_FAILED=0

validate_step() {
    local step_name="$1"
    local command="$2"
    
    echo -n "Testing $step_name... "
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((VALIDATION_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((VALIDATION_FAILED++))
        return 1
    fi
}

echo -e "${BOLD}1. Repository Structure Validation${NC}"
validate_step "Copilot integration files" "test -d .copilot && test -f .copilot/healthcare-commit-guidelines.yml"
validate_step "GitHub Actions workflows" "test -f .github/workflows/risk-adaptive-ci.yml"
validate_step "Healthcare policies" "test -f policies/healthcare/hipaa_phi_required.rego"
validate_step "AI forensics script" "test -x scripts/intelligent-bisect.sh"
validate_step "Healthcare demo script" "test -x healthcare-demo.sh"
echo ""

echo -e "${BOLD}2. Go Services${NC}"
validate_step "Payment gateway builds" "cd services/payment-gateway && go build -o /tmp/pg . 2>/dev/null && cd ../.."
validate_step "Auth service builds" "cd services/auth-service && go build -o /tmp/as . 2>/dev/null && cd ../.."
validate_step "Payment gateway tests" "cd services/payment-gateway && go test ./... 2>/dev/null && cd ../.."
validate_step "Auth service tests" "cd services/auth-service && go test ./... 2>/dev/null && cd ../.."
echo ""

echo -e "${BOLD}3. Python Tools${NC}"
validate_step "Healthcare commit generator" "python3 -c 'import tools.healthcare_commit_generator'"
validate_step "AI compliance framework" "python3 -c 'import tools.ai_compliance_framework'"
validate_step "Risk scorer" "python3 -c 'import tools.git_intel.risk_scorer'"
echo ""

echo -e "${BOLD}4. Documentation${NC}"
validate_step "README" "test -f README.md"
validate_step "Deployment guide" "test -f docs/DEPLOYMENT_GUIDE.md"
validate_step "Quick start" "test -f docs/QUICK_START.md"
validate_step "Changelog" "grep -q '2.0.0' CHANGELOG.md"
echo ""

echo "================================================================"
echo -e "${BOLD}Validation Summary${NC}"
echo "================================================================"
echo -e "Tests Passed:  ${GREEN}${VALIDATION_PASSED}${NC}"
echo -e "Tests Failed:  ${RED}${VALIDATION_FAILED}${NC}"
echo ""

if [ $VALIDATION_FAILED -eq 0 ]; then
    echo -e "${BOLD}${GREEN}✅ ALL VALIDATIONS PASSED${NC}"
    echo -e "${BOLD}${BLUE}Repository Status: PUBLICATION READY 🚀${NC}"
    exit 0
else
    echo -e "${BOLD}${YELLOW}⚠️  SOME VALIDATIONS FAILED${NC}"
    exit 1
fi
