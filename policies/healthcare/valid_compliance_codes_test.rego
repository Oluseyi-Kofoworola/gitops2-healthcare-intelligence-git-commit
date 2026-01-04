package healthcare.compliance_codes

# Tests for Valid Compliance Code Whitelists
# WHY: Ensure AI hallucination detection works correctly

# ==================================================================================
# Valid Code Tests - Should PASS
# ==================================================================================

test_valid_hipaa_section if {
	is_valid_compliance_code("164.312(e)(1)")
}

test_valid_hipaa_shorthand if {
	is_valid_compliance_code("HIPAA-SECURITY")
}

test_valid_fda_510k if {
	is_valid_compliance_code("510(k)")
}

test_valid_fda_21cfr11 if {
	is_valid_compliance_code("21CFR11.10")
}

test_valid_sox_section if {
	is_valid_compliance_code("SOX-404")
}

test_valid_gdpr_article if {
	is_valid_compliance_code("GDPR-ART32")
}

test_valid_iso_standard if {
	is_valid_compliance_code("ISO27001")
}

# Case insensitivity
test_case_insensitive_hipaa if {
	is_valid_compliance_code("hipaa-security")
}

test_case_insensitive_fda if {
	is_valid_compliance_code("fda-510k")
}

# ==================================================================================
# Invalid Code Tests - Should FAIL (AI Hallucinations)
# ==================================================================================

test_invalid_hipaa_fake_section if {
	not is_valid_compliance_code("164.999(z)(99)")  # Fake section
}

test_invalid_fda_imaginary if {
	not is_valid_compliance_code("FDA-SECTION-999")  # Hallucinated
}

test_invalid_sox_made_up if {
	not is_valid_compliance_code("SOX-123")  # Doesn't exist
}

test_invalid_gdpr_fake if {
	not is_valid_compliance_code("GDPR-ART999")  # Invalid article
}

test_invalid_random_code if {
	not is_valid_compliance_code("HIPAA-QUANTUM-SECURITY")  # AI hallucination
}

# ==================================================================================
# Code Extraction Tests
# ==================================================================================

test_extract_single_code if {
	message := "feat(auth): add HIPAA encryption\nHIPAA: 164.312(e)(1)"
	codes := extract_compliance_codes(message)
	count(codes) == 1
	"164.312(e)(1)" in codes
}

test_extract_multiple_codes if {
	message := "feat(device): FDA device validation\nFDA: 510(k), 21CFR11.10\nHIPAA: 164.312(a)(1)"
	codes := extract_compliance_codes(message)
	count(codes) == 3
}

test_extract_with_spaces if {
	message := "fix(payment): SOX controls\nSOX:  SOX-404  ,  SOX-302  "
	codes := extract_compliance_codes(message)
	"SOX-404" in codes
	"SOX-302" in codes
}

test_no_codes_if_none_present if {
	message := "feat(docs): update README\nNo compliance metadata"
	codes := extract_compliance_codes(message)
	count(codes) == 0
}

# ==================================================================================
# Commit Validation Tests (with deny rules)
# ==================================================================================

test_valid_commit_with_real_codes if {
	input_data := {
		"commits": [
			{
				"sha": "abc123",
				"message": "feat(phi): add encryption\nHIPAA: 164.312(e)(1)\nPHI-Impact: HIGH",
				"changed_files": ["services/phi-service/encryption.go"]
			}
		]
	}
	
	# Should not deny
	count(deny) == 0 with input as input_data
}

test_deny_commit_with_fake_codes if {
	input_data := {
		"commits": [
			{
				"sha": "def456",
				"message": "feat(auth): add auth\nHIPAA: 164.999(FAKE)\nPHI-Impact: LOW",
				"changed_files": ["services/auth-service/main.go"]
			}
		]
	}
	
	# Should deny with hallucination error
	count(deny) > 0 with input as input_data
}

test_deny_commit_with_ai_hallucinated_code if {	input_data := {
		"commits": [
			{
				"sha": "ghi789",
				"message": "feat(phi): add encryption\nHIPAA: 164.312(a)(2)(iv)",
				"changed_files": ["services/phi-service/encryption.go"]
			}
		]
	}
	
	# Should pass - valid HIPAA code
	count(deny) > 0 with input as input_data
}

test_allow_commit_without_compliance_codes if {
	input_data := {
		"commits": [
			{
				"sha": "jkl012",
				"message": "docs(readme): update installation instructions",
				"changed_files": ["README.md"]
			}
		]
	}
	
	# Should allow - no compliance codes to validate
	count(deny) == 0 with input as input_data
}

# ==================================================================================
# Edge Cases
# ==================================================================================

test_mixed_valid_and_invalid_codes if {
	input_data := {
		"commits": [
			{
				"sha": "mno345",
				"message": "feat(multi): complex change\nHIPAA: 164.312(e)(1), 164.999(FAKE)\nSOX: SOX-404",
				"changed_files": ["multiple-files"]
			}
		]
	}
	
	# Should deny because one code is invalid
	count(deny) > 0 with input as input_data
}

test_empty_compliance_line if {
	input_data := {
		"commits": [
			{
				"sha": "pqr678",
				"message": "feat(test): test\nHIPAA: ",
				"changed_files": ["test.go"]
			}
		]
	}
	
	# Should not deny - empty line is ignored
	count(deny) == 0 with input as input_data
}

# ==================================================================================
# Real-World Scenarios
# ==================================================================================

test_realistic_hipaa_commit if {
	input_data := {
		"commits": [
			{
				"sha": "real001",
				"message": concat("\n", [
					"security(phi): implement AES-256 encryption for PHI data",
					"",
					"Business Impact: Ensures HIPAA compliance for PHI at rest",
					"HIPAA: 164.312(a)(2)(iv), 164.312(e)(2)(ii)",
					"PHI-Impact: HIGH - Encrypts all patient identifiable data",
					"Testing: Encryption key rotation validated",
					"Reviewers: @security-team @privacy-officer"
				])
			}
		]
	}
	
	count(deny) == 0 with input as input_data
}

test_realistic_fda_commit if {
	input_data := {
		"commits": [
			{
				"sha": "real002",
				"message": concat("\n", [
					"feat(device): add diagnostic algorithm validation",
					"",
					"FDA: 510(k), 21CFR820.30",
					"FDA-510k: CLASS-II medical device software",
					"Clinical Safety: REQUIRES_CLINICAL_REVIEW",
					"Testing: Clinical accuracy >99.5% validated"
				])
			}
		]
	}
	
	count(deny) == 0 with input as input_data
}

test_ai_generated_commit_with_hallucination if {
	# Simulates AI generating fake compliance codes
	input_data := {
		"commits": [
			{
				"sha": "ai001",
				"message": concat("\n", [
					"feat(auth): AI-enhanced authentication",
					"",
					"HIPAA: 164.312-QUANTUM-AI-ENHANCED",  # AI hallucination
					"FDA: NEURAL-NETWORK-CLEARANCE-2024",  # Fake code
					"PHI-Impact: MEDIUM"
				])
			}
		]
	}
	
	# Should catch both hallucinations
	count(deny) >= 2 with input as input_data
}
