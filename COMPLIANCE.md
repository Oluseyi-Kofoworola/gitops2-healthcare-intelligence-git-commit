# Compliance Reference Guide

Quick reference for HIPAA, FDA 21 CFR Part 11, and SOX compliance controls in the Healthcare GitOps Intelligence Platform.

---

## HIPAA (Health Insurance Portability and Accountability Act)

### Security Rule Requirements

| Control | Implementation | Code Location |
|---------|---------------|---------------|
| **§164.308(a)(1)(ii)(D)** - Information System Activity Review | Audit logging with 7-year retention | `services/*/main.go` (logging), `tools/healthcare_commit_generator.py` (audit trail) |
| **§164.312(a)(1)** - Access Control | JWT authentication + RBAC | `services/auth-service/main.go` |
| **§164.312(b)** - Audit Controls | Structured logging, immutable audit trails | All services (`log.Info()`, `log.Audit()`) |
| **§164.312(e)(1)** - Transmission Security | TLS 1.3, certificate validation | `services/*/main.go` (HTTPS), `k8s/ingress.yaml` |
| **§164.312(e)(2)(ii)** - Encryption | AES-256-GCM for PHI at rest | `services/phi-service/main.go` |

### Privacy Rule Requirements

| Control | Implementation |
|---------|---------------|
| **Minimum Necessary** | RBAC limits data access to authorized roles |
| **Accounting of Disclosures** | Audit logs track all PHI access |
| **Patient Rights** | APIs for data access/export/deletion |

### Validation

```bash
# Check HIPAA-required commit metadata
git log --grep="HIPAA" --grep="PHI-Impact" --all-match

# Verify encryption enabled
kubectl exec -it phi-service-0 -- \
  env | grep ENCRYPTION_ENABLED

# Audit trail integrity
python tools/ai_compliance_framework.py verify-audit-trail \
  --framework HIPAA --since 7-years-ago
```

---

## FDA 21 CFR Part 11 (Electronic Records)

### Subpart B - Electronic Records

| Control | Implementation | Code Location |
|---------|---------------|---------------|
| **§11.10(a)** - System Validation | Automated testing (150+ tests), validation docs | `tests/` (unit/integration/E2E) |
| **§11.10(e)** - Audit Trail | Immutable commit history, structured logs | Git history + OpenTelemetry |
| **§11.10(k)** - Operational System Checks | Health checks, readiness probes | `services/*/main.go` (`/health`, `/ready`) |
| **§11.10(c)** - Change Control | OPA policies enforce metadata, dual approval | `policies/healthcare/high_risk_dual_approval.rego` |

### Subpart C - Electronic Signatures

| Control | Implementation |
|---------|---------------|
| **§11.200** - Electronic Signatures | GPG-signed commits, JWT-signed API requests |
| **§11.300** - Signature Manifestations | Commit metadata includes author, timestamp, GPG signature |

### Validation

```bash
# Verify system validation documentation
ls docs/validation/*.md

# Check audit trail for medical device changes
git log --grep="FDA\|medical-device" \
  --pretty=format:"%h %ad %s" --date=short

# Verify signed commits
git log --show-signature --grep="medical-device"
```

---

## SOX (Sarbanes-Oxley Act)

### Section 404 - Internal Controls

| Control | Implementation | Code Location |
|---------|---------------|---------------|
| **ITGC-001** - Change Management | All changes require commit metadata, peer review | `policies/healthcare/commit_metadata_required.rego` |
| **ITGC-002** - Access Management | RBAC, least privilege, JWT expiry | `services/auth-service/main.go` |
| **ITGC-003** - Segregation of Duties | Developer ≠ Approver (dual approval for HIGH risk) | `policies/healthcare/high_risk_dual_approval.rego` |
| **ITGC-005** - Audit Trails | All financial transactions logged, immutable | `services/payment-gateway/main.go` |

### Financial Controls

| Control | Implementation |
|---------|---------------|
| **Transaction Integrity** | AES-256-GCM encryption for payment data |
| **Access Logging** | All payment API calls audited with user ID |
| **7-Year Retention** | Audit logs retained for 7 years (HIPAA + SOX) |

### Validation

```bash
# Check SOX-required commit metadata
git log --grep="SOX" --grep="Financial-Impact" --all-match

# Verify payment gateway audit logs
kubectl logs -l app=payment-gateway --since=7d | grep AUDIT

# Access control verification
python tools/ai_compliance_framework.py verify-access-controls \
  --framework SOX --service payment-gateway
```

---

## Compliance Code Mapping

### Valid Compliance Codes

