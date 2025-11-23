# Getting Started with GitOps 2.0 Healthcare Intelligence

**Complete setup guide from zero to running demos in 15 minutes**

---

## 📋 Prerequisites

### Required Software
- **Git** 2.30+
- **Python** 3.9+
- **Go** 1.21+
- **Docker** 20.10+
- **kubectl** 1.28+ (for Kubernetes demos)
- **OpenAI API Key** (for AI features)

### Optional Tools
- **Kind** or **Minikube** (for local Kubernetes)
- **OPA** (Open Policy Agent CLI)
- **jq** (JSON processing)
- **Locust** (load testing)

### Verify Prerequisites

```bash
# Check versions
git --version        # Should be 2.30+
python3 --version    # Should be 3.9+
go version          # Should be 1.21+
docker --version    # Should be 20.10+
kubectl version     # Should be 1.28+
```

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/gitops2-enterprise-git-intel-demo.git
cd gitops2-enterprise-git-intel-demo
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r pyproject.toml

# Install Go dependencies
go mod download

# Install Node dependencies (for commit linting)
npm install
```

### Step 3: Configure Environment

```bash
# Copy example config
cp config/gitops-health.example.yml config/gitops-health.yml

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Or create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Step 4: Run Quick Demo

```bash
./scripts/demo.sh --quick
```

**You're done!** 🎉 You've just run your first AI-assisted healthcare compliance workflow.

---

## 🏥 Full Setup (15 Minutes)

### 1. Environment Setup

#### Set Up Git Hooks (Optional but Recommended)

```bash
# Install pre-commit hooks for automatic validation
./scripts/setup/setup-git-aliases.sh

# This enables:
# - Automatic secret detection
# - PHI pattern detection
# - Compliance code validation
# - Commit message linting
```

#### Configure AI Compliance Framework

```bash
# Edit config/gitops-health.yml
vi config/gitops-health.yml
```

**Key configurations**:
```yaml
ai:
  model: "gpt-4"  # or "gpt-3.5-turbo" for faster/cheaper
  temperature: 0.3
  max_tokens: 2000

compliance:
  frameworks:
    - HIPAA
    - FDA_21CFR11
    - SOX
  require_evidence: true
  
risk_scoring:
  thresholds:
    low: 30
    medium: 60
    high: 85
```

### 2. Service Setup

#### Option A: Docker Compose (Recommended for demos)

```bash
# Start all services
cd tests/integration
docker-compose up -d

# Verify services
curl http://localhost:8081/health  # Auth Service
curl http://localhost:8080/health  # Payment Gateway
curl http://localhost:8082/health  # PHI Service
curl http://localhost:8083/health  # Medical Device
curl http://localhost:8084/health  # Synthetic PHI
```

#### Option B: Kubernetes (Production-like)

```bash
# Create local cluster
kind create cluster --name gitops2-demo

# Deploy services
kubectl apply -f k8s/namespaces/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/

# Wait for ready
kubectl wait --for=condition=ready pod --all -n healthcare --timeout=300s

# Port forward for access
kubectl port-forward -n healthcare svc/auth-service 8081:8080 &
kubectl port-forward -n healthcare svc/payment-gateway 8080:8080 &
kubectl port-forward -n healthcare svc/phi-service 8082:8080 &
```

### 3. Verify Installation

```bash
# Run validation script
./scripts/validation/final-validation.sh

# Expected output:
# ✓ Python dependencies installed
# ✓ Go dependencies installed
# ✓ Docker running
# ✓ Services healthy
# ✓ OPA policies valid
# ✓ Config file present
```

---

## 🎯 Run Your First Workflow

### Scenario: Add Payment Encryption Feature

#### Step 1: Generate Compliant Commit

```bash
python3 tools/healthcare_commit_generator.py \
  --type feat \
  --scope payment \
  --description "implement AES-256 encryption for payment tokens" \
  --compliance "SOX-404,PCI-DSS-3.2.1" \
  --clinical-impact NONE \
  --files "payment_gateway.go,encryption.go,tests.go"
```

**Output**: Generates a HIPAA/SOX-compliant commit message with metadata

#### Step 2: Validate Compliance

```bash
# Run AI compliance analysis
python3 tools/ai_compliance_framework.py analyze-commit HEAD --json

# Output: Compliance status, risk score, framework validation
```

#### Step 3: Check Policies

```bash
# Run OPA policy tests
cd policies/healthcare
opa test . --verbose

# Output: 12/12 policies passed
```

#### Step 4: Calculate Risk

```bash
# Generate risk score
python3 tools/git_intel/risk_scorer.py --json

# Output: Risk score (0-100) and recommended deployment strategy
```

---

## 📚 Available Demos

### 1. Quick Demo (5 minutes)
```bash
./scripts/demo.sh --quick
```
- AI-assisted commit generation
- Compliance validation
- Policy enforcement

### 2. Healthcare Demo (15 minutes)
```bash
./scripts/demo.sh --healthcare
```
- Complete HIPAA/FDA/SOX workflow
- Risk assessment
- Evidence collection

