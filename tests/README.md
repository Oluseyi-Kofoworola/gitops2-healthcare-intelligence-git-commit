# GitOps Health - Test Suite

**Status**: Section F - Testing Suite  
**Coverage Target**: >85%  
**Framework**: pytest (Python), Go test (Go), OPA test (Rego)

---

## Test Structure

```
tests/
├── python/           # Python unit & integration tests
│   ├── conftest.py              # Shared pytest fixtures
│   ├── test_risk_scorer.py      # Risk scoring tests
│   ├── test_compliance.py       # Compliance validation tests
│   ├── test_bisect.py           # Intelligent bisect tests
│   ├── test_commitgen.py        # Commit generation tests
│   ├── test_sanitize.py         # PHI sanitization tests
│   └── test_audit.py            # Audit trail tests
│
├── go/               # Go microservice tests
│   ├── risk_scorer_test.go
│   ├── compliance_analyzer_test.go
│   └── phi_detector_test.go
│
├── opa/              # OPA policy tests
│   ├── hipaa_test.rego
│   ├── fda_test.rego
│   └── sox_test.rego
│
├── e2e/              # End-to-end workflow tests
│   ├── test_full_workflow.py
│   ├── test_regression_detection.py
│   └── test_incident_response.py
│
├── performance/      # Performance & load tests
│   └── load_testing.py
│
├── data/             # Test fixtures & sample data
│   ├── sample_commits.json
│   ├── phi_test_data.json
│   └── compliance_violations.json
│
└── README.md         # This file
```

---

## Running Tests

### All Tests
```bash
# Run entire test suite
pytest tests/python/ -v

# With coverage
pytest tests/python/ --cov=tools/gitops_health --cov-report=html
```

### Specific Test Files
```bash
# Risk scorer tests
pytest tests/python/test_risk_scorer.py -v

# Compliance tests
pytest tests/python/test_compliance.py -v

# Sanitization tests
pytest tests/python/test_sanitize.py -v
```

### By Marker
```bash
# Skip slow tests
pytest tests/python/ -m "not slow"

# Only integration tests
pytest tests/python/ -m integration

# Only unit tests
pytest tests/python/ -m "not integration and not slow"
```

### With Different Verbosity
```bash
# Minimal output
pytest tests/python/ -q

# Verbose output
pytest tests/python/ -v

# Very verbose (show all output)
pytest tests/python/ -vv -s
```

---

## Test Categories

### Unit Tests
Fast, isolated tests of individual components.

```bash
pytest tests/python/test_risk_scorer.py::TestRiskScorer::test_scorer_initialization
```

**Characteristics**:
- No external dependencies
- Fast execution (<100ms per test)
- Mock external services
- Test single functions/classes

### Integration Tests
Tests that verify component interactions.

```bash
pytest tests/python/ -m integration
```

**Characteristics**:
- May require git, OPA, or other tools
- Slower execution (1-5s per test)
- Test multiple components together
- Verify end-to-end flows

### E2E Tests
Full workflow tests simulating real usage.

```bash
pytest tests/e2e/
```

**Characteristics**:
- Require full environment setup
- Slowest execution (10-60s per test)
- Test complete user scenarios
- Verify production-like behavior

---

## Test Fixtures

### Provided by `conftest.py`

#### `temp_repo`
Temporary git repository with initial commit.

```python
def test_something(temp_repo):
    # temp_repo is a Path to initialized git repo
    assert (temp_repo / ".git").exists()
```

#### `temp_dir`
Temporary directory for file operations.

```python
def test_file_ops(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
```

#### `sample_files`
Pre-created test files (Python, JSON, text).

```python
def test_sanitize(sample_files):
    py_file = sample_files["python"]
    # Contains PHI patterns for testing
```

#### `sample_config`
Sample YAML configuration file.

```python
def test_config_loading(sample_config):
    from gitops_health.config import load_config
    config = load_config(sample_config)
```

#### `mock_opa_binary`
Mock OPA binary for testing without installation.

```python
def test_compliance(mock_opa_binary):
    # OPA available in PATH
```

---

## Custom Markers

### `@pytest.mark.slow`
Mark tests that take >1 second.

