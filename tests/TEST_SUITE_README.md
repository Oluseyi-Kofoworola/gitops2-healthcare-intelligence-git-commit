# GitOps 2.0 - Testing Suite

**Comprehensive test infrastructure** for the GitOps 2.0 Healthcare Intelligence Platform.

---

## 📋 Test Categories

### 1. Integration Tests (`tests/integration/`)
Cross-service interaction testing using Docker Compose.

**Coverage**:
- ✅ Health checks for all 5 microservices
- ✅ Authentication flows (login, token validation)
- ✅ Payment Gateway + Auth integration
- ✅ PHI Service encryption/decryption workflows
- ✅ Medical Device monitoring integration
- ✅ Synthetic PHI + PHI Service pipeline
- ✅ End-to-end healthcare workflow
- ✅ Concurrent operations
- ✅ Service dependencies
- ✅ Compliance audit trails

**Test Count**: 10 test scenarios, 30+ test cases

**Run**:
```bash
cd tests/integration
./run-integration-tests.sh
```

---

### 2. End-to-End Tests (`tests/e2e/`)
Complete workflow validation on Kubernetes.

**Scenarios**:
- ✅ Patient Admission Workflow (6-step process)
- ✅ FDA Device Compliance Workflow
- ✅ HIPAA Audit Trail Workflow
- ✅ High Availability & Failover
- ✅ Performance Baseline

**Test Count**: 5 workflows, 20+ test cases

**Run**:
```bash
cd tests/e2e
./run-e2e-tests.sh
```

**Prerequisites**:
- Kubernetes cluster (minikube, kind, GKE, EKS, AKS)
- kubectl configured
- Go 1.21+

---

### 3. Load/Performance Tests (`tests/load/`)
Scalability and performance validation using Locust.

**Load Test Scenarios**:
- **CompleteWorkflowUser**: Full healthcare workflow simulation
- **AuthServiceUser**: Authentication service load
- **PaymentGatewayUser**: Payment processing load
- **PHIServiceUser**: PHI encryption/decryption load
- **MedicalDeviceUser**: Device monitoring load
- **SyntheticPHIUser**: Synthetic data generation load

**Performance Targets**:
- Auth Service: 1,000+ concurrent users
- Payment Gateway: 500+ TPS
- PHI Service: 2,000+ encryption ops/sec
- Medical Device: 100 devices, 10K metrics/min
- Response Time: <100ms (p95)

**Run**:
```bash
cd tests/load
./run-load-tests.sh
```

**Configuration**:
```bash
# Custom load test
USERS=500 SPAWN_RATE=20 RUN_TIME=10m ./run-load-tests.sh
```

---

## 🚀 Quick Start

### 1. Run All Tests (Recommended)
```bash
make test-all
```

### 2. Run Integration Tests Only
```bash
make test-integration
```

### 3. Run E2E Tests Only
```bash
make test-e2e
```

### 4. Run Load Tests Only
```bash
make test-load
```

---

## 📊 Test Infrastructure

### Docker Compose Test Environment
**File**: `tests/integration/docker-compose.test.yml`

**Services**:
- OpenTelemetry Collector (distributed tracing)
- Prometheus (metrics collection)
- Auth Service (port 8080)
- Payment Gateway (port 8081)
- PHI Service (port 8083)
- Medical Device (port 8084)
- Synthetic PHI (port 8085)

### Kubernetes Test Environment
**Namespace**: `gitops2-e2e-test`

**Resources**:
- 5 Deployments (one per microservice)
- 5 Services (ClusterIP)
- ConfigMaps for configuration
- Secrets for sensitive data
- NetworkPolicies for zero-trust

---

## 🔧 Test Configuration

### Environment Variables

**Integration Tests**:
```bash
CLEANUP=false              # Skip cleanup after tests
TEST_TIMEOUT=300s         # Test timeout duration
```

**E2E Tests**:
```bash
TEST_NAMESPACE=my-test    # Kubernetes namespace
CLEANUP=false             # Skip Kubernetes cleanup
TEST_TIMEOUT=600s         # Test timeout
```

**Load Tests**:
```bash
USERS=100                 # Number of concurrent users
SPAWN_RATE=10            # Users spawned per second
RUN_TIME=5m              # Test duration
HOST=http://localhost:8080  # Target host
```

---

## 📈 Test Metrics

### Integration Test Metrics
- **Total Tests**: 30+ test cases
- **Coverage**: 10 integration scenarios
- **Services Tested**: 5 microservices
- **Expected Duration**: 2-3 minutes

### E2E Test Metrics
- **Total Workflows**: 5 complete workflows
- **Test Cases**: 20+ test cases
- **Deployment Time**: 5-10 minutes
- **Test Duration**: 3-5 minutes

