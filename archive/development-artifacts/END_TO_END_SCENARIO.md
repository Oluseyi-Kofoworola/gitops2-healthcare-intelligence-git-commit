# End-to-End Scenario: Healthcare Compliance Workflow

> **Scenario**: Developer adds encryption feature to PHI service  
> **Compliance**: HIPAA Security Rule  
> **Risk Level**: High  
> **Estimated Time**: 30 minutes

---

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Walkthrough](#step-by-step-walkthrough)
4. [System Interactions](#system-interactions)
5. [Validation & Monitoring](#validation--monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Scenario Overview

### Business Context

**Problem**: The PHI service currently stores patient records with database-level encryption only. HIPAA Security Rule §164.312(a)(2)(iv) requires encryption of electronic PHI at rest.

**Solution**: Implement application-level AES-256-GCM encryption for patient records before database storage.

**Compliance Requirements**:
- HIPAA metadata in commit messages
- Security team approval for PHI changes
- Automated validation evidence
- Audit trail generation

### Success Criteria

- ✅ Code implements AES-256-GCM encryption
- ✅ Commit includes required HIPAA metadata
- ✅ OPA policies validate compliance
- ✅ Risk score triggers appropriate CI/CD strategy
- ✅ Deployment succeeds with audit trail
- ✅ Monitoring confirms encryption is active

---

## Prerequisites

### Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# 2. Install tools
pip install -e tools/
brew install opa jq docker

# 3. Start local services
docker-compose up -d

# 4. Verify setup
gitops-health --version
opa version
docker ps | grep phi-service
```

### Permissions

- Developer access to `phi-service` repository
- Ability to create feature branches
- GitHub Actions enabled
- OPA policy validation configured

---

## Step-by-Step Walkthrough

### Step 1: Create Feature Branch

```bash
# Create and checkout feature branch
git checkout -b feature/phi-encryption-at-rest

# Verify you're on the right branch
git branch --show-current
# Output: feature/phi-encryption-at-rest
```

---

### Step 2: Implement Encryption

**File**: `services/phi-service/internal/encryption/aes.go`

```go
package encryption

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "encoding/base64"
    "fmt"
    "io"
)

// EncryptPHI encrypts patient health information using AES-256-GCM
// Compliance: HIPAA Security Rule §164.312(a)(2)(iv)
func EncryptPHI(plaintext []byte, key []byte) (string, error) {
    if len(key) != 32 {
        return "", fmt.Errorf("key must be 32 bytes for AES-256")
    }

    block, err := aes.NewCipher(key)
    if err != nil {
        return "", fmt.Errorf("failed to create cipher: %w", err)
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return "", fmt.Errorf("failed to create GCM: %w", err)
    }

    nonce := make([]byte, gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return "", fmt.Errorf("failed to generate nonce: %w", err)
    }

    ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)
    return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// DecryptPHI decrypts patient health information
func DecryptPHI(ciphertext string, key []byte) ([]byte, error) {
    data, err := base64.StdEncoding.DecodeString(ciphertext)
    if err != nil {
        return nil, fmt.Errorf("failed to decode ciphertext: %w", err)
    }

    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, fmt.Errorf("failed to create cipher: %w", err)
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, fmt.Errorf("failed to create GCM: %w", err)
    }

    nonceSize := gcm.NonceSize()
    if len(data) < nonceSize {
        return nil, fmt.Errorf("ciphertext too short")
    }

    nonce, ciphertext := data[:nonceSize], data[nonceSize:]
    plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {
        return nil, fmt.Errorf("failed to decrypt: %w", err)
    }

    return plaintext, nil
}
```

**File**: `services/phi-service/internal/repository/patient.go`

```go
// UpdatePatient updates patient record with encryption
func (r *Repository) UpdatePatient(ctx context.Context, patient *Patient) error {
    // Encrypt sensitive fields before storage
    encrypted, err := encryption.EncryptPHI(
        []byte(patient.MedicalRecord),
        r.encryptionKey,
    )
    if err != nil {
        r.logger.Error("encryption failed", 
            zap.String("patient_id", patient.ID),
            zap.Error(err),
        )
        return fmt.Errorf("failed to encrypt PHI: %w", err)
    }

    patient.EncryptedMedicalRecord = encrypted
    patient.MedicalRecord = "" // Clear plaintext

    // Audit log (no PHI)
    r.auditLog.Record(ctx, AuditEvent{
        Action:    "patient_update",
        Resource:  patient.ID,
        Encrypted: true,
        Timestamp: time.Now(),
    })

    return r.db.Save(patient).Error
}
```

---

### Step 3: Add Tests

**File**: `services/phi-service/internal/encryption/aes_test.go`

```go
package encryption_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestEncryptDecryptPHI(t *testing.T) {
    key := make([]byte, 32) // AES-256 key
    copy(key, []byte("test-key-must-be-32-bytes!!!"))

    testCases := []struct {
        name      string
        plaintext string
    }{
        {"basic", "Patient has Type 2 diabetes"},
        {"empty", ""},
        {"large", strings.Repeat("medical data", 1000)},
    }

    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            // Encrypt
            ciphertext, err := EncryptPHI([]byte(tc.plaintext), key)
            require.NoError(t, err)
            assert.NotEmpty(t, ciphertext)

            // Decrypt
            decrypted, err := DecryptPHI(ciphertext, key)
            require.NoError(t, err)
            assert.Equal(t, tc.plaintext, string(decrypted))
        })
    }
}

