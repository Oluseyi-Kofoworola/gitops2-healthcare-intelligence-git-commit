# Contributing Guide

Thank you for contributing to the Healthcare GitOps Intelligence Platform. This guide covers development workflow, testing requirements, and PR process.

---

## Quick Start

```bash
# 1. Fork & clone
git clone https://github.com/YOUR_USERNAME/gitops2-healthcare-intelligence.git
cd gitops2-healthcare-intelligence

# 2. Setup environment
./setup.sh

# 3. Create feature branch
git checkout -b feat/your-feature

# 4. Make changes
# ... edit code ...

# 5. Run tests
make test

# 6. Generate compliant commit
python tools/healthcare_commit_generator.py \
  --type feat \
  --scope api \
  --description "Add new endpoint" \
  --files services/auth-service/main.go

# 7. Push & create PR
git push origin feat/your-feature
```

---

## Development Workflow

### 1. Branch Naming

```
feat/feature-name      # New features
fix/bug-description    # Bug fixes
security/cve-number    # Security patches
docs/what-changed      # Documentation
refactor/component     # Code refactoring
```

### 2. Commit Requirements

**All commits MUST include**:
- Conventional Commits format: `type(scope): description`
- Business Impact statement
- Risk Level (LOW/MEDIUM/HIGH/CRITICAL)
- Clinical Safety assessment
- Compliance codes (if applicable)
- Audit trail timestamp

**Example**:
```
feat(phi): Add AES-256-GCM encryption for patient data

Business Impact: PHI security enhancement
Risk Level: HIGH
Clinical Safety: NO_CLINICAL_IMPACT
Compliance: HIPAA-164.312
Reviewers: @engineering-team, @security-team

Audit Trail: 2 files modified at 2025-12-07T10:30:00+00:00
```

**Use AI generator** (recommended):
```bash
python tools/healthcare_commit_generator.py \
  --type feat \
  --scope phi \
  --description "Add encryption" \
  --files services/phi-service/encryption.go
```

### 3. Testing Requirements

**Before submitting PR**:

```bash
# Run all tests
make test

# Check coverage (must be ≥90%)
make coverage

# Run security scans
make test-security

# Validate compliance
python tools/ai_compliance_framework.py analyze-commit HEAD
```

**Coverage thresholds**:
- Go services: ≥ 90%
- Python tools: ≥ 85%
- OPA policies: 100% (test all rules)

---

## Code Standards

### Go Services

```go
// ✅ Good: Error handling, logging, metrics
func EncryptPHI(data []byte) ([]byte, error) {
    start := time.Now()
    defer func() {
        metrics.RecordLatency("encrypt_phi", time.Since(start))
    }()
    
    encrypted, err := aes.Encrypt(data)
    if err != nil {
        log.Error().Err(err).Msg("Encryption failed")
        return nil, fmt.Errorf("encryption failed: %w", err)
    }
    
    log.Info().Int("bytes", len(data)).Msg("PHI encrypted")
    return encrypted, nil
}

// ❌ Bad: No error handling, no logging, no metrics
func EncryptPHI(data []byte) []byte {
    encrypted, _ := aes.Encrypt(data)
    return encrypted
}
```

### Python Tools

```python
# ✅ Good: Type hints, docstrings, validation
def generate_commit(
    commit_type: str,
    scope: str,
    files: List[str]
) -> str:
    """
    Generate HIPAA-compliant commit message.
    
    Args:
        commit_type: feat, fix, security, etc.
        scope: Component scope (phi, auth, payment)
        files: List of modified files
        
    Returns:
        Formatted commit message with audit trail
        
    Raises:
        ValidationError: If inputs invalid
    """
    if not files:
        raise ValidationError("At least one file required")
    # ... implementation

# ❌ Bad: No types, no docs, no validation
def generate_commit(commit_type, scope, files):
    return f"{commit_type}({scope}): change"
```

### OPA Policies

