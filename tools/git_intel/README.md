# Git Intelligence Tools

AI-assisted tools for risk scoring and incident response in healthcare Git repositories.

## Tools

### 1. `risk_scorer.py` - Risk Assessment for Commits

Calculates risk scores (0-100) for Git commits based on:
- **File paths modified** (PHI services, auth, payments)
- **Commit metadata** (HIPAA, FDA, clinical safety impact)
- **Change scope** (number of files, complexity)

**Usage:**

```bash
# Analyze current commit
python tools/git_intel/risk_scorer.py

# Analyze specific commit
python tools/git_intel/risk_scorer.py --commit abc123

# JSON output for CI/CD
python tools/git_intel/risk_scorer.py --format json

# GitHub Actions output
python tools/git_intel/risk_scorer.py --output-github-actions
```

**Risk Levels:**
- **Low (0-39)**: Auto-deploy, standard checks
- **Medium (40-69)**: Enhanced scanning, canary rollout, single approval
- **High (70-100)**: Dual approval, full audit trail, controlled rollout

**Example Output:**

```
🎯 Risk Assessment for Commit: HEAD
============================================================

📊 Risk Score: 75/100
🚦 Risk Level: HIGH
🚀 Deployment Strategy: controlled_rollout
✅ Approval Required: Yes
📝 Audit Level: full

📋 Risk Factors:
  • High-risk path modified: services/phi-service/encryption.go
  • Direct PHI impact declared
  • Critical clinical safety impact

============================================================

⚠️  HIGH RISK - Required Actions:
  • Dual approval from security + compliance teams
  • Full HIPAA/FDA evidence generation
  • Controlled rollout with extensive monitoring
  • Complete audit trail documentation
```

---

### 2. `git_intelligent_bisect.py` - AI-Assisted Incident Response

Intelligently narrows down problem commits by analyzing metadata to prioritize testing commits most likely to be the culprit.

**Usage:**

```bash
# PHI access incident
python tools/git_intel/git_intelligent_bisect.py \
  --good v1.0.0 \
  --bad HEAD \
  --involves-phi \
  --service phi-service

# Auth failure incident
python tools/git_intel/git_intelligent_bisect.py \
  --good HEAD~20 \
  --bad HEAD \
  --security-incident \
  --service auth-service

# Generate automated test script
python tools/git_intel/git_intelligent_bisect.py \
  --good HEAD~50 \
  --bad HEAD \
  --clinical-incident \
  --generate-script bisect_test.sh \
  --test-command "make test"
```

**Example Output:**

```
🔍 Intelligent Bisect Analysis
======================================================================

Range: abc123..def456
Total commits in range: 47

📋 Incident Context:
  • PHI-related incident
  • Service: phi-service

🎯 Top 10 Suspected Commits (by priority):
======================================================================

1. a1b2c3d - Score: 85/100
   feat(phi-service): update encryption algorithm
   Author: Jane Doe | Date: 2026-01-03
   Metadata: phi_impact=direct, clinical_safety=critical, risk_level=high
   Key files: services/phi-service/encryption.go

2. e4f5g6h - Score: 70/100
   refactor(phi-service): change database schema
   Author: John Smith | Date: 2026-01-02
   Metadata: phi_impact=direct, service=phi-service
   Key files: services/phi-service/models.go

...

======================================================================

💡 Suggested Testing Order:
   Test these commits in the order shown above.
   Start with #1 (highest priority score).
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Calculate Risk Score
  id: risk
  run: |
    python tools/git_intel/risk_scorer.py --output-github-actions

- name: Require Dual Approval for High Risk
  if: steps.risk.outputs.level == 'high'
  run: |
    echo "High-risk change detected - requiring dual approval"
    gh pr edit ${{ github.event.pull_request.number }} --add-label "requires-dual-approval"
```

### Pre-commit Hook Example

```bash
#!/bin/bash
# .git/hooks/pre-commit

python tools/git_intel/risk_scorer.py --commit HEAD

if [ $? -eq 1 ]; then
    echo "⚠️  High-risk commit detected. Ensure proper approvals before merging."
fi
```

---

## Architecture

```
tools/git_intel/
├── __init__.py
├── risk_scorer.py           # Risk scoring engine
├── git_intelligent_bisect.py # Incident response tool
└── README.md               # This file
```

---

## Requirements

- Python 3.8+
- Git 2.0+
- No external dependencies (uses stdlib only)

---

## HIPAA Compliance Note

These tools are designed for healthcare compliance workflows but do not process or store PHI. They analyze Git metadata only.

**HIPAA**: Not Applicable  
**PHI-Impact**: None  
**Clinical-Safety**: None
