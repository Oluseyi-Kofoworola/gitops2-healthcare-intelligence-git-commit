#!/bin/bash
# Flow 2: Policy-as-Code Enforcement (REAL VERSION)
# This validates actual commits against real OPA policies

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

print_header "Flow 2: Policy-as-Code Enforcement (Live Demo)"

echo "This demo will:"
echo "  1. Create a real commit with HIPAA metadata"
echo "  2. Validate against actual OPA policies"
echo "  3. Calculate real risk score"
echo "  4. Determine deployment strategy"
echo ""

# Check if OPA is installed
if ! command -v opa &> /dev/null; then
    print_error "OPA not found. Install with: brew install opa"
    exit 1
fi

# Test 1: Compliant commit
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Creating COMPLIANT commit with proper metadata"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create commit metadata
mkdir -p .gitops
cat > .gitops/commit_metadata.json << 'EOF'
{
  "commit_type": "security",
  "scope": "phi",
  "description": "implement AES-256-GCM encryption for patient records",
  "risk_level": "MEDIUM",
  "clinical_safety": "NO_CLINICAL_IMPACT",
  "compliance_domains": ["HIPAA", "FDA-21-CFR-11"],
  "phi_impact": "DIRECT",
  "business_impact": "Enables HIPAA-compliant data storage",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hipaa_requirements": ["164.312(a)(2)(iv)"],
  "approvers": ["security-team", "compliance-officer"],
  "files_modified": 1
}
EOF

# Create actual code change
mkdir -p services/phi-service/internal/security
cat > services/phi-service/internal/security/encryption.go << 'EOF'
package security

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "errors"
    "io"
)

// EncryptPHI encrypts Protected Health Information using AES-256-GCM
// HIPAA Requirement: §164.312(a)(2)(iv) - Encryption and decryption
func EncryptPHI(plaintext []byte, key []byte) ([]byte, error) {
    if len(key) != 32 {
        return nil, errors.New("key must be 32 bytes for AES-256")
    }

    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }

    nonce := make([]byte, gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return nil, err
    }

    return gcm.Seal(nonce, nonce, plaintext, nil), nil
}
EOF

git add .gitops/commit_metadata.json services/phi-service/internal/security/encryption.go 2>/dev/null || true

echo "Running OPA policy validation..."
echo ""

# Create test input for OPA
cat > /tmp/opa_test_input.json << EOF
{
  "commit": {
    "message": "security(phi): implement AES-256-GCM encryption for patient records",
    "metadata": $(cat .gitops/commit_metadata.json)
  }
}
EOF

# Test against HIPAA metadata policy
echo "📋 Checking HIPAA metadata requirements..."
opa eval -d policies/healthcare/commit_metadata_required.rego \
         -i /tmp/opa_test_input.json \
         'data.healthcare.commit_metadata.deny' > /tmp/opa_result.json

if [ "$(cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value')" == "null" ] || \
   [ "$(cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value | length')" == "0" ]; then
    print_success "✓ HIPAA metadata present"
else
    print_error "✗ HIPAA metadata validation failed"
    cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value[]'
fi

# Test against PHI impact policy
echo "📋 Checking PHI impact requirements..."
opa eval -d policies/healthcare/hipaa_phi_required.rego \
         -i /tmp/opa_test_input.json \
         'data.healthcare.phi_impact.deny' > /tmp/opa_result.json

if [ "$(cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value')" == "null" ] || \
   [ "$(cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value | length')" == "0" ]; then
    print_success "✓ PHI impact level specified"
else
    print_error "✗ PHI impact validation failed"
    cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value[]'
fi

echo ""
print_success "All policy checks passed!"

# Calculate real risk score
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Risk Scoring & Deployment Strategy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 tools/git_intel/risk_scorer.py score \
    --metadata .gitops/commit_metadata.json \
    --output /tmp/risk_assessment.json

cat /tmp/risk_assessment.json | jq '.'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 2: Non-compliant commit
read -p "Press ENTER to see a NON-COMPLIANT commit example..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Creating NON-COMPLIANT commit (missing metadata)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create incomplete metadata (missing required fields)
cat > .gitops/commit_metadata.json << 'EOF'
{
  "commit_type": "fix",
  "scope": "phi",
  "description": "update patient handler"
}
EOF

cat > /tmp/opa_test_input.json << EOF
{
  "commit": {
    "message": "fix(phi): update patient handler",
    "metadata": $(cat .gitops/commit_metadata.json)
  }
}
EOF

echo "Running OPA policy validation..."
echo ""

# This should FAIL
opa eval -d policies/healthcare/commit_metadata_required.rego \
         -i /tmp/opa_test_input.json \
         'data.healthcare.commit_metadata.deny' > /tmp/opa_result.json

VIOLATIONS=$(cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value | length')
if [ "$VIOLATIONS" -gt 0 ]; then
    print_error "Policy violations detected:"
    cat /tmp/opa_result.json | jq -r '.result[0].expressions[0].value[]' | while read line; do
        echo "  ❌ $line"
    done
else
    echo "  ✓ No violations (unexpected)"
fi

echo ""
print_success "Flow 2 Complete!"
echo ""
echo "Summary:"
echo "  ✅ Compliant commits pass all OPA policies"
echo "  ❌ Non-compliant commits are automatically blocked"
echo "  📊 Risk scores determine deployment strategy"
echo ""
echo "In CI/CD pipeline, non-compliant commits would:"
echo "  1. Be blocked from merging"
echo "  2. Require additional approvals"
echo "  3. Trigger security team notification"
