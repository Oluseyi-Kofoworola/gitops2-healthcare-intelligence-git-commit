#!/bin/bash
# Flow 2: Policy-as-Code Enforcement

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

print_header "Flow 2: Policy-as-Code Enforcement"

# Check if metadata exists
if [ ! -f ".gitops/commit_metadata.json" ]; then
    print_error "Metadata file not found"
    echo "Run Flow 1 first: ./scripts/flow-1-ai-commit.sh"
    exit 1
fi

echo "Running compliance checks..."
python3 tools/ai_compliance_framework.py check --file .gitops/commit_metadata.json

echo ""
echo "Calculating risk score..."
python3 tools/git_intel/risk_scorer.py score --metadata .gitops/commit_metadata.json

echo ""
print_success "Flow 2 Complete!"
echo ""
echo "Next steps:"
echo "  - Review the risk assessment"
echo "  - Check deployment strategy recommendation"
echo "  - Run Flow 3 for forensics demo"
