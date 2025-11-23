# Compliance Guide: HIPAA, FDA 21 CFR Part 11, and SOX

> **Target Audience**: Compliance officers, security teams, auditors, and healthcare IT administrators.

---

## Table of Contents

1. [Regulatory Framework Overview](#regulatory-framework-overview)
2. [HIPAA Compliance](#hipaa-compliance)
3. [FDA 21 CFR Part 11 Compliance](#fda-21-cfr-part-11-compliance)
4. [SOX Compliance](#sox-compliance)
5. [Evidence Collection](#evidence-collection)
6. [Audit Procedures](#audit-procedures)
7. [Incident Response](#incident-response)
8. [Continuous Compliance](#continuous-compliance)

---

## Regulatory Framework Overview

### Compliance Mapping Matrix

| Requirement | HIPAA § 164.312(b) | FDA 21 CFR 11.10 | SOX 404 | GitOps Implementation |
|-------------|-------------------|------------------|---------|----------------------|
| **Audit Controls** | ✅ Required | ✅ Required | ✅ Required | Immutable Git history + OPA logs |
| **Access Controls** | ✅ Required | ✅ Required | ✅ Required | GitHub branch protection + RBAC |
| **Data Integrity** | ✅ Required | ✅ Required | ✅ Required | Git commit signing + checksums |
| **Encryption** | ✅ Required | ❌ Not specified | ✅ Required | Git-crypt + Azure Key Vault |
| **Electronic Signatures** | ❌ Not required | ✅ Required | ❌ Not required | GPG commit signing |
| **Change Control** | ⚠️ Recommended | ✅ Required | ✅ Required | Pull request approvals + CI gates |
| **Data Retention** | ✅ Required (6 years) | ✅ Required (varies) | ✅ Required (7 years) | Git repository archival |

**Legend**:
- ✅ = Directly enforced by platform
- ⚠️ = Partially automated, manual review required
- ❌ = Not applicable to this framework

---

## HIPAA Compliance

### §164.312(b) - Audit Controls

**Requirement**:
> "Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information."

**GitOps Implementation**:

#### 1. PHI Detection Engine

```python
# tools/gitops_health/compliance.py
class PHIDetector:
    """
    Detects 18 HIPAA-defined PHI identifiers:
    1. Names
    2. Geographic subdivisions smaller than state
    3. Dates (except year)
    4. Telephone numbers
    5. Fax numbers
    6. Email addresses
    7. Social Security numbers
    8. Medical record numbers
    9. Health plan beneficiary numbers
    10. Account numbers
    11. Certificate/license numbers
    12. Vehicle identifiers
    13. Device identifiers and serial numbers
    14. Web URLs
    15. IP addresses
    16. Biometric identifiers
    17. Full-face photographs
    18. Any other unique identifying characteristic
    """
    
    PHI_PATTERNS = {
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "phone": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "date": r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        "mrn": r'\b(?:MRN|Medical Record|Patient ID)[:\s#]*([A-Z0-9]{6,12})\b',
        "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        "drivers_license": r'\b[A-Z]{1,2}\d{5,8}\b',
        # ... additional patterns
    }
    
    def scan_commit(self, commit: Commit) -> List[PHIViolation]:
        violations = []
        for file in commit.files_changed:
            for line_num, line in enumerate(file.content.split('\n'), 1):
                for phi_type, pattern in self.PHI_PATTERNS.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(PHIViolation(
                            file=file.path,
                            line=line_num,
                            phi_type=phi_type,
                            matched_text=self._redact(line),
                            severity="CRITICAL",
                            remediation=f"Remove {phi_type} or use synthetic data"
                        ))
        return violations
```

**OPA Policy**:
```rego
# policies/hipaa_phi_detection.rego
package compliance.hipaa

import future.keywords.in
import future.keywords.if

# Deny commits containing PHI
deny[msg] if {
    some file in input.files_changed
    contains_phi(file.content)
    
    msg := sprintf(
        "HIPAA VIOLATION: PHI detected in %s. Commit blocked until sanitized.",
        [file.path]
    )
}

# PHI detection function
contains_phi(content) if {
    phi_patterns := [
        `\b\d{3}-\d{2}-\d{4}\b`,  # SSN
        `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`,  # Email
        # ... additional patterns
    ]
    
    some pattern in phi_patterns
    regex.match(pattern, content)
}

# Require HIPAA officer approval for PHI-adjacent changes
requires_approval if {
    some file in input.files_changed
    startswith(file.path, "services/patient-data/")
    not input.approvers[_] == "hipaa-officer@example.com"
}
```

#### 2. Audit Trail Requirements

**Evidence Generated**:

```json
{
  "audit_id": "audit-2024-01-15-001",
  "timestamp": "2024-01-15T10:23:45Z",
  "event_type": "PHI_ACCESS_ATTEMPT",
  "actor": {
    "user_id": "jane.doe@hospital.com",
    "role": "developer",
    "ip_address": "10.0.1.45"
  },
  "resource": {
    "commit_hash": "a1b2c3d4e5f6",
    "files_accessed": ["patient-service/src/models/patient.go"],
    "phi_detected": true,
    "phi_types": ["email", "phone"]
  },
  "action": {
    "type": "COMMIT_BLOCKED",
    "reason": "PHI_VIOLATION",
    "policy": "hipaa_phi_detection.rego"
  },
  "remediation": {
    "action_taken": "COMMIT_REJECTED",
    "notification_sent_to": ["security@hospital.com", "hipaa-officer@hospital.com"],
    "ticket_created": "SEC-2024-0123"
  }
}
```

**Retention Policy**:
```yaml
# config/compliance/retention.yaml
hipaa_audit_logs:
  retention_period: 6_years
  storage:
    primary: azure_blob_storage
    backup: azure_archive_storage
  encryption: AES-256
  access_control: RBAC
  immutability: enabled
```

### §164.308(a)(5) - Security Awareness Training

**Automated Training Triggers**:

```python
# When developer first commits PHI violation
def trigger_training(developer: User, violation: PHIViolation):
    send_notification(
        to=developer.email,
        subject="HIPAA Training Required",
        body=f"""
        Your commit {violation.commit_hash} was blocked due to PHI detection.
        
        Required Action:
        1. Complete HIPAA Security Training Module 3: "Safe Coding Practices"
        2. Review synthetic data generation guide: /docs/SYNTHETIC_DATA.md
        3. Resubmit commit after removing PHI
        
        Detected PHI:
        - File: {violation.file}
        - Type: {violation.phi_type}
        - Line: {violation.line}
        
        Need Help? Contact: hipaa-officer@hospital.com
        """
    )
    
    create_training_assignment(
        user=developer,
        course="HIPAA_SAFE_CODING",
        due_date=datetime.now() + timedelta(days=7)
    )
```

---

## FDA 21 CFR Part 11 Compliance

### §11.10 - Controls for Closed Systems

**Requirement**:
> "Persons who use closed systems to create, modify, maintain, or transmit electronic records shall employ procedures and controls designed to ensure the authenticity, integrity, and confidentiality of electronic records."

#### (a) Validation of Systems

**System Validation Evidence**:

```yaml
# docs/validation/SYSTEM_VALIDATION_PLAN.md
---
title: GitOps 2.0 System Validation Plan
version: 2.0.0
effective_date: 2024-01-01
approval:
  qa_manager: John Smith
  regulatory_affairs: Sarah Johnson
  date: 2024-01-01

validation_tests:
  - id: VAL-001
    requirement: "§11.10(a) - System validation"
    test: "Verify commit signature validation"
    procedure: |
      1. Create unsigned commit
      2. Attempt to push to protected branch
      3. Verify commit is rejected
      4. Sign commit with GPG key
      5. Push again
      6. Verify commit is accepted
    expected_result: "Unsigned commits rejected, signed commits accepted"
    actual_result: "PASS - See test log VAL-001-2024-01-15.log"
    tester: "Jane Doe"
    date: "2024-01-15"

  - id: VAL-002
    requirement: "§11.10(b) - Audit trail generation"
    test: "Verify audit trail creation for all changes"
    procedure: |
      1. Make code change to regulated file
      2. Commit and push
      3. Query audit log database
      4. Verify entry contains: who, what, when, why
    expected_result: "Audit entry created with all required fields"
    actual_result: "PASS - Audit ID: audit-2024-01-15-002"
    tester: "Jane Doe"
    date: "2024-01-15"
```

#### (b) Audit Trail Generation

**Audit Trail Schema**:

```sql
-- Database schema for FDA-compliant audit trail
CREATE TABLE fda_audit_trail (
    audit_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_name VARCHAR(200) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- CREATE, MODIFY, DELETE, APPROVE
    resource_type VARCHAR(50) NOT NULL, -- CODE, CONFIG, POLICY
    resource_id VARCHAR(200) NOT NULL,  -- commit hash, file path
    change_description TEXT NOT NULL,
    change_reason TEXT,  -- "why" - business justification
    previous_value TEXT,
    new_value TEXT,
    approval_required BOOLEAN NOT NULL,
    approver_user_id VARCHAR(100),
    approval_timestamp TIMESTAMP,
    electronic_signature VARCHAR(500),  -- GPG signature
    client_ip_address INET NOT NULL,
    client_user_agent TEXT,
    
    -- FDA-specific fields
    regulatory_impact VARCHAR(20),  -- LOW, MEDIUM, HIGH
    validation_status VARCHAR(20),  -- VALIDATED, PENDING, FAILED
    
    -- Immutability controls
    record_hash VARCHAR(64) NOT NULL,  -- SHA-256 of row data
    previous_record_hash VARCHAR(64),  -- Chain of custody
    
    CONSTRAINT fk_actor FOREIGN KEY (actor_user_id) REFERENCES users(user_id),
    CONSTRAINT fk_approver FOREIGN KEY (approver_user_id) REFERENCES users(user_id)
);

-- Prevent modifications (append-only)
CREATE RULE no_update AS ON UPDATE TO fda_audit_trail DO INSTEAD NOTHING;
CREATE RULE no_delete AS ON DELETE TO fda_audit_trail DO INSTEAD NOTHING;
```

**Example Audit Entry**:

```sql
INSERT INTO fda_audit_trail VALUES (
    'FDA-2024-01-15-001',
    '2024-01-15 10:23:45',
    'john.doe@pharma.com',
    'John Doe',
    'MODIFY',
    'CODE',
    'services/drug-dosage-calculator/src/calculator.go',
    'Updated dosage calculation algorithm to fix rounding error',
    'Bug fix: Dosages were rounded down instead of to nearest integer, causing underdosing in 0.3% of cases',
    'func calculateDosage(weight float64) int { return int(weight * 0.5) }',
    'func calculateDosage(weight float64) int { return int(math.Round(weight * 0.5)) }',
    TRUE,
    'medical.director@pharma.com',
    '2024-01-15 14:30:00',
    '-----BEGIN PGP SIGNATURE-----\niQIzBAABCAAdFiEE...',
    '10.0.1.45',
    'git/2.40.0',
    'HIGH',
    'VALIDATED',
    'a3f5b8c9d2e1f7a4b6c8d9e0f1a2b3c4',
    '9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b'
);
```

#### (c) Electronic Signatures

**GPG Commit Signing**:

```bash
# 1. Generate GPG key
gpg --full-generate-key
# Select: RSA and RSA, 4096 bits, no expiration
# User ID: "John Doe (FDA Regulated Code) <john.doe@pharma.com>"

# 2. Configure Git
git config --global user.signingkey <GPG_KEY_ID>
git config --global commit.gpgSign true

# 3. All commits automatically signed
git commit -m "feat(dosage): fix rounding error in calculator"

# 4. Verify signature
git log --show-signature
# Output:
# commit a1b2c3d4e5f6
# gpg: Signature made Mon Jan 15 10:23:45 2024 PST
# gpg: using RSA key ABCD1234EFGH5678
# gpg: Good signature from "John Doe (FDA Regulated Code) <john.doe@pharma.com>"
```

**OPA Policy Enforcement**:

```rego
# policies/fda_21cfr11_signatures.rego
package compliance.fda

# Require signed commits for regulated files
deny[msg] if {
    some file in input.files_changed
    is_regulated_file(file.path)
    not input.commit.signed
    
    msg := "FDA 21 CFR Part 11 VIOLATION: Regulated file modified without electronic signature"
}

# Files requiring signatures
is_regulated_file(path) if {
    regulated_paths := [
        "services/drug-dosage-calculator/",
        "services/medical-device-control/",
        "services/clinical-trial-data/"
    ]
    
    some prefix in regulated_paths
    startswith(path, prefix)
}

# Require documented reason for changes
deny[msg] if {
    some file in input.files_changed
    is_regulated_file(file.path)
    not contains(input.commit.message, "Reason:")
    
    msg := "FDA 21 CFR Part 11 VIOLATION: Change reason not documented in commit message"
}
```

---

## SOX Compliance

### §404 - Assessment of Internal Control

**Requirement**:
> "Management must assess the effectiveness of internal controls over financial reporting annually."

#### Access Control Matrix

```yaml
# config/compliance/sox_access_control.yaml
---
financial_systems_access:
  # Principle: Separation of duties
  roles:
    developer:
      can_commit: true
      can_approve_pr: false  # Cannot approve own PRs
      can_deploy_production: false
      can_access_financial_data: false
    
    senior_developer:
      can_commit: true
      can_approve_pr: true
      can_deploy_production: false
      can_access_financial_data: false
    
    devops_engineer:
      can_commit: true
      can_approve_pr: false
      can_deploy_production: true  # Only after PR approval
      can_access_financial_data: false
    
    financial_auditor:
      can_commit: false
      can_approve_pr: false
      can_deploy_production: false
      can_access_financial_data: true  # Read-only audit trail
    
    cfo:
      can_commit: false
      can_approve_pr: false
      can_deploy_production: false
      can_access_financial_data: true

  # Critical financial services
  critical_services:
    - payment-gateway
    - billing-service
    - revenue-recognition
    - financial-reporting
  
  # Approval requirements
  approval_rules:
    - service: payment-gateway
      required_approvers: 2
      approver_roles: [senior_developer, technical_lead]
      deployment_window: "weekdays 9am-5pm EST"
      testing_required: [unit, integration, e2e, penetration]
    
    - service: financial-reporting
      required_approvers: 3
      approver_roles: [senior_developer, technical_lead, cfo]
      deployment_window: "after_market_close"  # After 4pm EST
      testing_required: [unit, integration, e2e, sox_audit]
```

#### Change Control Process

```yaml
# .github/workflows/sox-change-control.yml
name: SOX Change Control
on:
  pull_request:
    paths:
      - 'services/payment-gateway/**'
      - 'services/billing-service/**'
      - 'services/revenue-recognition/**'

jobs:
  sox-compliance-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Verify Approval Count
        run: |
          APPROVALS=$(gh pr view ${{ github.event.pull_request.number }} \
            --json reviews --jq '[.reviews[] | select(.state=="APPROVED")] | length')
          
          if [ "$APPROVALS" -lt 2 ]; then
            echo "❌ SOX VIOLATION: Financial system changes require 2 approvals"
            exit 1
          fi
      
      - name: Verify Approver Roles
        run: |
          # Check that approvers have correct roles
          APPROVERS=$(gh pr view ${{ github.event.pull_request.number }} \
            --json reviews --jq '[.reviews[] | select(.state=="APPROVED") | .author.login]')
          
          python3 tools/verify_sox_approvers.py \
            --approvers "$APPROVERS" \
            --required-roles "senior_developer,technical_lead"
      
      - name: Verify Testing Completion
        run: |
          # Ensure all required tests passed
          TESTS_PASSED=$(gh pr checks ${{ github.event.pull_request.number }} \
            --json state --jq '[.[] | select(.state=="success")] | length')
          
          REQUIRED_TESTS=4  # unit, integration, e2e, penetration
          
          if [ "$TESTS_PASSED" -lt "$REQUIRED_TESTS" ]; then
            echo "❌ SOX VIOLATION: All tests must pass before merge"
            exit 1
          fi
      
      - name: Create SOX Audit Record
        run: |
          gitops-health audit record \
            --type SOX_CHANGE_CONTROL \
            --pr-number ${{ github.event.pull_request.number }} \
            --service payment-gateway \
            --approvers "$APPROVERS" \
            --tests-passed "$TESTS_PASSED" \
            --output sox-audit-record.json
      
      - name: Store Audit Record
        run: |
          az storage blob upload \
            --account-name compliancestorage \
            --container sox-audit-trail \
            --file sox-audit-record.json \
            --name "2024/01/sox-audit-${{ github.event.pull_request.number }}.json"
```

---

## Evidence Collection

### Automated Evidence Generation

```python
# tools/gitops_health/compliance.py
class ComplianceEvidenceCollector:
    """
    Automatically collects evidence for audits.
    Evidence types:
    1. Policy enforcement logs
    2. Access control matrices
    3. Change control records
    4. Electronic signature verification
    5. Audit trail completeness
    """
    
    def collect_hipaa_evidence(self, start_date: datetime, end_date: datetime) -> HIPAAEvidence:
        return HIPAAEvidence(
            audit_trail=self._query_audit_trail(start_date, end_date),
            phi_scan_results=self._query_phi_scans(start_date, end_date),
            access_logs=self._query_access_logs(start_date, end_date),
            encryption_status=self._verify_encryption(),
            training_records=self._query_training_records(start_date, end_date)
        )
    
    def collect_fda_evidence(self, start_date: datetime, end_date: datetime) -> FDAEvidence:
        return FDAEvidence(
            system_validation=self._get_validation_reports(),
            change_control=self._query_change_control(start_date, end_date),
            electronic_signatures=self._verify_signatures(start_date, end_date),
            audit_trail=self._query_audit_trail(start_date, end_date),
            deviation_reports=self._query_deviations(start_date, end_date)
        )
    
    def collect_sox_evidence(self, start_date: datetime, end_date: datetime) -> SOXEvidence:
        return SOXEvidence(
            access_control_matrix=self._get_current_access_matrix(),
            separation_of_duties=self._verify_separation_of_duties(),
            change_approvals=self._query_approvals(start_date, end_date),
            deployment_logs=self._query_deployments(start_date, end_date),
            access_reviews=self._query_access_reviews(start_date, end_date)
        )
    
    def generate_audit_package(self, framework: str, year: int) -> AuditPackage:
        """
        Generate complete audit package for annual review.
        """
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)
        
        if framework == "HIPAA":
            evidence = self.collect_hipaa_evidence(start, end)
        elif framework == "FDA":
            evidence = self.collect_fda_evidence(start, end)
        elif framework == "SOX":
            evidence = self.collect_sox_evidence(start, end)
        
        return AuditPackage(
            framework=framework,
            period=f"{year}",
            evidence=evidence,
            summary_report=self._generate_summary(evidence),
            attestation=self._generate_attestation(evidence),
            generated_at=datetime.now()
        )
```

### Evidence Storage

```yaml
# Evidence retention in Azure Blob Storage
compliance_evidence:
  storage_account: complianceevidence
  containers:
    hipaa:
      retention: 6_years
      tier: Cool
      encryption: AES-256
      access: RBAC
      legal_hold: true
    
    fda:
      retention: 10_years  # Device records
      tier: Cool
      encryption: AES-256
      access: RBAC
      legal_hold: true
    
    sox:
      retention: 7_years
      tier: Cool
      encryption: AES-256
      access: RBAC
      legal_hold: true
```

---

## Audit Procedures

### Annual Compliance Audit Workflow

```bash
# 1. Generate audit package
gitops-health audit generate \
  --framework HIPAA \
  --year 2024 \
  --output audit-package-hipaa-2024.zip

# 2. Package contents:
# audit-package-hipaa-2024/
# ├── summary_report.pdf
# ├── audit_trail/
# │   ├── access_logs.csv
# │   ├── phi_scans.json
# │   └── policy_violations.json
# ├── evidence/
# │   ├── encryption_verification.pdf
# │   ├── training_records.csv
# │   └── access_control_matrix.xlsx
# ├── attestation/
# │   ├── management_attestation.pdf (signed by CIO)
# │   └── security_officer_attestation.pdf (signed by CISO)
# └── metadata.json

# 3. Submit to auditor
az storage blob upload \
  --account-name auditorshare \
  --container annual-audits \
  --file audit-package-hipaa-2024.zip
```

### Quarterly Self-Assessment

```python
# Run quarterly self-assessment
def run_quarterly_assessment(quarter: int, year: int):
    results = {
        "hipaa": assess_hipaa_compliance(),
        "fda": assess_fda_compliance(),
        "sox": assess_sox_compliance()
    }
    
    # Generate report
    report = generate_assessment_report(results)
    
    # Email to compliance committee
    send_email(
        to="compliance-committee@hospital.com",
        subject=f"Q{quarter} {year} Compliance Self-Assessment",
        body=report,
        attachments=["assessment-details.pdf"]
    )
    
    # Create action items for any deficiencies
    for framework, result in results.items():
        if result.deficiencies:
            for deficiency in result.deficiencies:
                create_jira_ticket(
                    project="COMPLIANCE",
                    summary=f"{framework} Deficiency: {deficiency.title}",
                    description=deficiency.description,
                    priority="High",
                    due_date=calculate_due_date(deficiency.severity)
                )
```

---

## Incident Response

### Compliance Breach Response Plan

```yaml
# Incident severity levels
incident_severity:
  P0_CRITICAL:
    description: "Actual PHI exposure or regulatory violation"
    response_time: 15_minutes
    escalation: [CISO, Legal, CEO, Regulatory Affairs]
    notification_required: [HHS OCR, State AG, Affected Individuals]
    notification_deadline: 60_days
    
  P1_HIGH:
    description: "Potential PHI exposure or policy violation"
    response_time: 1_hour
    escalation: [Security Team, Compliance Officer]
    notification_required: [Internal Audit]
    notification_deadline: 24_hours
    
  P2_MEDIUM:
    description: "Compliance control failure (no exposure)"
    response_time: 4_hours
    escalation: [Security Team]
    notification_required: [IT Management]
    notification_deadline: 48_hours
```

**Example Incident**:

```markdown
# INCIDENT REPORT: PHI-2024-001

## Incident Details
- **Date**: 2024-01-15
- **Severity**: P1 (High)
- **Type**: Potential PHI Exposure
- **Detected By**: Automated OPA policy scan

## Description
Developer committed patient email addresses to public repository branch before realizing branch visibility was set to "public".

## Timeline
- **10:23 AM**: Commit pushed to `feature/patient-notifications`
- **10:24 AM**: OPA policy detected PHI in diff
- **10:24 AM**: Automated alert sent to Security Team
- **10:30 AM**: Branch visibility changed to private
- **10:35 AM**: Git history rewritten to remove PHI
- **10:40 AM**: Force push completed
- **11:00 AM**: Verified no external forks/clones

## Root Cause
Developer created feature branch with default "public" visibility setting.

## Containment
1. Branch made private immediately
2. Git history rewritten using `git filter-branch`
3. GitHub API verified no forks created
4. External search engines checked (no indexing yet)

## Resolution
- **Impact**: No confirmed external access
- **Data Exposed**: 12 patient email addresses
- **Exposure Duration**: 7 minutes
- **External Access**: None detected

## Remediation
1. Updated default branch visibility to "private"
2. Added pre-push hook to verify branch visibility
3. Developer completed HIPAA refresher training
4. Implemented branch protection rules

## Regulatory Determination
- **Breach Notification Required**: No (no evidence of acquisition)
- **Regulatory Reporting**: Not required
- **Documentation**: Incident logged for annual audit
```

---

## Continuous Compliance

### Daily Compliance Monitoring

```yaml
# .github/workflows/daily-compliance-scan.yml
name: Daily Compliance Scan
on:
  schedule:
    - cron: '0 0 * * *'  # Midnight UTC

jobs:
  compliance-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Scan for PHI in Recent Commits
        run: |
          gitops-health compliance scan \
            --framework HIPAA \
            --since "24 hours ago" \
            --output phi-scan-results.json
      
      - name: Verify Audit Trail Integrity
        run: |
          gitops-health audit verify \
            --start-date "$(date -d '1 day ago' +%Y-%m-%d)" \
            --end-date "$(date +%Y-%m-%d)"
      
      - name: Check Access Control Violations
        run: |
          gitops-health access-control audit \
            --framework SOX \
            --output access-violations.json
      
      - name: Generate Daily Report
        run: |
          gitops-health compliance report \
            --frameworks HIPAA,FDA,SOX \
            --period daily \
            --output daily-compliance-report.pdf
      
      - name: Send Report to Compliance Team
        run: |
          az communication email send \
            --sender "compliance-bot@hospital.com" \
            --recipients "compliance-team@hospital.com" \
            --subject "Daily Compliance Report - $(date +%Y-%m-%d)" \
            --html daily-compliance-report.pdf
```

### Compliance Dashboard Metrics

```yaml
# Grafana dashboard metrics
compliance_metrics:
  - name: hipaa_violations_daily
    query: |
      sum(increase(gitops_compliance_violations_total{framework="HIPAA"}[24h]))
    alert_threshold: 0
    
  - name: fda_unsigned_commits_daily
    query: |
      sum(increase(gitops_unsigned_commits_total{regulated="true"}[24h]))
    alert_threshold: 0
    
  - name: sox_unauthorized_access_attempts
    query: |
      sum(increase(gitops_unauthorized_access_total{service=~"payment-.*|billing-.*"}[24h]))
    alert_threshold: 0
    
  - name: audit_trail_completeness
    query: |
      (sum(gitops_audit_records_total) / sum(gitops_commits_total)) * 100
    alert_threshold: 99.9  # Alert if < 99.9%
```

---

## Additional Resources

- [Engineering Guide](/docs/ENGINEERING_GUIDE.md)
- [AI Tools Reference](/docs/AI_TOOLS_REFERENCE.md)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [FDA 21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)
- [SOX Section 404](https://www.soxlaw.com/s404.htm)

---

**Maintained by**: Compliance Team  
**Last Updated**: 2024-01-15  
**Questions?**: compliance-team@hospital.com
