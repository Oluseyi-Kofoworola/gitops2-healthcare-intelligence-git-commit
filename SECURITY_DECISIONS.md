# Security Decisions Log

WHY: Maintain auditable record of temporary security exceptions and rationale during iterative hardening of the GitOps 2.0 healthcare demo.

## Overview
This document captures conscious risk acceptance for LOW severity findings surfaced by Trivy / CodeQL / dependency audits. Each entry includes:
- Date
- Component / Path
- Vulnerability / Issue ID
- Severity
- Decision (Accept / Mitigate / Defer)
- Rationale (business & technical)
- Expiry / Revisit Date
- Owner

Acceptance is limited strictly to LOW severity items without known exploit paths affecting PHI, financial integrity (SOX controls), or authentication domains. MEDIUM+ severity requires immediate mitigation unless a compensating control exists.

## Current Accepted Low Severity Items
| Date | Component | Issue | Severity | Decision | Rationale | Expiry | Owner |
|------|-----------|-------|----------|----------|-----------|--------|-------|
| 2025-11-21 | root modules (Go) | transitive crypto lib minor version lag | LOW | Accept | No active CVE; update bundled in scheduled dependency sweep | 2025-12-05 | platform-team |
| 2025-11-21 | tools/python deps | pyyaml minor version behind latest | LOW | Defer | Security fixes already backported; updating post v1.1.0-dev stability | 2025-12-10 | platform-team |

## Compensating Controls
- Continuous SBOM generation (Syft) provides inventory for rapid reassessment.
- Trivy SARIF scanning on each pipeline run highlights severity changes.
- OPA policy denies high-risk commit patterns ensuring reduced blast radius.
- AI compliance framework monitors for security metadata anomalies.

## Decision Workflow
1. Detect finding via automated scan.
2. Triage severity & domain impact (payment, auth, PHI, device).
3. If LOW and non-critical: log acceptance with expiry.
4. Track in upcoming sprint for remediation before expiry.
5. Re-scan to confirm status; remove entry once resolved.

## Future Actions
- Automate generation of this log via daily compliance summary workflow.
- Integrate cosign signature attestation of SBOM & vulnerability snapshot.
- Add severity trend metrics to observability dashboard.

## Revision History
- 2025-11-21: Initial creation.
