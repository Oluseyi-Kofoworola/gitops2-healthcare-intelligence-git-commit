# Contract Testing Guide

**Purpose**: Consumer-driven contract testing for GitOps 2.0 Healthcare Platform  
**Framework**: Pact  
**Test Count**: 8 contract tests across 3 services

---

## 📋 Overview

Contract testing ensures that **service interfaces remain compatible** when services evolve independently. This prevents integration issues in production.

### What is Contract Testing?

**Consumer-driven contract testing**:
1. **Consumer** defines expectations (contract)
2. **Provider** validates against contract
3. Changes breaking contracts are caught early

**Benefits**:
- ✅ Catch breaking API changes before deployment
- ✅ Test service integration without full integration tests
- ✅ Enable independent service deployment
- ✅ Document API behavior
- ✅ Faster feedback than E2E tests

---

## 🎯 Contract Test Coverage

### 1. Auth Service Contracts (4 tests)
**Consumers**: Payment Gateway, PHI Service, Medical Device

**Contracts**:
- ✅ Login with valid credentials (POST /api/v1/login)
- ✅ Login with invalid credentials (401 response)
- ✅ Token validation (POST /api/v1/validate)
- ✅ Health check (GET /health)

**Response Guarantees**:
```json
{
  "token": "string (JWT)",
  "expires_in": "number (seconds)",
  "token_type": "Bearer"
}
```

---

### 2. PHI Service Contracts (2 tests)
**Consumers**: Payment Gateway, Medical Device

**Contracts**:
- ✅ Encrypt PHI data (POST /api/v1/phi/encrypt)
- ✅ Decrypt PHI data (POST /api/v1/phi/decrypt)

**Encryption Response**:
```json
{
  "encrypted_data": "string (base64)",
  "key_id": "string",
  "algorithm": "AES-256-GCM",
  "encrypted_at": "string (ISO 8601)"
}
```

**Decryption Response**:
```json
{
  "data": "string (plaintext)",
  "decrypted_at": "string (ISO 8601)"
}
```

---

### 3. Medical Device Contracts (2 tests)
**Consumers**: Monitoring Dashboard, Alert System

**Contracts**:
- ✅ Register medical device (POST /api/v1/devices)
- ✅ Get device metrics (GET /api/v1/devices/{id}/metrics)

**Device Registration Response**:
```json
{
  "device_id": "string",
  "status": "registered|failed",
  "message": "string",
  "location": "string",
  "device_type": "MRI|CT_Scanner|X-Ray|ECG|Ventilator|Pump"
}
```

**Metrics Response**:
```json
{
  "device_id": "string",
  "temperature": "number",
  "power_usage": "number",
  "cpu_usage": "number",
  "memory_usage": "number",
  "network_rx": "number",
  "network_tx": "number",
  "timestamp": "string (ISO 8601)"
}
```

---

## 🚀 Running Contract Tests

### Prerequisites
```bash
# Install Pact CLI
brew install pact-foundation/pact-ruby/pact

# Or using npm
npm install -g @pact-foundation/pact

# Install Go dependencies
cd tests/contract
go mod download
```

### Run All Contract Tests
```bash
cd tests/contract
go test -v ./...
```

### Run Specific Contract Test
```bash
# Auth Service contracts
go test -v -run TestAuthServiceContract

# PHI Service contracts
go test -v -run TestPHIServiceContract

# Medical Device contracts
go test -v -run TestMedicalDeviceContract
```

---

## 📝 Contract Test Structure

### Test Pattern
```go
func TestAuthServiceContract(t *testing.T) {
    // 1. Create Pact DSL
    pact := &dsl.Pact{
        Consumer: "PaymentGateway",
        Provider: "AuthService",
        Host:     "localhost",
    }
    defer pact.Teardown()

    // 2. Define interaction
    pact.
        AddInteraction().
        Given("User admin exists").        // Provider state
        UponReceiving("Login request").    // Description
        WithRequest(dsl.Request{           // Expected request
            Method: "POST",
            Path:   "/api/v1/login",
            Body:   loginPayload,
        }).
        WillRespondWith(dsl.Response{      // Expected response
            Status: 200,
            Body:   responsePayload,
        })

    // 3. Verify contract
    err := pact.Verify(func() error {
        // Make actual HTTP request to mock server
        // Assert response matches contract
    })
}
```

---

## 🔧 Pact Matchers

### Type Matching
```go
dsl.Like("example")        // Matches any string
dsl.Like(123)              // Matches any number
dsl.Like(true)             // Matches any boolean
```

### Term Matching (Regex)
```go
dsl.Term("Bearer", "Bearer .+")  // Matches pattern
dsl.Term("active", "active|inactive|maintenance")
```

### Array Matching
```go
dsl.EachLike(map[string]interface{}{
    "id": dsl.Like("device-001"),
}, 1)  // Minimum 1 item
```

---

## 📊 Pact Broker Integration

### Local Pact Broker (Docker)
```bash
# Start Pact Broker
docker run -d -p 9292:9292 \
  pactfoundation/pact-broker:latest

# Publish pacts
pact-broker publish ./pacts \
  --consumer-app-version=1.0.0 \
  --broker-base-url=http://localhost:9292
```

