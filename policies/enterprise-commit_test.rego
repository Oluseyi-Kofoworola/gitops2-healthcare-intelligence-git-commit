package enterprise.commit

import rego.v1

# Test: Valid enterprise commit with all required fields
test_valid_enterprise_commit if {
    allow with input as {
        "message": "feat(api): add new endpoint\n\nBusiness Impact: Enhanced API functionality\nRisk Level: MEDIUM\nCompliance: HIPAA\nReviewers: @team",
        "type": "feat",
        "scope": "api",
        "files": ["api/handler.go"]
    }
}

# Test: Missing business impact should fail
test_missing_business_impact if {
    not allow with input as {
        "message": "feat(api): add new endpoint\n\nRisk Level: MEDIUM",
        "type": "feat",
        "scope": "api"
    }
}

# Test: Missing risk level should fail
test_missing_risk_level if {
    not allow with input as {
        "message": "feat(api): add new endpoint\n\nBusiness Impact: test",
        "type": "feat",
        "scope": "api"
    }
}

# Test: Invalid risk level should fail
test_invalid_risk_level if {
    not allow with input as {
        "message": "feat(api): add new endpoint\n\nBusiness Impact: test\nRisk Level: INVALID",
        "type": "feat",
        "scope": "api"
    }
}