```rego
# ✅ Good: Clear rules, specific deny messages
package healthcare.phi

deny contains msg if {
    input.commit
    phi_related(input.commit)
    not has_hipaa_metadata(input.commit)
    msg := sprintf(
        "PHI commit %s missing HIPAA metadata",
        [input.commit.sha]
    )
}

# ❌ Bad: Generic messages
deny[msg] {
    not valid_commit
    msg := "Invalid commit"
}
```

---

## Pull Request Process

### 1. PR Title

Use same format as commits:
```
feat(phi): Add encryption for patient records
fix(auth): Resolve JWT expiry bug
security(payment): Patch CVE-2025-12345
```

### 2. PR Description Template

```markdown
## Summary
Brief description of changes.

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Security patch
- [ ] Documentation
- [ ] Refactor

## Compliance Impact
- [ ] HIPAA: [COMPLIANT/REQUIRES_REVIEW/N/A]
- [ ] FDA: [VALIDATED/REQUIRES_REVIEW/N/A]
- [ ] SOX: [COMPLIANT/REQUIRES_REVIEW/N/A]

## Testing
- [ ] Unit tests pass (≥90% coverage)
- [ ] Integration tests pass
- [ ] Security scans pass
- [ ] Manual testing completed

## Risk Assessment
- Risk Level: [LOW/MEDIUM/HIGH/CRITICAL]
- Clinical Safety: [NO_IMPACT/REQUIRES_REVIEW]
- Rollback Plan: [Describe]

## Reviewers
@engineering-team
@security-team (if HIGH risk)
@privacy-officer (if PHI-related)
```

### 3. Review Criteria

**All PRs must**:
- Pass CI/CD pipeline
- Meet code coverage thresholds
- Include compliance metadata
- Have appropriate reviewer approval:
  - LOW risk: 1 approval
  - MEDIUM risk: 1 approval
  - HIGH risk: 2 approvals (security team required)
  - CRITICAL risk: 3 approvals (security + privacy + clinical)

### 4. Merge Process

```bash
# After approval, squash merge with compliant message
git merge --squash feat/your-feature
python tools/healthcare_commit_generator.py \
  --type feat \
  --scope component \
  --description "Your feature" \
  --files changed_files.go
git commit -F generated-message.txt
git push origin main
```

---

## Compliance-Specific Contributions

### PHI-Related Changes

**Required metadata**:
- `HIPAA-164.312` (if encryption)
- `PHI-Impact: HIGH/MEDIUM/LOW`
- Privacy officer review

**Example**:
```bash
python tools/healthcare_commit_generator.py \
  --type security \
  --scope phi \
  --description "Strengthen encryption" \
  --files services/phi-service/encryption.go
```

### Medical Device Changes

**Required metadata**:
- `FDA-21CFR11` or `FDA-510k`
- `Clinical-Safety: VALIDATED`
- Clinical affairs review

### Financial/Payment Changes

**Required metadata**:
- `SOX-404` or `SOX-ITGC`
- `Financial-Impact: description`
- Audit team review

---

## Documentation

### Update Documentation When:
- Adding new service
- Changing API endpoints
- Modifying compliance behavior
- Adding new OPA policies

### Required Docs:
- README.md in service directory
- API documentation (OpenAPI spec)
- Policy documentation (policies/healthcare/README.md)

---

## Getting Help

### Before Asking:
1. Check [README.md](README.md)
2. Review [DEPLOYMENT.md](DEPLOYMENT.md)
3. Search [GitHub Issues](https://github.com/YOUR_ORG/gitops2-healthcare-intelligence/issues)

### Where to Ask:
- **General questions**: [GitHub Discussions](https://github.com/YOUR_ORG/gitops2-healthcare-intelligence/discussions)
- **Bugs**: [GitHub Issues](https://github.com/YOUR_ORG/gitops2-healthcare-intelligence/issues)
- **Security**: security@your-org.com (private)
- **Compliance**: compliance@your-org.com

---

## Code of Conduct

### Our Standards:
- Be respectful and inclusive
- Focus on constructive feedback
- Prioritize patient safety in all discussions
- Follow healthcare regulatory requirements
- Maintain confidentiality of PHI/sensitive data

### Enforcement:
Violations may result in removal from project. Report to conduct@your-org.com.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
