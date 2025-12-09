#!/bin/bash
# Flow 1: AI-Assisted Commit Generation

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

print_header "Flow 1: AI-Assisted Healthcare Commit"

echo "Scenario: Adding encryption to patient records service"
echo ""

# Create actual encryption code in the correct location
cat > services/phi-service/encryption.go << 'EOF'
package main

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "errors"
    "io"
)

// EncryptPatientData encrypts patient data using AES-256-GCM
// Compliance: HIPAA Security Rule §164.312(a)(2)(iv)
func EncryptPatientData(plaintext []byte, key []byte) ([]byte, error) {
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

// DecryptPatientData decrypts AES-256-GCM encrypted data
func DecryptPatientData(ciphertext []byte, key []byte) ([]byte, error) {
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

    nonceSize := gcm.NonceSize()
    if len(ciphertext) < nonceSize {
        return nil, errors.New("ciphertext too short")
    }

    nonce, ciphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]
    return gcm.Open(nil, nonce, ciphertext, nil)
}
EOF

git add services/phi-service/encryption.go 2>/dev/null || true

echo "Running commit generator..."
mkdir -p .gitops

# Generate commit message and save to file
python3 tools/healthcare_commit_generator.py \
    --type security \
    --scope phi \
    --description "implement AES-256-GCM encryption for patient records" \
    --files services/phi-service/encryption.go \
    > .gitops/commit_message.txt 2>&1

# Extract just the commit message (remove warnings and logs)
grep -A 100 "^security(phi):" .gitops/commit_message.txt > .gitops/commit_clean.txt || true
if [ -s .gitops/commit_clean.txt ]; then
    mv .gitops/commit_clean.txt .gitops/commit_message.txt
fi

# Create metadata JSON
cat > .gitops/commit_metadata.json << 'EOFMETA'
{
  "commit_type": "security",
  "scope": "phi",
  "description": "implement AES-256-GCM encryption for patient records",
  "risk_level": "HIGH",
  "clinical_safety": "NO_CLINICAL_IMPACT",
  "compliance_domains": ["HIPAA", "FDA-21-CFR-11"],
  "phi_impact": "DIRECT",
  "business_impact": "Enables HIPAA-compliant data encryption at rest",
  "files_modified": 1,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOFMETA

echo ""
print_success "Flow 1 Complete!"
echo "Generated: .gitops/commit_message.txt"
echo "Metadata: .gitops/commit_metadata.json"
echo ""
echo "To commit:"
echo "  git commit -F .gitops/commit_message.txt"
