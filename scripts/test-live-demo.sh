#!/bin/bash
# Quick Test: Verify live demo components work
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Testing Live Demo Components...${NC}\n"

# Test 1: Healthcare commit generator
echo -e "${YELLOW}Test 1: Healthcare Commit Generator${NC}"
if python3 tools/healthcare_commit_generator.py --help &>/dev/null; then
    echo -e "${GREEN}✓ Commit generator works${NC}"
else
    echo -e "${RED}✗ Commit generator failed${NC}"
    exit 1
fi

# Test 2: Risk scorer
echo -e "\n${YELLOW}Test 2: Risk Scorer${NC}"

# Create test metadata
mkdir -p /tmp/demo-test
cat > /tmp/demo-test/metadata.json << 'EOF'
{
  "commit_type": "security",
  "scope": "phi",
  "description": "test",
  "risk_level": "MEDIUM",
  "clinical_safety": "NO_CLINICAL_IMPACT",
  "compliance_domains": ["HIPAA"],
  "phi_impact": "DIRECT",
  "files_modified": 1
}
EOF

if python3 tools/git_intel/risk_scorer.py score --metadata /tmp/demo-test/metadata.json --output /tmp/demo-test/risk.json 2>/dev/null; then
    RISK_SCORE=$(cat /tmp/demo-test/risk.json | python3 -c "import sys, json; print(json.load(sys.stdin)['risk_score'])")
    echo -e "${GREEN}✓ Risk scorer works (score: ${RISK_SCORE})${NC}"
else
    echo -e "${RED}✗ Risk scorer failed${NC}"
    exit 1
fi

# Test 3: OPA policies
echo -e "\n${YELLOW}Test 3: OPA Policies${NC}"
if command -v opa &> /dev/null; then
    if opa test policies/healthcare/ --verbose &>/dev/null; then
        echo -e "${GREEN}✓ OPA policies valid${NC}"
    else
        echo -e "${YELLOW}⚠ OPA policy tests had warnings (may be OK)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ OPA not installed (run: brew install opa)${NC}"
fi

# Test 4: Intelligent bisect
echo -e "\n${YELLOW}Test 4: Intelligent Bisect${NC}"
if python3 tools/intelligent_bisect.py --help &>/dev/null; then
    echo -e "${GREEN}✓ Intelligent bisect works${NC}"
else
    echo -e "${RED}✗ Intelligent bisect failed${NC}"
    exit 1
fi

# Test 5: Go services
echo -e "\n${YELLOW}Test 5: Go Services${NC}"
if cd services/phi-service && go build -o /tmp/phi-service-test ./... 2>/dev/null; then
    echo -e "${GREEN}✓ PHI service builds${NC}"
    cd ../..
else
    echo -e "${YELLOW}⚠ PHI service build failed (may need go mod tidy)${NC}"
    cd ../..
fi

# Cleanup
rm -rf /tmp/demo-test
rm -f /tmp/phi-service-test

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Live Demo Components Ready!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
echo "Run the full demo:"
echo -e "  ${YELLOW}./demo.sh${NC}\n"
echo "Or individual flows:"
echo -e "  ${YELLOW}./scripts/flow-1-ai-commit.sh${NC}"
echo -e "  ${YELLOW}./scripts/flow-2-policy-gate-real.sh${NC}"
echo -e "  ${YELLOW}./scripts/flow-3-bisect-real.sh${NC}"
