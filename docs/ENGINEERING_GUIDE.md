# Engineering Guide: GitOps 2.0 Healthcare Intelligence Platform

> **Target Audience**: Platform engineers, DevOps teams, SREs, and technical architects implementing AI-native compliance automation.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Deep Dive](#component-deep-dive)
3. [Integration Patterns](#integration-patterns)
4. [Development Workflow](#development-workflow)
5. [Deployment Strategies](#deployment-strategies)
6. [Observability & Monitoring](#observability--monitoring)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Developer Workspace                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ GitHub       │  │ Pre-commit   │  │ commitlint   │         │
│  │ Copilot      │──▶│ Hooks        │──▶│ +husky       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Git Commit Event                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Commit Metadata: Author, Message, Diff, Timestamp, PHI   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI Intelligence Layer                         │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Risk Scorer    │  │ Compliance     │  │ PHI Detector    │  │
│  │ (Python/ML)    │  │ Analyzer (OPA) │  │ (Go Service)    │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Policy Enforcement                           │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ OPA Gatekeeper │  │ Admission      │  │ Custom          │  │
│  │ Policies       │  │ Controllers    │  │ Validators      │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD Orchestration                          │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ GitHub Actions │  │ Canary         │  │ Blue/Green      │  │
│  │ Workflows      │──▶│ Deployment     │  │ Deployment      │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Production Infrastructure                       │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Kubernetes     │  │ Istio Service  │  │ Azure Monitor   │  │
│  │ Cluster (AKS)  │  │ Mesh           │  │ + Log Analytics │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Observability & Audit                          │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ OpenTelemetry  │  │ Audit Trail    │  │ Compliance      │  │
│  │ Traces         │  │ (Immutable)    │  │ Dashboards      │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technologies | Purpose |
|-------|-------------|---------|
| **Frontend/CLI** | Python 3.11+, Click, Rich | Developer tools & CLI |
| **Microservices** | Go 1.21+, Chi Router, OpenTelemetry | High-performance backend services |
| **Policy Engine** | OPA (Rego), Gatekeeper | Declarative compliance enforcement |
| **AI/ML** | OpenAI GPT-4, scikit-learn, NLTK | Commit analysis, risk scoring |
| **Container Runtime** | Docker, Kubernetes (AKS) | Container orchestration |
| **Service Mesh** | Istio, Envoy | Traffic management, mTLS |
| **Observability** | Prometheus, Grafana, Jaeger, Azure Monitor | Metrics, logs, traces |
| **IaC** | Terraform, Bicep | Infrastructure provisioning |
| **CI/CD** | GitHub Actions, Argo CD | Deployment automation |

---

## Component Deep Dive

### 1. Risk Scorer (`services/risk-scorer/`)

**Purpose**: Real-time commit risk assessment using ML models and heuristic analysis.

**Architecture**:
```go
// Main service structure
type RiskScorerService struct {
    HistoricalModel *MLModel          // Scikit-learn model via HTTP
    HeuristicEngine *HeuristicEngine  // Pattern-based rules
    Tracer          trace.Tracer      // OpenTelemetry tracing
    Logger          *zap.Logger       // Structured logging
}

// Request/Response
type RiskRequest struct {
    CommitHash    string            `json:"commit_hash"`
    Author        string            `json:"author"`
    Message       string            `json:"message"`
    FilesChanged  []string          `json:"files_changed"`
    LinesAdded    int               `json:"lines_added"`
    LinesDeleted  int               `json:"lines_deleted"`
    Timestamp     time.Time         `json:"timestamp"`
}

type RiskScore struct {
    OverallScore  float64           `json:"overall_score"`  // 0-100
    Category      string            `json:"category"`       // LOW/MEDIUM/HIGH/CRITICAL
    Factors       []RiskFactor      `json:"factors"`
    MLConfidence  float64           `json:"ml_confidence"`
    Recommendation string           `json:"recommendation"`
}
```

**Scoring Algorithm**:
```
Risk Score = (0.4 × ML_Score) + (0.3 × Heuristic_Score) + (0.3 × Context_Score)

Where:
- ML_Score: Historical commit analysis (success rate, revert frequency)
- Heuristic_Score: Pattern matching (CRITICAL_PATHS, security keywords)
- Context_Score: Temporal factors (time of day, weekend commits)

Categories:
- LOW (0-25): Automated deployment
- MEDIUM (25-50): Standard review + staging test
- HIGH (50-75): Senior review + extended staging + canary
- CRITICAL (75-100): Architect approval + blue/green + 24h bake
```

**Deployment**:
```yaml
# k8s/risk-scorer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: risk-scorer
  namespace: gitops-health
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: risk-scorer
        image: gitopshealth/risk-scorer:v2.0.0
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        - name: ML_MODEL_URL
          value: "http://ml-model-service:8080"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### 2. Compliance Analyzer (`services/compliance-analyzer/`)

**Purpose**: HIPAA/FDA/SOX requirement validation using OPA policies.

**Policy Structure**:
```rego
# policies/hipaa_phi_detection.rego
package compliance.hipaa

# PHI patterns (18 HIPAA identifiers)
phi_patterns := {
    "ssn": `\b\d{3}-\d{2}-\d{4}\b`,
    "email": `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`,
    "phone": `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`,
    "mrn": `MRN[:\s]*[A-Z0-9]{8,12}`,
    # ... 14 more patterns
}

# Violation detection
violations[violation] {
    some file in input.files_changed
    some pattern_type, pattern in phi_patterns
    regex.match(pattern, file.content)
    
    violation := {
        "type": "PHI_EXPOSURE",
        "severity": "CRITICAL",
        "file": file.path,
        "line": file.line_number,
        "pattern": pattern_type,
        "remediation": "Remove PHI or use synthetic data generator"
    }
}

# Approval requirements
requires_hipaa_officer_approval {
    count(violations) > 0
}
```

**Service Implementation**:
```go
// services/compliance-analyzer/main.go
func analyzeCompliance(ctx context.Context, req ComplianceRequest) (*ComplianceResult, error) {
    ctx, span := tracer.Start(ctx, "analyzeCompliance")
    defer span.End()
    
    // Load OPA policies
    policies, err := loadOPAPolicies("policies/")
    if err != nil {
        return nil, fmt.Errorf("failed to load policies: %w", err)
    }
    
    // Evaluate each framework
    results := make(map[string]FrameworkResult)
    for _, framework := range []string{"HIPAA", "FDA_21CFR11", "SOX"} {
        result, err := evaluateFramework(ctx, framework, req, policies)
        if err != nil {
            span.RecordError(err)
            continue
        }
        results[framework] = result
    }
    
    return &ComplianceResult{
        OverallStatus: calculateOverallStatus(results),
        Frameworks:    results,
        Violations:    aggregateViolations(results),
        Timestamp:     time.Now(),
    }, nil
}
```

### 3. Intelligent Bisect (`tools/intelligent_bisect.py`)

**Purpose**: AI-powered git bisect for rapid regression identification.

**Algorithm**:
```python
class IntelligentBisect:
    """
    Smarter than linear bisect:
    1. ML model predicts likely culprit commits
    2. Prioritize high-risk commits from risk scorer
    3. Use test failure patterns to narrow search
    4. Parallel testing of candidate commits
    """
    
    def find_regression(self, good_commit: str, bad_commit: str) -> BisectResult:
        # Get commit range
        commits = self.git.get_commit_range(good_commit, bad_commit)
        
        # Score commits by regression likelihood
        scored_commits = []
        for commit in commits:
            score = self._calculate_regression_likelihood(commit)
            scored_commits.append((commit, score))
        
        # Sort by likelihood (highest first)
        scored_commits.sort(key=lambda x: x[1], reverse=True)
        
        # Binary search with ML guidance
        for commit, score in scored_commits:
            test_result = self._run_tests(commit)
            if test_result.failed:
                return BisectResult(
                    culprit_commit=commit,
                    confidence=score,
                    test_failures=test_result.failures,
                    bisect_steps=len(tested_commits)
                )
        
        return BisectResult(culprit_not_found=True)
    
    def _calculate_regression_likelihood(self, commit: Commit) -> float:
        """
        Score = (0.3 × risk_score) + 
                (0.3 × file_overlap) + 
                (0.2 × author_history) + 
                (0.2 × temporal_proximity)
        """
        risk = self.risk_scorer.score_commit(commit)
        overlap = self._file_overlap_with_failure(commit)
        history = self._author_reliability(commit.author)
        proximity = self._temporal_score(commit.timestamp)
        
        return (0.3 * risk) + (0.3 * overlap) + (0.2 * history) + (0.2 * proximity)
```

**Usage**:
```bash
# CLI usage
gitops-health forensics bisect \
  --good v1.2.3 \
  --bad v1.2.5 \
  --test-command "npm test" \
  --parallel-jobs 4 \
  --output bisect-report.json

# Output
{
  "culprit_commit": "a1b2c3d",
  "confidence": 0.94,
  "bisect_steps": 3,
  "traditional_steps_saved": 8,
  "root_cause": "Introduced null pointer in payment-gateway/src/processor.go:145",
  "remediation": "Revert commit or apply hotfix PR #456"
}
```

---

## Integration Patterns

### GitHub Actions Integration

```yaml
# .github/workflows/ai-compliance-gate.yml
name: AI Compliance Gate
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  compliance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for context
      
      - name: Risk Scoring
        id: risk
        run: |
          SCORE=$(gitops-health risk score \
            --commit ${{ github.event.pull_request.head.sha }} \
            --output json | jq -r '.overall_score')
          echo "score=$SCORE" >> $GITHUB_OUTPUT
      
      - name: Compliance Analysis
        id: compliance
        run: |
          gitops-health compliance analyze \
            --frameworks HIPAA,FDA,SOX \
            --commit ${{ github.event.pull_request.head.sha }} \
            --output compliance-report.json
      
      - name: Determine Deployment Strategy
        run: |
          RISK_SCORE=${{ steps.risk.outputs.score }}
          
          if (( $(echo "$RISK_SCORE < 25" | bc -l) )); then
            echo "DEPLOY_STRATEGY=standard" >> $GITHUB_ENV
          elif (( $(echo "$RISK_SCORE < 50" | bc -l) )); then
            echo "DEPLOY_STRATEGY=canary" >> $GITHUB_ENV
          else
            echo "DEPLOY_STRATEGY=bluegreen" >> $GITHUB_ENV
          fi
      
      - name: Gate Decision
        run: |
          VIOLATIONS=$(jq '.violations | length' compliance-report.json)
          if [ "$VIOLATIONS" -gt 0 ]; then
            echo "❌ Compliance violations detected. Blocking merge."
            exit 1
          fi
```

### Pre-commit Hook Integration

```python
# .husky/pre-commit
#!/usr/bin/env python3
"""
Pre-commit hook for local compliance validation.
Runs before every commit to catch issues early.
"""

import subprocess
import sys
import json

def main():
    # Get staged files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )
    staged_files = result.stdout.strip().split('\n')
    
    # Quick PHI scan
    phi_violations = scan_for_phi(staged_files)
    if phi_violations:
        print("❌ PHI detected in staged files:")
        for violation in phi_violations:
            print(f"  - {violation['file']}:{violation['line']}")
        print("\n💡 Use: gitops-health sanitize --files <file>")
        return 1
    
    # Quick risk score
    risk_score = get_quick_risk_score(staged_files)
    if risk_score > 75:
        print(f"⚠️  High risk score: {risk_score}/100")
        print("   Consider:")
        print("   - Smaller commits")
        print("   - Additional testing")
        print("   - Peer review")
        response = input("   Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return 1
    
    print("✅ Pre-commit checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## Development Workflow

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# 2. Install dependencies
make setup  # Installs Python, Go, Node.js dependencies

# 3. Start local services
make dev-up  # Starts Docker Compose environment

# 4. Run tests
make test    # Runs full test suite

# 5. Verify compliance
gitops-health compliance verify --local
```

### Commit Workflow

```bash
# 1. AI-assisted commit message generation
gitops-health commit generate --context

# Output:
# feat(payment): add retry logic for failed transactions
# 
# Add exponential backoff retry mechanism to handle transient
# payment gateway failures. Implements circuit breaker pattern.
#
# Business Impact: Reduces payment failure rate from 2.3% to 0.1%
# Testing: Unit tests + integration tests with mock gateway
# Compliance: HIPAA audit trail maintained, no PHI in logs

# 2. Stage changes
git add payment-gateway/src/retry.go payment-gateway/src/retry_test.go

# 3. Commit (pre-commit hooks run automatically)
git commit -m "$(gitops-health commit generate --context)"

# 4. Push (triggers CI/CD)
git push origin feature/payment-retry
```

### Testing Pyramid

```
                    ┌────────────────┐
                    │  E2E Tests     │  <── 5% (critical paths)
                    │  (Playwright)  │
                    └────────────────┘
                  ┌──────────────────────┐
                  │  Integration Tests   │  <── 15% (service contracts)
                  │  (Testcontainers)    │
                  └──────────────────────┘
              ┌────────────────────────────────┐
              │     Unit Tests                  │  <── 80% (business logic)
              │     (Go: testing, Python: pytest)│
              └────────────────────────────────┘
```

---

## Deployment Strategies

### Standard Deployment (Risk Score < 25)

```yaml
# Direct deployment to production
- name: Deploy to Production
  run: |
    kubectl set image deployment/api \
      api=gitopshealth/api:${{ github.sha }} \
      --namespace=production
    kubectl rollout status deployment/api
```

### Canary Deployment (Risk Score 25-50)

```yaml
# Gradual traffic shift
- name: Deploy Canary
  run: |
    # Deploy canary version (10% traffic)
    kubectl apply -f k8s/canary/deployment.yaml
    
    # Monitor for 10 minutes
    sleep 600
    
    # Check metrics
    ERROR_RATE=$(check_error_rate canary)
    if [ "$ERROR_RATE" -lt 1 ]; then
      # Promote canary to 50% traffic
      kubectl patch virtualservice api \
        --type merge \
        -p '{"spec":{"http":[{"route":[{"destination":{"subset":"canary"},"weight":50}]}]}}'
      
      sleep 600
      
      # Final promotion to 100%
      kubectl set image deployment/api api=gitopshealth/api:${{ github.sha }}
    else
      # Rollback
      kubectl delete -f k8s/canary/deployment.yaml
      exit 1
    fi
```

### Blue/Green Deployment (Risk Score > 50)

```yaml
# Zero-downtime switch
- name: Deploy Green Environment
  run: |
    # Deploy to green (inactive) environment
    kubectl apply -f k8s/green/deployment.yaml
    kubectl wait --for=condition=ready pod -l app=api,version=green
    
    # Run smoke tests
    kubectl exec -it test-runner -- ./smoke-tests.sh https://green.api.internal
    
    # Switch traffic (atomic operation)
    kubectl patch service api \
      -p '{"spec":{"selector":{"version":"green"}}}'
    
    # Keep blue environment for 24h rollback window
    # (cleanup via cron job)
```

---

## Observability & Monitoring

### OpenTelemetry Instrumentation

```go
// services/shared/telemetry/tracer.go
package telemetry

import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/trace"
)

func InitTracer(serviceName string) (*trace.TracerProvider, error) {
    exporter, err := otlptracegrpc.New(
        context.Background(),
        otlptracegrpc.WithEndpoint("otel-collector:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }
    
    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String(serviceName),
            attribute.String("environment", os.Getenv("ENV")),
        )),
    )
    
    otel.SetTracerProvider(tp)
    return tp, nil
}
```

### Key Metrics

```yaml
# Prometheus metrics
- gitops_commits_total{status="success|failure"}
- gitops_risk_score_bucket{category="low|medium|high|critical"}
- gitops_compliance_violations_total{framework="hipaa|fda|sox"}
- gitops_deployment_duration_seconds{strategy="standard|canary|bluegreen"}
- gitops_bisect_steps_saved_total

# SLIs/SLOs
Availability SLO: 99.9% (43.2 min downtime/month)
Latency SLO: P95 < 500ms, P99 < 1000ms
Error Rate SLO: < 0.1%
```

---

## Performance Tuning

### Go Service Optimization

```go
// Connection pooling
db, err := sql.Open("postgres", dsn)
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(25)
db.SetConnMaxLifetime(5 * time.Minute)

// Response caching
cache := ristretto.NewCache(&ristretto.Config{
    NumCounters: 1e7,     // 10M entries
    MaxCost:     1 << 30, // 1GB
    BufferItems: 64,
})

// Request batching
batcher := NewBatcher(100, 50*time.Millisecond)
```

### Python Service Optimization

```python
# Async I/O for ML inference
async def score_commits_batch(commits: List[Commit]) -> List[RiskScore]:
    async with aiohttp.ClientSession() as session:
        tasks = [score_commit(session, commit) for commit in commits]
        return await asyncio.gather(*tasks)

# Model caching
@lru_cache(maxsize=1000)
def load_ml_model(model_path: str) -> MLModel:
    return joblib.load(model_path)
```

---

## Troubleshooting

### Common Issues

#### Issue: High false positive rate in PHI detection

**Symptoms**:
```
WARN: PHI pattern matched but is test data
File: test/fixtures/sample_patient.json
Pattern: SSN (000-00-0000)
```

**Solution**:
```python
# Add test data exemptions
PHI_SCAN_EXCLUDE_PATTERNS = [
    r'test/.*',
    r'.*/fixtures/.*',
    r'.*\.test\.(js|py|go)$'
]
```

#### Issue: Risk scorer returning all HIGH scores

**Symptoms**:
```json
{
  "overall_score": 85,
  "category": "HIGH",
  "reason": "ML model confidence low"
}
```

**Solution**:
```bash
# Retrain ML model with recent commit data
cd tools/ml_models
python train_risk_model.py \
  --training-data ../data/commits_last_6_months.json \
  --output risk_model_v2.pkl

# Update model reference
export ML_MODEL_PATH=/path/to/risk_model_v2.pkl
```

#### Issue: OPA policy evaluation timeout

**Symptoms**:
```
ERROR: OPA evaluation exceeded 30s timeout
Policy: hipaa_phi_detection.rego
```

**Solution**:
```bash
# Optimize Rego policy
# Before: Nested loops O(n²)
violations[v] {
    some i, j
    input.files[i].content[j].line
    # slow pattern matching
}

# After: Indexed lookups O(n)
violations[v] {
    some file in input.files
    some match in regex.find_all_string_submatch_n(pattern, file.content, -1)
    # fast single-pass regex
}
```

---

## Additional Resources

- [API Reference](/docs/AI_TOOLS_REFERENCE.md)
- [Compliance Guide](/docs/COMPLIANCE_GUIDE.md)
- [Runbook](/docs/runbooks/INCIDENT_RESPONSE.md)
- [Architecture Decision Records](/docs/adr/)

---

**Maintained by**: Platform Engineering Team  
**Last Updated**: 2024-01-15  
**Questions?**: Open an issue at https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues
