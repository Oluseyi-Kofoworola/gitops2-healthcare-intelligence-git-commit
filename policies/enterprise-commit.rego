package enterprise.git

import future.keywords

# ============================================================================
# DEVELOPER-FRIENDLY COMMIT POLICY
# ============================================================================
# PHILOSOPHY: Make it easy to do the right thing, hard to do the wrong thing
#
# RULES:
# 1. Documentation/tests/config: Zero friction (no requirements)
# 2. Regular service code: Conventional commits format required
# 3. Critical paths (PHI/payment/device): Format + compliance metadata required
# 4. Emergency bypass: Add [skip-policy] to commit message
#
# WHY: Reduce developer friction while maintaining compliance where it matters
# ============================================================================

default allow := false

# Allow if all commits are OK
allow if {
  every c in input.commits { commit_ok(c) }
  count(deny) == 0
}

# Emergency bypass (use sparingly!)
allow if {
  some c in input.commits
  contains(lower(c.message), "[skip-policy]")
}

# ============================================================================
# COMMIT APPROVAL RULES (Ordered by Priority)
# ============================================================================

# Rule 1: Low-friction changes (docs, tests, config, tooling)
commit_ok(c) if {
  is_low_friction_change(c)
  not low_signal(c.message)
}

# Rule 2: Regular service code (not critical)
commit_ok(c) if {
  not is_low_friction_change(c)
  not is_critical_path_change(c)
  valid_format(c.message)
  not low_signal(c.message)
}

# Rule 3: Critical path changes
commit_ok(c) if {
  is_critical_path_change(c)
  valid_format(c.message)
  not low_signal(c.message)
  has_compliance_metadata(c)
}

# ============================================================================
# CHANGE CLASSIFICATION
# ============================================================================

# Low-friction: docs, tests, scripts, config examples, CI files
is_low_friction_change(c) if {
  count(c.changed_files) > 0
  every file in c.changed_files {
    is_low_friction_file(file)
  }
}

is_low_friction_file(file) if { startswith(file, "docs/") }
is_low_friction_file(file) if { startswith(file, "tests/") }
is_low_friction_file(file) if { startswith(file, "scripts/") }
is_low_friction_file(file) if { startswith(file, "tools/") }
is_low_friction_file(file) if { startswith(file, ".github/") }
is_low_friction_file(file) if { startswith(file, "config/") }
is_low_friction_file(file) if { startswith(file, "policies/") }
is_low_friction_file(file) if { endswith(file, ".md") }
is_low_friction_file(file) if { endswith(file, ".txt") }
is_low_friction_file(file) if { endswith(file, "_test.go") }
is_low_friction_file(file) if { endswith(file, "_test.py") }
is_low_friction_file(file) if { endswith(file, ".example.yml") }
is_low_friction_file(file) if { endswith(file, ".example.yaml") }
is_low_friction_file(file) if { file == "pyproject.toml" }
is_low_friction_file(file) if { file == "package.json" }
is_low_friction_file(file) if { file == "go.mod" }
is_low_friction_file(file) if { file == "go.sum" }
is_low_friction_file(file) if { file == ".husky/commit-msg" }
is_low_friction_file(file) if { contains(file, "validate-commit.sh") }

# Critical paths: PHI, payment, medical device, auth
is_critical_path_change(c) if {
  some file in c.changed_files
  is_critical_file(file)
  not is_low_friction_file(file)
}

is_critical_file(file) if { contains(file, "services/phi-service/") }
is_critical_file(file) if { contains(file, "services/payment-gateway/") }
is_critical_file(file) if { contains(file, "services/medical-device/") }
is_critical_file(file) if { contains(file, "services/auth-service/") }

# ============================================================================
# VALIDATION RULES
# ============================================================================

# Conventional commits format (flexible scopes)
valid_format(msg) if {
  regex.match("^(feat|fix|perf|security|docs|refactor|chore|test|ci|build|style|breaking)\\([a-z0-9_-]+\\): .+", msg)
}

# Low-signal commits (reject these)
low_signal(msg) if { contains(lower(msg), "wip") }
low_signal(msg) if { msg == "update" }
low_signal(msg) if { contains(lower(msg), "temp") }
low_signal(msg) if { contains(lower(msg), "fixup") }

# Compliance metadata (flexible - any one is sufficient)
has_compliance_metadata(c) if {
  contains(c.message, "HIPAA:")
}

has_compliance_metadata(c) if {
  contains(c.message, "PHI-Impact:")
}

has_compliance_metadata(c) if {
  contains(c.message, "FDA-510k:")
}

has_compliance_metadata(c) if {
  contains(c.message, "SOX-Control:")
}

# ============================================================================
# DENY RULES (Clear, Actionable Messages)
# ============================================================================

deny[msg] if {
  some c in input.commits
  is_critical_path_change(c)
  not has_compliance_metadata(c)
  msg := sprintf(
    "❌ Critical path change requires compliance metadata.\n   Add one of: HIPAA:, PHI-Impact:, FDA-510k:, or SOX-Control:\n   Files: %v",
    [c.changed_files]
  )
}

deny[msg] if {
  some c in input.commits
  not is_low_friction_change(c)
  not valid_format(c.message)
  preview := substring(c.message, 0, 80)
  msg := sprintf(
    "❌ Invalid commit format.\n   Use: type(scope): description\n   Examples:\n   - feat(api): add user endpoint\n   - fix(auth): resolve login bug\n   - docs(readme): update install steps\n   Got: '%s'",
    [preview]
  )
}

deny[msg] if {
  some c in input.commits
  low_signal(c.message)
  msg := sprintf(
    "❌ Low-signal commit message: '%s'\n   Please provide meaningful description of changes.",
    [c.message]
  )
}
