# AI Tools Guide: Using gitops-health CLI

> **Status**: Reference Implementation  
> **Audience**: Developers, DevOps Engineers, Platform Teams  
> **Last Updated**: November 23, 2025

---

## Overview

The `gitops-health` CLI is a unified Python package that provides AI-powered tools for healthcare compliance automation. It consolidates multiple standalone scripts into a cohesive command-line interface.

**What it does**:
- Generates compliant commit messages with HIPAA/FDA/SOX metadata
- Validates commits against OPA policies
- Scores risk level of code changes
- Automates intelligent git bisect for incident response

**What it is NOT**:
- Not a replacement for human judgment on compliance decisions
- Not certified for production use without security review
- Not a guarantee of regulatory compliance

---

## Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# Install CLI (editable mode for development)
pip install -e tools/

# Verify installation
gitops-health --version
```

### Prerequisites

- Python 3.10+
- Git 2.30+
- OPA CLI (for policy validation)
- Docker (optional, for service testing)

---

## Core Commands

### 1. Commit Generation

Generate AI-powered commit messages with compliance metadata.

```bash
# Basic usage
gitops-health commit generate \
  --type feat \
  --scope payment \
  --description "add retry logic for failed transactions"

# With compliance context
gitops-health commit generate \
  --type security \
  --scope phi \
  --description "implement AES-256 encryption for patient records" \
  --compliance HIPAA \
  --risk-level high
```

**Output Example**:
```
feat(payment): add retry logic for failed transactions

Implements exponential backoff retry mechanism to handle transient
payment gateway failures.

Business Impact: Reduces transaction failure rate
Testing: Added unit tests + integration tests
Compliance: SOX-FINANCIAL-CONTROLS validated

HIPAA-ADMIN: false
FDA-SOFTWARE: false
SOX-FINANCIAL: true
RISK-LEVEL: medium
```

### 2. Compliance Analysis

Validate commits against OPA policies.

```bash
# Analyze current commit
gitops-health compliance analyze --commit HEAD

# Analyze specific commit
gitops-health compliance analyze --commit abc123

# Analyze all commits in PR
gitops-health compliance analyze --pr origin/main..HEAD
```

**Output Example**:
```json
{
  "commit": "abc123",
  "compliant": false,
  "violations": [
    {
      "policy": "healthcare/hipaa_metadata.rego",
      "rule": "require_hipaa_metadata_for_phi_changes",
      "severity": "error",
      "message": "PHI-touching changes must include HIPAA-ADMIN metadata",
      "files": ["services/phi-service/handlers.go"]
    }
  ],
  "warnings": [
    {
      "policy": "enterprise-commit.rego",
      "rule": "suggest_reviewers",
      "severity": "warning",
      "message": "High-risk changes should specify reviewers"
    }
  ]
}
```

### 3. Risk Scoring

Assess the risk level of code changes.

```bash
# Score current changes
gitops-health risk score --commit HEAD

# Score with detailed breakdown
gitops-health risk score --commit HEAD --verbose

# Score multiple commits
gitops-health risk score --range HEAD~10..HEAD
```

**Output Example**:
```json
{
  "commit": "abc123",
  "overall_risk": "high",
  "risk_score": 8.5,
  "factors": {
    "semantic_type": {
      "type": "security",
      "base_score": 6.0,
      "weight": 0.3
    },
    "path_criticality": {
      "critical_paths": ["services/payment-gateway/"],
      "score": 10.0,
      "weight": 0.4
    },
    "change_magnitude": {
      "files_changed": 12,
      "lines_added": 450,
      "lines_deleted": 120,
      "score": 7.0,
      "weight": 0.3
    }
  },
  "deployment_strategy": "blue-green-with-approval",
  "required_approvals": 2,
  "recommended_reviewers": ["@security-team", "@compliance-team"]
}
```

### 4. Intelligent Forensics

Automate incident response with intelligent git bisect.

```bash
# Find performance regression
gitops-health forensics bisect \
  --metric latency \
  --threshold 200 \
  --start HEAD~20

# Find error rate spike
gitops-health forensics bisect \
  --metric error_rate \
  --threshold 0.05 \
  --test-command "./scripts/integration-test.sh"

# With custom health check
gitops-health forensics bisect \
  --health-check "./scripts/check-patient-safety.sh" \
  --start v2.0.0 \
  --end v2.1.0
```

**Output Example**:
```json
{
  "regression_found": true,
  "bad_commit": "def456",
  "good_commit": "abc123",
  "bisect_steps": 5,
  "analysis": {
    "commit": "def456",
    "author": "jane.doe@example.com",
    "date": "2025-11-20T14:30:00Z",
    "message": "refactor(api): optimize database queries",
    "impact": {
      "metric": "latency",
      "before": "150ms",
      "after": "350ms",
      "change": "+133%"
    },
    "root_cause": "Missing index on patient_records.created_at",
    "patient_safety_impact": "none",
    "recommended_action": "Immediate rollback + add missing index"
  }
}
```

---

## Configuration

### Global Configuration

Create `~/.gitops-health/config.yml`:

```yaml
# Default compliance frameworks
compliance:
  frameworks:
    - HIPAA
    - FDA_21_CFR_PART_11
    - SOX
  
# Risk scoring thresholds
risk:
  thresholds:
    low: 0-3
    medium: 4-6
    high: 7-8
    critical: 9-10
  
  critical_paths:
    - services/payment-gateway/
    - services/phi-service/
    - services/medical-device/
  
# AI models (optional)
ai:
  provider: openai  # or azure-openai, anthropic
  model: gpt-4
  temperature: 0.3

# OPA policy settings
opa:
  policy_dir: ./policies
  strict_mode: true
```

### Project Configuration

Create `gitops-health.yml` in your repository root:

```yaml
project:
  name: healthcare-platform
  compliance_frameworks:
    - HIPAA
    - FDA_21_CFR_PART_11

risk:
  critical_services:
    - payment-gateway
    - phi-service
  
  deployment_strategies:
    low: rolling-update
    medium: canary
    high: blue-green
    critical: blue-green-with-approval

commit:
  required_metadata:
    - HIPAA-ADMIN
    - FDA-SOFTWARE
    - SOX-FINANCIAL
    - RISK-LEVEL
  
  auto_suggest_reviewers: true
  enforce_conventional_commits: true
```

---

## Integration Examples

### GitHub Actions

```yaml
name: Compliance Check

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install gitops-health
        run: pip install -e tools/
      
      - name: Analyze commits
        run: |
          gitops-health compliance analyze --pr origin/main..HEAD
          gitops-health risk score --range origin/main..HEAD
```

### Pre-commit Hook

Create `.git/hooks/commit-msg`:

```bash
#!/bin/bash
# Validate commit message with gitops-health

gitops-health compliance analyze --commit HEAD

if [ $? -ne 0 ]; then
  echo "❌ Commit validation failed"
  exit 1
fi

echo "✅ Commit compliant"
```

### VS Code Integration

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Generate Commit",
      "type": "shell",
      "command": "gitops-health commit generate --interactive",
      "problemMatcher": []
    },
    {
      "label": "Check Compliance",
      "type": "shell",
      "command": "gitops-health compliance analyze --commit HEAD",
      "problemMatcher": []
    }
  ]
}
```

---

## Common Workflows

### Workflow 1: Create Compliant Commit

```bash
# 1. Make code changes
vim services/phi-service/encryption.go

# 2. Stage changes
git add .

# 3. Generate compliant commit
gitops-health commit generate \
  --type security \
  --scope phi \
  --description "implement AES-256 encryption" \
  --compliance HIPAA \
  --risk-level high

# 4. Validate before push
gitops-health compliance analyze --commit HEAD

# 5. Push
git push origin feature/phi-encryption
```

### Workflow 2: PR Review

```bash
# 1. Fetch PR changes
git fetch origin pull/123/head:pr-123
git checkout pr-123

# 2. Analyze all commits in PR
gitops-health compliance analyze --pr origin/main..HEAD

# 3. Score risk
gitops-health risk score --range origin/main..HEAD --verbose

# 4. Generate review checklist
gitops-health review generate --pr origin/main..HEAD
```

### Workflow 3: Incident Response

```bash
# 1. User reports latency spike at 2:30 PM
# 2. Find regression commit
gitops-health forensics bisect \
  --metric latency \
  --threshold 200 \
  --start HEAD~50 \
  --end HEAD

# 3. Analyze impact
gitops-health forensics analyze --commit <bad-commit>

# 4. Generate incident report
gitops-health forensics report \
  --commit <bad-commit> \
  --output incident-$(date +%Y%m%d).md
```