func TestEncryptPHI_InvalidKey(t *testing.T) {
    shortKey := []byte("short")
    _, err := EncryptPHI([]byte("data"), shortKey)
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "must be 32 bytes")
}
```

---

### Step 4: Stage Changes & Generate Commit

```bash
# Stage all changes
git add services/phi-service/

# Generate compliant commit with AI assistance
gitops-health commit generate \
  --type security \
  --scope phi \
  --description "implement AES-256-GCM encryption for patient records at rest" \
  --compliance HIPAA \
  --risk-level high \
  --interactive
```

**AI Output**:
```
security(phi): implement AES-256-GCM encryption for patient records at rest

Adds application-level encryption for PHI before database storage to comply
with HIPAA Security Rule §164.312(a)(2)(iv).

Implementation:
- AES-256-GCM encryption in services/phi-service/internal/encryption/
- Automatic encryption/decryption in repository layer
- Secure key management with environment-based configuration
- Audit logging (no PHI) for all encryption operations

Business Impact:
- Achieves HIPAA encryption compliance for PHI at rest
- Reduces breach notification risk if database is compromised
- Enables granular access control via key management

Testing:
- Unit tests: encryption/decryption round-trip validation
- Integration tests: end-to-end patient record storage
- Security tests: key validation, error handling
- Performance tests: encryption overhead <10ms per operation

Compliance Evidence:
- HIPAA Security Rule §164.312(a)(2)(iv): Encryption at rest ✓
- NIST 800-53 SC-28: Protection of information at rest ✓
- Audit trail: All encryption operations logged

HIPAA-ADMIN: true
FDA-SOFTWARE: false
SOX-FINANCIAL: false
RISK-LEVEL: high
SUGGESTED-REVIEWERS: @security-team,@compliance-team,@phi-service-owners
```

---

### Step 5: Validate Commit Compliance

```bash
# Validate against OPA policies
gitops-health compliance analyze --commit HEAD

# Output:
{
  "commit": "abc123",
  "compliant": true,
  "violations": [],
  "warnings": [],
  "policies_evaluated": [
    "healthcare/hipaa_metadata.rego",
    "healthcare/phi_detection.rego",
    "enterprise-commit.rego"
  ],
  "summary": {
    "hipaa_metadata_present": true,
    "suggested_reviewers_present": true,
    "risk_level_specified": true,
    "conventional_commits_format": true
  }
}
```

```bash
# Score risk
gitops-health risk score --commit HEAD --verbose

