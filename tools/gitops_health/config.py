"""Configuration management for GitOps Health CLI"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG = {
    "ai": {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    "services": {
        "risk_scorer": {
            "url": os.getenv("RISK_SCORER_URL", "http://localhost:8080"),
            "timeout": 30
        },
        "compliance_analyzer": {
            "url": os.getenv("COMPLIANCE_ANALYZER_URL", "http://localhost:8081"),
            "timeout": 30
        }
    },
    "compliance": {
        "frameworks": ["HIPAA", "FDA", "SOX"],
        "severity_threshold": "MEDIUM",
        "hipaa": {
            "enable_phi_detection": True,
            "phi_patterns_file": "config/phi-patterns.yaml"
        },
        "fda": {
            "require_signatures": True,
            "regulated_paths": [
                "services/drug-dosage-calculator/",
                "services/medical-device-control/"
            ]
        },
        "sox": {
            "enable_separation_of_duties": True,
            "financial_services": [
                "payment-gateway",
                "billing-service",
                "revenue-recognition"
            ]
        }
    },
    "risk": {
        "ml_model_path": "models/risk_model.pkl",
        "weights": {
            "ml_score": 0.4,
            "heuristic_score": 0.3,
            "context_score": 0.3
        },
        "critical_paths": [
            "payment-gateway/",
            "auth-service/",
            "patient-data-service/",
            "medical-device/",
            "phi-service/"
        ]
    },
    "output": {
        "default_format": "json",
        "color_output": True,
        "verbose": False
    },
    "git": {
        "default_branch": "main",
        "require_signed_commits": True,
        "commit_template": "conventional"
    }
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults.
    
    Priority order:
    1. Specified config_path
    2. ~/.gitops-health/config.yaml
    3. ./config/gitops-health.yaml
    4. DEFAULT_CONFIG
    """
    
    # Try specified path first
    if config_path and Path(config_path).exists():
        return _load_yaml_config(config_path)
    
    # Try user home directory
    user_config = Path.home() / ".gitops-health" / "config.yaml"
    if user_config.exists():
        return _load_yaml_config(user_config)
    
    # Try project config directory
    project_config = Path("config") / "gitops-health.yaml"
    if project_config.exists():
        return _load_yaml_config(project_config)
    
    # Fall back to defaults
    return DEFAULT_CONFIG


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load and merge YAML config with defaults"""
    with open(path) as f:
        user_config = yaml.safe_load(f) or {}
    
    # Deep merge with defaults
    return _deep_merge(DEFAULT_CONFIG, user_config)


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def save_config(config: Dict[str, Any], path: Optional[str] = None):
    """Save configuration to file"""
    if not path:
        path = Path.home() / ".gitops-health" / "config.yaml"
    else:
        path = Path(path)
    
    # Create directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write config
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
