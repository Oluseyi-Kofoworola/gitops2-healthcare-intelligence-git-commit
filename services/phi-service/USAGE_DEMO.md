# GitOps 2.0 Healthcare Intelligence Platform – PHI Encryption Service Demo

This service demonstrates:
- **Live PHI encryption/decryption** with real code and output
- **Defensive error handling** (invalid key, bad salt)
- **Policy-as-code, compliance, and risk automation** (see repo tools)
- **AI-powered commit metadata and audit trail** (see repo tools)
- **Forensics and incident response** (see repo tools)
- **Copilot integration and extensibility**

## Usage Stages

### 1. Live PHI Encryption/Decryption Demo
```
go run services/phi-service/encryption.go
```

### 2. Defensive Error Handling Demo
- Try invalid key or bad salt in code (see demoErrorHandling in main)

### 3. Policy-as-Code, Compliance, Audit, Forensics
- Make a code change, then run:
```
python3 tools/healthcare_commit_generator.py --type feat --scope phi --description "improve PHI encryption" --files services/phi-service/encryption.go
python3 tools/ai_compliance_framework.py analyze-commit HEAD
python3 tools/git_intel/risk_scorer.py --max-commits 1
python3 tools/intelligent_bisect.py --file services/phi-service/encryption.go
```

### 4. See README.md and DEMO_EVALUATION.md for full workflow and business value.

---

For more, see inline comments in `encryption.go` and the repo documentation.
