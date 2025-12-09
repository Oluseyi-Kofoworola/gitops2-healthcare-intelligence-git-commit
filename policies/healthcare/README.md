# Healthcare OPA Policies

Open Policy Agent (OPA) policies for enforcing healthcare compliance in GitOps workflows.

---

## Policy Files

| Policy | Purpose | Validates |
|--------|---------|-----------|
| `commit_metadata_required.rego` | Basic metadata validation | Conventional Commits format |
| `valid_compliance_codes.rego` | Compliance tags | HIPAA/FDA/SOX code format |
| `hipaa_phi_required.rego` | PHI impact assessment | HIPAA-Impact field for PHI changes |
| `high_risk_dual_approval.rego` | Dual approval for high risk | Risk score > 7.0 requires 2+ approvers |

---

## Quick Start

### Test All Policies

```bash
# Run all policy tests
opa test policies/healthcare/

# Verbose output
opa test policies/healthcare/ -v

# Specific policy
opa test policies/healthcare/commit_metadata_required.rego
```

### Validate a Commit

```bash
# Create test input
cat > commit.json << 'JSON'
{
  "type": "feat",
  "scope": "api",
  "description": "Add new endpoint",
  "compliance_codes": ["HIPAA-164.308"],
  "risk_score": 3.5
}
JSON

# Evaluate policy
opa eval --data policies/healthcare/ \
  --input commit.json \
  "data.healthcare.commit_metadata_required.violation"
```

---

## Policy Details

### 1. Commit Metadata Required

**File**: `commit_metadata_required.rego`

Enforces Conventional Commits format:

```
type(scope): description

- type: feat, fix, security, etc.
- scope: Component name (required)
- description: Brief summary (required)
```

**Test**:
```bash
opa test policies/healthcare/commit_metadata_required.rego -v
```

### 2. Valid Compliance Codes

**File**: `valid_compliance_codes.rego`

Validates compliance framework codes:

- **HIPAA**: `HIPAA-164.xxx`
- **FDA**: `FDA-CFR21-11.xxx`
- **SOX**: `SOX-404.xxx`, `SOX-302.xxx`

**Example**:
```json
{
  "compliance_codes": ["HIPAA-164.312", "FDA-CFR21-11.10"]
}
```

### 3. HIPAA PHI Required

**File**: `hipaa_phi_required.rego`

Requires `HIPAA-Impact` field for PHI-related changes.

**Example**:
```json
{
  "type": "feat",
  "scope": "phi-service",
  "hipaa_impact": "Adds encryption for patient records"
}
```

### 4. High Risk Dual Approval

**File**: `high_risk_dual_approval.rego`

Requires 2+ approvers for high-risk changes (risk_score > 7.0).

**Example**:
```json
{
  "risk_score": 8.5,
  "approvers": ["user1", "user2"]
}
```

---

## Integration

### Pre-commit Hook

Install the pre-commit hook to validate commits automatically:

```bash
./scripts/install-pre-commit-hook.sh
```

### CI/CD Pipeline

Add to your CI pipeline:

```yaml
# .github/workflows/validate.yml
- name: Validate Commit Policies
  run: |
    opa test policies/healthcare/
```

---

## Writing Custom Policies

### Example Policy

```rego
# policies/healthcare/custom_policy.rego
package healthcare.custom_policy

violation[msg] {
  input.type == "security"
  not input.cve_id
  msg := "Security commits must include CVE ID"
}
```

### Test File

```rego
# policies/healthcare/custom_policy_test.rego
package healthcare.custom_policy

test_security_needs_cve {
  result = violation with input as {"type": "security"}
  count(result) > 0
}

test_security_with_cve_valid {
  result = violation with input as {"type": "security", "cve_id": "CVE-2025-12345"}
  count(result) == 0
}
```

### Run Test

```bash
opa test policies/healthcare/custom_policy.rego \
  policies/healthcare/custom_policy_test.rego -v
```

---

## Troubleshooting

### Policy Violations

If a policy fails, check:

1. **Commit format**: Use the healthcare commit generator
   ```bash
   python tools/healthcare_commit_generator.py --help
   ```

2. **Test the policy**: Run OPA tests to understand requirements
   ```bash
   opa test policies/healthcare/ -v
   ```

3. **View examples**: Check test files for valid input examples
   ```bash
   cat policies/healthcare/*_test.rego
   ```

---

## Resources

- [OPA Documentation](https://www.openpolicyagent.org/docs/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-reference/)
- [Policy Testing Guide](https://www.openpolicyagent.org/docs/latest/policy-testing/)

---

## Demo

See policies in action:

```bash
./demo.sh  # Full demo with policy validation (Flow 2)
```

See `START_HERE.md` for step-by-step walkthrough.
