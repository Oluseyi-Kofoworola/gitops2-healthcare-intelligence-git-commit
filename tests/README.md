# Test Suite

Testing infrastructure for the Healthcare GitOps Intelligence demo.

---

## Test Structure

```
tests/
├── python/              # Python tests for tools
│   ├── test_risk_scorer.py
│   ├── test_compliance.py
│   └── conftest.py
│
├── integration/         # Docker Compose integration tests
│   └── docker-compose.yml
│
└── README.md           # This file
```

**Note**: Services have their own Go tests in `services/*/main_test.go`

---

## Running Tests

### Python Tests

```bash
# All Python tests
pytest tests/python/

# Specific test
pytest tests/python/test_risk_scorer.py -v

# With coverage
pytest tests/python/ --cov=tools --cov-report=html
```

### Go Service Tests

```bash
# All service tests
go test ./services/...

# Specific service
cd services/phi-service
go test -v

# With coverage
go test -cover ./services/...
```

### OPA Policy Tests

```bash
# All policies
opa test policies/healthcare/

# Specific policy
opa test policies/healthcare/commit_metadata_required.rego -v
```

### Integration Tests

```bash
# Start all services
cd tests/integration
docker-compose up -d

# Test services are running
curl http://localhost:8081/health  # auth-service
curl http://localhost:8082/health  # phi-service
curl http://localhost:8083/health  # payment-gateway

# Cleanup
docker-compose down
```

---

## Writing Tests

### Python Test Example

```python
# tests/python/test_my_tool.py
def test_my_function():
    from tools.my_tool import my_function
    
    result = my_function("input")
    assert result == "expected_output"
```

### Go Test Example

```go
// services/my-service/main_test.go
func TestMyHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/health", nil)
    w := httptest.NewRecorder()
    
    healthHandler(w, req)
    
    assert.Equal(t, 200, w.Code)
}
```

### OPA Policy Test Example

```rego
# policies/healthcare/my_policy_test.rego
test_valid_commit {
    result = violation with input as {"type": "feat", "scope": "api"}
    count(result) == 0
}

test_invalid_commit {
    result = violation with input as {"type": "invalid"}
    count(result) > 0
}
```

---

## CI/CD

Tests run automatically on:
- Pre-commit hooks (OPA policies)
- Pull requests (all tests)
- Main branch pushes (all tests + coverage)

See `.github/workflows/` for CI configuration.
