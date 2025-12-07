# AI Tools Reference

Quick reference for healthcare compliance automation tools.

---

## Overview

```mermaid
flowchart LR
    A[Developer] --> B[healthcare_commit_generator.py]
    B --> C[secret_sanitizer.py]
    C --> D[OPA Policies]
    D --> E[Git Commit]
    E --> F[Audit Trail]
    
    B -.-> G[token_limit_guard.py]
    C -.-> H[ai_compliance_framework.py]
    
    style B fill:#e1f5ff
    style C fill:#ffe1e1
    style D fill:#fff3cd
    style E fill:#d4edda
    style F fill:#d4edda
```

---

## 1. Healthcare Commit Generator

Generate HIPAA/FDA/SOX-compliant commit messages with AI.

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
| `--skip-safety` | No | Skip safety checks | Flag only |
| `--output` | No | text, json | `json` |

### Examples

```bash
# Security patch
python tools/healthcare_commit_generator.py \
  --type security \
  --scope payment \
  --description "Patch token exposure vulnerability" \
  --files services/payment-gateway/config.go

# Feature addition
python tools/healthcare_commit_generator.py \
  --type feat \
  --scope phi \
  --description "Add AES-256-GCM encryption" \
  --files services/phi-service/encryption.go

# Bug fix
python tools/healthcare_commit_generator.py \
  --type fix \
  --scope auth \
  --description "Resolve JWT expiry bug" \
  --files services/auth-service/main.go \
  --output json
```

### Output Format

```
security(payment): Patch token exposure vulnerability

Business Impact: payment security enhancement
Risk Level: HIGH
Clinical Safety: NO_CLINICAL_IMPACT
Compliance: PCI-DSS, SOX
Reviewers: @engineering-team, @audit-team

Audit Trail: 1 files modified at 2025-12-07T10:30:00+00:00
```

---

## 2. Secret Sanitizer

Detect PHI/PII/credentials in commits before AI processing.

### Usage

```bash
# Test mode
python tools/secret_sanitizer.py --test

# As Python module
from tools.secret_sanitizer import SecretSanitizer

sanitizer = SecretSanitizer(confidence_threshold=0.7)
is_safe, matches = sanitizer.validate_for_ai_processing(text)
```

### Detection Patterns

| Category | Patterns | Examples |
|----------|----------|----------|
| **PHI** | SSN, MRN, DOB, Phone, Email | `123-45-6789`, `MRN123456` |
| **Credentials** | API keys, AWS keys, Tokens, Passwords | `AKIAIOSFODNN7EXAMPLE` |
| **Financial** | Credit cards, Bank accounts | `4532-1234-5678-9010` |

### Confidence Thresholds

- `0.9+`: CRITICAL - Always block
- `0.7-0.9`: HIGH - Block unless whitelisted
- `0.5-0.7`: MEDIUM - Warn
- `<0.5`: LOW - Log only

### Whitelisting

Test data is automatically whitelisted:
- SSN: `000-00-0000`, `123-45-6789`
- Email: `*@example.com`, `*@test.com`
- IP: `192.168.*`, `10.*`, `172.16-31.*`

---

## 3. Token Limit Guard

Manage LLM context windows and prevent token overflows.

### Usage

```bash
# Test mode
python tools/token_limit_guard.py

# As Python module
from tools.token_limit_guard import TokenLimitGuard

guard = TokenLimitGuard(model="gpt-4", safety_margin=0.7)
estimate = guard.check_token_limit(text, "commit-diff")
if not estimate.is_safe:
    chunks = guard.chunk_text_smartly(text, ChunkingStrategy.FILE_BOUNDARY)
```

### Supported Models

| Model | Context Window | Output Tokens |
|-------|---------------|---------------|
| `gpt-4` | 8,192 | 2,048 |
| `gpt-4-turbo` | 128,000 | 4,096 |
| `gpt-3.5-turbo` | 16,385 | 4,096 |
| `claude-3-opus` | 200,000 | 4,096 |
| `claude-3-sonnet` | 200,000 | 4,096 |

### Chunking Strategies

```python
# By file boundaries (recommended for diffs)
ChunkingStrategy.FILE_BOUNDARY

# By diff hunks (for large files)
ChunkingStrategy.HUNK_BOUNDARY

# By character count (fallback)
ChunkingStrategy.SIZE_ONLY
```