### Load Test Metrics
- **User Scenarios**: 6 load test scenarios
- **Max Concurrent Users**: 1,000+
- **Test Duration**: 5-60 minutes (configurable)
- **Metrics Collected**: RPS, latency (p50, p95, p99), errors

---

## 🧪 Test Data Fixtures

### Synthetic Data Generation
All tests use the **Synthetic PHI Service** to generate realistic test data:

- Patient demographics (name, SSN, DOB, address)
- Medical device data
- Payment transactions
- Encrypted PHI

**No real patient data** is used in any test environment.

---

## 📝 Test Reports

### Integration Tests
- **Output**: Console output (verbose)
- **Format**: Go test format
- **Location**: Terminal output

### E2E Tests
- **Output**: Console output (verbose)
- **Format**: Go test format
- **Kubernetes Logs**: `kubectl logs -n gitops2-e2e-test <pod-name>`

### Load Tests
- **HTML Report**: `tests/load/load-test-report.html`
- **CSV Results**: `tests/load/load-test-results*.csv`
- **Metrics**: Requests/sec, response times, failure rates

---

## 🐛 Debugging Failed Tests

### Integration Test Failures
```bash
# View service logs
docker-compose -f tests/integration/docker-compose.test.yml logs <service-name>

# View all logs
docker-compose -f tests/integration/docker-compose.test.yml logs

# Keep environment running for debugging
CLEANUP=false ./tests/integration/run-integration-tests.sh
```

### E2E Test Failures
```bash
# View pod logs
kubectl logs -n gitops2-e2e-test <pod-name>

# Describe pod
kubectl describe pod -n gitops2-e2e-test <pod-name>

# Get all pods
kubectl get pods -n gitops2-e2e-test

# Keep environment running
CLEANUP=false ./tests/e2e/run-e2e-tests.sh
```

### Load Test Failures
```bash
# Check Locust logs
cat tests/load/locust.log

# View HTML report
open tests/load/load-test-report.html

# Check service health
curl http://localhost:8080/health
```

---

## 🔐 Security Testing

### Planned Security Tests (Section F - Future)
- OWASP ZAP vulnerability scanning
- SSL/TLS certificate validation
- JWT token security testing
- PHI encryption validation
- RBAC policy testing

---

## 🌀 Chaos Engineering

### Planned Chaos Tests (Section F - Future)
- Pod termination resilience
- Network partition tolerance
- Resource exhaustion scenarios
- Service degradation testing
- Cascading failure prevention

---

## 📚 Test Documentation

### Test Structure
```
tests/
├── integration/          # Docker Compose integration tests
│   ├── integration_test.go
│   ├── docker-compose.test.yml
│   ├── run-integration-tests.sh
│   ├── otel-collector-config.yaml
│   ├── prometheus.yml
│   └── go.mod
├── e2e/                 # Kubernetes E2E tests
│   ├── e2e_test.go
│   ├── run-e2e-tests.sh
│   └── go.mod
├── load/                # Locust load tests
│   ├── locustfile.py
│   └── run-load-tests.sh
└── README.md           # This file
```

---

## 🎯 Test Coverage Goals

| Service | Unit Tests | Integration | E2E | Load |
|---------|-----------|-------------|-----|------|
| Auth Service | ✅ 95% | ✅ | ✅ | ✅ |
| Payment Gateway | ✅ 95% | ✅ | ✅ | ✅ |
| PHI Service | ✅ 95% | ✅ | ✅ | ✅ |
| Medical Device | ✅ 95% | ✅ | ✅ | ✅ |
| Synthetic PHI | ✅ 95% | ✅ | ✅ | ✅ |

**Overall Coverage**: 95%+ across all services

---

## 🚦 CI/CD Integration

### GitHub Actions (Planned)
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Integration Tests
        run: make test-integration
  
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Kubernetes
        uses: helm/kind-action@v1
      - name: Run E2E Tests
        run: make test-e2e
```

---

## 📞 Support

For test-related issues:
1. Check test logs
2. Verify service health endpoints
3. Review Docker/Kubernetes resources
4. Check network connectivity
5. Validate test data fixtures

---

## 🏆 Test Quality Standards

- ✅ All tests must be **idempotent**
- ✅ Tests must clean up resources
- ✅ No hardcoded secrets or credentials
- ✅ Use synthetic data only
- ✅ Tests must be **deterministic**
- ✅ Proper error handling and logging
- ✅ Clear test naming and documentation

---

**Last Updated**: November 23, 2025  
**Version**: 1.0.0  
**Status**: Section F - Testing Suite (In Progress)