# Output:
{
  "commit": "abc123",
  "overall_risk": "high",
  "risk_score": 8.2,
  "factors": {
    "semantic_type": {
      "type": "security",
      "base_score": 6.0,
      "rationale": "Security changes require careful review"
    },
    "path_criticality": {
      "critical_paths": ["services/phi-service/"],
      "score": 10.0,
      "rationale": "PHI service is critical infrastructure"
    },
    "change_magnitude": {
      "files_changed": 4,
      "lines_added": 215,
      "lines_deleted": 12,
      "score": 6.5,
      "rationale": "Moderate code change volume"
    }
  },
  "deployment_strategy": "blue-green-with-approval",
  "required_approvals": 2,
  "approval_teams": ["security-team", "compliance-team"],
  "ci_workflow": ".github/workflows/deploy-bluegreen.yml"
}
```

---

### Step 6: Push & Create Pull Request

```bash
# Push feature branch
git push origin feature/phi-encryption-at-rest

# Create PR (using GitHub CLI)
gh pr create \
  --title "security(phi): implement AES-256-GCM encryption for patient records" \
  --body "$(git log -1 --pretty=%B)" \
  --reviewer @security-team,@compliance-team \
  --label "security,hipaa,high-risk"
```

---

### Step 7: CI/CD Pipeline Execution

**GitHub Actions Workflow**: `.github/workflows/risk-adaptive-ci.yml`

```yaml
name: Risk-Adaptive CI/CD

