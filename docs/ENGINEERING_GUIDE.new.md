# Engineering Guide - GitOps 2.0 Healthcare Intelligence

**Last Updated**: November 23, 2025  
**Version**: 2.0.0  
**Audience**: Platform Engineers, DevOps, Backend Developers

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Deep Dive](#component-deep-dive)
3. [Data Flow](#data-flow)
4. [Integration Patterns](#integration-patterns)
5. [Service Details](#service-details)
6. [CI/CD Pipeline Architecture](#cicd-pipeline-architecture)
7. [Observability & Monitoring](#observability--monitoring)
8. [Security Boundaries](#security-boundaries)
9. [Development Workflow](#development-workflow)
10. [Deployment Patterns](#deployment-patterns)

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Systems                            │
├─────────────────────────────────────────────────────────────────┤
│  • GitHub (SCM, Actions)                                        │
│  • OpenAI API / LLM Provider (AI agents)                        │
│  • Docker Registry                                              │
│  • Kubernetes Cluster (deployment target)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              GitOps 2.0 Healthcare Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐        │
│  │ AI Agents   │  │ Policy Engine│  │ Microservices  │        │
│  │ Layer       │  │ (OPA)        │  │ Layer          │        │
│  └─────────────┘  └──────────────┘  └────────────────┘        │
│         ↓                ↓                    ↓                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │           CI/CD Orchestration Layer                 │       │
│  │  (GitHub Actions + Risk-Adaptive Logic)             │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Logical Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   Developer Interface Layer                      │
├──────────────────────────────────────────────────────────────────┤
│  • Git CLI / GitHub UI                                           │
│  • gitops-health CLI (Python)                                    │
│  • GitHub Copilot (VS Code extension)                            │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   Intelligence Layer (AI Agents)                 │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐              │
│  │ Commit Gen  │  │ Risk Scorer │  │ Compliance │              │
│  │             │  │             │  │ Checker    │              │
│  └─────────────┘  └─────────────┘  └────────────┘              │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Forensics   │  │ Audit Export│                               │
│  │ (Bisect)    │  │             │                               │
│  └─────────────┘  └─────────────┘                               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   Policy Enforcement Layer                       │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPA (Open Policy Agent)                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │ │
│  │  │  HIPAA   │  │   FDA    │  │   SOX    │                 │ │
│  │  │  Rules   │  │  Rules   │  │  Rules   │                 │ │
│  │  └──────────┘  └──────────┘  └──────────┘                 │ │
│  │  ┌──────────┐  ┌──────────┐                                │ │
│  │  │   Risk   │  │ Metadata │                                │ │
│  │  │ Policies │  │Validation│                                │ │
│  │  └──────────┘  └──────────┘                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   CI/CD Orchestration Layer                      │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  GitHub Actions Workflows                                   ││
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐    ││
│  │  │ Risk-Adaptive│  │ Compliance    │  │ Security     │    ││
│  │  │ CI Pipeline  │  │ Gate          │  │ Scan         │    ││
│  │  └──────────────┘  └───────────────┘  └──────────────┘    ││
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐    ││
│  │  │ Deploy Canary│  │ Deploy        │  │ Rollback     │    ││
│  │  │              │  │ Blue-Green    │  │              │    ││
│  │  └──────────────┘  └───────────────┘  └──────────────┘    ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                   Application Services Layer                     │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ auth-service │  │ payment-gw   │  │ phi-service  │          │
│  │ (Go)         │  │ (Go)         │  │ (Go)         │          │
│  │              │  │              │  │              │          │
│  │ HIPAA Access │  │ SOX Financial│  │ PHI Storage  │          │
│  │ Controls     │  │ Controls     │  │ & Encryption │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │medical-device│  │synthetic-phi │                             │
│  │ (Go)         │  │ (Go)         │                             │
│  │              │  │              │                             │
│  │ FDA Device   │  │ Test Data    │                             │
│  │ Controls     │  │ Generation   │                             │
│  └──────────────┘  └──────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. AI Agents (Intelligence Layer)

#### Commit Generator (`tools/gitops_health/commitgen.py`)

**Purpose**: Generate healthcare-compliant commit messages with regulatory metadata.

**Inputs**:
- Change type (`feat`, `fix`, `security`, etc.)
- Scope (service or domain, e.g., `phi`, `payment`)
- Description (natural language)
- Changed files list

**Processing**:
1. Analyze changed files to detect PHI, financial, or device code
2. Call LLM (GPT-4 or configured model) with healthcare context
3. Generate conventional commit format with compliance metadata
4. Validate against OPA policies before returning

**Outputs**:
```json
{
  "commit_message": "security(phi): implement AES-256 encryption for patient records\n\nBusiness Impact: ...\n\nhipaa: 164.312(a)(2)(iv)\nphi-impact: high\nfda-510k: FDA-SOFTWARE",
  "risk_score": 75,
  "suggested_reviewers": ["@privacy-officer", "@security-team"],
  "compliance_frameworks": ["HIPAA", "FDA"]
}
```

**Configuration**: `gitops_health.yml`
```yaml
commit_generator:
  llm_provider: openai  # or anthropic, google
  model: gpt-4
  temperature: 0.3
  max_tokens: 500
```

#### Risk Scorer (`tools/gitops_health/risk.py`)

**Purpose**: Assess change risk based on multiple factors.

**Risk Calculation Algorithm**:
```python
risk_score = (
    semantic_risk * 0.3 +      # Type: security=high, docs=low
    domain_risk * 0.3 +         # Domain: phi=high, config=low
    file_criticality * 0.2 +    # Files: payment-gw/auth.go=critical
    change_size * 0.1 +         # Lines changed
    historical_risk * 0.1       # Past issues in these files
)
```

**Risk Levels**:
- **0-30**: Low (rolling update)
- **30-70**: Medium (canary deployment)
- **70-90**: High (blue-green + approval)
- **90-100**: Critical (dual approval + manual)

**Output Schema**:
```json
{
  "risk_score": 75,
  "risk_level": "high",
  "factors": {
    "semantic_risk": 80,
    "domain_risk": 90,
    "file_criticality": 70,
    "change_size": 40,
    "historical_risk": 60
  },
  "deployment_strategy": "blue-green",
  "approval_required": true,
  "approvers": ["@infra-lead"]
}
```

#### Compliance Checker (`tools/gitops_health/compliance.py`)

**Purpose**: Validate commits against OPA healthcare policies.

**Validation Flow**:
```
1. Extract commit metadata (message, files, author)
2. Build OPA input JSON
3. Evaluate against policies:
   - data.enterprise.git.allow (main allow rule)
   - data.enterprise.git.deny (violation messages)
4. Return pass/fail + violation details
```

**Integration Points**:
- Git hooks (`.husky/commit-msg`)
- GitHub Actions (`compliance-gate.yml`)
- CLI (`gitops-health compliance analyze`)

#### Intelligent Bisect (`tools/gitops_health/forensics.py`)

**Purpose**: AI-assisted git bisect for regression detection.

**Features**:
- Automated good/bad commit identification
- Metric-based regression detection (latency, error rate)
- Patient safety impact analysis
- Incident report generation

**Usage**:
```bash
gitops-health forensics bisect \
  --metric latency \
  --threshold 200 \
  --start HEAD~20 \
  --end HEAD
```

---

### 2. Policy Engine (OPA)

#### Policy Structure

```
policies/
├── enterprise-commit.rego       # Main commit validation
├── enterprise-commit_test.rego  # Policy tests
└── healthcare/
    ├── commit_metadata_required.rego
    ├── high_risk_dual_approval.rego
    ├── hipaa_phi_required.rego
    ├── valid_compliance_codes.rego
    └── valid_compliance_codes_test.rego
```

#### Key Policy Rules

**1. HIPAA PHI Protection** (`hipaa_phi_required.rego`):
```rego
# Require HIPAA metadata for PHI-touching commits
deny[reason] if {
  some c in input.commits
  touches_phi_code(c)
  not has_hipaa_metadata(c)
  reason := sprintf("Commit %s touches PHI code without HIPAA metadata", [c.sha])
}

touches_phi_code(c) if {
  some file in c.changed_files
  contains(file, "phi-service/")
}
```

**2. FDA Medical Device Controls**:
```rego
deny[reason] if {
  some c in input.commits
  touches_device_code(c)
  not has_fda_metadata(c)
  reason := sprintf("Commit %s touches device code without FDA-510k metadata", [c.sha])
}
```

**3. High-Risk Dual Approval**:
```rego
deny[reason] if {
  some c in input.commits
  multi_domain_high_risk(c)
  not has_dual_approval(c)
  reason := sprintf("Commit %s requires dual approval", [c.sha])
}
```

#### OPA Testing

```bash
# Run all policy tests
opa test policies/ --verbose

# Test specific policy
opa test policies/healthcare/hipaa_phi_required.rego

# Evaluate commit against policies
echo '{"commits":[{"sha":"abc123","message":"fix: update","changed_files":["phi-service/patient.go"]}]}' | \
  opa eval -d policies/ 'data.enterprise.git.allow' -i -
```

---

### 3. Microservices

#### Service Responsibilities

| Service | Compliance | Responsibilities | Port |
|---------|-----------|------------------|------|
| **auth-service** | HIPAA | Authentication, authorization, access logging | 8081 |
| **payment-gateway** | SOX | Payment processing, financial audit trail | 8080 |
| **phi-service** | HIPAA | PHI storage, encryption, access control | 8082 |
| **medical-device** | FDA | Device data collection, telemetry | 8083 |
| **synthetic-phi-service** | N/A | Test data generation (no real PHI) | 8084 |

#### PHI Boundaries

```
┌─────────────────────────────────────────┐
│     Public Zone (No PHI)                │
│  • medical-device (telemetry only)      │
│  • synthetic-phi-service (fake data)    │
└─────────────────────────────────────────┘
              ↓ TLS + Auth
┌─────────────────────────────────────────┐
│     Protected Zone (PHI Access)         │
│  • auth-service (authenticates)         │
│  • payment-gateway (billing w/ PHI)     │
│  • phi-service (stores encrypted PHI)   │
│                                         │
│  Requirements:                          │
│  • TLS 1.3+ encryption in transit       │
│  • AES-256-GCM encryption at rest       │
│  • Audit all access                     │
│  • Role-based access control (RBAC)     │
└─────────────────────────────────────────┘
```

#### Service Template (auth-service example)

**File**: `services/auth-service/main.go`

```go
package main

import (
    "context"
    "log"
    "net/http"
    
    "github.com/prometheus/client_golang/prometheus"
    "go.opentelemetry.io/otel/trace"
)

// Observability hooks (placeholder - needs full implementation)
var (
    requestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "auth_request_duration_seconds",
            Help: "Request duration in seconds",
        },
        []string{"method", "endpoint", "status"},
    )
)

// PHI-aware logging (structured with correlation IDs)
func logAccess(ctx context.Context, userID, resource string) {
    traceID := trace.SpanFromContext(ctx).SpanContext().TraceID().String()
    
    log.Printf(`{"timestamp":"%s","level":"INFO","service":"auth","action":"access","trace_id":"%s","user_id":"%s","resource":"%s","phi_access":true}`,
        time.Now().Format(time.RFC3339), traceID, userID, resource)
}

// Handler with observability
func AuthHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    timer := prometheus.NewTimer(requestDuration.WithLabelValues(r.Method, r.URL.Path, "200"))
    defer timer.ObserveDuration()
    
    // Extract trace context
    span := trace.SpanFromContext(ctx)
    span.SetAttributes(attribute.String("service", "auth"))
    
    // HIPAA-compliant authentication logic
    // ...
    
    logAccess(ctx, userID, resource)
}
```

**Current Status**: Basic structure exists, needs full observability implementation.

---

## Data Flow

### End-to-End Commit Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ STEP 1: Developer Makes Changes                                  │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Edit: services/phi-service/encryption.go (PHI code)
    ├─ Stage: git add services/phi-service/encryption.go
    │
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 2: AI Commit Generation (Optional)                          │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Command: gitops-health commit generate \
    │              --type security --scope phi \
    │              --description "implement AES-256 encryption"
    │
    ├─ AI Analysis:
    │   • Detects PHI-touching files
    │   • Identifies security scope
    │   • Generates HIPAA metadata
    │   • Suggests reviewers
    │
    ├─ Output: Commit message with compliance metadata
    │
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 3: Git Commit (Triggers Hooks)                              │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Command: git commit -m "security(phi): implement AES-256..."
    │
    ├─ Pre-commit Hook (.husky/pre-commit):
    │   • Runs linters
    │   • Checks for secrets
    │   • Validates file permissions
    │
    ├─ Commit-msg Hook (.husky/commit-msg):
    │   • Calls scripts/validate-commit.sh
    │   • Extracts commit message + changed files
    │   • Builds OPA input JSON
    │   • Evaluates: opa eval -d policies 'data.enterprise.git.allow'
    │   • PASS: Commit proceeds
    │   • FAIL: Commit blocked, show violations
    │
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 4: Push to GitHub                                           │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Command: git push origin feature/phi-encryption
    │
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 5: GitHub Actions CI/CD Triggered                           │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Workflow: .github/workflows/risk-adaptive-ci.yml
    │
    ├─ Job 1: Risk Assessment
    │   • Checkout code
    │   • Run: gitops-health risk score --commit HEAD
    │   • Output: risk_score=75, risk_level=high
    │   • Set output: echo "::set-output name=risk_score::75"
    │
    ├─ Job 2: Compliance Gate
    │   • Run: gitops-health compliance analyze --commit HEAD
    │   • Verify OPA policies pass
    │   • Check for PHI exposure
    │
    ├─ Job 3: Security Scanning
    │   • Run: govulncheck ./...
    │   • Run: trivy scan
    │   • Upload SARIF to GitHub Security
    │
    ├─ Job 4: Unit Tests
    │   • Run: go test ./... -race -cover
    │   • Upload coverage to Codecov
    │
    ├─ Job 5: Deployment Strategy Selection
    │   • if: needs.risk-assessment.outputs.risk_score < 30
    │     then: rolling update
    │   • if: needs.risk-assessment.outputs.risk_score >= 30 && < 70
    │     then: canary deployment
    │   • if: needs.risk-assessment.outputs.risk_score >= 70
    │     then: blue-green deployment + approval
    │
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 6: Deployment (Example: Blue-Green)                         │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Workflow: .github/workflows/deploy-bluegreen.yml
    │
    ├─ Phase 1: Deploy to Green Environment
    │   • Build Docker image
    │   • Push to registry
    │   • Deploy to green namespace (kubectl apply)
    │   • Wait for health checks
    │
    ├─ Phase 2: Smoke Tests
    │   • Run automated smoke tests against green
    │   • Check: response time < 200ms
    │   • Check: error rate < 1%
    │
    ├─ Phase 3: Manual Approval (if required)
    │   • Notify approvers (@infra-lead)
    │   • Wait for GitHub approval
    │
    ├─ Phase 4: Traffic Cutover
    │   • Update service selector: version=green
    │   • Monitor metrics for 5 minutes
    │   • if success: keep green, decommission blue
    │   • if failure: rollback to blue
    │
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ STEP 7: Monitoring & Audit                                       │
└──────────────────────────────────────────────────────────────────┘
    │
    ├─ Audit Trail (stored in git log + CI artifacts):
    │   • Commit SHA
    │   • Timestamp
    │   • Author
    │   • Compliance metadata (HIPAA, FDA, SOX)
    │   • Risk score
    │   • Deployment strategy used
    │   • Approvers (if any)
    │   • Test results
    │
    ├─ Metrics (Prometheus - placeholder):
    │   • Deployment frequency
    │   • Lead time for changes
    │   • Mean time to recovery
    │   • Change failure rate
    │
    └─ Alerting (planned):
        • PHI exposure detected
        • Policy violation
        • Deployment failure
        • Performance regression
```

---

## Integration Patterns

### 1. GitHub Copilot Integration

**Location**: `.copilot/COPILOT_WORKFLOW_DEMO.md`

**Pattern**: Use Copilot to generate commit messages in VS Code

```
1. Developer: Makes code changes
2. Stage files: git add .
3. Open commit message input in VS Code
4. Copilot suggestion: Type "security(phi): " and let Copilot complete
5. Copilot generates: Full message with HIPAA metadata
6. Developer: Reviews and accepts/edits
7. Commit: Triggers validation hooks
```

**Current Status**: Documentation exists, needs VS Code extension development.

### 2. LLM Provider Integration

**Supported Providers**:
- OpenAI (GPT-4, GPT-3.5-turbo)
- Anthropic (Claude)
- Google (Gemini) - planned
- Local models (Llama, Mistral) - planned

**Configuration**: `gitops_health.yml`
```yaml
llm:
  provider: openai
  api_key_env: OPENAI_API_KEY
  model: gpt-4
  temperature: 0.3
  max_tokens: 500
  
  # Fallback providers
  fallback:
    - provider: anthropic
      model: claude-3-sonnet
```

### 3. CI/CD Platform Integration

**Current**: GitHub Actions

**Planned**:
- GitLab CI
- Jenkins
- Azure DevOps
- CircleCI

**Integration Points**:
1. **Pre-commit**: Local validation before push
2. **PR checks**: Automated compliance validation
3. **Deployment**: Risk-adaptive strategy selection
4. **Post-deployment**: Monitoring and rollback

---

## CI/CD Pipeline Architecture

### Workflow Dependency Graph

```
risk-adaptive-ci.yml
    ├─ unit-tests (matrix: 5 services)
    ├─ integration-tests
    ├─ contract-tests
    ├─ security-scan
    ├─ compliance-gate
    └─ risk-assessment
           ↓
    ┌──────┴──────┐
    ↓             ↓
deploy-rolling  deploy-canary  deploy-bluegreen
(risk < 30)     (30-70)        (70-90)
```

### Risk-Adaptive Logic

**File**: `.github/workflows/risk-adaptive-ci.yml`

```yaml
jobs:
  risk-assessment:
    runs-on: ubuntu-latest
    outputs:
      risk_score: ${{ steps.score.outputs.risk_score }}
      risk_level: ${{ steps.score.outputs.risk_level }}
      strategy: ${{ steps.score.outputs.deployment_strategy }}
    steps:
      - uses: actions/checkout@v4
      - name: Score commit risk
        id: score
        run: |
          RISK=$(gitops-health risk score --commit HEAD --json)
          echo "risk_score=$(echo $RISK | jq -r '.risk_score')" >> $GITHUB_OUTPUT
          echo "risk_level=$(echo $RISK | jq -r '.risk_level')" >> $GITHUB_OUTPUT
          echo "deployment_strategy=$(echo $RISK | jq -r '.deployment_strategy')" >> $GITHUB_OUTPUT
  
  deploy-strategy:
    needs: [unit-tests, integration-tests, risk-assessment]
    runs-on: ubuntu-latest
    steps:
      - name: Select deployment
        run: |
          if [ "${{ needs.risk-assessment.outputs.risk_score }}" -lt 30 ]; then
            echo "Triggering rolling deployment"
            gh workflow run deploy-rolling.yml
          elif [ "${{ needs.risk-assessment.outputs.risk_score }}" -lt 70 ]; then
            echo "Triggering canary deployment"
            gh workflow run deploy-canary.yml
          else
            echo "Triggering blue-green deployment"
            gh workflow run deploy-bluegreen.yml
          fi
```

**Current Status**: Logic exists, but deployments are simulated (no real K8s traffic splitting).

---

## Observability & Monitoring

### Current State: Basic (🟡)

**Logging**:
- Standard Go `log` package
- No structured logging
- No correlation IDs
- No distributed tracing

**Metrics**:
- Placeholder Prometheus metrics defined
- Not actually collected
- No Grafana dashboards

**Tracing**:
- Not implemented
- Needs OpenTelemetry integration

### Target State: Production-Grade (Planned)

```go
// Example: Structured logging with correlation
import (
    "go.uber.org/zap"
    "go.opentelemetry.io/otel/trace"
)

func HandleRequest(ctx context.Context, req *Request) error {
    span := trace.SpanFromContext(ctx)
    traceID := span.SpanContext().TraceID().String()
    
    logger.Info("processing_request",
        zap.String("trace_id", traceID),
        zap.String("service", "auth"),
        zap.String("user_id", req.UserID),
        zap.Bool("phi_access", true),
        zap.String("action", "authenticate"),
    )
    
    // Process request...
    
    metrics.RequestDuration.WithLabelValues("auth", "POST", "200").Observe(duration)
    return nil
}
```

---

## Security Boundaries

### Network Segmentation

```
┌─────────────────────────────────────────┐
│  Internet / External Traffic            │
└─────────────────────────────────────────┘
              ↓ HTTPS
┌─────────────────────────────────────────┐
│  Load Balancer / Ingress                │
│  • TLS termination                      │
│  • Rate limiting                        │
│  • WAF (planned)                        │
└─────────────────────────────────────────┘
              ↓ mTLS
┌─────────────────────────────────────────┐
│  Service Mesh (planned)                 │
│  • Istio/Linkerd                        │
│  • Mutual TLS between services          │
│  • Traffic policies                     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Application Services                   │
│  • auth-service                         │
│  • payment-gateway                      │
│  • phi-service                          │
└─────────────────────────────────────────┘
```

### Secrets Management

**Current** (🔴 Insecure):
- Environment variables in docker-compose
- Secrets in GitHub repository secrets
- No rotation

**Target** (Planned):
- HashiCorp Vault or AWS Secrets Manager
- Automatic rotation
- Fine-grained access control
- Audit logging

### Encryption

| Data State | Current | Target |
|------------|---------|--------|
| **In Transit** | 🟡 TLS 1.2+ (not enforced) | 🟢 TLS 1.3 + mTLS |
| **At Rest** | 🔴 None | 🟢 AES-256-GCM |
| **In Memory** | 🔴 Plaintext | 🟡 Encrypted buffers for PHI |
| **Backups** | 🔴 None | 🟢 Encrypted backups |

---

## Development Workflow

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# 2. Install dependencies
pip install -e tools/              # Python CLI
go mod download                    # Go dependencies
brew install opa jq                # Tools

# 3. Configure
cp gitops_health.yml.example gitops_health.yml
# Edit with your LLM API key, etc.

# 4. Run services locally
cd services/auth-service && go run main.go &
cd services/payment-gateway && go run main.go &

# 5. Test AI tools
gitops-health commit generate --type feat --scope auth --description "add OAuth2"
gitops-health risk score --commit HEAD
gitops-health compliance analyze --commit HEAD
```

### Testing Workflow

```bash
# Unit tests (per service)
cd services/auth-service && go test ./... -v -cover

# Integration tests (Docker Compose)
cd tests/integration && docker-compose -f docker-compose.test.yml up
go test ./... -v

# Policy tests
opa test policies/ --verbose

# E2E test (basic scenario)
cd tests/e2e && ./run-e2e-scenario.sh

# CLI tests
cd tools && pytest tests/
```

---

## Deployment Patterns

### Pattern 1: Rolling Update (Low Risk)

**When**: Risk score < 30

**Steps**:
1. Build new version
2. Deploy to K8s with rolling update strategy
3. K8s gradually replaces old pods with new
4. Monitor during rollout
5. Auto-rollback if health checks fail

**Example**: `deploy-rolling.yml` (simulated)

### Pattern 2: Canary Deployment (Medium Risk)

**When**: Risk score 30-70

**Phases**:
1. Deploy canary (10% traffic)
2. Monitor for 5 minutes
3. If OK, increase to 25%
4. Monitor for 5 minutes
5. If OK, increase to 50%
6. Monitor for 10 minutes
7. If OK, promote to 100%
8. If any failure, instant rollback

**Example**: `deploy-canary.yml` (simulated - needs Flagger/Argo Rollouts)

### Pattern 3: Blue-Green (High Risk)

**When**: Risk score 70-90

**Steps**:
1. Deploy to green environment (parallel to blue)
2. Run smoke tests on green
3. Require manual approval
4. Cut over traffic to green
5. Monitor for 30 minutes
6. If OK, decommission blue
7. If failure, instant cutover back to blue

**Example**: `deploy-bluegreen.yml` (simulated)

### Pattern 4: Manual Review (Critical Risk)

**When**: Risk score > 90

**Requirements**:
- Dual approval from infra lead + compliance officer
- Detailed change documentation
- Rollback plan documented
- On-call engineer available during deployment

---

## API Contracts (Planned)

### OpenAPI Specs

Each service should have: `services/<service>/openapi.yaml`

**Example**: `services/auth-service/openapi.yaml` (to be created)

```yaml
openapi: 3.0.0
info:
  title: Auth Service API
  version: 1.0.0
  description: HIPAA-compliant authentication and authorization
paths:
  /auth/login:
    post:
      summary: Authenticate user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                    type: string
                  expires_at:
                    type: string
                    format: date-time
        '401':
          description: Unauthorized
```

**Status**: Not yet implemented - planned for v2.1

---

## Next Steps for Engineers

1. **Review this guide** to understand architecture
2. **Read [COMPLIANCE_GUIDE.md](COMPLIANCE_GUIDE.md)** for policy details
3. **Read [AI_TOOLS_GUIDE.md](AI_TOOLS_GUIDE.md)** for CLI usage
4. **Walk through [END_TO_END_SCENARIO.md](END_TO_END_SCENARIO.md)** for complete workflow
5. **Check [STATUS.md](../STATUS.md)** for current implementation gaps
6. **See [ROADMAP.md](../ROADMAP.md)** for upcoming features

---

## Troubleshooting

### Common Issues

**Issue**: OPA policy validation fails locally
```bash
# Debug: See what OPA receives
./scripts/validate-commit.sh /path/to/commit-msg

# Check policy syntax
opa check policies/

# Run policy tests
opa test policies/ --verbose
```

**Issue**: AI agents not working
```bash
# Check configuration
cat gitops_health.yml

# Verify API key
echo $OPENAI_API_KEY

# Test with verbose logging
gitops-health --verbose commit generate ...
```

**Issue**: Services failing to build
```bash
# Update dependencies
cd services/<service> && go mod tidy

# Check for missing tools
go version  # Should be 1.22+
docker --version

# Review errors
cat services/<service>/go.mod
```

---

## Contributing

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

When submitting PRs:
1. Include tests for new features
2. Update this guide if architecture changes
3. Follow conventional commits with compliance metadata
4. Ensure OPA policies pass

---

**Version**: 2.0.0 | **Last Updated**: November 23, 2025