---

## 4. AI Compliance Framework

Validate commits against HIPAA/FDA/SOX requirements.

### Usage

```bash
# Analyze specific commit
python tools/ai_compliance_framework.py analyze-commit HEAD

# Analyze commit range
python tools/ai_compliance_framework.py analyze-commit HEAD~5..HEAD

# Generate audit report
python tools/ai_compliance_framework.py audit-report \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output report-2024.json
```

### Validation Checks

```mermaid
flowchart TD
    A[Commit Message] --> B{Has Metadata?}
    B -->|No| C[FAIL: Missing metadata]
    B -->|Yes| D{Valid Codes?}
    D -->|No| E[FAIL: Invalid compliance codes]
    D -->|Yes| F{Risk Level?}
    F -->|Missing| G[FAIL: No risk assessment]
    F -->|Present| H{PHI-related?}
    H -->|Yes| I{Has HIPAA metadata?}
    I -->|No| J[FAIL: Missing HIPAA]
    I -->|Yes| K[PASS]
    H -->|No| K[PASS]
    
    style K fill:#d4edda
    style C fill:#ffe1e1
    style E fill:#ffe1e1
    style G fill:#ffe1e1
    style J fill:#ffe1e1
```

---

## 5. Intelligent Bisect

Automated git bisect for incident root cause analysis.

### Usage

```bash
# Find commit that broke tests
python tools/intelligent_bisect.py \
  --test-command "make test" \
  --start HEAD~20 \
  --end HEAD

# Find performance regression
python tools/intelligent_bisect.py \
  --metric latency \
  --threshold 200 \
  --start HEAD~50 \
  --end HEAD
```

### Output

```json
{
  "culprit_commit": "abc123",
  "commit_message": "feat(phi): optimize encryption",
  "risk_level": "HIGH",
  "files_changed": ["services/phi-service/encryption.go"],
  "recommended_action": "Rollback to previous version"
}
```

---

## Environment Variables

### Global Settings

```bash
# AI Model
export AI_MODEL_DEFAULT="gpt-4"
export OPENAI_API_KEY="your-key"

# Logging
export LOG_LEVEL="info"  # debug, info, warn, error
export LOG_FORMAT="json"  # json or text

# Safety
export ENABLE_SAFETY_CHECKS="true"
export CONFIDENCE_THRESHOLD="0.7"
```

### Configuration File

Place in `config/production.yaml`:

```yaml
ai_tools:
  model: gpt-4
  max_tokens: 2048
  temperature: 0.3
  
secret_detection:
  confidence_threshold: 0.7
  enable_cache: true
  whitelist_test_data: true

token_limits:
  safety_margin: 0.7
  enable_retry: true
  max_retries: 3
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ValidationError` | Invalid input | Check parameters, file paths |
| `TokenLimitExceededError` | Diff too large | Enable chunking, reduce file count |
| `ConfigurationError` | Invalid config | Check config/production.yaml |
| `SecretDetectedError` | PHI/secrets in diff | Remove secrets, use whitelisting |

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL="debug"

# Run with verbose output
python tools/healthcare_commit_generator.py --help
```

---

## Integration Examples

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run secret sanitizer
python tools/secret_sanitizer.py --check-staged || exit 1

# Validate commit message format
python tools/ai_compliance_framework.py validate-format || exit 1

echo "✓ Pre-commit checks passed"
```

### CI/CD Pipeline

```yaml
# .github/workflows/compliance.yml
- name: Validate Compliance
  run: |
    python tools/ai_compliance_framework.py analyze-commit ${{ github.sha }}
    
- name: Check Secrets
  run: |
    python tools/secret_sanitizer.py --check-diff
```

---

## Performance Tips

1. **Enable Caching**: Set `enable_cache: true` in config
2. **Use Whitelisting**: Whitelist test data patterns
3. **Batch Operations**: Process multiple commits together
4. **Parallel Execution**: Use `--parallel` flag when available

---

## Support

- **Tool Issues**: https://github.com/YOUR_ORG/gitops2-healthcare-intelligence/issues
- **API Docs**: Run `python tools/TOOL_NAME.py --help`
- **Examples**: See [docs/README.md](../docs/README.md)
