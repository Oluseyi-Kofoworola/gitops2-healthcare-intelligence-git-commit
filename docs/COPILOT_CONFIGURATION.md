# GitHub Copilot Configuration for Healthcare Compliance

**How to configure GitHub Copilot to generate HIPAA-compliant commit messages**

---

## Overview

This document explains **exactly how** GitHub Copilot is configured to understand healthcare compliance requirements and generate structured commit messages with proper metadata.

---

## Configuration Methods

### Method 1: GitHub Copilot Instructions (Recommended)

**Location:** `.github/copilot-instructions.md`

GitHub Copilot now supports repository-level instructions that provide context to the AI model. This is the **primary method** used in this repository.

**How it works:**
1. Create `.github/copilot-instructions.md` in your repository root
2. Add healthcare-specific guidelines and examples
3. Copilot reads this file automatically when generating code/commits
4. Works across VS Code, JetBrains IDEs, and GitHub.com

**Our Implementation:**
```markdown
<!-- .github/copilot-instructions.md -->
When generating Git commit messages for this healthcare platform:

1. Always include compliance metadata:
   - HIPAA: Applicable/Not Applicable
   - PHI-Impact: Direct/Indirect/None
   - Clinical-Safety: Critical/Important/Minor/None
   - Risk-Level: High/Medium/Low

2. Follow conventional commit format:
   type(scope): description

3. Reference regulations when applicable:
   - HIPAA §164.312(a)(2)(iv) for encryption
   - FDA 21 CFR Part 11 for electronic records
   - SOX for financial controls

4. Example:
   security(phi-service): implement AES-256-GCM encryption
   
   HIPAA: Applicable
   PHI-Impact: Direct
   Clinical-Safety: Critical
   Regulation: HIPAA §164.312(a)(2)(iv)
```

---

### Method 2: VS Code Copilot Instructions

**Location:** `.vscode/settings.json`

For team-specific VS Code configuration:

```json
{
  "github.copilot.advanced": {
    "customInstructions": [
      "Generate healthcare-compliant commit messages with HIPAA metadata",
      "Include PHI-Impact and Clinical-Safety fields",
      "Reference applicable regulations (HIPAA, FDA, SOX)",
      "Follow conventional commit format with metadata block"
    ]
  }
}
```

**Limitation:** Only affects VS Code users, not JetBrains or GitHub.com.

---

### Method 3: Git Commit Template (Fallback)

**Location:** `.gitmessage`

For developers without Copilot access:

```bash
# Configure Git to use commit template
git config commit.template .gitmessage
```

**Template content (`.gitmessage`):**
```
# type(scope): brief description
# 
# Detailed explanation of changes and their impact.
# 
# Compliance Metadata:
# HIPAA: [Applicable/Not Applicable]
# PHI-Impact: [Direct/Indirect/None]
# Clinical-Safety: [Critical/Important/Minor/None]
# Regulation: [HIPAA/FDA/SOX/Multiple]
# Risk-Level: [High/Medium/Low]
# 
# Changes:
# - [List of modified files with brief descriptions]
# 
# Testing:
# - [Description of testing performed]
# 
# Reviewers: @username
```

---

## How Copilot Learns Your Patterns

GitHub Copilot uses **multiple signals** to generate contextually appropriate suggestions:

### 1. Repository Context
- Recent commit history (last 50 commits)
- File structure and naming patterns
- Existing metadata examples

### 2. Configuration Files
- `.github/copilot-instructions.md` (primary)
- `.copilot/healthcare-commit-guidelines.yml` (this repo)
- `.vscode/settings.json` (team settings)

### 3. Active File Context
- Files you're currently editing
- Git diff of staged changes
- Related files in the same directory

---

## Verification: Ensuring Copilot Compliance

**Problem:** How do we verify Copilot-generated commits are actually compliant?

**Solution:** Multi-layer verification (defense in depth)

### Layer 1: Pre-commit Hooks (Client-side)

**File:** `.git/hooks/commit-msg`

```bash
#!/bin/bash
# Validate commit message before allowing commit

python tools/git_copilot_commit.py --validate-message "$1"

if [ $? -ne 0 ]; then
    echo "❌ Commit message validation failed"
    echo "💡 Run: python tools/git_copilot_commit.py --analyze"
    exit 1
fi
```

**What it checks:**
- ✅ Metadata fields present (HIPAA, PHI-Impact, Clinical-Safety)
- ✅ Conventional commit format
- ✅ Regulation codes valid (if provided)
- ✅ Risk level matches file changes

---

### Layer 2: OPA Policy Enforcement (Server-side)

**File:** `policies/healthcare/commit_metadata_required.rego`

