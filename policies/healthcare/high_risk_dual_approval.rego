package healthcare.risk_approval

# High-Risk Dual Approval Policy
# Ensures high-risk healthcare changes require multiple approvals

default allow = false

# Allow low and medium risk commits with single approval
allow if {
    input.commit.risk_level == "low"
    has_single_approval(input.commit)
}

allow if {
    input.commit.risk_level == "medium" 
    has_single_approval(input.commit)
}

# High-risk commits require dual approval
allow if {
    input.commit.risk_level == "high"
    has_dual_approval(input.commit)
    has_clinical_review_if_needed(input.commit)
}

# Critical commits require triple approval + clinical review
allow if {
    input.commit.risk_level == "critical"
    has_triple_approval(input.commit)
    has_clinical_review(input.commit)
    has_regulatory_review(input.commit)
}

# Approval validation functions
has_single_approval(commit) if {
    reviewers := extract_reviewers(commit.message)
    count(reviewers) >= 1
}

has_dual_approval(commit) if {
    reviewers := extract_reviewers(commit.message)
    count(reviewers) >= 2
    
    # Must include security team for high-risk
    some reviewer in reviewers
    contains(reviewer, "security-team")
}

has_triple_approval(commit) if {
    reviewers := extract_reviewers(commit.message)
    count(reviewers) >= 3
    
    # Must include security, privacy, and engineering
    security_review := [r | r := reviewers[_]; contains(r, "security")]
    privacy_review := [r | r := reviewers[_]; contains(r, "privacy")]
    engineering_review := [r | r := reviewers[_]; contains(r, "engineering")]
    
    count(security_review) >= 1
    count(privacy_review) >= 1  
    count(engineering_review) >= 1
}

has_clinical_review_if_needed(commit) if {
    # If medical device or clinical changes, require clinical review
    not medical_device_change(commit)
}

has_clinical_review_if_needed(commit) if {
    medical_device_change(commit)
    has_clinical_review(commit)
}

has_clinical_review(commit) if {
    reviewers := extract_reviewers(commit.message)
    some reviewer in reviewers
    contains(reviewer, "clinical-affairs")
}

has_regulatory_review(commit) if {
    reviewers := extract_reviewers(commit.message)
    some reviewer in reviewers
    contains(reviewer, "regulatory-team")
}

# Helper functions
extract_reviewers(message) := reviewers if {
    lines := split(message, "\n")
    reviewer_line := [line | line := lines[_]; startswith(line, "Reviewers:")]
    count(reviewer_line) > 0
    reviewer_text := reviewer_line[0]
    reviewer_part := split(reviewer_text, "Reviewers: ")[1]
    reviewers := [trim_space(r) | r := split(reviewer_part, ",")[_]]
}

medical_device_change(commit) if {
    medical_keywords := ["diagnostic", "therapeutic", "clinical", "device", "algorithm"]
    some keyword in medical_keywords
    contains(lower(commit.message), keyword)
}

medical_device_change(commit) if {
    # No device paths check needed - service removed
    some path in device_paths
    some file in commit.changed_files
    startswith(file, path)
}

# Deny rules with specific guidance
deny contains msg if {
    input.commit.risk_level == "high"
    not has_dual_approval(input.commit)
    msg := sprintf("High-risk commit %s requires dual approval (minimum 2 reviewers including @security-team)", [input.commit.sha])
}

deny contains msg if {
    input.commit.risk_level == "critical" 
    not has_triple_approval(input.commit)
    msg := sprintf("Critical commit %s requires triple approval (@security-team, @privacy-officer, @engineering-team)", [input.commit.sha])
}

deny contains msg if {
    input.commit.risk_level == "critical"
    not has_clinical_review(input.commit)
    msg := sprintf("Critical commit %s requires @clinical-affairs review", [input.commit.sha])
}

deny contains msg if {
    input.commit.risk_level == "critical"
    not has_regulatory_review(input.commit)  
    msg := sprintf("Critical commit %s requires @regulatory-team review", [input.commit.sha])
}

deny contains msg if {
    medical_device_change(input.commit)
    input.commit.risk_level in ["high", "critical"]
    not has_clinical_review(input.commit)
    msg := sprintf("Medical device commit %s requires @clinical-affairs review", [input.commit.sha])
}
