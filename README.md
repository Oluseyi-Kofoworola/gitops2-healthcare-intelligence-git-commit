# Healthcare Intelligence Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Compliance](https://img.shields.io/badge/Compliance-HIPAA%20|%20FDA%20|%20SOX-green)](#compliance)

A clean, production-ready healthcare compliance platform that automates HIPAA, FDA, and SOX compliance through AI-powered tooling.

## Core Features

- **🔐 PHI Encryption**: Secure AES-256-GCM encryption for healthcare data
- **📋 Compliance Automation**: Real-time HIPAA/FDA/SOX validation
- **🤖 AI-Powered Commits**: Generate compliant commit messages with audit metadata
- **🛡️ Policy Enforcement**: Automated policy-as-code validation using OPA

## Quick Start (5 minutes)

```bash
# Setup
make setup

# Run PHI encryption demo
make demo

# Generate compliant commit
python3 tools/healthcare_commit_generator.py \
  --type feat --scope phi \
  --description "add encryption validation" \
  --files services/phi-service/encryption.go

# Check compliance
python3 tools/ai_compliance_framework.py analyze-commit HEAD
```

## Core Services

- **PHI Service** (`services/phi-service/`): Secure PHI encryption and validation
- **Auth Service** (`services/auth-service/`): Authentication and authorization
- **Payment Gateway** (`services/payment-gateway/`): PCI-compliant payments
- **Medical Device** (`services/medical-device/`): FDA device integration

## Core Tools

- **Commit Generator** (`tools/healthcare_commit_generator.py`): AI-powered commits
- **Compliance Framework** (`tools/ai_compliance_framework.py`): Real-time validation
- **Risk Scorer** (`tools/git_intel/risk_scorer.py`): Risk assessment

## Compliance Features

- ✅ **HIPAA**: PHI encryption, access logging, audit trails
- ✅ **FDA**: Device validation, change control, traceability  
- ✅ **SOX**: Financial controls, segregation of duties, audit logs

## Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - 5-minute setup guide
- **[Compliance Guide](docs/COMPLIANCE_GUIDE.md)** - Regulatory requirements
- **[Engineering Guide](docs/ENGINEERING_GUIDE.md)** - Architecture and development

## License

MIT License - see [LICENSE](LICENSE) file.
