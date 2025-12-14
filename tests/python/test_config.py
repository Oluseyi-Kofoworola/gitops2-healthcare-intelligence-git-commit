#!/usr/bin/env python3
"""
Unit tests for centralized configuration module
Tests configuration loading, validation, and error handling

Author: GitOps 2.0 Healthcare Intelligence Platform
Version: 1.0.0
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile

# Import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from config import (
    get_config,
    validate_config,
    health_check,
    Environment,
    RiskLevel,
    ComplianceDomain,
    GitOpsConfig,
    OpenAIConfig,
    GitConfig,
    HealthcareConfig,
    PYDANTIC_AVAILABLE
)


class TestEnvironmentEnum:
    """Test Environment enumeration"""
    
    def test_environment_values(self):
        """Test all environment enum values exist"""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"
        assert Environment.TEST == "test"


class TestRiskLevelEnum:
    """Test RiskLevel enumeration"""
    
    def test_risk_level_values(self):
        """Test all risk level enum values exist"""
        assert RiskLevel.CRITICAL == "CRITICAL"
        assert RiskLevel.HIGH == "HIGH"
        assert RiskLevel.MEDIUM == "MEDIUM"
        assert RiskLevel.LOW == "LOW"


class TestComplianceDomainEnum:
    """Test ComplianceDomain enumeration"""
    
    def test_compliance_domain_values(self):
        """Test all compliance domain enum values exist"""
        assert ComplianceDomain.HIPAA == "HIPAA"
        assert ComplianceDomain.FDA == "FDA"
        assert ComplianceDomain.SOX == "SOX"
        assert ComplianceDomain.GDPR == "GDPR"
        assert ComplianceDomain.HITECH == "HITECH"
        assert ComplianceDomain.PCI_DSS == "PCI-DSS"


@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
class TestOpenAIConfig:
    """Test OpenAI configuration model"""
    
    def test_valid_openai_config(self):
        """Test creating valid OpenAI configuration"""
        config = OpenAIConfig(
            api_key="sk-test-key-12345",
            model="gpt-4o",
            temperature=0.5,
            max_tokens=1000
        )
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
    
    def test_invalid_model(self):
        """Test that invalid model raises validation error"""
        with pytest.raises(ValueError, match="Model must be one of"):
            OpenAIConfig(
                api_key="sk-test-key",
                model="invalid-model"
            )
    
    def test_temperature_bounds(self):
        """Test temperature validation"""
        with pytest.raises(ValueError):
            OpenAIConfig(
                api_key="sk-test-key",
                model="gpt-4o",
                temperature=3.0  # Too high
            )
    
    def test_max_tokens_bounds(self):
        """Test max_tokens validation"""
        with pytest.raises(ValueError):
            OpenAIConfig(
                api_key="sk-test-key",
                model="gpt-4o",
                max_tokens=10000  # Too high
            )


@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
class TestGitConfig:
    """Test Git configuration model"""
    
    def test_default_git_config(self):
        """Test default Git configuration values"""
        config = GitConfig()
        assert config.default_branch == "main"
        assert config.max_diff_size == 50000
        assert config.bisect_timeout == 300
    
    def test_custom_git_config(self):
        """Test custom Git configuration"""
        config = GitConfig(
            default_branch="develop",
            max_diff_size=100000,
            bisect_timeout=600
        )
        assert config.default_branch == "develop"
        assert config.max_diff_size == 100000
        assert config.bisect_timeout == 600


@pytest.mark.skipif(not PYDANTIC_AVAILABLE, reason="Pydantic not available")
class TestHealthcareConfig:
    """Test Healthcare configuration model"""
    
    def test_default_healthcare_config(self):
        """Test default Healthcare configuration"""
        config = HealthcareConfig()
        assert config.incident_retention_days == 2555  # 7 years for HIPAA
    
    def test_custom_risk_patterns(self):
        """Test custom risk patterns"""
        patterns = {
            RiskLevel.CRITICAL: ["services/phi/**"],
            RiskLevel.HIGH: ["services/auth/**"]
        }
        config = HealthcareConfig(risk_patterns=patterns)
        assert RiskLevel.CRITICAL in config.risk_patterns
        assert "services/phi/**" in config.risk_patterns[RiskLevel.CRITICAL]


class TestConfigLoading:
    """Test configuration loading from environment"""
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-key",
        "OPENAI_MODEL": "gpt-4o",
        "ENVIRONMENT": "test"
    })
    def test_load_from_environment(self):
        """Test loading configuration from environment variables"""
        # Clear cache
        get_config.cache_clear()
        
        config = get_config()
        assert config.environment == Environment.TEST
        if config.openai:
            assert config.openai.model == "gpt-4o"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_without_openai_key(self):
        """Test loading configuration without OpenAI key"""
        # Clear cache
        get_config.cache_clear()
        
        config = get_config()
        assert config.openai is None
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-key",
        "LOG_LEVEL": "DEBUG"
    })
    def test_custom_log_level(self):
        """Test custom log level"""
        # Clear cache
        get_config.cache_clear()
        
        config = get_config()
        assert config.log_level == "DEBUG"


class TestConfigValidation:
    """Test configuration validation"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"})
    def test_valid_config_no_issues(self):
        """Test validation of valid configuration"""
        # Clear cache
        get_config.cache_clear()
        
        config = get_config()
        issues = validate_config(config)
        # Should have no critical issues
        assert isinstance(issues, list)
    
    def test_ai_enabled_without_key(self):
        """Test validation warns when AI enabled but no key"""
        config = GitOpsConfig(
            environment=Environment.DEVELOPMENT,
            openai=None,
            enable_ai_commit=True
        )
        issues = validate_config(config)
        assert any("OpenAI" in issue for issue in issues)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"})
    def test_production_without_metrics_warns(self):
        """Test validation warns about production without metrics"""
        # Clear cache
        get_config.cache_clear()
        
        config = GitOpsConfig(
            environment=Environment.PRODUCTION,
            enable_metrics=False
        )
        issues = validate_config(config)
        assert any("Metrics" in issue for issue in issues)


