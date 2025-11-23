"""
Pytest Configuration and Shared Fixtures

This file provides shared test fixtures, configuration, and utilities
for all test files in the gitops_health test suite.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add tools directory to path for imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))


# ============================================================================
# FIXTURES: Test Directories
# ============================================================================


@pytest.fixture
def temp_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary git repository for testing.
    
    Yields:
        Path to temporary git repository
    """
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    
    # Create initial commit
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    
    yield repo_dir


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_files(temp_dir: Path) -> dict[str, Path]:
    """
    Create sample files for testing.
    
    Returns:
        Dictionary mapping file types to file paths
    """
    files = {}
    
    # Python file
    py_file = temp_dir / "sample.py"
    py_file.write_text('''
def process_patient(patient_id: str):
    """Process patient data."""
    # SSN: 123-45-6789
    email = "patient@example.com"
    return patient_id
''')
    files["python"] = py_file
    
    # JSON file
    json_file = temp_dir / "data.json"
    json_file.write_text('''{
  "patient_name": "John Doe",
  "mrn": "MRN: 123456789",
  "phone": "(555) 123-4567"
}''')
    files["json"] = json_file
    
    # Text file
    txt_file = temp_dir / "notes.txt"
    txt_file.write_text("Patient SSN: 987-65-4321")
    files["text"] = txt_file
    
    return files


# ============================================================================
# FIXTURES: Configuration
# ============================================================================


@pytest.fixture
def sample_config(temp_dir: Path) -> Path:
    """
    Create a sample configuration file.
    
    Returns:
        Path to config file
    """
    config_file = temp_dir / "config.yaml"
    config_file.write_text('''
version: "2.0"

risk:
  critical_paths:
    - "payment-gateway"
    - "auth-service"
  complexity_threshold: 10

compliance:
  frameworks:
    - "HIPAA"
    - "FDA"
  opa_binary: "opa"

audit:
  retention_days: 2555
''')
    return config_file


# ============================================================================
# FIXTURES: Mock Data
# ============================================================================


@pytest.fixture
def sample_git_commit() -> dict:
    """Sample git commit metadata."""
    return {
        "sha": "abc123def456",
        "author": "Test User <test@example.com>",
        "date": "2025-11-23T10:00:00Z",
        "message": "feat(payment): add new payment processor",
        "files": [
            "services/payment-gateway/processor.go",
            "services/payment-gateway/processor_test.go"
        ],
        "insertions": 150,
        "deletions": 20
    }


@pytest.fixture
def sample_diff() -> str:
    """Sample git diff output."""
    return '''
diff --git a/services/payment-gateway/processor.go b/services/payment-gateway/processor.go
index abc123..def456 100644
--- a/services/payment-gateway/processor.go
+++ b/services/payment-gateway/processor.go
@@ -10,6 +10,15 @@ import (
     "time"
 )
 
+// NewProcessor creates a payment processor
+func NewProcessor(config *Config) (*Processor, error) {
+    if config == nil {
+        return nil, errors.New("config cannot be nil")
+    }
+    return &Processor{config: config}, nil
+}
+
 // Process handles payment transaction
 func (p *Processor) Process(tx *Transaction) error {
     // Validate transaction
'''


@pytest.fixture
def sample_phi_data() -> list[dict]:
    """Sample PHI data for testing sanitization."""
    return [
        {"type": "ssn", "value": "123-45-6789", "line": 5},
        {"type": "email", "value": "patient@example.com", "line": 6},
        {"type": "mrn", "value": "MRN: 987654321", "line": 8},
        {"type": "phone", "value": "(555) 123-4567", "line": 10}
    ]


# ============================================================================
# FIXTURES: Mock API Responses
# ============================================================================


@pytest.fixture
def mock_openai_response() -> dict:
    """Mock OpenAI API response for commit generation."""
    return {
        "choices": [{
            "message": {
                "content": '''```json
{
  "type": "feat",
  "scope": "payment",
  "subject": "add stripe payment processor",
  "body": "Implements Stripe integration for payment processing",
  "breaking": false,
  "reasoning": "New feature adds payment capability"
}
```'''
            }
        }]
    }


# ============================================================================
# UTILITIES
# ============================================================================


@pytest.fixture
def mock_opa_binary(monkeypatch, tmp_path: Path):
    """Mock OPA binary for testing."""
    # Create a fake OPA script
    opa_script = tmp_path / "opa"
    opa_script.write_text('''#!/bin/bash
if [ "$1" = "version" ]; then
    echo "Version: 0.58.0"
elif [ "$1" = "eval" ]; then
    echo '{"result": [{"expressions": [{"value": {}}]}]}'
fi
''')
    opa_script.chmod(0o755)
    
    # Update PATH
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    
    return opa_script


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_git: marks tests that require git to be installed"
    )
    config.addinivalue_line(
        "markers", "requires_opa: marks tests that require OPA to be installed"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require external API (OpenAI, etc.)"
    )


# ============================================================================
# TEST COLLECTION
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    # Skip tests requiring external dependencies if not available
    skip_api = pytest.mark.skip(reason="API key not available")
    skip_git = pytest.mark.skip(reason="git not installed")
    skip_opa = pytest.mark.skip(reason="OPA not installed")
    
    for item in items:
        # Check for API tests
        if "requires_api" in item.keywords:
            if not os.getenv("OPENAI_API_KEY"):
                item.add_marker(skip_api)
        
        # Check for git
        if "requires_git" in item.keywords:
            import shutil
            if not shutil.which("git"):
                item.add_marker(skip_git)
        
        # Check for OPA
        if "requires_opa" in item.keywords:
            import shutil
            if not shutil.which("opa"):
                item.add_marker(skip_opa)
