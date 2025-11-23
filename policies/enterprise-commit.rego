package enterprise.git

import future.keywords
import data.healthcare.compliance_codes  # WHY: Import AI hallucination prevention

# Simple, demo-level commit policy.
# In a real system, this input would be a structured representation of commits,
# usually built from `git log` by a small adapter.

default allow := false

allow if {
  # All commits in the push satisfy commit_ok
  every c in input.commits { commit_ok(c) }
  count(deny) == 0
}

# Multi-domain high risk when touching both payment-gateway and auth-service
multi_domain_high_risk(c) if {
  some i
  some j
  contains(c.changed_files[i], "payment-gateway")
  contains(c.changed_files[j], "auth-service")
}

# Documentation-only commits don't require compliance metadata
commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  is_docs_only(c)
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
# Updated: now requires BOTH HIPAA and PHI-Impact lines to pass.
commit_ok(c) if {
  multi_domain_high_risk(c)
  valid_format(c.message)
  not low_signal(c.message)
  has_compliance_metadata(c)
  has_phi_impact_metadata(c)
}

valid_format(msg) if {
  regex.match("^(feat|fix|perf|security|docs|refactor|chore|breaking)\\([a-z0-9_-]+\\): .+", msg)
}

low_signal(msg) if { contains(lower(msg), "wip") }
low_signal(msg) if { msg == "update" }
low_signal(msg) if { contains(lower(msg), "temp") }

# Check if commit only touches documentation files
is_docs_only(c) if {
  count(c.changed_files) > 0
  every file in c.changed_files {
    is_docs_file(file)
  }
}

is_docs_file(file) if { startswith(file, "docs/") }
is_docs_file(file) if { endswith(file, ".md") }
is_docs_file(file) if { endswith(file, ".txt") }
is_docs_file(file) if { contains(file, "/README") }
is_docs_file(file) if { contains(file, "/CHANGELOG") }
is_docs_file(file) if { contains(file, "/CONTRIBUTING") }
is_docs_file(file) if { 
  startswith(file, "config/")
  endswith(file, ".example.yml")
}
is_docs_file(file) if { 
  startswith(file, "config/")
  endswith(file, ".example.yaml")
}

# --- Helper stubs (WHY: simplify demo; real logic would parse metadata) ---
healthcare_compliance_required(c) if { regex.match(".*\\b(phi|medical|fda)\\b.*", lower(c.message)) }
healthcare_compliance_required(c) if { multi_domain_high_risk(c) }

fda_validation_required(c) if { contains(lower(c.message), "device") }

has_fda_validation(c) if { contains(lower(c.message), "fda") }

security_commit_touches_critical(c) if {
  regex.match("^security\\([^)]+\\):", c.message)
  some i
  contains(c.changed_files[i], "payment-gateway")
}

# --- Structured metadata parsing helpers (WHY: move from naive substring to explicit key parsing) ---
lines(msg) = split(msg, "\n")

has_line_prefix(msg, p) if {
  some i
  li := lines(lower(msg))[i]
  startswith(li, lower(p))
}

# Consolidated: only line-based compliance metadata retained (WHY: remove naive substring match) 
has_compliance_metadata(c) if {
  has_line_prefix(c.message, "hipaa:")
}

has_phi_impact_metadata(c) if {
  has_line_prefix(c.message, "phi-impact:")
}

# --- New structured metadata prefixes (WHY: extend beyond HIPAA/PHI to FDA/SOX/GDPR) ---
has_fda_510k_metadata(c) if { has_line_prefix(c.message, "fda-510k:") }
has_sox_control_metadata(c) if { has_line_prefix(c.message, "sox-control:") }
has_gdpr_data_class_metadata(c) if { has_line_prefix(c.message, "gdpr-data-class:") }

# Domain triggers (WHY: enforce domain-specific metadata when referenced) 
fda_device_domain(c) if { contains(lower(c.message), "device") }
sox_domain(c) if { contains(lower(c.message), "sox") }
sox_domain(c) if { contains(lower(c.message), "financial") }
sox_domain(c) if { contains(lower(c.message), "audit") }
gdpr_domain(c) if { contains(lower(c.message), "gdpr") }

# Device (FDA) commits must include FDA-510k metadata line
commit_ok(c) if {
  fda_device_domain(c)
  valid_format(c.message)
  not low_signal(c.message)
  has_fda_510k_metadata(c)
}

# SOX domain commits must include SOX-Control metadata line
commit_ok(c) if {
  sox_domain(c)
  valid_format(c.message)
  not low_signal(c.message)
  has_sox_control_metadata(c)
}

# GDPR domain commits must include GDPR-Data-Class metadata line
commit_ok(c) if {
  gdpr_domain(c)
  valid_format(c.message)
  not low_signal(c.message)
  has_gdpr_data_class_metadata(c)
}

# Adjust healthcare compliance requirement (single-domain): if term appears require HIPAA line
commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  healthcare_compliance_required(c)
  not multi_domain_high_risk(c)
  has_compliance_metadata(c)
}

# --- Granular deny messages (WHY: improve developer feedback) ---
# We accumulate reasons for each commit; CI can surface them.

deny[reason] if {
  some c in input.commits
  multi_domain_high_risk(c)
  not has_compliance_metadata(c)
  reason := sprintf("commit %s missing HIPAA line for multi-domain change", [c.sha])
}

deny[reason] if {
  some c in input.commits
  multi_domain_high_risk(c)
  has_compliance_metadata(c)
  not has_phi_impact_metadata(c)
  reason := sprintf("commit %s missing PHI-Impact line for multi-domain change", [c.sha])
}

deny[reason] if {
  some c in input.commits
  fda_device_domain(c)
  not has_fda_510k_metadata(c)
  reason := sprintf("commit %s missing FDA-510k metadata line", [c.sha])
}

deny[reason] if {
  some c in input.commits
  sox_domain(c)
  not has_sox_control_metadata(c)
  reason := sprintf("commit %s missing SOX-Control metadata line", [c.sha])
}

deny[reason] if {
  some c in input.commits
  gdpr_domain(c)
  not has_gdpr_data_class_metadata(c)
  reason := sprintf("commit %s missing GDPR-Data-Class metadata line", [c.sha])
}

# === ENTERPRISE: AI Hallucination Prevention ===
# WHY: Detect and reject AI-generated fake compliance codes
# WHAT: Validate all compliance codes against authoritative whitelists

deny[reason] if {
  some c in input.commits
  codes := compliance_codes.extract_compliance_codes(c.message)
  count(codes) > 0
  
  some code in codes
  not compliance_codes.is_valid_compliance_code(code)
  
  reason := sprintf(
    "commit %s contains invalid compliance code '%s' (possible AI hallucination - verify against official regulations)",
    [c.sha, code]
  )
}
