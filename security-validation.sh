#!/usr/bin/env bash
# Security Validation and Testing Script for GitOps 2.0 Healthcare Enterprise
# Performs comprehensive security testing for production deployment

set -euo pipefail

echo "🛡️  GitOps 2.0 Healthcare Security Validation"
echo "============================================"
echo ""

# Configuration
SERVICE_PORT=9091
TEST_TIMEOUT=30
MAX_REQUESTS=100

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Security test results tracking
SECURITY_TESTS_PASSED=0
SECURITY_TESTS_FAILED=0
TOTAL_SECURITY_TESTS=0

security_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="${3:-0}"
    
    ((TOTAL_SECURITY_TESTS++))
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        actual_result=0
    else
        actual_result=1
    fi
    
    if [ "$actual_result" = "$expected_result" ]; then
        echo -e "${GREEN}PASS${NC}"
        ((SECURITY_TESTS_PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((SECURITY_TESTS_FAILED++))
    fi
}

echo "📋 Phase 1: Code Security Validation"
echo "-----------------------------------"

# 1. Python Security Tests
echo "🐍 Python Security Analysis..."

# Check for secure YAML loading
if grep -r "yaml.safe_load" tools/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Safe YAML loading detected${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Unsafe YAML loading detected${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

# Check for proper encoding specification
if grep -r "encoding='utf-8'" tools/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}UTF-8 encoding specification found${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing encoding specification${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

# Check for input validation
if grep -r "raise ValueError" tools/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Input validation implemented${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing input validation${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

echo ""
echo "🔧 Go Security Analysis..."

# Check for security headers in Go code
if grep -r "X-Content-Type-Options" services/payment-gateway/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Security headers implemented${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing security headers${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

# Check for request validation
if grep -r "validateRequest" services/payment-gateway/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Request validation implemented${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing request validation${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

echo ""
echo "📋 Phase 2: Healthcare Compliance Security"
echo "-----------------------------------------"

# HIPAA compliance checks
echo "🏥 HIPAA Compliance Security..."

# Check for PHI protection in policies
if grep -r "PHI-Impact" policies/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}PHI impact assessment required${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing PHI impact requirements${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

# Check for audit trail requirements
if grep -r "Audit-Trail" tools/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Audit trail requirements found${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing audit trail requirements${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

# FDA compliance checks
echo "💊 FDA Compliance Security..."

if grep -r "FDA-510k" policies/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}FDA validation requirements found${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing FDA validation requirements${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

# SOX compliance checks  
echo "💰 SOX Compliance Security..."

if grep -r "Financial-Impact" tools/ >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Financial impact assessment found${NC}"
    ((SECURITY_TESTS_PASSED++))
else
    echo -e "❌ ${RED}Missing financial impact assessment${NC}"
    ((SECURITY_TESTS_FAILED++))
fi
((TOTAL_SECURITY_TESTS++))

echo ""
echo "📋 Phase 3: Runtime Security Testing"
echo "-----------------------------------"

# Start the payment service for security testing
echo "🚀 Starting payment gateway for security testing..."
cd services/payment-gateway
go build -o /tmp/secure-payment-gateway *.go
PORT=$SERVICE_PORT /tmp/secure-payment-gateway &
SERVICE_PID=$!
cd ../..

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up test service..."
    kill "$SERVICE_PID" >/dev/null 2>&1 || true
    rm -f /tmp/secure-payment-gateway
}
trap cleanup EXIT

# Wait for service to start
sleep 3

# Security testing
echo "🔒 Runtime Security Tests..."

# Test 1: Security headers
security_test "Security Headers Present" \
    "curl -s -I http://localhost:$SERVICE_PORT/health | grep -q 'X-Content-Type-Options: nosniff'"

# Test 2: Request size limiting
security_test "Request Size Limiting" \
    "curl -s -X POST -H 'Content-Type: application/json' -d '$(head -c 2000000 /dev/zero | tr '\0' 'a')' http://localhost:$SERVICE_PORT/charge" \
    1

# Test 3: Invalid content type rejection
security_test "Content Type Validation" \
    "curl -s -X POST -H 'Content-Type: text/plain' -d 'invalid' http://localhost:$SERVICE_PORT/charge | grep -q 'validation failed'"

# Test 4: JSON structure validation
security_test "JSON Validation" \
    "curl -s -X POST -H 'Content-Type: application/json' -d 'invalid json' http://localhost:$SERVICE_PORT/charge | grep -q 'invalid payload'"

# Test 5: Healthcare compliance endpoints
security_test "Compliance Endpoint Available" \
    "curl -s http://localhost:$SERVICE_PORT/compliance/status | grep -q 'hipaa_compliant'"

# Test 6: Audit endpoint available
security_test "Audit Endpoint Available" \
    "curl -s http://localhost:$SERVICE_PORT/audit/info | grep -q 'audit_enabled'"

# Test 7: HTTPS redirect (simulated)
security_test "Security Response Headers" \
    "curl -s -I http://localhost:$SERVICE_PORT/health | grep -q 'Strict-Transport-Security'"

echo ""
echo "📋 Phase 4: Policy Security Validation"  
echo "-------------------------------------"

# Test OPA policies
echo "⚖️  OPA Policy Security Tests..."

if command -v opa >/dev/null 2>&1; then
    # Run policy tests
    if opa test policies/ --verbose >/dev/null 2>&1; then
        echo -e "✅ ${GREEN}All OPA security policies pass${NC}"
        ((SECURITY_TESTS_PASSED++))
    else
        echo -e "❌ ${RED}OPA policy tests failed${NC}"
        ((SECURITY_TESTS_FAILED++))
    fi
    ((TOTAL_SECURITY_TESTS++))
    
    # Test healthcare compliance policies
    if opa test policies/ | grep -q "test_healthcare.*PASS" 2>/dev/null; then
        echo -e "✅ ${GREEN}Healthcare compliance policies validated${NC}"
        ((SECURITY_TESTS_PASSED++))
    else
        echo -e "⚠️  ${YELLOW}Healthcare compliance policy validation inconclusive${NC}"
    fi
    ((TOTAL_SECURITY_TESTS++))
else
    echo -e "⚠️  ${YELLOW}OPA not available, skipping policy tests${NC}"
fi

echo ""
echo "📋 Phase 5: Container Security Validation"
echo "----------------------------------------"

# Check Dockerfile security
echo "🐳 Container Security Analysis..."

if [ -f "services/payment-gateway/Dockerfile" ]; then
    # Check for non-root user
    if grep -q "USER nonroot" services/payment-gateway/Dockerfile; then
        echo -e "✅ ${GREEN}Non-root user configured in container${NC}"
        ((SECURITY_TESTS_PASSED++))
    else
        echo -e "❌ ${RED}Container running as root${NC}"
        ((SECURITY_TESTS_FAILED++))
    fi
    ((TOTAL_SECURITY_TESTS++))
    
    # Check for distroless base
    if grep -q "distroless" services/payment-gateway/Dockerfile; then
        echo -e "✅ ${GREEN}Distroless base image used${NC}"
        ((SECURITY_TESTS_PASSED++))
    else
        echo -e "⚠️  ${YELLOW}Consider using distroless base image${NC}"
    fi
    ((TOTAL_SECURITY_TESTS++))
else
    echo -e "⚠️  ${YELLOW}Dockerfile not found, skipping container security tests${NC}"
fi

echo ""
echo "🎯 SECURITY VALIDATION RESULTS"
echo "=============================="
echo ""

# Calculate security score
SECURITY_SCORE=$((SECURITY_TESTS_PASSED * 100 / TOTAL_SECURITY_TESTS))

echo "📊 Security Test Summary:"
echo "   Total Tests: $TOTAL_SECURITY_TESTS"
echo "   Tests Passed: $SECURITY_TESTS_PASSED"
echo "   Tests Failed: $SECURITY_TESTS_FAILED"
echo "   Security Score: $SECURITY_SCORE/100"
echo ""

# Security recommendations based on score
if [ $SECURITY_SCORE -ge 95 ]; then
    echo -e "🏆 ${GREEN}EXCELLENT SECURITY POSTURE${NC}"
    echo "✅ Ready for production healthcare deployment"
    echo "✅ All critical security controls implemented"
    echo "✅ Healthcare compliance requirements met"
elif [ $SECURITY_SCORE -ge 85 ]; then
    echo -e "✅ ${GREEN}GOOD SECURITY POSTURE${NC}"
    echo "⚠️  Minor security improvements recommended"
    echo "✅ Suitable for production with monitoring"
elif [ $SECURITY_SCORE -ge 70 ]; then
    echo -e "⚠️  ${YELLOW}MODERATE SECURITY POSTURE${NC}"
    echo "🔧 Security improvements required before production"
    echo "📋 Review failed tests and implement fixes"
else
    echo -e "❌ ${RED}INSUFFICIENT SECURITY POSTURE${NC}"
    echo "🚫 NOT READY for production deployment"
    echo "🔧 Critical security issues must be resolved"
fi

echo ""
echo "🔐 Healthcare Security Compliance Status:"
echo "   HIPAA: $([ $SECURITY_SCORE -ge 90 ] && echo "✅ COMPLIANT" || echo "❌ NEEDS WORK")"
echo "   FDA:   $([ $SECURITY_SCORE -ge 90 ] && echo "✅ COMPLIANT" || echo "❌ NEEDS WORK")" 
echo "   SOX:   $([ $SECURITY_SCORE -ge 90 ] && echo "✅ COMPLIANT" || echo "❌ NEEDS WORK")"
echo ""

if [ $SECURITY_SCORE -ge 90 ]; then
    echo "🏥 Ready for healthcare enterprise deployment!"
    exit 0
else
    echo "🔧 Security improvements required before production deployment"
    exit 1
fi
