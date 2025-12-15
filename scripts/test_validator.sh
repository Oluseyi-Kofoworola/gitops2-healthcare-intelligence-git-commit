#!/bin/bash
# Test GitOps 2.0 Commit Message Validator

set -e

VALIDATOR="scripts/validate_commit_msg.py"
TEMP_FILE="/tmp/test-commit-msg.txt"

echo "🧪 Testing GitOps 2.0 Commit Message Validator"
echo "=============================================="
echo ""

# Test 1: Valid compliant commit
echo "Test 1: Valid Compliant Commit"
cat > "$TEMP_FILE" << 'EOF'
feat(auth-service): implement MFA for PHI access

Add multi-factor authentication requirement for all endpoints
that retrieve patient health information.

HIPAA: Applicable
PHI-Impact: Direct
Clinical-Safety: Critical
Regulation: HIPAA
Service: auth-service
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "✅ Test 1 PASSED"
else
    echo "❌ Test 1 FAILED"
fi
echo ""

# Test 2: Missing required fields
echo "Test 2: Missing Required Fields (Should Fail)"
cat > "$TEMP_FILE" << 'EOF'
feat(auth-service): implement MFA

Add MFA support.

HIPAA: Applicable
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "❌ Test 2 FAILED (should have been rejected)"
else
    echo "✅ Test 2 PASSED (correctly rejected)"
fi
echo ""

# Test 3: Invalid field values
echo "Test 3: Invalid Field Values (Should Fail)"
cat > "$TEMP_FILE" << 'EOF'
feat(auth-service): implement MFA

Add MFA support.

HIPAA: Maybe
PHI-Impact: Direct
Clinical-Safety: Critical
Regulation: HIPAA
Service: auth-service
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "❌ Test 3 FAILED (should have been rejected)"
else
    echo "✅ Test 3 PASSED (correctly rejected)"
fi
echo ""

# Test 4: Wrong commit format
echo "Test 4: Wrong Commit Format (Should Fail)"
cat > "$TEMP_FILE" << 'EOF'
implement MFA

HIPAA: Applicable
PHI-Impact: Direct
Clinical-Safety: Critical
Regulation: HIPAA
Service: auth-service
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "❌ Test 4 FAILED (should have been rejected)"
else
    echo "✅ Test 4 PASSED (correctly rejected)"
fi
echo ""

# Test 5: Documentation change (low risk)
echo "Test 5: Documentation Change (Low Risk)"
cat > "$TEMP_FILE" << 'EOF'
docs(readme): update deployment instructions

Add step-by-step guide for Azure deployment.

HIPAA: Not Applicable
PHI-Impact: None
Clinical-Safety: Low
Regulation: None
Service: infrastructure
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "✅ Test 5 PASSED"
else
    echo "❌ Test 5 FAILED"
fi
echo ""

# Test 6: Security patch (critical)
echo "Test 6: Security Patch (Critical)"
cat > "$TEMP_FILE" << 'EOF'
sec(phi-service): patch SQL injection vulnerability

Fixed unparameterized SQL query in patient search endpoint.

HIPAA: Applicable
PHI-Impact: Direct
Clinical-Safety: Critical
Regulation: HIPAA
Service: phi-service
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "✅ Test 6 PASSED"
else
    echo "❌ Test 6 FAILED"
fi
echo ""

# Test 7: Merge commit (should skip validation)
echo "Test 7: Merge Commit (Should Skip Validation)"
cat > "$TEMP_FILE" << 'EOF'
Merge branch 'feature/new-feature' into main
EOF

if python3 "$VALIDATOR" "$TEMP_FILE"; then
    echo "✅ Test 7 PASSED (merge commit skipped)"
else
    echo "❌ Test 7 FAILED"
fi
echo ""

# Clean up
rm -f "$TEMP_FILE"

echo "=============================================="
echo "✅ All validator tests completed!"
echo ""
echo "Next steps:"
echo "  1. Install pre-commit hook: ./scripts/install_pre_commit_hook.sh"
echo "  2. Read the schema: .github/gitops-copilot-instructions.md"
echo "  3. Try making a commit!"
