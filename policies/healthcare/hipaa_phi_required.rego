package healthcare.hipaa

# HIPAA Compliance Policy for Healthcare GitOps 2.0
# Enforces Protected Health Information (PHI) handling requirements

default allow = false

# Allow commits that comply with HIPAA requirements
allow if {
    input.commit
    hipaa_compliant(input.commit)
}

# HIPAA compliance validation
hipaa_compliant(commit) if {
    # Basic commit format validation
    valid_semantic_format(commit.message)
    
    # PHI-related commits must have proper metadata
    phi_related(commit)
    has_phi_metadata(commit)
    has_required_reviewers(commit)
    
    # Audit requirements
    has_audit_trail(commit)
}

# Non-PHI commits still need basic compliance
hipaa_compliant(commit) if {
    valid_semantic_format(commit.message)
    not phi_related(commit)
    not high_risk_change(commit)
}

# High-risk non-PHI changes need review
hipaa_compliant(commit) if {
    valid_semantic_format(commit.message)
    not phi_related(commit)
    high_risk_change(commit)
    has_security_review(commit)
}

# PHI detection logic
phi_related(commit) if {
    phi_keywords := ["phi", "patient", "medical", "health", "diagnosis", "treatment"]
    some keyword in phi_keywords
    contains(lower(commit.message), keyword)
}

phi_related(commit) if {
    phi_paths := ["services/phi-service/", "services/patient-"]
    some path in phi_paths
    some file in commit.changed_files
    startswith(file, path)
}

# Metadata validation
has_phi_metadata(commit) if {
    contains(commit.message, "PHI-Impact:")
    contains(commit.message, "Audit-Trail:")
    contains(commit.message, "Encryption-Status:")
}

has_audit_trail(commit) if {
    contains(commit.message, "Audit Trail: Commit")
}

has_required_reviewers(commit) if {
    reviewers := split(commit.message, "Reviewers: ")[1]
    contains(reviewers, "@privacy-officer")
}

has_security_review(commit) if {
    reviewers := split(commit.message, "Reviewers: ")[1]
    contains(reviewers, "@security-team")
}

# Risk assessment
high_risk_change(commit) if {
    high_risk_keywords := ["security", "auth", "encryption", "access", "permission"]
    some keyword in high_risk_keywords
    contains(lower(commit.message), keyword)
}

high_risk_change(commit) if {
    critical_paths := ["services/auth-service/", "services/payment-gateway/security"]
    some path in critical_paths
    some file in commit.changed_files
    startswith(file, path)
}

# Semantic format validation
valid_semantic_format(message) if {
    # Must start with type(scope): 
    regex.match(`^(feat|fix|security|perf|breaking|chore|docs)\([^)]+\):`, message)
}

# Deny rules with specific messages
deny contains msg if {
    input.commit
    phi_related(input.commit)
    not has_phi_metadata(input.commit)
    msg := sprintf("HIPAA violation: PHI-related commit %s missing required metadata (PHI-Impact, Audit-Trail, Encryption-Status)", [input.commit.sha])
}

deny contains msg if {
    input.commit
    phi_related(input.commit)
    not has_required_reviewers(input.commit)
    msg := sprintf("HIPAA violation: PHI-related commit %s missing @privacy-officer review", [input.commit.sha])
}

deny contains msg if {
    input.commit
    high_risk_change(input.commit)
    not has_security_review(input.commit)
    msg := sprintf("HIPAA violation: High-risk commit %s missing @security-team review", [input.commit.sha])
}