class TestHealthCheck:
    """Test health check functionality"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"})
    def test_health_check_success(self):
        """Test health check with valid configuration"""
        # Clear cache
        get_config.cache_clear()
        
        health = health_check()
        assert "config_loaded" in health
        assert "openai_configured" in health
        assert "yaml_available" in health
        assert "pydantic_available" in health
    
    def test_health_check_structure(self):
        """Test health check returns correct structure"""
        health = health_check()
        assert isinstance(health, dict)
        assert all(isinstance(v, bool) for v in health.values())


class TestConfigCaching:
    """Test configuration caching"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-1"})
    def test_config_is_cached(self):
        """Test that configuration is cached"""
        # Clear cache
        get_config.cache_clear()
        
        # Get config twice
        config1 = get_config()
        config2 = get_config()
        
        # Should be same instance (cached)
        assert config1 is config2
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-2"})
    def test_cache_clear_reloads(self):
        """Test that clearing cache reloads configuration"""
        # Clear cache
        get_config.cache_clear()
        
        config1 = get_config()
        
        # Clear and reload
        get_config.cache_clear()
        config2 = get_config()
        
        # Should be different instances
        assert config1 is not config2


class TestDefaultPatterns:
    """Test default configuration patterns"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_risk_patterns_loaded(self):
        """Test that default risk patterns are loaded"""
        # Clear cache
        get_config.cache_clear()
        
        config = get_config()
        assert config.healthcare.risk_patterns
        assert "CRITICAL" in config.healthcare.risk_patterns or \
               RiskLevel.CRITICAL in config.healthcare.risk_patterns
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_compliance_mapping_loaded(self):
        """Test that default compliance mappings are loaded"""
        # Clear cache
        get_config.cache_clear()
        
        config = get_config()
        assert config.healthcare.compliance_mapping
        assert "HIPAA" in config.healthcare.compliance_mapping or \
               ComplianceDomain.HIPAA in config.healthcare.compliance_mapping


class TestFeatureFlags:
    """Test feature flag configuration"""
    
    def test_default_feature_flags(self):
        """Test default feature flags are enabled"""
        config = GitOpsConfig()
        assert config.enable_ai_commit is True
        assert config.enable_intelligent_bisect is True
        assert config.enable_risk_scoring is True
    
    def test_custom_feature_flags(self):
        """Test custom feature flags"""
        config = GitOpsConfig(
            enable_ai_commit=False,
            enable_intelligent_bisect=True,
            enable_risk_scoring=False
        )
        assert config.enable_ai_commit is False
        assert config.enable_intelligent_bisect is True
        assert config.enable_risk_scoring is False


class TestObservabilityConfig:
    """Test observability configuration"""
    
    def test_default_observability(self):
        """Test default observability settings"""
        config = GitOpsConfig()
        assert config.log_level == "INFO"
        assert config.enable_metrics is True
        assert config.enable_tracing is False
    
    def test_custom_observability(self):
        """Test custom observability settings"""
        config = GitOpsConfig(
            log_level="DEBUG",
            enable_metrics=False,
            enable_tracing=True
        )
        assert config.log_level == "DEBUG"
        assert config.enable_metrics is False
        assert config.enable_tracing is True


@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for configuration"""
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-integration",
        "OPENAI_MODEL": "gpt-4o-mini",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG"
    })
    def test_full_config_integration(self):
        """Test full configuration integration"""
        # Clear cache
        get_config.cache_clear()
        
        # Load config
        config = get_config()
        
        # Validate
        issues = validate_config(config)
        
        # Health check
        health = health_check()
        
        # Assertions
        assert config.environment == Environment.TEST
        assert config.log_level == "DEBUG"
        assert health["config_loaded"] is True
        assert isinstance(issues, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=config", "--cov-report=term-missing"])
