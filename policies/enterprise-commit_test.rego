package enterprise.git

import future.keywords

# Positive test: valid commit should be allowed

test_valid_commit if {
  test_input := {"commits": [{"sha": "abc123", "message": "feat(payment): add apple pay support", "changed_files": ["services/payment-gateway/payment.go"]}]}
  allow with input as test_input
}

# Negative test: WIP commit should be denied

test_invalid_commit_wip if {
  test_input := {"commits": [{"sha": "def456", "message": "WIP: some stuff", "changed_files": ["services/payment-gateway/payment.go"]}]}
  not allow with input as test_input
}

# Multi-domain commit must include compliance metadata (HIPAA + PHI-Impact)

test_multi_domain_requires_compliance if {
  test_input := {"commits": [{"sha": "xyz111", "message": "feat(payment): cross-domain payment/auth sync\nHIPAA: compliant\nPHI-Impact: low", "changed_files": ["services/payment-gateway/payment.go", "services/auth-service/main.go"]}]}
  allow with input as test_input
}

# Missing metadata should fail (no HIPAA line)

test_multi_domain_missing_metadata if {
  test_input := {"commits": [{"sha": "xyz222", "message": "feat(payment): cross-domain payment/auth sync", "changed_files": ["services/payment-gateway/payment.go", "services/auth-service/main.go"]}]}
  not allow with input as test_input
}

# Multi-domain payment+auth with compliance metadata variant

test_multi_domain_auth_payment if {
  test_input := {"commits": [{"sha": "xyz333", "message": "feat(auth): synchronize token scopes with payment\nHIPAA: compliant\nPHI-Impact: none", "changed_files": ["services/payment-gateway/payment.go", "services/auth-service/main.go"]}]}
  allow with input as test_input
}

# Negative: missing PHI-Impact line should fail

test_multi_domain_missing_phi_impact if {
  test_input := {"commits": [{"sha": "xyz444", "message": "feat(auth): synchronize token scopes with payment\nHIPAA: compliant", "changed_files": ["services/payment-gateway/payment.go", "services/auth-service/main.go"]}]}
  not allow with input as test_input
}

# Positive: FDA device commit with required metadata

test_fda_device_with_metadata if {
  test_input := {"commits": [{"sha": "fda111", "message": "feat(device): update diagnostics pipeline\nFDA-510k: pending-validation", "changed_files": ["services/medical-device/diagnostic.go"]}]}
  allow with input as test_input
}

# Negative: FDA device commit missing metadata

test_fda_device_missing_metadata if {
  test_input := {"commits": [{"sha": "fda222", "message": "feat(device): update diagnostics pipeline", "changed_files": ["services/medical-device/diagnostic.go"]}]}
  not allow with input as test_input
}

# Positive: SOX domain commit with control metadata

test_sox_control_with_metadata if {
  test_input := {"commits": [{"sha": "sox111", "message": "feat(payment): enhance financial audit export\nSOX-Control: FC-TRANSACTION-IMMUTABLE", "changed_files": ["services/payment-gateway/payment.go"]}]}
  allow with input as test_input
}

# Negative: SOX domain commit missing control metadata

test_sox_control_missing_metadata if {
  test_input := {"commits": [{"sha": "sox222", "message": "feat(payment): enhance financial audit export", "changed_files": ["services/payment-gateway/payment.go"]}]}
  not allow with input as test_input
}

# Positive: GDPR domain commit with data class metadata

test_gdpr_commit_with_metadata if {
  test_input := {"commits": [{"sha": "gdpr111", "message": "feat(auth): align GDPR consent flow\nGDPR-Data-Class: pseudonymized", "changed_files": ["services/auth-service/main.go"]}]}
  allow with input as test_input
}

# Negative: GDPR domain commit missing data class metadata

test_gdpr_commit_missing_metadata if {
  test_input := {"commits": [{"sha": "gdpr222", "message": "feat(auth): align GDPR consent flow", "changed_files": ["services/auth-service/main.go"]}]}
  not allow with input as test_input
}
