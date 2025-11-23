# Documentation Index

**Complete documentation for GitOps 2.0 Healthcare Intelligence Platform**

---

## 🚀 Getting Started

Start here if you're new to the platform:

### Quick Start (5 minutes)
- **[START_HERE.md](../START_HERE.md)** - Fastest path to running your first demo
- Run: `./scripts/demo.sh --quick`

### Complete Setup (15 minutes)
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Full installation and configuration guide
- Covers: Prerequisites, installation, service setup, validation, first workflow

---

## 📖 Core Documentation

### End-to-End Workflows
- **[SCENARIO_END_TO_END.md](SCENARIO_END_TO_END.md)** - Complete walkthrough of all three flagship flows
  - Flow 1: AI-assisted healthcare commits
  - Flow 2: Policy-as-code + risk gates  
  - Flow 3: Intelligent forensics (bonus)
  - Includes: Business metrics, compliance evidence, incident simulation

### Deployment
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Production deployment guide
  - Local development (Docker Compose)
  - Kubernetes deployment (Kind, Minikube, EKS, AKS, GKE)
  - Service mesh (Istio)
  - Certificate management (cert-manager)
  - ArgoCD GitOps setup
  - Monitoring and alerting

### Compliance & Security
- **[COMPLIANCE_GUIDE.md](COMPLIANCE_GUIDE.md)** - Healthcare compliance reference
  - HIPAA requirements and implementation
  - FDA 21 CFR Part 11 validation
  - SOX financial controls
  - Policy customization
  - Evidence collection

### AI Tools
- **[AI_TOOLS_REFERENCE.md](AI_TOOLS_REFERENCE.md)** - AI features documentation
  - Healthcare commit generator
  - Compliance validation framework
  - Risk scoring engine
  - Intelligent bisect for incident response
  - Configuration and customization

### CI/CD Automation
- **[CI_CD_AUTOMATION_GUIDE.md](CI_CD_AUTOMATION_GUIDE.md)** - GitHub Actions integration
  - Workflow setup and configuration
  - Risk-adaptive deployment strategies
  - Compliance gates in CI/CD
  - Automated testing pipelines

### Architecture
- **[ENGINEERING_GUIDE.md](ENGINEERING_GUIDE.md)** - Technical deep-dive
  - System architecture
  - Design patterns
  - Service interactions
  - Technology stack
  - Best practices

---

## 🔧 Technical References

### Services
Each service has detailed README documentation:

- **[Auth Service](../services/auth-service/README.md)** - JWT authentication with RBAC
- **[Payment Gateway](../services/payment-gateway/README.md)** - SOX-compliant payment processing
- **[PHI Service](../services/phi-service/README.md)** - HIPAA-compliant encryption
- **[Medical Device](../services/medical-device/README.md)** - FDA 21 CFR Part 11 compliance
- **[Synthetic PHI](../services/synthetic-phi-service/README.md)** - HIPAA-compliant test data generation

### Testing
- **[Test Suite Overview](../tests/README.md)** - Complete testing documentation
  - Unit tests (95%+ coverage)
  - Integration tests (Docker Compose)
  - E2E tests (Kubernetes)
  - Contract tests (Pact)
  - Load tests (Locust)
  - Chaos engineering (Chaos Mesh)
  - Security testing (OWASP ZAP)

---

## 🎯 Quick Navigation by Role

### For Developers
1. [GETTING_STARTED.md](GETTING_STARTED.md) - Setup your environment
2. [SCENARIO_END_TO_END.md](SCENARIO_END_TO_END.md) - Learn the workflows
3. [AI_TOOLS_REFERENCE.md](AI_TOOLS_REFERENCE.md) - Use AI features
4. Service READMEs - Understand microservices
5. [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribute code

### For DevOps/Platform Engineers
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deploy to production
2. [CI_CD_AUTOMATION_GUIDE.md](CI_CD_AUTOMATION_GUIDE.md) - Setup CI/CD
3. [ENGINEERING_GUIDE.md](ENGINEERING_GUIDE.md) - Architecture details
4. [Test Suite](../tests/README.md) - Testing infrastructure

### For Compliance Officers
1. [COMPLIANCE_GUIDE.md](COMPLIANCE_GUIDE.md) - Framework mappings
2. [SCENARIO_END_TO_END.md](SCENARIO_END_TO_END.md) - Evidence collection
3. [AI_TOOLS_REFERENCE.md](AI_TOOLS_REFERENCE.md) - Validation automation
4. [Security Testing](../tests/security/) - Security controls

---

## 📝 Examples & Templates

See **[examples/](examples/)** for:
- Compliance analysis JSON examples
- Risk score calculations
- Incident report templates
- CI/CD log samples

---

## ❓ Need Help?

- **Issues**: [GitHub Issues](https://github.com/your-org/gitops2-healthcare-intelligence/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/gitops2-healthcare-intelligence/discussions)
- **Security**: See [SECURITY.md](../SECURITY.md) for vulnerability reporting

---

**Last Updated**: November 23, 2025  
**Version**: 2.0  
**License**: MIT
