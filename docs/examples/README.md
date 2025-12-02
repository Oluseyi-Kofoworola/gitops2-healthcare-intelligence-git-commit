# Example Outputs

This directory contains real-world example outputs from the GitOps 2.0 Healthcare Intelligence platform tools.

## 📁 Files

### 1. `compliance_analysis_example.json`

**Tool**: `tools/ai_compliance_framework.py`

**Description**: Complete AI-powered compliance analysis for a payment gateway feature commit.

**Usage**:
```bash
# Generate similar output for your commits
python3 tools/ai_compliance_framework.py analyze-commit HEAD --json
```

**Key Sections**:
- HIPAA compliance validation (Privacy Rule, Security Rule, Breach Notification)
- FDA 21 CFR Part 11 validation (Electronic records, Change controls)
- SOX compliance validation (Section 404, Financial controls)
- AI hallucination detection results
- Deployment recommendations
- Evidence collection metadata

**Use Cases**:
- Audit trail documentation
- Compliance report templates
- Integration testing reference
- Stakeholder demonstrations

---

### 2. `risk_score_example.json`

**Tool**: `tools/git_intel/risk_scorer.py`

**Description**: Comprehensive risk assessment for a high-risk payment gateway fix.

**Usage**:
```bash
# Generate similar output for your commits
python3 tools/git_intel/risk_scorer.py --json
```

**Key Sections**:
- Overall risk score (0-100) and risk level classification
- Risk factor breakdown (semantic, path criticality, change magnitude, historical)
- Compliance impact assessment (HIPAA, FDA, SOX)
- Deployment strategy recommendation (Blue-Green, Canary, Rolling)
- Approval requirements and rollback plan
- Test coverage metrics
- Historical context and incident correlation
- AI-generated insights and recommendations

**Use Cases**:
- Deployment planning
- Risk management reporting
- Approval workflow configuration
- Post-incident analysis

---

### 3. `incident_report_example.md`

**Tool**: `scripts/intelligent-bisect.sh`

**Description**: Complete incident report from automated root cause analysis and resolution.

**Usage**:
```bash
# Generate similar output for incident response
./scripts/intelligent-bisect.sh \
  --start-commit <good-commit> \
  --end-commit <bad-commit> \
  --metric payment_processing_latency_p95 \
  --threshold 200 \
  --service payment-gateway
```

**Key Sections**:
- Executive summary with MTTR metrics
- Detailed timeline of incident detection and resolution
- Intelligent bisect execution logs
- AI-powered root cause analysis
- Automated rollback execution
- Compliance evidence collection (SOX, HIPAA, FDA)
- Business impact assessment
- Lessons learned and action items

**Use Cases**:
- Incident postmortems
- SOX/HIPAA audit evidence
- SRE team training
- Executive reporting
- Process improvement planning

---

## 🎯 How to Use These Examples

### For Developers

```bash
# 1. Generate a compliant commit
python3 tools/healthcare_commit_generator.py \
  --type feat \
  --scope payment \
  --description "your feature description"

# 2. Analyze compliance
python3 tools/ai_compliance_framework.py analyze-commit HEAD --json

# 3. Check risk score
python3 tools/git_intel/risk_scorer.py --json

# Compare your output with examples in this directory
```

### For Compliance Officers

Use these examples to understand:
- What evidence is automatically collected
- How compliance codes are validated
- Where audit trails are stored
- How to generate compliance reports

### For SRE/DevOps Teams

Use these examples to:
- Configure deployment strategies based on risk scores
- Set up automated incident response workflows
- Design rollback triggers and validation criteria
- Plan capacity and performance testing

### For Executives

Use these examples to demonstrate:
- Automated compliance capabilities
- Time and cost savings
- Incident response effectiveness
- Audit readiness

---

## 🔄 Generating Your Own Examples

### Full End-to-End Demo

Run the complete healthcare demo to generate real outputs:

```bash
# Run the 10-minute demonstration
./healthcare-demo.sh

# This will generate:
# - Compliant commits
# - Compliance analysis reports
# - Risk assessments
# - Deployment logs
# - Incident response simulations
```

### Individual Tool Examples

```bash
# Example 1: Compliance Analysis
python3 tools/ai_compliance_framework.py analyze-commit HEAD --json > my_compliance_report.json

# Example 2: Risk Scoring
python3 tools/git_intel/risk_scorer.py --json > my_risk_assessment.json

# Example 3: Load Testing
python3 tools/load_testing.py > my_load_test_report.md

# Example 4: Secret Detection
python3 -c "
from tools.secret_sanitizer import SecretSanitizer
sanitizer = SecretSanitizer()
result = sanitizer.scan_file('path/to/file.py')
print(result)
"
```

---

## 📊 Expected Outputs

### Compliance Analysis (`compliance_analysis_example.json`)

```json
{
  "compliance_status": "COMPLIANT",
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "analysis": {
    "hipaa": { "status": "COMPLIANT", "evidence": [...] },
    "fda": { "status": "COMPLIANT", "evidence": [...] },
    "sox": { "status": "COMPLIANT", "evidence": [...] }
  },
  "deployment_recommendation": {
    "strategy": "CANARY",
    "rollout_plan": {...}
  }
}
```

### Risk Score (`risk_score_example.json`)

```json
{
  "overall_risk_score": 78,
  "risk_level": "HIGH",
  "risk_factors": {
    "semantic_risk": { "score": 85, "weight": 0.4 },
    "path_criticality": { "score": 90, "weight": 0.3 },
    "change_magnitude": { "score": 65, "weight": 0.2 },
    "historical_patterns": { "score": 55, "weight": 0.1 }
  },
  "deployment_strategy": {
    "recommended_strategy": "BLUE_GREEN",
    "approval_required": true
  }
}
```

### Incident Report (`incident_report_example.md`)

```markdown
# Incident Report: Payment Processing Latency Spike

**MTTR**: 27 minutes 25 seconds
**Root Cause**: Database connection pool misconfiguration
**Resolution**: Automated rollback to last known good commit
**Business Impact**: None (caught before customer exposure)
```

---

## 🔗 Related Documentation

- [End-to-End Scenario](../SCENARIO_END_TO_END.md) - Complete workflow walkthrough
- [Enterprise Readiness](../ENTERPRISE_READINESS.md) - Safety and security features
- [Engineering Journal](../../ENGINEERING_JOURNAL.md) - Infrastructure and CI/CD history
- [Compliance Journal](../../COMPLIANCE_AND_SECURITY_JOURNAL.md) - Security decisions

---

## 🤝 Contributing

To add new examples:

1. Run the tool with real or test data
2. Sanitize any sensitive information (no real PHI, credentials, etc.)
3. Add descriptive filename: `<tool_name>_example_<scenario>.json`
4. Update this README with description and usage
5. Submit PR with example and documentation

---

## 📜 License

These examples are provided under the same MIT license as the main repository.

---

**Last Updated**: November 22, 2025  
**Maintained By**: GitOps 2.0 Healthcare Intelligence Team
