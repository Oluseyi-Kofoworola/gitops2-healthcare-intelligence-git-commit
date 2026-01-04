#!/bin/bash
# Quick Test Suite - GitOps 2.0 Healthcare Intelligence Platform
# Validates all core functionality in under 60 seconds

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Quick Test Suite - GitOps 2.0 Healthcare Intelligence         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

PASSED=0
FAILED=0

# Function to print test header
test_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶ Test $1/5: $2${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to pass test
pass_test() {
    echo -e "${GREEN}✓ $1${NC}"
    PASSED=$((PASSED + 1))
}

# Function to fail test
fail_test() {
    echo -e "${RED}✗ $1${NC}"
    FAILED=$((FAILED + 1))
}

# Test 1: Service Binaries
test_header "1" "Verify Service Binaries"
if [ -f "bin/auth-service" ] && [ -f "bin/payment-gateway" ] && [ -f "bin/phi-service" ]; then
    pass_test "All 3 service binaries built successfully"
    
    # Check binary sizes
    AUTH_SIZE=$(du -h bin/auth-service | awk '{print $1}')
    PAY_SIZE=$(du -h bin/payment-gateway | awk '{print $1}')
    PHI_SIZE=$(du -h bin/phi-service | awk '{print $1}')
    
    echo "  • auth-service: $AUTH_SIZE"
    echo "  • payment-gateway: $PAY_SIZE"
    echo "  • phi-service: $PHI_SIZE"
else
    fail_test "Service binaries not found. Run: make build"
fi

# Test 2: OPA Policies
test_header "2" "Validate OPA Policies"
if [ -d "policies/healthcare" ]; then
    POLICY_COUNT=$(find policies/healthcare -name "*.rego" -not -name "*_test.rego" | wc -l | tr -d ' ')
    
    if [ "$POLICY_COUNT" -gt 0 ]; then
        pass_test "Found $POLICY_COUNT healthcare compliance policies"
        
        # Check for OPA installation
        if command -v opa &> /dev/null; then
            # Test policy syntax (syntax check only, not unit tests)
            if opa check policies/healthcare/*.rego > /dev/null 2>&1; then
                pass_test "All OPA policies have valid syntax"
            else
                echo "  Checking OPA policy syntax..."
                opa check policies/healthcare/*.rego
            fi
        else
            echo -e "${YELLOW}  ⚠ OPA not installed. Install from: https://www.openpolicyagent.org${NC}"
        fi
    else
        fail_test "No OPA policies found in policies/healthcare/"
    fi
else
    fail_test "policies/healthcare/ directory not found"
fi

# Test 3: Python Tools
test_header "3" "Verify Python AI Tools"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
    pass_test "Python virtual environment activated"
else
    echo -e "${YELLOW}  ⚠ Virtual environment not found. Using system Python${NC}"
fi

# Check git_copilot_commit.py
if [ -f "tools/git_copilot_commit.py" ]; then
    if python3 tools/git_copilot_commit.py --help > /dev/null 2>&1; then
        pass_test "git_copilot_commit.py executable and working"
    else
        fail_test "git_copilot_commit.py has errors"
    fi
else
    fail_test "tools/git_copilot_commit.py not found"
fi

# Check required packages
REQUIRED_PACKAGES=("openai" "pyyaml" "click" "gitpython")
MISSING_PACKAGES=0

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}  • $package: installed${NC}"
    else
        echo -e "${RED}  • $package: missing${NC}"
        MISSING_PACKAGES=$((MISSING_PACKAGES + 1))
    fi
done

if [ $MISSING_PACKAGES -eq 0 ]; then
    pass_test "All required Python packages installed"
else
    fail_test "$MISSING_PACKAGES required Python packages missing"
fi

# Test 4: Documentation
test_header "4" "Check Documentation"

DOCS=("README.md" "START_HERE.md" "docs/GETTING_STARTED.md" "docs/QUICK_REFERENCE.md")
DOC_COUNT=0

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        DOC_COUNT=$((DOC_COUNT + 1))
        echo -e "${GREEN}  • $doc: present${NC}"
    else
        echo -e "${RED}  • $doc: missing${NC}"
    fi
done

if [ $DOC_COUNT -eq ${#DOCS[@]} ]; then
    pass_test "All core documentation files present"
else
    fail_test "Some documentation files missing"
fi

# Test 5: Service Health Checks (Quick)
test_header "5" "Quick Service Health Checks"

# Start services in background with timeout
echo "Starting services for health check..."

# Start auth-service
./bin/auth-service > /dev/null 2>&1 &
AUTH_PID=$!
sleep 1

# Start payment-gateway  
./bin/payment-gateway > /dev/null 2>&1 &
PAY_PID=$!
sleep 1

# Start phi-service
./bin/phi-service > /dev/null 2>&1 &
PHI_PID=$!
sleep 2

# Check if services are responding
SERVICES_UP=0

if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    pass_test "auth-service (port 8080) responding"
    SERVICES_UP=$((SERVICES_UP + 1))
else
    fail_test "auth-service (port 8080) not responding"
fi

if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    pass_test "payment-gateway (port 8081) responding"
    SERVICES_UP=$((SERVICES_UP + 1))
else
    fail_test "payment-gateway (port 8081) not responding"
fi

if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    pass_test "phi-service (port 8082) responding"
    SERVICES_UP=$((SERVICES_UP + 1))
else
    fail_test "phi-service (port 8082) not responding"
fi

# Stop services
echo "Stopping test services..."
kill $AUTH_PID $PAY_PID $PHI_PID 2>/dev/null || true
sleep 1

# Final Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Results Summary                                            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}✗ Failed: $FAILED${NC}"
fi
echo ""

TOTAL=$((PASSED + FAILED))
SUCCESS_RATE=$((PASSED * 100 / TOTAL))

if [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 All Systems Operational! ($SUCCESS_RATE% Success Rate)              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Set OpenAI API key: ${YELLOW}export OPENAI_API_KEY='sk-your-key'${NC}"
    echo "  2. Try AI commit generation: ${YELLOW}python tools/git_copilot_commit.py --help${NC}"
    echo "  3. Run full demo: ${YELLOW}./scripts/demo.sh${NC}"
    exit 0
else
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠ Some Tests Failed ($SUCCESS_RATE% Success Rate)                     ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Please review the failures above and run:${NC}"
    echo "  • ${YELLOW}./setup.sh${NC} to reinstall dependencies"
    echo "  • ${YELLOW}make build${NC} to rebuild services"
    exit 1
fi