Use these codes in commit messages (enforced by OPA):

```
# HIPAA
HIPAA-164.308    # Administrative safeguards
HIPAA-164.310    # Physical safeguards
HIPAA-164.312    # Technical safeguards
HIPAA-PHI        # PHI handling
HIPAA-BAA        # Business Associate Agreement

# FDA
FDA-510k         # 510(k) premarket notification
FDA-QSR          # Quality System Regulation
FDA-21CFR11      # Electronic records/signatures
FDA-IVD          # In Vitro Diagnostic
FDA-SaMD         # Software as Medical Device

# SOX
SOX-302          # CEO/CFO certification
SOX-404          # Internal controls
SOX-409          # Real-time disclosure
SOX-ITGC         # IT General Controls
SOX-Financial    # Financial data handling
```

### Example Compliant Commit

```
security(payment): Patch CVE-2025-12345 token exposure vulnerability

Business Impact: payment security enhancement
Risk Level: HIGH
Clinical Safety: NO_CLINICAL_IMPACT
Compliance: PCI-DSS, SOX-404, SOX-ITGC
Reviewers: @engineering-team, @audit-team

Technical Details:
- Added token sanitization configuration
- Implemented TokenMaskPattern for log sanitization
- Default sanitization enabled for production safety

Audit Trail: 1 files modified at 2025-12-07T06:12:10+00:00
CVE: CVE-2025-12345
Priority: P0 (Critical Security)
```

---

## Automated Compliance Validation

### Generate Compliant Commit

```bash
python tools/healthcare_commit_generator.py \
  --type security \
  --scope payment \
  --description "Patch token exposure" \
  --files services/payment-gateway/config.go
```

### Validate Commit Compliance

```bash
# Check compliance codes
python tools/ai_compliance_framework.py analyze-commit HEAD

# Validate against OPA policies
opa eval --data policies/healthcare/ \
  --input <(git log -1 --pretty=format:'{"commit":{"message":"%B"}}') \
  "data.healthcare.valid_compliance_codes.allow"
```

### Risk Scoring

```bash
# Calculate risk score (0-100)
python tools/git_intel/risk_scorer.py --commit HEAD

# Output: risk_level (LOW/MEDIUM/HIGH/CRITICAL) + deployment strategy
```

---

## Audit Queries

### HIPAA Audit Queries

```bash
# All PHI-related changes (last 7 years)
git log --grep="PHI\|HIPAA" --since="7 years ago" \
  --pretty=format:"%h | %ad | %s" --date=short

# Access control changes
git log --grep="HIPAA-164.312" --grep="access" \
  --all-match --pretty=format:"%h | %ad | %s"
```

### FDA Audit Queries

```bash
# Medical device changes
git log --grep="FDA\|medical-device" --since="2024-01-01" \
  --pretty=format:"%h | %ad | %an | %s"

# Clinical safety validations
git log --grep="Clinical-Safety: REQUIRES_CLINICAL_REVIEW" \
  --pretty=format:"%h | %ad | %s"
```

### SOX Audit Queries

```bash
# Financial system changes (HIGH risk)
git log --grep="SOX" --grep="Risk Level: HIGH" \
  --all-match --pretty=format:"%h | %ad | %s"

# Changes requiring dual approval
git log --grep="Reviewers:.*@audit-team" \
  --pretty=format:"%h | %ad | %s"
```

---

## Compliance Reporting

### Generate Annual Report

```bash
# Full compliance report (HIPAA/FDA/SOX)
python tools/ai_compliance_framework.py annual-report \
  --year 2024 \
  --frameworks HIPAA,FDA,SOX \
  --output compliance-report-2024.pdf
```

### Evidence Collection

```bash
# Export audit evidence for auditors
python tools/ai_compliance_framework.py export-evidence \
  --framework HIPAA \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output evidence-hipaa-2024.zip
```

---

## Compliance Training

### For Developers

1. **Read**: [GETTING_STARTED.md](docs/GETTING_STARTED.md) - compliance workflow
2. **Practice**: Generate 5 compliant commits using AI tool
3. **Validate**: Run OPA policies on your commits
4. **Quiz**: Complete compliance knowledge check

### For Reviewers

1. Review commit metadata completeness
2. Verify appropriate risk level assigned
3. Check compliance codes match changed files
4. Ensure dual approval for HIGH/CRITICAL risk

---

## Support

- **Compliance Questions**: compliance@your-org.com
- **HIPAA Privacy Officer**: privacy@your-org.com
- **FDA Regulatory Affairs**: regulatory@your-org.com
- **SOX Audit Team**: audit@your-org.com