```python
@pytest.mark.slow
def test_large_repository():
    # Long-running test
    pass
```

### `@pytest.mark.integration`
Mark integration tests.

```python
@pytest.mark.integration
def test_full_workflow():
    pass
```

### `@pytest.mark.requires_git`
Mark tests requiring git.

```python
@pytest.mark.requires_git
def test_git_operations():
    pass
```

### `@pytest.mark.requires_opa`
Mark tests requiring OPA.

```python
@pytest.mark.requires_opa
def test_policy_validation():
    pass
```

### `@pytest.mark.requires_api`
Mark tests requiring API keys (OpenAI, etc.).

```python
@pytest.mark.requires_api
def test_ai_commit_generation():
    pass
```

---

## Coverage Requirements

### Minimum Coverage
- **Overall**: 85%
- **Critical modules**: 90%
  - `risk.py`
  - `compliance.py`
  - `sanitize.py`
  - `audit.py`

### Generate Coverage Report
```bash
# HTML report
pytest tests/python/ --cov=tools/gitops_health --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/python/ --cov=tools/gitops_health --cov-report=term-missing

# XML report (for CI/CD)
pytest tests/python/ --cov=tools/gitops_health --cov-report=xml
```

---

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    pip install -e .[dev]
    pytest tests/python/ --cov=tools/gitops_health --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/python/ -m "not slow" -x
```

---

## Writing New Tests

### Test File Naming
- `test_*.py` - Pytest will discover these
- `*_test.go` - Go test will discover these
- `*_test.rego` - OPA test will discover these

### Test Function Naming
```python
def test_<what_is_being_tested>():
    """One-line description of test."""
    # Arrange
    # Act
    # Assert
```

### Example Test
```python
import pytest
from gitops_health.risk import RiskScorer

def test_risk_scorer_initialization(temp_repo):
    """Test RiskScorer can be initialized with repo path."""
    # Arrange
    repo_path = temp_repo
    
    # Act
    scorer = RiskScorer(repo_path=repo_path)
    
    # Assert
    assert scorer is not None
    assert scorer.repo_path == repo_path

@pytest.mark.slow
@pytest.mark.requires_git
def test_large_repository_analysis():
    """Test analyzing a large repository."""
    # This test is marked as slow and requires git
    pass
```

---

## Test Data

### Location
`tests/data/` contains sample data for tests:
- `sample_commits.json` - Example commit metadata
- `phi_test_data.json` - PHI patterns for sanitization tests
- `compliance_violations.json` - Known violations for testing

### Usage
```python
def test_with_sample_data():
    data_file = Path(__file__).parent.parent / "data" / "sample_commits.json"
    with open(data_file) as f:
        commits = json.load(f)
    # Use commits for testing
```

---

## Debugging Tests

### Run Single Test
```bash
pytest tests/python/test_risk_scorer.py::TestRiskScorer::test_scorer_initialization -v
```

### Show Print Statements
```bash
pytest tests/python/ -s
```

### Drop into Debugger on Failure
```bash
pytest tests/python/ --pdb
```

### Show Local Variables on Failure
```bash
pytest tests/python/ -l
```

---

## Current Status

### Implemented Tests
- ✅ `test_risk_scorer.py` - Risk scoring unit tests
- ⏳ `test_compliance.py` - Pending
- ⏳ `test_bisect.py` - Pending
- ⏳ `test_commitgen.py` - Pending
- ⏳ `test_sanitize.py` - Pending
- ⏳ `test_audit.py` - Pending

### Test Coverage
```
Module                    Statements    Missing    Coverage
--------------------------------------------------------
risk.py                   150           15         90%
compliance.py             180           90         50%
bisect.py                 200           150        25%
commitgen.py              220           180        18%
sanitize.py               200           160        20%
audit.py                  210           170        19%
--------------------------------------------------------
TOTAL                     1160          765        34%
```

**Target**: 85% coverage by end of Section F

---

## Next Steps

1. Implement remaining test files
2. Increase coverage to >85%
3. Add Go tests for microservices
4. Add OPA policy tests
5. Create E2E test suite
6. Setup coverage reporting in CI/CD

---

**Last Updated**: November 23, 2025
