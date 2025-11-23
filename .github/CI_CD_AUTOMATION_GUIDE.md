# CI/CD Automation Guide
# GitOps 2.0 Healthcare Intelligence Platform

## Overview

Comprehensive CI/CD automation for the GitOps 2.0 Healthcare testing suite, covering all test types with automated reporting and notifications.

## GitHub Actions Workflows

### Main Testing Workflow

**File**: `.github/workflows/testing-suite.yml`

**Triggers**:
- Push to `main`, `develop`, `feature/**` branches
- Pull requests to `main`, `develop`
- Scheduled nightly runs (2 AM UTC)
- Manual workflow dispatch

**Jobs**:

1. **Unit Tests** (5 parallel jobs)
   - Tests all 5 microservices in parallel
   - Generates coverage reports
   - Uploads to Codecov
   - **Duration**: ~3-5 minutes

2. **Integration Tests**
   - Starts Docker Compose environment
   - Runs full integration test suite
   - Collects service logs on failure
   - **Duration**: ~10-15 minutes

3. **Contract Tests**
   - Runs Pact consumer/provider tests
   - Publishes contracts to Pact Broker
   - Fast feedback on API compatibility
   - **Duration**: ~2-3 minutes

4. **E2E Tests** (main branch only)
   - Deploys to Kubernetes (Kind)
   - Runs end-to-end workflows
   - Validates production scenarios
   - **Duration**: ~20-30 minutes

5. **Load Tests** (scheduled only)
   - Runs performance benchmarks
   - Generates HTML/CSV reports
   - Validates SLA compliance
   - **Duration**: ~10-15 minutes

6. **Security Tests**
   - OWASP ZAP scanning
   - Dependency vulnerability scanning (govulncheck, Trivy)
   - JWT/PHI security validation
   - Uploads SARIF to GitHub Security
   - **Duration**: ~8-12 minutes

7. **Chaos Tests** (scheduled only)
   - Deploys Chaos Mesh
   - Runs resilience experiments
   - Validates recovery mechanisms
   - **Duration**: ~15-20 minutes

8. **Report Generation**
   - Consolidates all test results
   - Generates unified dashboard
   - Archives artifacts
   - **Duration**: ~1-2 minutes

9. **Notifications**
   - Sends Slack notifications
   - Updates GitHub deployment status
   - Emails on critical failures
   - **Duration**: ~30 seconds

## Workflow Execution Matrix

| Event | Unit | Integration | Contract | E2E | Load | Security | Chaos |
|-------|------|-------------|----------|-----|------|----------|-------|
| Push (feature) | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Push (main) | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Pull Request | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Nightly | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manual | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Setup Instructions

### 1. GitHub Repository Secrets

Configure the following secrets in your GitHub repository:

```bash
# Codecov integration
CODECOV_TOKEN=<your-codecov-token>

# Slack notifications
SLACK_WEBHOOK_URL=<your-slack-webhook-url>

# Pact Broker (optional)
PACT_BROKER_URL=<your-pact-broker-url>
PACT_BROKER_TOKEN=<your-pact-broker-token>

# Azure Container Registry (for E2E tests)
ACR_USERNAME=<your-acr-username>
ACR_PASSWORD=<your-acr-password>
```

### 2. Enable GitHub Actions

1. Navigate to **Settings** → **Actions** → **General**
2. Enable **Allow all actions and reusable workflows**
3. Set **Workflow permissions** to **Read and write permissions**
4. Enable **Allow GitHub Actions to create and approve pull requests**

### 3. Configure Branch Protection

```yaml
# Settings → Branches → Add rule
Branch name pattern: main

Required status checks:
  - unit-tests (auth-service)
  - unit-tests (payment-gateway)
  - unit-tests (phi-service)
  - unit-tests (medical-device-service)
  - unit-tests (notification-service)
  - integration-tests
  - contract-tests
  - security-tests

Require branches to be up to date: true
Require review from Code Owners: true
Require status checks to pass before merging: true
```