---

## Advanced Usage

### Custom Risk Scoring

Create `custom_risk_scorer.py`:

```python
from gitops_health.risk import RiskScorer

class CustomRiskScorer(RiskScorer):
    def score_commit(self, commit):
        base_score = super().score_commit(commit)
        
        # Add custom logic
        if self._touches_ml_models(commit):
            base_score += 2.0  # ML changes are riskier
        
        if self._has_patient_safety_tests(commit):
            base_score -= 1.0  # Good tests reduce risk
        
        return min(base_score, 10.0)
```

### Custom Compliance Policies

Create `policies/custom/ml_validation.rego`:

```rego
package custom.ml_validation

# ML model changes must include validation evidence
violation[{"msg": msg}] {
    input.files[_].path contains "models/"
    not input.metadata["ML-VALIDATION"]
    msg := "ML model changes require validation evidence"
}
```

### Batch Operations

```bash
# Analyze entire repository history
gitops-health compliance analyze --all-history > compliance-report.json

# Risk score all releases
for tag in $(git tag); do
  gitops-health risk score --commit $tag >> risk-trends.csv
done

# Generate compliance dashboard
gitops-health dashboard generate \
  --start-date 2025-01-01 \
  --output compliance-dashboard.html
```

---

## Troubleshooting

### Common Issues

**Issue**: `gitops-health: command not found`
```bash
# Solution: Ensure tools/ is installed
pip install -e /path/to/gitops2-healthcare-intelligence/tools/
```

**Issue**: `OPA policy validation failed`
```bash
# Solution: Check OPA is installed and policies exist
which opa  # Should show path
ls policies/  # Should show policy files
```

**Issue**: `AI model rate limit exceeded`
```bash
# Solution: Add API key or reduce usage
export OPENAI_API_KEY="your-key"
# Or use cached mode
gitops-health commit generate --use-cache
```

---

## API Reference

### Python API

```python
from gitops_health import CommitGenerator, ComplianceChecker, RiskScorer

# Generate commit
generator = CommitGenerator(config_path="./gitops-health.yml")
commit_msg = generator.generate(
    type="feat",
    scope="payment",
    description="add retry logic"
)

# Check compliance
checker = ComplianceChecker()
result = checker.analyze_commit("HEAD")
if not result.compliant:
    print(f"Violations: {result.violations}")

# Score risk
scorer = RiskScorer()
risk = scorer.score_commit("HEAD")
print(f"Risk Level: {risk.level} ({risk.score}/10)")
```

---

## Performance

- **Commit Generation**: ~2-5 seconds (AI model dependent)
- **Compliance Analysis**: ~0.5-1 second (OPA evaluation)
- **Risk Scoring**: ~0.3-0.5 seconds (local computation)
- **Forensic Bisect**: Variable (depends on commit range and test duration)

**Optimization Tips**:
- Use `--cache` flag for repeated operations
- Limit commit range with `--max-commits`
- Run in parallel with `--jobs` flag

---

## Limitations

### Current Implementation

- **AI Models**: Requires external API (OpenAI, Azure, etc.) - not self-hosted
- **OPA Policies**: Basic rule set - needs customization for your org
- **Risk Scoring**: Heuristic-based - not ML-powered (yet)
- **Forensics**: Single-metric bisect - doesn't handle multi-variate regressions

### Production Readiness

Before production use:
- [ ] Security audit of AI prompt injection risks
- [ ] Custom policy development for your compliance requirements
- [ ] Integration with your SIEM/observability platform
- [ ] Load testing for high-volume repositories
- [ ] Secrets management for API keys
- [ ] Role-based access controls

---

## Further Reading

- [Engineering Guide](ENGINEERING_GUIDE.md) - Architecture details
- [Compliance Guide](COMPLIANCE_GUIDE.md) - Policy customization
- [End-to-End Scenario](END_TO_END_SCENARIO.md) - Complete walkthrough
- [API Reference](AI_TOOLS_REFERENCE.md) - Detailed API docs

---

**Version**: 2.0.0  
**Status**: Reference Implementation (Not Production-Ready)  
**License**: MIT

*For issues or questions, open a GitHub issue or see [CONTRIBUTING.md](../CONTRIBUTING.md)*