```rego
# Validates that PHI-related changes have proper metadata
violation[{"msg": msg}] {
    phi_files_changed
    not has_phi_metadata
    msg := "PHI-related changes require proper metadata"
}

phi_files_changed {
    some file in input.commit.files
    contains(file, "phi-service")
}

has_phi_metadata {
    input.commit.metadata["PHI-Impact"]
    input.commit.metadata["HIPAA"]
}
```

**Runs in CI/CD** - cannot be bypassed by developers.

---

### Layer 3: AI Risk Scoring (Verification)

**File:** `tools/git_intel/risk_scorer.py`

**Cross-references declared metadata with actual code changes:**

```python
def verify_metadata_accuracy(self, declared_metadata: Dict, 
                             actual_changes: List[str]) -> bool:
    """
    Verify that declared metadata matches actual code changes.
    
    Example:
    - Developer declares: PHI-Impact: None
    - AI detects: Changed services/phi-service/encryption.go
    - Result: ⚠️ MISMATCH - Flag for review
    """
    
    # Check for PHI service changes
    phi_changes = any('phi-service' in f for f in actual_changes)
    declared_phi = declared_metadata.get('phi_impact', 'none')
    
    if phi_changes and declared_phi == 'none':
        # Developer tried to bypass - flag it!
        return False
    
    # Check for auth changes
    auth_changes = any('auth-service' in f for f in actual_changes)
    declared_hipaa = declared_metadata.get('hipaa', False)
    
    if auth_changes and not declared_hipaa:
        # Suspicious - auth changes usually need HIPAA review
        return False
    
    return True
```

**Prevents gaming the system** - AI validates declared intent against actual code.

---

## Preventing Metadata Gaming

**Attack Vector:** Developer writes `PHI-Impact: Low` to avoid dual approval, but actually changes PHI encryption.

**Defense Strategy:**

### 1. Semantic Analysis (AI-powered)

```python
# tools/git_intel/metadata_verifier.py

def detect_metadata_fraud(commit: Dict) -> Optional[str]:
    """Detect mismatched metadata and code changes."""
    
    declared_risk = commit['metadata'].get('risk_level', 'low')
    actual_files = commit['files']
    
    # High-risk paths
    high_risk_patterns = [
        'services/phi-service/',
        'services/auth-service/jwt',
        'services/payment-gateway/transaction',
        'policies/healthcare/'
    ]
    
    # Check for risk understatement
    for pattern in high_risk_patterns:
        if any(pattern in f for f in actual_files):
            if declared_risk == 'low':
                return f"⚠️ FRAUD DETECTED: Modified {pattern} but declared risk=low"
    
    return None
```

### 2. Static Analysis Integration (Semgrep)

**File:** `.semgrep.yml`

```yaml
rules:
  - id: detect-phi-access-without-metadata
    pattern: |
      func.*PHI.*
    message: "PHI-related function detected. Ensure commit has PHI-Impact metadata."
    severity: ERROR
    metadata:
      requires_commit_metadata: 
        - PHI-Impact
        - HIPAA
  
  - id: detect-encryption-changes-without-metadata
    patterns:
      - pattern: aes.NewCipher(...)
      - pattern: cipher.NewGCM(...)
    message: "Encryption change detected. Ensure commit has HIPAA metadata."
    severity: ERROR
```

**Runs in CI/CD** - detects PHI/encryption changes and ensures metadata exists.

---

### 3. GitHub Actions Verification

**File:** `.github/workflows/metadata-verification.yml`

```yaml
name: Verify Commit Metadata Accuracy

on: [pull_request]

jobs:
  verify-metadata:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Verify Metadata Matches Code Changes
        run: |
          python tools/git_intel/risk_scorer.py --verify-metadata
          
          if [ $? -eq 1 ]; then
            echo "❌ Metadata verification failed"
            echo "Declared risk level doesn't match actual code changes"
            exit 1
          fi
      
      - name: Run Semgrep Static Analysis
        uses: semgrep/semgrep-action@v1
        with:
          config: .semgrep.yml
```

**Cannot be disabled** - runs on every PR, enforced by branch protection.

---

## Implementation Challenges & Solutions

### Challenge 1: Commit Squashing

**Problem:** Many teams use "Squash and Merge" which destroys individual commit metadata.

**Solution:** Preserve metadata in PR description

#### Our Approach:

**1. GitHub PR Template**

**File:** `.github/pull_request_template.md`

