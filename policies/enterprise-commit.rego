package enterprise.git

import future.keywords

# Simple, demo-level commit policy.
# In a real system, this input would be a structured representation of commits,
# usually built from `git log` by a small adapter.

default allow := false

allow if {
  # All commits in the push satisfy commit_ok
  every c in input.commits { commit_ok(c) }
}

# Multi-domain high risk when touching both payment-gateway and auth-service
multi_domain_high_risk(c) if {
  some i
  some j
  contains(c.changed_files[i], "payment-gateway")
  contains(c.changed_files[j], "auth-service")
}

# Baseline commit rule: exclude multi-domain high risk so metadata rules can apply
commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  not regex.match("^security\\([^)]+\\):", c.message)
  not healthcare_compliance_required(c)
  not multi_domain_high_risk(c)
}

commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  not regex.match("^security\\([^)]+\\):", c.message)
  healthcare_compliance_required(c)
  has_compliance_metadata(c)
}

commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  not regex.match("^security\\([^)]+\\):", c.message)
  fda_validation_required(c)
  has_fda_validation(c)
}

commit_ok(c) if {
  regex.match("^security\\([^)]+\\):", c.message)
  valid_format(c.message)
  not low_signal(c.message)
  security_commit_touches_critical(c)
}

# Multi-domain high risk requires explicit compliance metadata (WHY: cross-domain changes elevate audit risk)
commit_ok(c) if {
  multi_domain_high_risk(c)
  valid_format(c.message)
  not low_signal(c.message)
  has_compliance_metadata(c)
}

valid_format(msg) if {
  regex.match("^(feat|fix|perf|security|docs|refactor|chore|breaking)\\([a-z-]+\\): .+", msg)
}

low_signal(msg) if { contains(lower(msg), "wip") }
low_signal(msg) if { msg == "update" }
low_signal(msg) if { contains(lower(msg), "temp") }

# --- Helper stubs (WHY: simplify demo; real logic would parse metadata) ---
healthcare_compliance_required(c) if { regex.match(".*\\b(phi|medical|fda)\\b.*", lower(c.message)) }

has_compliance_metadata(c) if { contains(lower(c.message), "hipaa") }

fda_validation_required(c) if { contains(lower(c.message), "device") }

has_fda_validation(c) if { contains(lower(c.message), "fda") }

security_commit_touches_critical(c) if {
  regex.match("^security\\([^)]+\\):", c.message)
  some i
  contains(c.changed_files[i], "payment-gateway")
}
