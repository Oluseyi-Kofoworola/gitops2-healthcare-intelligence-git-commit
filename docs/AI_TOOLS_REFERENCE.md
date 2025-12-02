# AI Tools Reference: GitOps Health CLI

> **Target Audience**: Developers, DevOps engineers, and platform teams using the GitOps Health CLI.

---

## Table of Contents

1. [Installation](#installation)
2. [CLI Commands](#cli-commands)
3. [Python API](#python-api)
4. [Go Services API](#go-services-api)
5. [Configuration](#configuration)
6. [Examples](#examples)
7. [Integration Guides](#integration-guides)

---

## Installation

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Go 1.21+
- Git 2.40+
- Docker 24.0+ (for containerized services)

# Optional
- kubectl (for Kubernetes deployments)
- terraform (for infrastructure provisioning)
```

### Quick Install

```bash
# Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# Install CLI globally
pip install -e .

# Verify installation
gitops-health --version
# Output: gitops-health version 2.0.0
```

### Docker Install

```bash
# Pull image
docker pull gitopshealth/cli:latest

# Create alias
alias gitops-health='docker run --rm -v $(pwd):/workspace gitopshealth/cli:latest'

# Test
gitops-health --version
```

---

## CLI Commands

### Commit Generation

#### `gitops-health commit generate`

Generate AI-powered commit messages following Conventional Commits format.

**Syntax**:
```bash
gitops-health commit generate [OPTIONS]
```

**Options**:
- `--context` - Include AI analysis of code changes
- `--template <name>` - Use predefined template (feat|fix|docs|style|refactor|test|chore)
- `--scope <scope>` - Specify commit scope (e.g., payment, auth, api)
- `--interactive` - Interactive mode with Q&A
- `--dry-run` - Preview commit message without committing
- `--output <file>` - Save message to file

**Examples**:

```bash
# Basic usage (analyzes staged changes)
gitops-health commit generate --context

# Output:
# feat(payment): add retry logic for failed transactions
# 
# Implements exponential backoff retry mechanism (3 attempts, 2s delay)
# to handle transient payment gateway failures. Adds circuit breaker
# pattern to prevent cascading failures.
#
# Business Impact: Reduces payment failure rate from 2.3% to <0.1%
# Testing: Added unit tests (payment_retry_test.go) + integration tests
# Compliance: HIPAA audit trail maintained, no PHI in logs
#
# Closes #234

# Interactive mode
gitops-health commit generate --interactive

# Q: What type of change is this? [feat/fix/docs/etc]
# A: feat
# Q: What component does this affect?
# A: payment
# Q: Brief description (50 chars):
# A: add retry logic for failed transactions
# Q: Detailed explanation:
# A: Implements exponential backoff...
# Q: Business impact:
# A: Reduces payment failure rate...

# Use template
gitops-health commit generate --template fix --scope auth

# fix(auth): [AI will complete based on code changes]

# Save to file (for review before committing)
gitops-health commit generate --context --output commit-msg.txt
```

**AI Analysis Includes**:
- Code diff analysis (what changed)
- Impact assessment (which components affected)
- Testing recommendations
- Compliance considerations (HIPAA/FDA/SOX)
- Business impact estimation
- Related issues/PRs

---

### Compliance Analysis

#### `gitops-health compliance analyze`

Analyze commits for HIPAA, FDA, and SOX compliance violations.

**Syntax**:
```bash
gitops-health compliance analyze [OPTIONS]
```

**Options**:
- `--frameworks <list>` - Frameworks to check (HIPAA,FDA,SOX) [default: all]
- `--commit <hash>` - Specific commit to analyze [default: HEAD]
- `--since <date>` - Analyze commits since date
- `--branch <name>` - Analyze entire branch
- `--output <format>` - Output format (json|yaml|html|pdf) [default: json]
- `--severity <level>` - Minimum severity to report (low|medium|high|critical)
- `--fail-on-violations` - Exit code 1 if violations found (for CI/CD)

**Examples**:

```bash
# Analyze current commit
gitops-health compliance analyze

# Output (JSON):
{
  "commit": "a1b2c3d4e5f6",
  "timestamp": "2024-01-15T10:23:45Z",
  "frameworks": {
    "HIPAA": {
      "status": "PASS",
      "violations": [],
      "warnings": [
        {
          "type": "PHI_ADJACENT",
          "file": "services/patient-api/src/handlers.go",
          "message": "File handles patient data - ensure encryption in transit",
          "severity": "LOW"
        }
      ]
    },
    "FDA_21CFR11": {
      "status": "FAIL",
      "violations": [
        {
          "type": "MISSING_SIGNATURE",
          "file": "services/drug-dosage/src/calculator.go",
          "message": "Regulated file modified without GPG signature",
          "severity": "CRITICAL",
          "remediation": "Sign commit with: git commit --amend -S"
        }
      ]
    },
    "SOX": {
      "status": "PASS",
      "violations": [],
      "controls_verified": [
        "SEPARATION_OF_DUTIES",
        "CHANGE_APPROVAL",
        "AUDIT_TRAIL"
      ]
    }
  },
  "overall_status": "FAIL",
  "blocking_violations": 1
}

# Analyze specific framework
gitops-health compliance analyze --frameworks HIPAA --output html

# Generates: compliance-report.html

# Check last week's commits
gitops-health compliance analyze --since "7 days ago" --severity high

# CI/CD usage (fails pipeline if violations found)
gitops-health compliance analyze \
  --frameworks HIPAA,FDA,SOX \
  --severity critical \
  --fail-on-violations \
  --output ci-compliance-report.json
```

---

### Risk Scoring

#### `gitops-health risk score`

Calculate risk score for commits using ML + heuristics.

**Syntax**:
```bash
gitops-health risk score [OPTIONS]
```

**Options**:
- `--commit <hash>` - Commit to score [default: HEAD]
- `--explain` - Show detailed risk factor breakdown
- `--recommend-strategy` - Suggest deployment strategy
- `--historical` - Include historical analysis of similar commits
- `--output <format>` - Output format (json|text|table)

**Examples**:

```bash
# Score current commit
gitops-health risk score --commit HEAD --explain

# Output:
{
  "commit": "a1b2c3d4e5f6",
  "overall_score": 68,
  "category": "HIGH",
  "deployment_strategy": "BLUE_GREEN",
  "factors": [
    {
      "name": "critical_path_changes",
      "score": 85,
      "weight": 0.4,
      "details": "Modified payment-gateway/src/processor.go (CRITICAL)"
    },
    {
      "name": "historical_performance",
      "score": 45,
      "weight": 0.3,
      "details": "Author has 95% success rate on similar changes"
    },
    {
      "name": "code_complexity",
      "score": 72,
      "weight": 0.2,
      "details": "Cyclomatic complexity: 18 (threshold: 15)"
    },
    {
      "name": "temporal_context",
      "score": 55,
      "weight": 0.1,
      "details": "Committed during business hours (lower risk)"
    }
  ],
  "recommendations": [
    "Deploy using blue/green strategy",
    "Require 2+ senior engineer approvals",
    "Extended staging validation (4+ hours)",
    "Monitor payment success rate for 24h post-deploy"
  ],
  "similar_commits": [
    {
      "commit": "xyz789",
      "similarity": 0.87,
      "outcome": "successful",
      "deployment_time": "2h 15m"
    }
  ]
}

# Quick score (just the number)
gitops-health risk score --commit a1b2c3d
# Output: 68

# Get deployment recommendation
gitops-health risk score --recommend-strategy
# Output: BLUE_GREEN

# Batch scoring (for analytics)
git log --format="%H" --since="30 days ago" | \
  xargs -I {} gitops-health risk score --commit {} --output json > risk-history.jsonl
```

**Risk Categories**:
- **LOW (0-25)**: Standard deployment, automated pipeline
- **MEDIUM (25-50)**: Canary deployment, extended testing
- **HIGH (50-75)**: Blue/green deployment, manual approval, 24h monitoring
- **CRITICAL (75-100)**: Architect approval, phased rollout, 48h bake time

---

### Intelligent Forensics

#### `gitops-health forensics bisect`

AI-powered git bisect for rapid regression identification.

**Syntax**:
```bash
gitops-health forensics bisect [OPTIONS]
```

**Options**:
- `--good <commit>` - Known good commit/tag
- `--bad <commit>` - Known bad commit/tag [default: HEAD]
- `--test-command <cmd>` - Command to test each commit
- `--parallel <n>` - Number of parallel test jobs [default: 1]
- `--timeout <seconds>` - Test timeout per commit [default: 300]
- `--ml-guidance` - Use ML to prioritize likely culprits [default: true]
- `--output <file>` - Save detailed report

**Examples**:

```bash
# Basic bisect
gitops-health forensics bisect \
  --good v1.2.3 \
  --bad v1.2.5 \
  --test-command "npm test"

# Output:
# 🔍 Intelligent Bisect Started
# Range: v1.2.3 (good) → v1.2.5 (bad)
# Commits to test: 47
# 
# 🧠 AI Analysis:
# - Prioritizing commits touching payment-gateway/ (test failure location)
# - Author 'john.doe' has 3 commits in range (95% historical success rate)
# - Focusing on high-risk commits first
#
# Testing commits (intelligent order):
# ✅ a1b2c3d (score: 23) - PASS
# ✅ d4e5f6g (score: 45) - PASS
# ❌ h7i8j9k (score: 87) - FAIL ← CULPRIT FOUND
#
# 🎯 Regression Found!
# Culprit Commit: h7i8j9k
# Author: jane.smith@hospital.com
# Date: 2024-01-10 14:32:11
# Message: refactor(payment): simplify transaction processor
#
# Root Cause Analysis:
# - Removed null check in payment-gateway/src/processor.go:145
# - Causes NPE when processing refunds without original transaction ID
# - Affects 0.3% of transactions (refund-only cases)
#
# Remediation Options:
# 1. Revert: git revert h7i8j9k
# 2. Hotfix: Apply PR #456 (already prepared)
# 3. Forward fix: Add null check back (1-line change)
#
# Bisect Stats:
# - Steps taken: 3 (traditional bisect would need 6)
# - Time saved: 67% (15 minutes vs 45 minutes)
# - Confidence: 94%

# Parallel testing (4x faster)
gitops-health forensics bisect \
  --good v1.2.0 \
  --bad HEAD \
  --test-command "make test" \
  --parallel 4 \
  --timeout 600

# Generate detailed report
gitops-health forensics bisect \
  --good last-deploy-success \
  --bad HEAD \
  --test-command "./e2e-tests.sh" \
  --output bisect-report.json

# Use with custom test script
cat > test.sh << 'EOF'
#!/bin/bash
make build && ./integration-tests
EOF
chmod +x test.sh

gitops-health forensics bisect \
  --good v2.0.0 \
  --bad v2.1.0 \
  --test-command "./test.sh"
```

---

### Audit Trail Export

#### `gitops-health audit export`

Export compliance audit trail for regulatory review.

**Syntax**:
```bash
gitops-health audit export [OPTIONS]
```

**Options**:
- `--framework <name>` - Framework to export (HIPAA|FDA|SOX)
- `--start-date <date>` - Start of audit period
- `--end-date <date>` - End of audit period [default: today]
- `--format <type>` - Export format (json|csv|pdf|xlsx)
- `--include-evidence` - Include supporting evidence files
- `--output <file>` - Output file path

**Examples**:

```bash
# Annual HIPAA audit
gitops-health audit export \
  --framework HIPAA \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --format pdf \
  --include-evidence \
  --output hipaa-audit-2024.pdf

# SOX quarterly report
gitops-health audit export \
  --framework SOX \
  --start-date 2024-10-01 \
  --end-date 2024-12-31 \
  --format xlsx \
  --output sox-q4-2024.xlsx

# FDA system validation evidence
gitops-health audit export \
  --framework FDA \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --format json \
  --include-evidence \
  --output fda-validation-2024.zip
```

---

### Data Sanitization

#### `gitops-health sanitize`

Remove PHI from files before committing.

**Syntax**:
```bash
gitops-health sanitize [OPTIONS] <files...>
```

**Options**:
- `--dry-run` - Preview changes without modifying files
- `--replace-with <strategy>` - Replacement strategy (synthetic|redacted|placeholder)
- `--preserve-format` - Keep original data format (e.g., email → fake@example.com)
- `--output-report <file>` - Save sanitization report

**Examples**:

```bash
# Sanitize single file
gitops-health sanitize services/patient-api/test-data.json

# Output:
# 🧹 Sanitizing: services/patient-api/test-data.json
# 
# PHI Detected:
# - Line 12: email (john.doe@gmail.com) → faker_123@example.com
# - Line 15: phone (555-123-4567) → 555-000-0001
# - Line 23: ssn (123-45-6789) → 000-00-0000
#
# ✅ Sanitized 3 PHI instances
# Original backed up to: services/patient-api/test-data.json.bak

# Dry run (preview only)
gitops-health sanitize --dry-run test-fixtures/*.json

# Use synthetic data (realistic but fake)
gitops-health sanitize \
  --replace-with synthetic \
  --preserve-format \
  data/sample-patients.csv

# Output:
# john.doe@gmail.com → jennifer.martinez@example.com
# 555-123-4567 → 555-342-8901
# 123-45-6789 → 472-89-3451
```

---

## Python API

### Risk Scorer API

```python
from gitops_health.risk import RiskScorer

# Initialize scorer
scorer = RiskScorer(
    ml_model_path="models/risk_model.pkl",
    config_path="config/risk-config.yaml"
)

# Score a commit
commit_hash = "a1b2c3d4e5f6"
result = scorer.score_commit(commit_hash)

print(f"Risk Score: {result.overall_score}")
print(f"Category: {result.category}")
print(f"Recommendation: {result.deployment_strategy}")

# Get detailed breakdown
for factor in result.factors:
    print(f"- {factor.name}: {factor.score} (weight: {factor.weight})")

# Batch scoring
commits = ["abc123", "def456", "ghi789"]
results = scorer.score_commits_batch(commits)

# Historical analysis
author = "jane.doe@hospital.com"
history = scorer.analyze_author_history(author, days=90)
print(f"Success Rate: {history.success_rate}%")
print(f"Average Risk Score: {history.avg_risk_score}")
```

### Compliance Analyzer API

```python
from gitops_health.compliance import ComplianceAnalyzer

# Initialize analyzer
analyzer = ComplianceAnalyzer(
    policies_path="policies/",
    frameworks=["HIPAA", "FDA", "SOX"]
)

# Analyze commit
commit_hash = "a1b2c3d4e5f6"
result = analyzer.analyze(commit_hash)

if result.has_violations():
    print("❌ Compliance violations found:")
    for violation in result.violations:
        print(f"  - {violation.framework}: {violation.message}")
        print(f"    Severity: {violation.severity}")
        print(f"    Remediation: {violation.remediation}")
else:
    print("✅ No compliance violations")

# Framework-specific analysis
hipaa_result = analyzer.analyze_hipaa(commit_hash)
if hipaa_result.contains_phi:
    print("PHI detected in:")
    for location in hipaa_result.phi_locations:
        print(f"  - {location.file}:{location.line}")
        print(f"    Type: {location.phi_type}")
```

### Commit Generator API

```python
from gitops_health.commitgen import CommitGenerator

# Initialize generator
generator = CommitGenerator(
    openai_api_key="sk-...",
    model="gpt-4"
)

# Generate commit message
staged_files = ["payment-gateway/src/processor.go", "payment-gateway/src/processor_test.go"]
message = generator.generate(
    files=staged_files,
    template="feat",
    include_business_impact=True,
    include_testing_notes=True
)

print(message)
# Output:
# feat(payment): add retry logic for failed transactions
#
# Implements exponential backoff retry mechanism to handle
# transient payment gateway failures. Adds circuit breaker.
#
# Business Impact: Reduces failure rate 2.3% → 0.1%
# Testing: Unit + integration tests added
# Compliance: HIPAA audit trail maintained

# Interactive generation
message = generator.generate_interactive()
```

---

## Go Services API

### Risk Scorer Service

```go
package main

import (
    "context"
    "fmt"
    "github.com/gitopshealth/risk-scorer-client-go"
)

func main() {
    // Initialize client
    client := riskscorer.NewClient("http://risk-scorer:8080")
    
    // Score commit
    ctx := context.Background()
    req := &riskscorer.RiskRequest{
        CommitHash:   "a1b2c3d4e5f6",
        Author:       "jane.doe@hospital.com",
        FilesChanged: []string{"payment-gateway/src/processor.go"},
        LinesAdded:   45,
        LinesDeleted: 12,
    }
    
    score, err := client.ScoreCommit(ctx, req)
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Risk Score: %.2f\n", score.OverallScore)
    fmt.Printf("Category: %s\n", score.Category)
    fmt.Printf("Strategy: %s\n", score.RecommendedStrategy)
    
    // Check if high risk
    if score.OverallScore > 75 {
        fmt.Println("⚠️  HIGH RISK - Requires architect approval")
    }
}
```

### Compliance Analyzer Service

```go
package main

import (
    "context"
    "fmt"
    "github.com/gitopshealth/compliance-analyzer-client-go"
)

func main() {
    // Initialize client
    client := compliance.NewClient("http://compliance-analyzer:8081")
    
    // Analyze commit
    ctx := context.Background()
    req := &compliance.AnalyzeRequest{
        CommitHash: "a1b2c3d4e5f6",
        Frameworks: []string{"HIPAA", "FDA", "SOX"},
    }
    
    result, err := client.Analyze(ctx, req)
    if err != nil {
        panic(err)
    }
    
    // Check for violations
    if len(result.Violations) > 0 {
        fmt.Println("❌ Compliance violations:")
        for _, v := range result.Violations {
            fmt.Printf("  - %s: %s\n", v.Framework, v.Message)
        }
        os.Exit(1)
    }
    
    fmt.Println("✅ Compliance check passed")
}
```

---

## Configuration

### CLI Configuration File

```yaml
# ~/.gitops-health/config.yaml
---
ai:
  openai_api_key: ${OPENAI_API_KEY}
  model: gpt-4
  temperature: 0.7
  max_tokens: 1000

services:
  risk_scorer:
    url: http://localhost:8080
    timeout: 30s
  
  compliance_analyzer:
    url: http://localhost:8081
    timeout: 30s

compliance:
  frameworks:
    - HIPAA
    - FDA
    - SOX
  
  severity_threshold: MEDIUM
  
  hipaa:
    enable_phi_detection: true
    phi_patterns_file: config/phi-patterns.yaml
  
  fda:
    require_signatures: true
    regulated_paths:
      - services/drug-dosage-calculator/
      - services/medical-device-control/
  
  sox:
    enable_separation_of_duties: true
    financial_services:
      - payment-gateway
      - billing-service

risk:
  ml_model_path: models/risk_model.pkl
  weights:
    ml_score: 0.4
    heuristic_score: 0.3
    context_score: 0.3
  
  critical_paths:
    - payment-gateway/
    - auth-service/
    - patient-data-service/

output:
  default_format: json
  color_output: true
  verbose: false

git:
  default_branch: main
  require_signed_commits: true
  commit_template: conventional
```

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."
export GITOPS_HEALTH_CONFIG="~/.gitops-health/config.yaml"

# Optional
export RISK_SCORER_URL="http://localhost:8080"
export COMPLIANCE_ANALYZER_URL="http://localhost:8081"
export LOG_LEVEL="info"  # debug, info, warn, error
export OUTPUT_FORMAT="json"  # json, yaml, text
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Make code changes
vim services/payment-gateway/src/processor.go

# 2. Stage changes
git add services/payment-gateway/src/processor.go

# 3. Check for PHI
gitops-health sanitize --dry-run $(git diff --cached --name-only)

# 4. Generate commit message
gitops-health commit generate --context > commit-msg.txt

# 5. Review and edit message
vim commit-msg.txt

# 6. Commit with message
git commit -F commit-msg.txt

# 7. Run compliance check
gitops-health compliance analyze --fail-on-violations

# 8. Check risk score
RISK_SCORE=$(gitops-health risk score --commit HEAD)
echo "Risk Score: $RISK_SCORE"

# 9. Push (pre-push hooks run automatically)
git push origin feature/payment-retry

# 10. CI/CD pipeline runs full compliance + risk analysis
```

### CI/CD Integration Example

```yaml
# .github/workflows/compliance-gate.yml
- name: Compliance & Risk Analysis
  run: |
    # Analyze compliance
    gitops-health compliance analyze \
      --commit ${{ github.sha }} \
      --frameworks HIPAA,FDA,SOX \
      --severity critical \
      --fail-on-violations \
      --output compliance-report.json
    
    # Calculate risk score
    RISK_SCORE=$(gitops-health risk score --commit ${{ github.sha }})
    echo "risk_score=$RISK_SCORE" >> $GITHUB_OUTPUT
    
    # Determine deployment strategy
    if [ "$RISK_SCORE" -lt 25 ]; then
      echo "strategy=standard" >> $GITHUB_OUTPUT
    elif [ "$RISK_SCORE" -lt 50 ]; then
      echo "strategy=canary" >> $GITHUB_OUTPUT
    else
      echo "strategy=bluegreen" >> $GITHUB_OUTPUT
    fi
```

---

## Integration Guides

### GitHub Actions

See: [.github/workflows/ai-compliance-gate.yml](../.github/workflows/ai-compliance-gate.yml)

### GitLab CI

```yaml
# .gitlab-ci.yml
compliance_check:
  stage: test
  script:
    - gitops-health compliance analyze --fail-on-violations
    - gitops-health risk score --commit $CI_COMMIT_SHA
  artifacts:
    reports:
      compliance: compliance-report.json
```

### Jenkins

```groovy
// Jenkinsfile
stage('Compliance Gate') {
    steps {
        sh 'gitops-health compliance analyze --fail-on-violations'
        script {
            def riskScore = sh(
                script: 'gitops-health risk score --commit $GIT_COMMIT',
                returnStdout: true
            ).trim()
            
            if (riskScore.toInteger() > 75) {
                input message: 'High risk commit. Approve deployment?'
            }
        }
    }
}
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: phi-detection
        name: PHI Detection
        entry: gitops-health sanitize --dry-run
        language: system
        pass_filenames: true
      
      - id: compliance-check
        name: Compliance Check
        entry: gitops-health compliance analyze --severity high
        language: system
```

---

## Additional Resources

- [Engineering Guide](/docs/ENGINEERING_GUIDE.md)
- [Compliance Guide](/docs/COMPLIANCE_GUIDE.md)
- [End-to-End Scenario](/docs/SCENARIO_END_TO_END.md)
- [Example Outputs](/docs/examples/)

---

**Maintained by**: Platform Engineering Team  
**Last Updated**: 2024-01-15  
**API Support**: api-support@gitopshealth.com