```markdown
## Summary
Brief description of changes

## Compliance Metadata (Aggregate)

**Highest Risk Level:** [Low/Medium/High]  
**HIPAA Applicable:** [Yes/No]  
**PHI Impact:** [Direct/Indirect/None]  
**Clinical Safety:** [Critical/Important/Minor/None]  
**Regulations:** [HIPAA/FDA/SOX]

## Individual Commit Metadata

<!-- Auto-populated by workflow -->
```

**2. Automated PR Metadata Aggregation**

**File:** `.github/workflows/aggregate-pr-metadata.yml`

```yaml
name: Aggregate PR Commit Metadata

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  aggregate-metadata:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Extract Metadata from All Commits
        id: aggregate
        run: |
          python tools/aggregate_pr_metadata.py \
            --pr-number ${{ github.event.pull_request.number }} \
            --base ${{ github.event.pull_request.base.sha }} \
            --head ${{ github.event.pull_request.head.sha }}
      
      - name: Update PR Description
        uses: actions/github-script@v7
        with:
          script: |
            const metadata = ${{ steps.aggregate.outputs.metadata }};
            
            await github.rest.pulls.update({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
              body: context.payload.pull_request.body + '\n\n' + metadata
            });
```

**3. Squash Commit Template**

When merging, use this template for the squash commit:

```
feat(phi-service): implement patient data encryption (#123)

Aggregate Metadata:
HIPAA: Applicable
PHI-Impact: Direct (3 commits)
Clinical-Safety: Critical (1 commit), Important (2 commits)
Risk-Level: High (requires dual approval)
Regulations: HIPAA §164.312(a)(2)(iv), FDA 21 CFR Part 11

Individual Commits:
- abc123: Add AES-256-GCM encryption (HIGH)
- def456: Update key rotation policy (MEDIUM)
- ghi789: Add encryption tests (LOW)

Reviewers: @security-team @privacy-officer
```

---

### Challenge 2: Developer Experience (DX)

**Problem:** Writing metadata blocks manually is tedious and error-prone.

**Solution:** Automated tooling with interactive CLI

#### Tool 1: Git Hook (Automatic)

**File:** `.git/hooks/prepare-commit-msg`

```bash
#!/bin/bash
# Auto-scaffold commit message with metadata template

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Only run for new commits (not merges, amendments)
if [ "$COMMIT_SOURCE" = "message" ] || [ "$COMMIT_SOURCE" = "merge" ]; then
    exit 0
fi

# Get staged files
STAGED_FILES=$(git diff --cached --name-only)

# Run AI analysis
python tools/git_copilot_commit.py --analyze --template-only >> "$COMMIT_MSG_FILE"

# Add helpful comments
cat >> "$COMMIT_MSG_FILE" << 'EOF'

# ────────────────────────────────────────────────────────────────
# Healthcare Compliance Commit Template
# 
# 1. Write a clear type(scope): description (required)
# 2. Fill in metadata fields below (AI-suggested values provided)
# 3. Remove this comment block before committing
# 
# Need help? Run: python tools/git_copilot_commit.py --analyze
# ────────────────────────────────────────────────────────────────
EOF
```

**Installed automatically** by `./setup.sh`.

---

#### Tool 2: Interactive CLI

**File:** `tools/commit_helper.py`

