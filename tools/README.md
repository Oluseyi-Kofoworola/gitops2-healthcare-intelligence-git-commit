# AI Tools Reference

Quick reference for healthcare compliance automation tools.

---

## 1. Healthcare Commit Generator

Generate HIPAA/FDA/SOX-compliant commit messages.

### Usage

```bash
python tools/healthcare_commit_generator.py \
  --type TYPE \
  --scope SCOPE \
  --description "DESCRIPTION" \
  --files FILE1 FILE2 ...
```

### Parameters

| Parameter | Required | Options | Example |
|-----------|----------|---------|---------|
| `--type` | Yes | feat, fix, security, perf, breaking, refactor, test, docs, chore | `security` |
| `--scope` | Yes | Component name | `payment`, `phi`, `auth` |
| `--description` | Yes | Brief description | `"Patch CVE-2025-12345"` |
| `--files` | Yes | Space-separated files | `services/payment-gateway/config.go` |

### Example

```bash
python tools/healthcare_commit_generator.py \
  --type security \
  --scope payment \
  --description "Fix token exposure vulnerability" \
  --files services/payment-gateway/config.go
```

---

## 2. Secret Sanitizer

Detect PHI/PII/secrets in code before commits.

### Usage

```bash
# Scan specific files
python tools/secret_sanitizer.py --files path/to/file.go path/to/another.py

# Test mode (dry run)
python tools/secret_sanitizer.py --test

# Scan all staged files
python tools/secret_sanitizer.py --staged
```

### Detects

- SSNs, medical record numbers, patient IDs
- API keys, passwords, tokens
- Credit card numbers, bank accounts
- Email addresses, phone numbers

---

## 3. Risk Scorer

Calculate deployment risk scores (0-10) and suggest strategies.

### Usage

```bash
# Score a commit
python tools/git_intel/risk_scorer.py --commit-hash abc123def

# Score current changes
python tools/git_intel/risk_scorer.py --current
```

### Output

```
Risk Score: 7.2 (HIGH)
Strategy: Canary Deployment (10% → 50% → 100%)
Estimated Review Time: 45 minutes
```

---

## 4. Intelligent Bisect

Automated git bisect for finding regressions.

### Usage

```bash
# Find regression with test command
python tools/intelligent_bisect.py \
  --test-command "go test ./services/phi-service/" \
  --good-commit abc123 \
  --bad-commit def456
```

---

## 5. Compliance Framework

Validate commits against compliance frameworks.

### Usage

```bash
# Validate commit
python tools/ai_compliance_framework.py validate \
  --framework HIPAA \
  --commit-hash abc123
```

---

## Demo Integration

All tools are used in the live demos:

```bash
./demo.sh  # Full demo using all tools
```

See `START_HERE.md` for step-by-step walkthroughs.