on:
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      risk_level: ${{ steps.risk.outputs.level }}
      deployment_strategy: ${{ steps.risk.outputs.strategy }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Tools
        run: pip install -e tools/
      
      - name: Compliance Check
        run: |
          gitops-health compliance analyze --pr origin/main..HEAD
          if [ $? -ne 0 ]; then
            echo "❌ Compliance validation failed"
            exit 1
          fi
      
      - name: Risk Assessment
        id: risk
        run: |
          RESULT=$(gitops-health risk score --commit HEAD --json)
          echo "level=$(echo $RESULT | jq -r '.overall_risk')" >> $GITHUB_OUTPUT
          echo "strategy=$(echo $RESULT | jq -r '.deployment_strategy')" >> $GITHUB_OUTPUT

  test:
    needs: analyze
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Unit Tests
        run: |
          cd services/phi-service
          go test ./... -v -cover
      
      - name: Integration Tests
        run: |
          docker-compose up -d phi-service
          go test ./tests/integration/... -v
      
      - name: Security Tests
        run: |
          # Test encryption strength
          ./scripts/test-encryption-strength.sh
          
          # Verify no PHI in logs
          ./scripts/verify-no-phi-in-logs.sh

  deploy:
    needs: [analyze, test]
    if: needs.analyze.outputs.risk_level == 'high'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Blue-Green with Approval
        uses: ./.github/actions/deploy-bluegreen
        with:
          service: phi-service
          approval_required: true
          approvers: security-team,compliance-team
```

**Pipeline Output**:
```
✓ Compliance Check: PASSED
  - HIPAA metadata: Present ✓
  - Suggested reviewers: Present ✓
  - Conventional commits: Valid ✓

✓ Risk Assessment: HIGH (8.2/10)
  - Deployment strategy: blue-green-with-approval
  - Required approvals: 2
  - Approval teams: security-team, compliance-team

✓ Unit Tests: PASSED (95% coverage)
  - encryption/aes_test.go: 15/15 tests passed
  - repository/patient_test.go: 24/24 tests passed

✓ Integration Tests: PASSED
  - Encrypt/decrypt patient record: PASSED
  - Audit trail generation: PASSED
  - Performance: 7ms average encryption time

✓ Security Tests: PASSED
  - AES-256-GCM cipher mode: VERIFIED
  - Key length validation: PASSED
  - No PHI in logs: VERIFIED

⏳ Awaiting Approval (2/2 required):
  - @security-team: ✓ Approved
  - @compliance-team: ✓ Approved

✓ Blue-Green Deployment: IN PROGRESS
  - Green environment: HEALTHY
  - Traffic split: 0% → 50% → 100%
  - Health checks: PASSING
  - Rollback ready: YES
```

---

### Step 8: Monitor Deployment

```bash
# Watch deployment progress
kubectl get pods -l app=phi-service -w

# Check metrics
curl http://metrics.example.com/phi-service | jq '.encryption_operations'

# Output:
{
  "total_encryptions": 1523,
  "total_decryptions": 1489,
  "average_encryption_time_ms": 6.8,
  "average_decryption_time_ms": 5.2,
  "errors": 0,
  "success_rate": 1.0
}
```

**Grafana Dashboard**: `http://grafana.example.com/d/phi-service`

```
┌─ PHI Service Encryption Metrics ─────────────────────────┐
│                                                            │
│  Encryption Operations/min:     ████████░░░░  245 ops/min │
│  Average Latency:               ███░░░░░░░░░  6.8ms       │
│  Error Rate:                    ░░░░░░░░░░░░  0%          │
│  Database Encryption Status:    ████████████  100%        │
│                                                            │
│  Last 24h Audit Trail:          4,521 events logged       │
│  HIPAA Compliance Status:       ✓ COMPLIANT               │
└────────────────────────────────────────────────────────────┘
```

---

### Step 9: Generate Audit Report

```bash
# Generate compliance evidence
gitops-health audit report \
  --start-date 2025-11-23 \
  --end-date 2025-11-23 \
  --service phi-service \
  --output audit-report-20251123.pdf
```

**Audit Report Contents**:

```markdown
# HIPAA Compliance Audit Report
## PHI Service - Encryption Implementation

**Date**: November 23, 2025
**Service**: phi-service v2.1.0
**Compliance Framework**: HIPAA Security Rule §164.312(a)(2)(iv)

### Change Summary
- **Commit**: abc123def
- **Type**: Security Enhancement
- **Risk Level**: High
- **Deployment Strategy**: Blue-Green with Approval

### Compliance Evidence
✓ Encryption Algorithm: AES-256-GCM (FIPS 140-2 compliant)
✓ Key Length: 256 bits
✓ Key Management: Environment-based (production: AWS KMS)
✓ Audit Logging: Enabled (no PHI in logs)
✓ Access Controls: Role-based (dev/security/compliance only)

### Testing Evidence
✓ Unit Tests: 39/39 passed (95% coverage)
✓ Integration Tests: 12/12 passed
✓ Security Tests: 5/5 passed
✓ Performance Tests: <10ms latency requirement met

### Deployment Evidence
✓ Approval Gate: 2/2 approvals (security-team, compliance-team)
✓ Blue-Green Deployment: Successful
✓ Traffic Migration: 0% → 50% → 100% (no errors)
✓ Rollback Capability: Verified (blue environment preserved 24h)

### Operational Metrics (First 24h)
- Total Encryptions: 4,521
- Total Decryptions: 4,489
- Error Rate: 0.0%
- Average Latency: 6.8ms
- Patient Safety Incidents: 0

### Attestation
This change has been reviewed and approved by qualified personnel
and meets HIPAA Security Rule requirements for PHI encryption at rest.

Approved By:
- Security Team: Jane Doe (jane.doe@example.com)
- Compliance Team: John Smith (john.smith@example.com)

Date: November 23, 2025
```

---

## System Interactions

### Component Diagram

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Developer   │────▶│ gitops-health │────▶│  OPA Engine  │
│              │     │      CLI      │     │              │
└──────────────┘     └───────────────┘     └──────────────┘
                             │                     │
                             ▼                     ▼
                     ┌───────────────┐     ┌──────────────┐
                     │  Git Commit   │────▶│   Policies   │
                     │               │     │ ✓ HIPAA      │
                     └───────────────┘     │ ✓ FDA        │
                             │             │ ✓ SOX        │
                             ▼             └──────────────┘
                     ┌───────────────┐
                     │  GitHub PR    │
                     │               │
                     └───────────────┘
                             │
                             ▼
                     ┌───────────────┐     ┌──────────────┐
                     │ GitHub Actions│────▶│ Risk Scorer  │
                     │   Workflow    │     │              │
                     └───────────────┘     └──────────────┘
                             │                     │
                             ▼                     ▼
                     ┌───────────────┐     ┌──────────────┐
                     │  Test Suite   │     │ Deployment   │
                     │ ✓ Unit        │     │  Strategy    │
                     │ ✓ Integration │     │ Selector     │
                     │ ✓ Security    │     │              │
                     └───────────────┘     └──────────────┘
                             │                     │
                             └──────────┬──────────┘
                                        ▼
                             ┌───────────────────┐
                             │  Blue-Green       │
                             │  Deployment       │
                             │  (High Risk)      │
                             └───────────────────┘
                                        │
                                        ▼
                             ┌───────────────────┐
                             │  Production       │
                             │  PHI Service      │
                             └───────────────────┘
                                        │
                                        ▼
                             ┌───────────────────┐
                             │  Monitoring &     │
                             │  Audit Trail      │
                             └───────────────────┘
```

---

## Validation & Monitoring

### Post-Deployment Checks

```bash
# 1. Verify encryption is active
curl https://api.example.com/phi/health | jq '.encryption_enabled'
# Output: true

# 2. Check audit logs
kubectl logs -l app=phi-service | grep "encryption" | tail -5

# 3. Validate compliance status
gitops-health audit check --service phi-service
# Output: ✓ HIPAA compliant (encryption at rest: enabled)

# 4. Monitor error rates
kubectl top pod -l app=phi-service
```

### Continuous Monitoring

**Datadog Monitors**:
- PHI encryption operation errors > 0.1%
- PHI service latency > 100ms (p95)
- Unencrypted PHI detected in storage
- Audit log gaps > 5 minutes

**Alerts**:
- PagerDuty: Critical incidents
- Slack: Compliance warnings
- Email: Daily compliance summary

---

## Troubleshooting

### Issue 1: Commit Validation Fails

**Error**:
```
❌ Compliance validation failed
Violation: Missing HIPAA-ADMIN metadata for PHI changes
```

**Solution**:
```bash
# Amend commit with metadata
git commit --amend

# Add to commit message:
HIPAA-ADMIN: true
RISK-LEVEL: high
```

### Issue 2: Deployment Blocked

**Error**:
```
⏳ Awaiting approval (1/2 required)
Missing: @compliance-team approval
```

**Solution**:
- Contact compliance team
- Provide compliance evidence document
- Wait for approval (SLA: 4 business hours)

### Issue 3: Performance Regression

**Error**:
```
❌ Performance test failed
Average encryption time: 45ms (threshold: 10ms)
```

**Solution**:
```bash
# Profile encryption performance
go test -bench=. -cpuprofile=cpu.prof

# Optimize hot path
# Consider: connection pooling, key caching, batch operations

# Re-test
go test -bench=BenchmarkEncryptPHI
```

---

## Key Takeaways

### What We Demonstrated

1. **AI-Powered Compliance**: Automatic generation of compliant commit messages
2. **Policy Enforcement**: OPA validation ensures HIPAA requirements are met
3. **Risk-Adaptive CI/CD**: High-risk changes trigger stricter deployment controls
4. **Automated Evidence**: Audit trails generated automatically for regulators
5. **End-to-End Traceability**: From code change to production deployment

### What This Proves

- Compliance automation **can** reduce manual overhead
- Git metadata **can** serve as audit evidence
- Risk scoring **can** inform deployment strategies
- AI agents **can** assist (not replace) engineers

### What's Still Needed for Production

- [ ] Real Kubernetes cluster with traffic splitting
- [ ] Production-grade key management (AWS KMS, HashiCorp Vault)
- [ ] Comprehensive security audit and penetration testing
- [ ] Formal HIPAA compliance assessment by qualified professionals
- [ ] Disaster recovery and backup procedures
- [ ] On-call runbooks and incident response procedures

---

**Scenario Status**: ✅ Complete  
**Next Steps**: See [ROADMAP.md](../ROADMAP.md) for production hardening plan

*For questions or issues with this scenario, open a GitHub issue.*
