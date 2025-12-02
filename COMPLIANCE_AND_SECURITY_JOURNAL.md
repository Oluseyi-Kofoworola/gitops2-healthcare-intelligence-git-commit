# Compliance & Security Journal – GitOps 2.0 Healthcare Intelligence

This journal consolidates security decisions, healthcare compliance behavior, and evidence/retention strategy into a single reference for auditors, security teams, and compliance officers.

## 1. Security Decisions & Risk Tradeoffs

Consolidated from `SECURITY_DECISIONS.md` and related status docs:

- Clear separation of demo/teaching behavior vs. production-grade expectations.
- Explicit documentation of where scans are warning-only vs. hard-fail.
- Token/permissions choices for CodeQL, Trivy, and artifact uploads.

## 2. Healthcare Compliance Pipelines

### 2.1 policy-check.yml – OPA Healthcare Policies

- Entry point: `data.enterprise.git.allow` (from `policies/enterprise-commit.rego`).
- Policies enforce:
  - HIPAA/PHI metadata on healthcare-related commits.
  - FDA 510(k) metadata for device/diagnostic changes.
  - SOX control metadata for financial/payment changes.
  - GDPR data-class metadata for privacy-related changes.
- Sample commit tests in the workflow now match the Rego metadata rules.

### 2.2 compliance-scan.yml – HIPAA/FDA/SOX Scans

- HIPAA job:
  - PHI pattern scanning with optional blocking via `BLOCKING_HIPAA_SCAN` flag.
  - Encryption, access control, and audit trail pattern checks over services.
- FDA job:
  - Commit-message metadata checks for FDA-related changes.
  - Clinical safety assessment for files with diagnostic/clinical patterns.
- SOX job:
  - Commit-message metadata checks for payment/financial changes.
  - SOX evidence generation (`sox-compliance-evidence.json`).
- Daily compliance summary:
  - Always runs on `schedule` even if upstream jobs fail.
  - Aggregates HIPAA/FDA/SOX status into a single JSON report.

### 2.3 risk-adaptive-ci.yml – Risk & Regulatory Evidence

- AI risk assessment determines compliance domains (HIPAA/FDA/SOX).
- OPA-based healthcare validation ensures commit metadata is present.
- Security & vulnerability scan:
  - Trivy runs and uploads SARIF via `github/codeql-action/upload-sarif@v3`.
  - Permissions explicitly set (`security-events: write`).
- Regulatory reporting:
  - `compliance-report.json` and `deployment-evidence.json` artifacts.

## 3. Evidence Retention vs. Regulatory Requirements

- GitHub artifact retention is capped by repo/org settings (often 90 days).
- This repo demonstrates three tiers:
  - **Policy Reports**: 90 days (teaching default).
  - **Daily Compliance Reports**: 365 days (where allowed).
  - **Regulatory Evidence**: intended 7-year HIPAA retention.
- Where YAML previously attempted `retention-days: 2555`, workflows now:
  - Use `retention-days: 90` in `risk-adaptive-ci.yml` with comments explaining the gap.
  - Document that long-term evidence must be exported to external, compliant storage.

## 4. Incident Forensics & Telemetry

- `docs/INCIDENT_FORENSICS_DEMO.md` captures example incidents, MTTR, and healthcare-specific impact.
- `docs/PIPELINE_TELEMETRY_LOGS.md` shows how pipeline telemetry is captured, stored, and correlated with incidents.

## 5. How to Use This Journal

- **Auditors**: start here to understand how HIPAA/FDA/SOX controls map into CI/CD.
- **Security Engineers**: use this as the ground truth for token/permission and scanner behavior.
- **Platform Teams**: adopt these patterns, but replace demo-friendly defaults (warning-only scans, truncated retention) with your organization’s production policies.