```python
#!/usr/bin/env python3
"""
Interactive commit message builder for healthcare compliance.

Usage:
    python tools/commit_helper.py

Features:
- Analyzes staged changes
- Suggests metadata values
- Validates inputs
- Generates compliant commit message
"""

import subprocess
import sys
from typing import Dict, List
import questionary  # pip install questionary

def get_staged_files() -> List[str]:
    """Get list of staged files."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n') if result.stdout else []

def analyze_changes(files: List[str]) -> Dict:
    """Analyze changes and suggest metadata."""
    suggestions = {
        'hipaa': 'Not Applicable',
        'phi_impact': 'None',
        'clinical_safety': 'None',
        'risk_level': 'Low'
    }
    
    # AI-powered suggestions based on files
    if any('phi-service' in f for f in files):
        suggestions['hipaa'] = 'Applicable'
        suggestions['phi_impact'] = 'Direct'
        suggestions['risk_level'] = 'Medium'
    
    if any('auth-service' in f for f in files):
        suggestions['hipaa'] = 'Applicable'
        suggestions['risk_level'] = 'Medium'
    
    return suggestions

def interactive_commit():
    """Interactive commit message builder."""
    
    # Check for staged changes
    files = get_staged_files()
    if not files:
        print("❌ No staged changes. Run: git add <files>")
        sys.exit(1)
    
    print("📋 Staged files:")
    for f in files:
        print(f"  • {f}")
    print()
    
    # Analyze and suggest
    suggestions = analyze_changes(files)
    print("🤖 AI Suggestions:")
    print(f"  HIPAA: {suggestions['hipaa']}")
    print(f"  PHI-Impact: {suggestions['phi_impact']}")
    print(f"  Risk-Level: {suggestions['risk_level']}")
    print()
    
    # Interactive prompts
    commit_type = questionary.select(
        "Commit type:",
        choices=['feat', 'fix', 'refactor', 'docs', 'test', 'security', 'perf']
    ).ask()
    
    scope = questionary.text("Scope (e.g., phi-service):").ask()
    
    description = questionary.text(
        "Brief description:",
        validate=lambda x: len(x) > 10 or "Description too short"
    ).ask()
    
    hipaa = questionary.select(
        f"HIPAA: (suggested: {suggestions['hipaa']})",
        choices=['Applicable', 'Not Applicable'],
        default=suggestions['hipaa']
    ).ask()
    
    phi_impact = questionary.select(
        f"PHI-Impact: (suggested: {suggestions['phi_impact']})",
        choices=['Direct', 'Indirect', 'None'],
        default=suggestions['phi_impact']
    ).ask()
    
    clinical_safety = questionary.select(
        "Clinical-Safety:",
        choices=['Critical', 'Important', 'Minor', 'None'],
        default=suggestions['clinical_safety']
    ).ask()
    
    risk_level = questionary.select(
        f"Risk-Level: (suggested: {suggestions['risk_level']})",
        choices=['High', 'Medium', 'Low'],
        default=suggestions['risk_level']
    ).ask()
    
    # Generate commit message
    commit_msg = f"""{commit_type}({scope}): {description}

HIPAA: {hipaa}
PHI-Impact: {phi_impact}
Clinical-Safety: {clinical_safety}
Risk-Level: {risk_level}

Changes:
{chr(10).join(f'- {f}' for f in files[:5])}
"""
    
    # Preview and confirm
    print("\n📝 Generated Commit Message:")
    print("=" * 70)
    print(commit_msg)
    print("=" * 70)
    
    if questionary.confirm("Commit with this message?").ask():
        # Write to temp file and commit
        with open('/tmp/commit_msg.txt', 'w') as f:
            f.write(commit_msg)
        
        subprocess.run(['git', 'commit', '-F', '/tmp/commit_msg.txt'])
        print("✅ Committed successfully!")
    else:
        print("❌ Commit cancelled")

if __name__ == '__main__':
    interactive_commit()
```

**Usage:**
```bash
# Stage your changes
git add services/phi-service/encryption.go

# Run interactive helper
python tools/commit_helper.py

# Or use Git alias
git commit-healthcare  # (configured in setup.sh)
```

---

## Best Practices

### 1. Team Onboarding

**Include in your team docs:**

```markdown
## Making Compliant Commits

### Option 1: Let Copilot Help (Easiest)
1. Stage your changes: `git add <files>`
2. Type `git commit` in VS Code
3. Start typing, Copilot will suggest metadata
4. Review and accept suggestions

### Option 2: Use Interactive Helper
```bash
python tools/commit_helper.py
```

### Option 3: Manual (with template)
```bash
git commit  # Template auto-loads
# Fill in metadata fields
```

---

### 2. Code Review Checklist

Before approving a PR, verify:
- [ ] All commits have required metadata
- [ ] Risk levels match actual code changes
- [ ] High-risk changes have dual approval
- [ ] CI/CD metadata verification passed
- [ ] Semgrep analysis passed

---

### 3. Audit Trail

All metadata verification results are logged:

```bash
# View verification history
python tools/git_intel/audit_log.py --last-30-days

# Output:
# ✅ 2026-01-04 | abc123 | PHI encryption | VERIFIED
# ⚠️  2026-01-03 | def456 | Auth changes | MISMATCH (manual review)
# ✅ 2026-01-02 | ghi789 | Documentation | VERIFIED
```

---

## Summary

**Copilot Configuration:**
- ✅ Primary: `.github/copilot-instructions.md`
- ✅ Fallback: `.gitmessage` template
- ✅ Team settings: `.vscode/settings.json`

**Verification (Defense in Depth):**
- ✅ Pre-commit hooks (client-side)
- ✅ OPA policies (server-side)
- ✅ AI risk scoring (cross-reference)
- ✅ Semgrep static analysis
- ✅ GitHub Actions enforcement

**Developer Experience:**
- ✅ Auto-scaffolding via Git hooks
- ✅ Interactive CLI helper
- ✅ Copilot AI suggestions
- ✅ Git aliases for convenience

**Commit Squashing:**
- ✅ PR metadata aggregation
- ✅ GitHub Actions automation
- ✅ Squash commit template

**Result:** Compliant commits that can't be gamed, with excellent DX.