### CI/CD Integration
```yaml
# .github/workflows/contract-tests.yml
name: Contract Tests
on: [push, pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Install Pact
        run: |
          brew install pact-foundation/pact-ruby/pact
      
      - name: Run Contract Tests
        run: |
          cd tests/contract
          go test -v ./...
      
      - name: Publish Pacts
        if: github.ref == 'refs/heads/main'
        run: |
          pact-broker publish ./tests/contract/pacts \
            --consumer-app-version=${{ github.sha }} \
            --broker-base-url=${{ secrets.PACT_BROKER_URL }}
```

---

## 🎯 Provider Verification

### Verifying Contracts (Provider Side)
```go
// In auth-service/contract_test.go
func TestAuthServicePactVerification(t *testing.T) {
    pact := dsl.Pact{
        Provider: "AuthService",
    }

    // Start your actual service
    go startAuthService()

    // Verify against consumer contracts
    _, err := pact.VerifyProvider(t, types.VerifyRequest{
        ProviderBaseURL: "http://localhost:8080",
        PactURLs:        []string{"../pacts/PaymentGateway-AuthService.json"},
        StateHandlers: types.StateHandlers{
            "User admin exists": func() error {
                // Setup test data
                return setupAdminUser()
            },
        },
    })

    assert.NoError(t, err)
}
```

---

## 🧪 Testing Best Practices

### 1. Keep Contracts Minimal
```go
// ✅ Good - Test what matters
Body: dsl.Match(map[string]interface{}{
    "token": dsl.Like("jwt-token"),
    "expires_in": dsl.Like(900),
})

// ❌ Bad - Over-specification
Body: map[string]interface{}{
    "token": "exact-token-value",
    "expires_in": 900,
    "iat": 1700000000,
    "nbf": 1700000000,
    // ... too many fields
}
```

### 2. Use Provider States
```go
Given("User admin exists with password admin123")
Given("PHI encryption key exists")
Given("Device MRI-001 is registered")
```

### 3. Test Error Cases
```go
// Test 401 Unauthorized
UponReceiving("Login with invalid credentials").
WillRespondWith(dsl.Response{
    Status: 401,
    Body: errorResponse,
})

// Test 404 Not Found
UponReceiving("Get non-existent device").
WillRespondWith(dsl.Response{
    Status: 404,
})
```

### 4. Version Your Contracts
```go
// Tag contracts with version
publishPacts(brokerURL, "1.0.0")
publishPacts(brokerURL, "1.1.0")
```

---

## 📈 Contract Testing Workflow

```
┌─────────────────────────────────────────────┐
│ 1. Consumer writes contract test           │
│    (PaymentGateway expects AuthService     │
│     to return JWT token on login)          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 2. Consumer test generates Pact file       │
│    (PaymentGateway-AuthService.json)       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 3. Publish Pact to Pact Broker             │
│    (Shared contract repository)            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 4. Provider runs verification test         │
│    (AuthService validates it meets         │
│     PaymentGateway's expectations)         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 5. Can I Deploy?                           │
│    (Check if consumer/provider versions    │
│     are compatible)                        │
└─────────────────────────────────────────────┘
```

---

## 🚦 Contract Test vs Integration Test

| Aspect | Contract Test | Integration Test |
|--------|--------------|------------------|
| **Speed** | Fast (mock server) | Slow (real services) |
| **Isolation** | Consumer-focused | Full system |
| **Dependencies** | None | All services needed |
| **Scope** | API interface | End-to-end flow |
| **When to Run** | Every commit | Before release |
| **Feedback** | Immediate | Delayed |

**Use both** for comprehensive testing!

---

## 📊 Expected Outcomes

### Contract Test Results
```
=== RUN   TestAuthServiceContract
=== RUN   TestAuthServiceContract/Login_with_valid_credentials
    ✓ Contract verified: Login returns JWT token
=== RUN   TestAuthServiceContract/Login_with_invalid_credentials
    ✓ Contract verified: Invalid login returns 401
=== RUN   TestAuthServiceContract/Token_validation
    ✓ Contract verified: Token validation succeeds
=== RUN   TestAuthServiceContract/Health_check_endpoint
    ✓ Contract verified: Health check returns status
--- PASS: TestAuthServiceContract (2.35s)

=== RUN   TestPHIServiceContract
=== RUN   TestPHIServiceContract/Encrypt_PHI_data
    ✓ Contract verified: PHI encryption succeeds
=== RUN   TestPHIServiceContract/Decrypt_PHI_data
    ✓ Contract verified: PHI decryption succeeds
--- PASS: TestPHIServiceContract (1.12s)

=== RUN   TestMedicalDeviceContract
=== RUN   TestMedicalDeviceContract/Register_medical_device
    ✓ Contract verified: Device registration succeeds
=== RUN   TestMedicalDeviceContract/Get_device_metrics
    ✓ Contract verified: Metrics retrieval succeeds
--- PASS: TestMedicalDeviceContract (0.98s)

PASS
ok      github.com/gitops2-enterprise/contract-tests    4.450s
```

---

## 🔍 Debugging Failed Contracts

### View Pact Files
```bash
cat pacts/PaymentGateway-AuthService.json
```

### Run with Verbose Output
```bash
go test -v -run TestAuthServiceContract
```

### Check Mock Server Logs
```bash
# Pact creates a mock server on random port
# Check logs for request/response details
```

---

## 📚 Resources

- [Pact Documentation](https://docs.pact.io/)
- [Pact Go](https://github.com/pact-foundation/pact-go)
- [Contract Testing Best Practices](https://docs.pact.io/best_practices)

---

**Last Updated**: November 23, 2025  
**Version**: 1.0.0  
**Test Count**: 8 contract tests