### 3. Executive Demo (30 minutes)
```bash
./scripts/demo.sh --executive
```
- Business value demonstration
- ROI calculation
- Time savings metrics

### 4. Run All Demos
```bash
./scripts/demo.sh --all
```

---

## 🧪 Run Tests

### Unit Tests
```bash
# Test all services
cd tests
make test-unit

# Test specific service
cd services/auth-service
go test -v ./...
```

### Integration Tests
```bash
cd tests
make test-integration

# Or manually
cd tests/integration
docker-compose up -d
go test -v ./...
```

### End-to-End Tests
```bash
cd tests
make test-e2e

# Or with Kubernetes
cd tests/e2e
./run-e2e-tests.sh
```

### Load Tests
```bash
cd tests/load
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --host http://localhost:8080
```

### Security Tests
```bash
cd tests/security
./run-security-tests.sh --all
```

### Chaos Tests
```bash
cd tests/chaos
./run-chaos-tests.sh --all
```

---

## 🛠️ Development Workflow

### Create a Feature Branch

```bash
git checkout -b feat/payment-encryption
```

### Make Changes

```bash
# Edit code
vi services/payment-gateway/encryption.go

# Write tests
vi services/payment-gateway/encryption_test.go

# Run tests
go test -v ./...
```

### Generate Compliant Commit

```bash
# Use AI assistant
python3 tools/healthcare_commit_generator.py \
  --type feat \
  --scope payment \
  --description "your feature description" \
  --compliance "HIPAA-164.312(e)(1),SOX-404" \
  --clinical-impact LOW \
  --files "encryption.go,tests.go"

# Copy generated commit message
# Commit your changes
git add .
git commit -F /tmp/commit_message.txt
```

### Validate Before Push

```bash
# Run all checks
./scripts/validation/validate-code-quality.sh

# Run compliance check
python3 tools/ai_compliance_framework.py analyze-commit HEAD

# Run policy tests
opa test policies/healthcare/ --verbose
```

### Push and Create PR

```bash
git push origin feat/payment-encryption

# Create pull request
# CI/CD will automatically:
# - Run all tests
# - Validate compliance
# - Calculate risk score
# - Generate deployment strategy
```

---

## 🔧 Troubleshooting

### Issue: OpenAI API Errors

```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# If using Azure OpenAI
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_KEY="your-key"
```

### Issue: Services Not Starting

```bash
# Check Docker
docker ps
docker-compose ps

# View logs
docker-compose logs auth-service
docker-compose logs payment-gateway

# Restart services
docker-compose restart
```

### Issue: OPA Policy Failures

```bash
# Validate policy syntax
opa check policies/healthcare/*.rego

# Run specific test
opa test policies/healthcare/hipaa.rego --verbose

# Debug policy
opa eval -d policies/healthcare/ -i input.json "data.healthcare.allow"
```

### Issue: Port Already in Use

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different ports
docker-compose -f docker-compose.test.yml up -d
```

---

## 📖 Next Steps

### Learn More
- **[Complete Walkthrough](SCENARIO_END_TO_END.md)** - Full end-to-end scenario
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Compliance Guide](COMPLIANCE_GUIDE.md)** - HIPAA/FDA/SOX reference
- **[AI Tools Reference](AI_TOOLS_REFERENCE.md)** - AI features documentation

### Explore Services
- **[Auth Service](../services/auth-service/)** - JWT authentication
- **[Payment Gateway](../services/payment-gateway/)** - SOX-compliant payments
- **[PHI Service](../services/phi-service/)** - HIPAA encryption
- **[Medical Device](../services/medical-device/)** - FDA compliance
- **[Synthetic PHI](../services/synthetic-phi-service/)** - Test data generation

### Customize for Your Organization
1. **Update OPA policies** in `policies/healthcare/`
2. **Configure risk thresholds** in `config/gitops-health.yml`
3. **Add custom compliance codes** to whitelists
4. **Integrate with your CI/CD** pipeline
5. **Configure evidence storage** (S3, Azure Blob, etc.)

---

## 🤝 Contributing

See **[CONTRIBUTING.md](../CONTRIBUTING.md)** for:
- Code style guidelines
- Commit conventions
- Pull request process
- Development setup

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/gitops2-enterprise-git-intel-demo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/gitops2-enterprise-git-intel-demo/discussions)
- **Documentation**: [docs/](.)
- **Security**: See [SECURITY.md](../SECURITY.md)

---

## ✅ Checklist

Use this checklist to track your setup:

- [ ] Prerequisites installed (Git, Python, Go, Docker)
- [ ] Repository cloned
- [ ] Dependencies installed (`pip`, `go mod`, `npm`)
- [ ] OpenAI API key configured
- [ ] Config file created (`config/gitops-health.yml`)
- [ ] Services running (Docker Compose or Kubernetes)
- [ ] Quick demo completed (`./scripts/demo.sh --quick`)
- [ ] Tests passing (`make test`)
- [ ] First compliant commit generated
- [ ] Documentation reviewed

**Ready to go!** 🚀

---

**Last Updated**: November 23, 2025  
**Version**: 2.0  
**License**: MIT
