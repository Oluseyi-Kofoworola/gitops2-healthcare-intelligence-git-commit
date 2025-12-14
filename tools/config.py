#!/usr/bin/env python3
"""
Centralized Configuration Management for GitOps 2.0 Healthcare Intelligence
Enterprise-grade configuration with validation, caching, and secure credential handling

Features:
- Environment-based configuration with fallbacks
- Pydantic validation for type safety
- Secure credential management
- Configuration caching for performance
- Health checks and validation

Author: GitOps 2.0 Healthcare Intelligence Platform
Version: 2.0.0 (Production)
License: MIT
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

try:
    from pydantic import BaseModel, Field, SecretStr, field_validator, ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback for basic usage
    class BaseModel:
        pass
    def Field(*args, **kwargs):  # noqa: ARG001
        return None
    def field_validator(*args, **kwargs):  # noqa: ARG001
        def decorator(func):
            return func
        return decorator
    SecretStr = str
    ConfigDict = dict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Environment(str, Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComplianceDomain(str, Enum):
    """Healthcare compliance frameworks"""
    HIPAA = "HIPAA"
    FDA = "FDA"
    SOX = "SOX"
    GDPR = "GDPR"
    HITECH = "HITECH"
    PCI_DSS = "PCI-DSS"


if PYDANTIC_AVAILABLE:
    class OpenAIConfig(BaseModel):
        """OpenAI API configuration"""
        model_config = ConfigDict(use_enum_values=True)
        
        api_key: SecretStr = Field(..., description="OpenAI API key")
        model: str = Field(default="gpt-4o", description="Default model to use")
        temperature: float = Field(default=0.3, ge=0.0, le=2.0)
        max_tokens: int = Field(default=1000, ge=1, le=4096)
        timeout: int = Field(default=30, ge=1, le=300)
        max_retries: int = Field(default=3, ge=0, le=10)
        
        @field_validator('model')
        @classmethod
        def validate_model(cls, v: str) -> str:
            allowed_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4']
            if v not in allowed_models:
                raise ValueError(f"Model must be one of {allowed_models}")
            return v


    class GitConfig(BaseModel):
        """Git configuration"""
        default_branch: str = Field(default="main")
        max_diff_size: int = Field(default=50000, description="Max diff size in characters")
        bisect_timeout: int = Field(default=300, description="Bisect timeout in seconds")
        

    class HealthcareConfig(BaseModel):
        """Healthcare-specific configuration"""
        risk_patterns: Dict[RiskLevel, List[str]] = Field(default_factory=dict)
        compliance_mapping: Dict[ComplianceDomain, List[str]] = Field(default_factory=dict)
        reviewer_mapping: Dict[str, List[str]] = Field(default_factory=dict)
        incident_retention_days: int = Field(default=2555, description="7 years for HIPAA")
        

    class GitOpsConfig(BaseModel):
        """Main configuration for GitOps 2.0 system"""
        model_config = ConfigDict(use_enum_values=True)
        
        environment: Environment = Field(default=Environment.DEVELOPMENT)
        openai: Optional[OpenAIConfig] = None
        git: GitConfig = Field(default_factory=GitConfig)
        healthcare: HealthcareConfig = Field(default_factory=HealthcareConfig)
        
        # Feature flags
        enable_ai_commit: bool = Field(default=True)
        enable_intelligent_bisect: bool = Field(default=True)
        enable_risk_scoring: bool = Field(default=True)
        
        # Observability
        log_level: str = Field(default="INFO")
        enable_metrics: bool = Field(default=True)
        enable_tracing: bool = Field(default=False)
else:
    # Fallback configuration classes without validation
    class OpenAIConfig:
        def __init__(self, api_key: str, model: str = "gpt-4o", **kwargs):
            self.api_key = api_key
            self.model = model
            self.temperature = kwargs.get('temperature', 0.3)
            self.max_tokens = kwargs.get('max_tokens', 1000)
            self.timeout = kwargs.get('timeout', 30)
            self.max_retries = kwargs.get('max_retries', 3)
    
    class GitConfig:
        def __init__(self, **kwargs):
            self.default_branch = kwargs.get('default_branch', 'main')
            self.max_diff_size = kwargs.get('max_diff_size', 50000)
            self.bisect_timeout = kwargs.get('bisect_timeout', 300)
    
    class HealthcareConfig:
        def __init__(self, **kwargs):
            self.risk_patterns = kwargs.get('risk_patterns', {})
            self.compliance_mapping = kwargs.get('compliance_mapping', {})
            self.reviewer_mapping = kwargs.get('reviewer_mapping', {})
            self.incident_retention_days = kwargs.get('incident_retention_days', 2555)
    
    class GitOpsConfig:
        def __init__(self, **kwargs):
            self.environment = kwargs.get('environment', 'development')
            self.openai = kwargs.get('openai')
            self.git = GitConfig(**kwargs.get('git', {}))
            self.healthcare = HealthcareConfig(**kwargs.get('healthcare', {}))
            self.enable_ai_commit = kwargs.get('enable_ai_commit', True)
            self.enable_intelligent_bisect = kwargs.get('enable_intelligent_bisect', True)
            self.enable_risk_scoring = kwargs.get('enable_risk_scoring', True)
            self.log_level = kwargs.get('log_level', 'INFO')
            self.enable_metrics = kwargs.get('enable_metrics', True)
            self.enable_tracing = kwargs.get('enable_tracing', False)


@lru_cache(maxsize=1)
def get_config() -> GitOpsConfig:
    """
    Get cached configuration instance
    
    Loads configuration from:
    1. Environment variables (highest priority)
    2. Configuration file (.copilot/healthcare-commit-guidelines.yml)
    3. Default values (lowest priority)
    
    Returns:
        GitOpsConfig: Validated configuration instance
    """
    # Load from config file
    config_file = Path(".copilot/healthcare-commit-guidelines.yml")
    config_data = {}
    
    if config_file.exists() and YAML_AVAILABLE:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
    
    # Override with environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Build healthcare config
    healthcare_config = HealthcareConfig(
        risk_patterns=config_data.get("risk_patterns", _get_default_risk_patterns()),
        compliance_mapping=config_data.get("compliance_mapping", _get_default_compliance_mapping()),
        reviewer_mapping=config_data.get("reviewer_mapping", _get_default_reviewer_mapping()),
    )
    
    # Build OpenAI config if key is available
    openai_config = None
    if openai_api_key:
        try:
            openai_config = OpenAIConfig(
                api_key=openai_api_key,
                model=openai_model,
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
            )
        except Exception as e:
            print(f"Warning: Failed to configure OpenAI: {e}")
    
    # Build main config
    if PYDANTIC_AVAILABLE:
        config = GitOpsConfig(
            environment=Environment(environment),
            openai=openai_config,
            healthcare=healthcare_config,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    else:
        config = GitOpsConfig(
            environment=environment,
            openai=openai_config,
            healthcare=healthcare_config,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    return config


def _get_default_risk_patterns() -> Dict[str, List[str]]:
    """Default risk patterns for file path matching"""
    return {
        "CRITICAL": [
            "services/phi-service/**",
            "services/medical-device/**",
            "**/*encryption*",
        ],
        "HIGH": [
            "services/payment-gateway/**",
            "services/auth-service/**",
            "**/*auth*",
        ],
        "MEDIUM": [
            "services/*/api/**",
            ".github/workflows/**",
            "**/*config*",
        ],
        "LOW": [
            "docs/**",
            "**/*.md",
            "**/*test*",
        ],
    }


def _get_default_compliance_mapping() -> Dict[str, List[str]]:
    """Default compliance domain mappings"""
    return {
        "HIPAA": [
            "services/phi-service/**",
            "**/*phi*",
            "**/*patient*",
            "**/*medical-record*",
        ],
        "FDA": [
            "services/medical-device/**",
            "**/*device*",
            "**/*clinical*",
        ],
        "SOX": [
            "services/payment-gateway/**",
            "**/*financial*",
            "**/*audit*",
        ],
        "PCI-DSS": [
            "services/payment-gateway/**",
            "**/*payment*",
            "**/*card*",
        ],
    }


def _get_default_reviewer_mapping() -> Dict[str, List[str]]:
    """Default reviewer assignments by domain/risk"""
    return {
        "HIPAA": ["@privacy-officer", "@compliance-team"],
        "FDA": ["@clinical-safety", "@qa-lead"],
        "SOX": ["@financial-audit", "@compliance-team"],
        "CRITICAL_RISK": ["@cto", "@security-lead"],
        "HIGH_RISK": ["@tech-lead", "@security-team"],
    }


def validate_config(config: GitOpsConfig) -> List[str]:
    """
    Validate configuration and return list of warnings/errors
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of validation messages (empty if valid)
    """
    issues = []
    
    # Check OpenAI configuration
    if config.enable_ai_commit and not config.openai:
        issues.append("AI commit generation enabled but OpenAI API key not configured")
    
    # Check healthcare patterns
    if not config.healthcare.risk_patterns:
        issues.append("No risk patterns configured - using defaults")
    
    if not config.healthcare.compliance_mapping:
        issues.append("No compliance mappings configured - using defaults")
    
    # Check environment
    if config.environment == Environment.PRODUCTION:
        if not config.enable_metrics:
            issues.append("WARNING: Metrics disabled in production environment")
        if config.log_level == "DEBUG":
            issues.append("WARNING: Debug logging enabled in production")
    
    return issues


def health_check() -> Dict[str, bool]:
    """
    Perform health check on configuration and dependencies
    
    Returns:
        Dict with component health status
    """
    health = {
        "config_loaded": False,
        "openai_configured": False,
        "yaml_available": YAML_AVAILABLE,
        "pydantic_available": PYDANTIC_AVAILABLE,
    }
    
    try:
        config = get_config()
        health["config_loaded"] = True
        health["openai_configured"] = config.openai is not None
    except Exception:
        pass
    
    return health


if __name__ == "__main__":
    # CLI for configuration validation and testing
    
    print("🔧 GitOps 2.0 Configuration Validator\n")
    
    # Load config
    try:
        cfg = get_config()
        print("✅ Configuration loaded successfully")
        
        # Validate
        validation_issues = validate_config(cfg)
        if validation_issues:
            print("\n⚠️  Configuration Warnings:")
            for issue in validation_issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration validation passed")
        
        # Health check
        health_status = health_check()
        print("\n🏥 Health Check:")
        for component, status in health_status.items():
            symbol = "✅" if status else "❌"
            print(f"   {symbol} {component}: {status}")
        
        # Display config (without secrets)
        print("\n📋 Configuration Summary:")
        print(f"   Environment: {cfg.environment}")
        print(f"   OpenAI Model: {cfg.openai.model if cfg.openai else 'Not configured'}")
        print(f"   AI Features: {cfg.enable_ai_commit}")
        print(f"   Log Level: {cfg.log_level}")
        
    except (ValueError, RuntimeError, OSError) as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
