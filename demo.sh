#!/bin/bash
set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║   Healthcare GitOps Intelligence - Interactive Demo          ║
║   Golden Path: AI Commit → Policy Gate → Forensics           ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if setup was run
if [ ! -f ".gitops/config.json" ]; then
    echo -e "${RED}✗ Setup not complete${NC}"
    echo -e "  Run: ${YELLOW}./setup.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}This demo will walk you through 3 workflows:${NC}"
echo "  1. AI-Assisted Commit Generation (30 seconds)"
echo "  2. Policy-as-Code Enforcement (automated)"
echo "  3. Intelligent Regression Detection (< 3 minutes)"
echo ""

read -p "Press ENTER to start the demo..."

# Flow 1: AI-Assisted Commit
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Flow 1: AI-Assisted Healthcare Commit${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

./scripts/flow-1-ai-commit.sh

read -p "Press ENTER to continue to Flow 2..."

# Flow 2: Policy Enforcement
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Flow 2: Policy-as-Code Enforcement${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

./scripts/flow-2-policy-gate.sh

read -p "Press ENTER to continue to Flow 3..."

# Flow 3: Intelligent Forensics
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Flow 3: Intelligent Regression Detection${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

./scripts/flow-3-bisect.sh

# Demo complete
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Demo Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "What you experienced:"
echo "  1. ✅ AI-generated compliant commit (15 min → 30 sec)"
echo "  2. ✅ Automated policy enforcement (100% coverage)"
echo "  3. ✅ Intelligent forensics (2-4 hours → 2.7 min)"
echo ""
echo "Next steps:"
echo "  • Read START_HERE.md for detailed walkthrough"
echo "  • Run individual flows: ./scripts/flow-*.sh"
echo "  • Explore code: tools/ and policies/"
echo "  • Run tests: pytest tests/python/ -v"
echo ""
echo -e "${YELLOW}Clean up demo artifacts:${NC} ./scripts/cleanup-demo.sh"
echo ""