### 4. Set Up Codecov

1. Sign up at https://codecov.io
2. Add your GitHub repository
3. Copy the **Upload Token**
4. Add to GitHub Secrets as `CODECOV_TOKEN`

### 5. Configure Slack Notifications

```bash
# Create Slack Incoming Webhook
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Enable Incoming Webhooks
4. Add New Webhook to Workspace
5. Select channel (#ci-cd-notifications)
6. Copy Webhook URL
7. Add to GitHub Secrets as SLACK_WEBHOOK_URL
```

## Manual Workflow Triggers

### Via GitHub UI

1. Navigate to **Actions** tab
2. Select **Testing Suite - Full CI/CD Pipeline**
3. Click **Run workflow**
4. Select branch and test type
5. Click **Run workflow**

### Via GitHub CLI

```bash
# Run all tests
gh workflow run testing-suite.yml \
  --ref main \
  --field test_type=all

# Run specific test type
gh workflow run testing-suite.yml \
  --ref main \
  --field test_type=security

# Run on feature branch
gh workflow run testing-suite.yml \
  --ref feature/new-payment-flow \
  --field test_type=integration
```

### Via API

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/testing-suite.yml/dispatches \
  -d '{"ref":"main","inputs":{"test_type":"all"}}'
```

## Test Artifacts

All test runs generate artifacts that are stored for **90 days**:

### Coverage Reports
- **Path**: `coverage-{service}/coverage.html`
- **Format**: HTML
- **Size**: ~500KB per service

### Integration Logs
- **Path**: `integration-logs/integration-logs.txt`
- **Format**: Plain text
- **Size**: ~2-5MB

### Load Test Results
- **Path**: `load-test-results/load-report.html`
- **Format**: HTML + CSV
- **Size**: ~1-2MB

### Security Reports
- **Path**: `security-reports/*.{html,json,sarif}`
- **Format**: Multiple formats
- **Size**: ~5-10MB

### Chaos Results
- **Path**: `chaos-test-results/*.{yaml,txt}`
- **Format**: YAML + logs
- **Size**: ~1-3MB

## Viewing Test Results

### 1. GitHub Actions UI

```
Repository → Actions → Select workflow run → View jobs and artifacts
```

### 2. GitHub Security Tab

Security vulnerabilities from Trivy and OWASP ZAP are automatically uploaded to:

```
Repository → Security → Code scanning alerts
```

### 3. Codecov Dashboard

Coverage trends and reports available at:

```
https://codecov.io/gh/OWNER/REPO
```

### 4. Downloadable Artifacts

```bash
# List artifacts for a run
gh run view <run-id> --log

# Download specific artifact
gh run download <run-id> -n coverage-auth-service

# Download all artifacts
gh run download <run-id>
```

## Performance Optimization

### Caching Strategy

1. **Go Modules Cache**
   - Cache key: `${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}`
   - Speedup: ~2-3 minutes per job

2. **Docker Layer Cache**
   - Uses Docker Buildx with cache-from/cache-to
   - Speedup: ~5-10 minutes for integration tests

3. **Dependency Cache**
   - Python packages, npm modules cached
   - Speedup: ~1-2 minutes per job

### Parallel Execution

```
Total serial time: ~90 minutes
With parallelization: ~30 minutes
Speedup: 3x faster
```

### Job Dependencies

```
unit-tests (parallel)
  ↓
integration-tests
  ↓
contract-tests
  ↓
[e2e-tests | security-tests] (parallel)
  ↓
generate-reports
  ↓
notify
```

## Troubleshooting

### Workflow Fails to Start

**Symptom**: Workflow doesn't trigger on push

**Solution**:
```bash
# Check workflow syntax
gh workflow view testing-suite.yml

# Verify workflow file location
ls -la .github/workflows/testing-suite.yml

# Check GitHub Actions permissions
# Settings → Actions → General → Workflow permissions
```

### Integration Tests Timeout

**Symptom**: Integration tests exceed 15-minute timeout

**Solution**:
```yaml
# Increase timeout in workflow
- name: Run integration tests
  run: |
    cd tests/integration
    go test -v -timeout 30m ./...
```

### Docker Compose Issues

**Symptom**: Services fail to start in CI

**Solution**:
```bash
# Add health check retries
for i in {1..60}; do
  if curl -f http://localhost:8081/health; then
    echo "Services ready"
    break
  fi
  sleep 2
done
```

### Coverage Upload Fails

**Symptom**: Codecov upload returns 403 error

**Solution**:
```bash
# Verify CODECOV_TOKEN is set
gh secret list

# Re-generate token in Codecov
# Settings → Repository → Upload Token → Regenerate
```

### Security Scan False Positives

**Symptom**: OWASP ZAP reports false positives

**Solution**:
```bash
# Add .zap/rules.tsv to suppress specific alerts
10011  IGNORE  https://localhost:8080/api/*  # Example rule
```

## Monitoring and Alerts

### GitHub Actions Status Badge

Add to your README.md:

```markdown
[![Testing Suite](https://github.com/OWNER/REPO/actions/workflows/testing-suite.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/testing-suite.yml)
```

### Slack Notifications Format

```
GitOps 2.0 Healthcare - Test Suite: success

Branch: main
Commit: a1b2c3d
Unit Tests: success
Integration Tests: success
Security Tests: success

View Run: https://github.com/OWNER/REPO/actions/runs/123456
```

### Email Notifications

Configure in **Settings** → **Notifications**:
- ✅ Send notifications for failed workflows
- ✅ Send notifications for workflow runs you triggered
- ✅ Include workflow logs in failure notifications

## Best Practices

### 1. Commit Hygiene

```bash
# Run tests locally before pushing
make test-all

# Push only when tests pass
git push origin feature-branch
```

### 2. Pull Request Workflow

```bash
1. Create feature branch
2. Make changes
3. Run local tests (make test-all)
4. Push to GitHub
5. Create PR
6. Wait for CI to pass
7. Request review
8. Merge when approved + CI green
```

### 3. Nightly Test Review

```bash
# Every morning, review nightly test results
1. Check GitHub Actions for failures
2. Review security scan alerts
3. Check load test performance trends
4. Address any chaos engineering failures
```

### 4. Release Process

```bash
# Before releasing to production
1. Merge to main (triggers full CI)
2. Wait for all tests to pass (including E2E)
3. Review security scan results
4. Tag release (git tag v1.0.0)
5. Push tag (triggers deployment workflow)
```

## Advanced Features

### Matrix Testing

Test across multiple Go versions:

```yaml
strategy:
  matrix:
    go-version: ['1.20', '1.21', '1.22']
```

### Conditional Execution

Run expensive tests only on main:

```yaml
if: github.ref == 'refs/heads/main'
```

### Reusable Workflows

Create shared workflow for multiple repos:

```yaml
uses: gitops2-org/.github/.github/workflows/reusable-tests.yml@main
```

### Custom Test Runners

Use self-hosted runners for faster execution:

```yaml
runs-on: [self-hosted, linux, x64, gpu]
```

## Cost Optimization

### GitHub Actions Minutes

- **Free tier**: 2,000 minutes/month
- **Estimated usage**: ~5,000 minutes/month
- **Cost**: ~$8/month (Pro plan)

### Optimization Tips

1. Cache dependencies aggressively
2. Use matrix jobs for parallelization
3. Skip tests when only docs changed
4. Use self-hosted runners for heavy workloads

```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

## Support

### Documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [OWASP ZAP](https://www.zaproxy.org/docs/)

### Help
- GitHub Issues: Report CI/CD issues
- Slack: #ci-cd-support
- Email: devops@gitops2-healthcare.io

---

**Last Updated**: November 23, 2025  
**Version**: 1.0.0  
**Maintained By**: GitOps 2.0 Healthcare DevOps Team
