# 🚀 START HERE - GitOps 2.0 Healthcare Intelligence Platform

> **Welcome!** This is your complete getting-started guide for the GitOps 2.0 Healthcare Intelligence Platform - an educational demonstration of AI-powered compliance automation for healthcare software development.

---

## ⚠️ Important: This is an Educational Platform

**Before you begin**, please understand:

- ✅ **Purpose**: Learning and demonstration of GitOps 2.0 concepts
- ✅ **What You'll Get**: Hands-on experience with AI-assisted healthcare compliance
- ⚠️ **Not For**: Production use without significant additional work
- 📚 **Best Use**: Educational projects, demos, portfolio, learning AI/compliance patterns

**See full disclaimer in [README.md](README.md)**

---

## 🎯 Quick Decision Guide

### **Choose Your Path:**

<table>
<tr>
<td width="50%">

### 👨‍💻 **I Want to Run the Demo** (5 min)
**Perfect for**: First-time users, quick demonstrations

**Go to**: [Quick Demo](#-5-minute-quick-demo)

</td>
<td width="50%">

### 🛠️ **I Want to Set Up Fully** (30 min)
**Perfect for**: Developers, learning the architecture

**Go to**: [Full Setup](#-30-minute-full-setup)

</td>
</tr>
<tr>
<td width="50%">

### 📖 **I Want to Understand It First**
**Perfect for**: Technical decision makers

**Go to**: [Platform Overview](#-platform-overview)

</td>
<td width="50%">

### 🔧 **I Want to Extend/Customize**
**Perfect for**: Contributors, advanced users

**Go to**: [Developer Guide](#-developer-guide)

</td>
</tr>
</table>

---

## ⚡ 5-Minute Quick Demo

**Goal**: See the platform in action without setup.

### Prerequisites
- Git installed
- Terminal/command line access

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# 2. Explore the documentation
cat README.md

# 3. View the architecture diagrams
open docs/GETTING_STARTED.md  # Opens in browser with Mermaid rendering

# 4. Check out sample policies
cat policies/healthcare/hipaa_phi_required.rego

# 5. Review AI commit generation tool
cat tools/git_copilot_commit.py
```

### What You'll See
- ✅ 3 production-grade Go microservices (Auth, Payment, PHI)
- ✅ 5 Open Policy Agent compliance policies (HIPAA, FDA, SOX)
- ✅ AI-powered commit message generator
- ✅ Intelligent Git bisect for root cause analysis
- ✅ Complete observability stack configuration

### Next Steps
- **Learn More**: Read [Platform Overview](#-platform-overview)
- **Try It Out**: Follow [Full Setup](#-30-minute-full-setup)
- **Deep Dive**: Explore [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)

---

## 🏗️ 30-Minute Full Setup

**Goal**: Get a working environment with all features enabled.

### Prerequisites Checklist

```bash
# Check your system has these installed:
go version      # Need 1.24+
python3 --version  # Need 3.11+
git --version   # Need 2.40+
docker --version   # Need 24.0+
```

**Don't have these?** See [Installation Guide](docs/GETTING_STARTED.md#prerequisites)

### Setup Steps

#### Step 1: Clone & Bootstrap (2 min)

```bash
# Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# Run automated setup
./setup.sh
```

**What `setup.sh` does:**
- Installs Python dependencies
- Builds all 3 Go microservices
- Installs Open Policy Agent CLI
- Configures Git hooks
- Creates `.env` file

#### Step 2: Configure API Keys (5 min)

```bash
# Get OpenAI API Key (required for AI features)
# Visit: https://platform.openai.com/api-keys

# Set environment variable
export OPENAI_API_KEY='sk-your-key-here'

# Or add to .env file for persistence
echo "OPENAI_API_KEY='sk-your-key-here'" >> .env
```

**Optional**: Azure Cosmos DB setup for database features
```bash
# Add to .env file
echo "AZURE_COSMOS_ENDPOINT='https://your-account.documents.azure.com:443/'" >> .env
echo "AZURE_COSMOS_KEY='your-key-here'" >> .env
```

#### Step 3: Verify Installation (2 min)

```bash
# Run quick test suite
./QUICK_TEST.sh
```

**Expected output:**
```
✅ Policy validation test passed
✅ AI commit generation test passed
✅ Intelligent bisect test passed
✅ Service build test passed
✅ Integration test passed
```

#### Step 4: Try the Core Workflows (20 min)

##### **Workflow 1: AI-Powered Commit Generation**

```bash
# Make a code change
echo "// Test comment" >> services/auth-service/main.go

# Generate AI commit message
python tools/git_copilot_commit.py --analyze

# Review and commit
git add services/auth-service/main.go
python tools/git_copilot_commit.py --auto-commit
```

##### **Workflow 2: Policy Validation**

```bash
# Validate last commit against policies
opa eval -d policies/healthcare/ \
  -i <(git show HEAD --format="%B" --no-patch) \
  "data.healthcare"
```

##### **Workflow 3: Start Microservices**

```bash
# Terminal 1: Auth Service
./bin/auth-service

# Terminal 2: Payment Gateway
./bin/payment-gateway

# Terminal 3: PHI Service
./bin/phi-service

# Test services
curl http://localhost:8080/health  # Auth Service
curl http://localhost:8081/health  # Payment Gateway
curl http://localhost:8082/health  # PHI Service
```

### 🎉 Success! You Now Have:
- ✅ 3 running microservices
- ✅ AI commit generation working
- ✅ Policy validation active
- ✅ Full development environment

### What's Next?
- **Learn the Architecture**: [Platform Overview](#-platform-overview)
- **Deep Dive**: [Complete Guide](docs/GETTING_STARTED.md)
- **API Reference**: [Quick Reference](docs/QUICK_REFERENCE.md)

---

## 📊 Platform Overview

### What This Platform Demonstrates

This is an **educational demonstration** of "GitOps 2.0" - the next evolution of GitOps enhanced with:

1. **AI-Powered Automation** - GPT-4 generates HIPAA-compliant commit messages
2. **Risk-Adaptive Policies** - OPA enforces healthcare regulations (HIPAA, FDA, SOX)
3. **Intelligent Incident Response** - AI-assisted root cause analysis
4. **Healthcare-Specific Patterns** - PHI handling, encryption, audit trails

### Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Workflow                        │
│  [Code Change] → [AI Commit] → [Policy Check] → [Deploy]   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              GitOps 2.0 Intelligence Layer                   │
│  • AI Commit Generator (OpenAI GPT-4)                       │
│  • Policy Engine (Open Policy Agent)                         │
│  • Intelligent Bisect (Root Cause Analysis)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  3 Core Microservices                        │
│  • Auth Service (:8080)     - JWT + MFA                     │
│  • Payment Gateway (:8081)  - PCI-DSS Compliant            │
│  • PHI Service (:8082)      - HIPAA Encryption             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  • Azure Cosmos DB (Patient Records)                         │
│  • Redis Cache (Session Store)                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **AI Commit Generation** | GPT-4 generates structured, compliant commit messages | ✅ Working |
| **Policy Enforcement** | OPA validates HIPAA, FDA, SOX requirements | ✅ Working |
| **3 Microservices** | Production-quality Go services with OpenAPI specs | ✅ Working |
| **Observability** | Prometheus + OpenTelemetry integration | ✅ Configured |
| **CI/CD Pipelines** | GitHub Actions workflows included | ✅ Included |
| **Infrastructure as Code** | Bicep + Terraform for Azure deployment | ✅ Included |

### Technology Stack

- **Languages**: Go 1.24+, Python 3.11+
- **AI/ML**: OpenAI GPT-4 API
- **Policy**: Open Policy Agent (OPA)
- **Observability**: Prometheus, OpenTelemetry
- **Cloud**: Azure (Cosmos DB, Container Apps)
- **CI/CD**: GitHub Actions

---

## 🔧 Developer Guide

### Project Structure

```
gitops2-healthcare-intelligence-git-commit/
├── services/                    # 3 Go microservices
│   ├── auth-service/           # Authentication + MFA
│   ├── payment-gateway/        # PCI-DSS compliant payments
│   └── phi-service/            # HIPAA-compliant PHI handling
├── policies/healthcare/        # OPA compliance policies
├── tools/                      # AI commit generation tools
├── tests/                      # Integration & E2E tests
├── infra/                      # Infrastructure as Code
├── docs/                       # Comprehensive documentation
└── observability/              # Monitoring configuration
```

### Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature

# 2. Make changes to code
# ... edit files ...

# 3. Generate AI commit
python tools/git_copilot_commit.py --analyze

# 4. Commit changes (triggers policy validation)
git commit -m "$(python tools/git_copilot_commit.py --generate-only)"

# 5. Run tests
make test

# 6. Build services
make build

# 7. Push changes
git push origin feature/your-feature
```

### Key Commands

```bash
# Build all services
make build

# Run all tests
make test

# Start all services
make run-all

# Run policy validation
make validate-policies

# Generate AI commit
make ai-commit

# Run full demo
./demo.sh
```

### VS Code Tasks

This project includes pre-configured VS Code tasks:

- **AI: Readiness Scan** - Check PHI compliance
- **Git: Forensics Report** - Generate impact analysis
- **Build: All Go Services** - Build all microservices
- **Demo: Full Live Demo** - Run complete demonstration

Press `Cmd+Shift+P` → "Tasks: Run Task" to access.

---

## 📚 Additional Resources

### Core Documentation

| Document | Purpose | Time |
|----------|---------|------|
| **[README.md](README.md)** | Project overview & features | 5 min |
| **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** | Detailed setup guide with diagrams | 30 min |
| **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** | API reference & command cheatsheet | 10 min |
| **[AZURE_COSMOS_DB.md](docs/AZURE_COSMOS_DB.md)** | Database integration guide | 15 min |

### Contributing & Support

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[SECURITY.md](SECURITY.md)** - Security policy & vulnerability reporting
- **[GitHub Issues](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues)** - Bug reports & feature requests

### External Resources

- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/)
- [Azure Cosmos DB Best Practices](https://learn.microsoft.com/azure/cosmos-db/)
- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa/index.html)
- [FDA 21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)

---

## 🎓 Learning Path

### Beginner (1-2 hours)
1. Read [README.md](README.md)
2. Run [5-Minute Quick Demo](#-5-minute-quick-demo)
3. Explore the code structure
4. Review sample policies

### Intermediate (4-6 hours)
1. Complete [Full Setup](#-30-minute-full-setup)
2. Run all 3 core workflows
3. Study [GETTING_STARTED.md](docs/GETTING_STARTED.md)
4. Experiment with AI commit generation
5. Modify policies and test

### Advanced (1-2 days)
1. Deep dive into service architecture
2. Implement custom policies
3. Extend AI commit features
4. Deploy to Azure
5. Contribute improvements

---

## 🤝 Getting Help

### Common Issues

<details>
<summary><b>❌ "OPENAI_API_KEY not set"</b></summary>

**Solution:**
```bash
export OPENAI_API_KEY='sk-your-key-here'
# Or add to .env file
echo "OPENAI_API_KEY='sk-your-key-here'" >> .env
```
</details>

<details>
<summary><b>❌ "Go build failed"</b></summary>

**Solution:**
```bash
# Check Go version (need 1.24+)
go version

# Clean and rebuild
cd services/auth-service
go clean
go mod tidy
go build
```
</details>

<details>
<summary><b>❌ "Policy validation failed"</b></summary>

**Solution:**
```bash
# Check OPA installation
opa version

# Validate policy syntax
opa test policies/healthcare/ -v
```
</details>

### Support Channels

- **Documentation**: Check [docs/](docs/) folder first
- **GitHub Issues**: [Open an issue](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/discussions)

---

## ✅ Quick Checklist

Before diving in, make sure you:

- [ ] Read the [educational disclaimer](README.md#-important-disclaimer)
- [ ] Have all [prerequisites installed](#prerequisites-checklist)
- [ ] Obtained an [OpenAI API key](https://platform.openai.com/api-keys)
- [ ] Cloned the repository
- [ ] Ran `./setup.sh` successfully
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Ran `./QUICK_TEST.sh` with passing tests

**All checked?** You're ready to go! 🎉

---

## 🚀 Ready to Start?

<div align="center">

### Choose Your Next Step:

**[📖 Read Full Guide](docs/GETTING_STARTED.md)** | **[⚡ Quick Demo](#-5-minute-quick-demo)** | **[🛠️ Full Setup](#-30-minute-full-setup)**

---

**Questions?** Check [docs/](docs/) or [open an issue](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues)

**Want to Contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)

**Security Concern?** See [SECURITY.md](SECURITY.md)

</div>

---

<div align="center">

**Built with ❤️ for the healthcare technology community**

[⭐ Star on GitHub](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit) | [🐛 Report Issue](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues) | [💬 Discuss](https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/discussions)

</div>
