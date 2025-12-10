"""
Unit tests for git_policy.cli

Tests Conventional Commits validation, tier-based rules, and healthcare compliance codes.
"""

import pytest
from src.git_policy.cli import validate_commit_message


class TestConventionalCommits:
    """Test Conventional Commits v1.0.0 format validation."""
    
    def test_valid_feat_commit(self):
        """Test valid feat commit with scope and ticket."""
        msg = "feat(auth): add MFA support EHR-123"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is True
        assert result['metadata']['type'] == 'feat'
        assert result['metadata']['scope'] == 'auth'
        assert 'EHR-123' in msg
    
    def test_valid_fix_commit(self):
        """Test valid fix commit."""
        msg = "fix(phi): correct encryption at rest for MRN storage HIPAA-456"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is True
        assert result['metadata']['type'] == 'fix'
        assert result['metadata']['scope'] == 'phi'
    
    def test_valid_security_commit(self):
        """Test valid security commit with CVE."""
        msg = "security(api): patch JWT validation bypass CVE-2025-12345 SEC-789"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is True
        assert result['metadata']['type'] == 'security'
        assert 'CVE' in msg
    
    def test_invalid_no_type(self):
        """Test commit missing type prefix."""
        msg = "added new feature"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is False
        assert any('Conventional Commits' in err for err in result['errors'])
    
    def test_invalid_uppercase_type(self):
        """Test commit with uppercase type (should be lowercase)."""
        msg = "FEAT(auth): add feature"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is False
    
    def test_breaking_change_with_exclamation(self):
        """Test breaking change notation with ! symbol."""
        msg = "feat(api)!: migrate to v2 authentication EHR-456"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is True
        assert result['metadata']['breaking'] is True
        assert result['metadata']['requires_dual_approval'] is True


class TestHealthcareCompliance:
    """Test healthcare-specific compliance rules."""
    
    def test_phi_change_requires_compliance_code(self):
        """Test PHI-related changes trigger compliance warnings."""
        msg = "fix(service): update PHI encryption logic"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        # Should have warning about missing compliance framework
        assert any('compliance framework' in warn.lower() for warn in result['warnings'])
    
    def test_security_fix_without_cve_warns(self):
        """Test security fixes without CVE get warning."""
        msg = "security(auth): fix authentication bug SEC-123"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        # Should warn about missing CVE
        assert any('CVE' in warn for warn in result['warnings'])
    
    def test_security_fix_with_cve_passes(self):
        """Test security fix with CVE reference."""
        msg = "security(auth): patch JWT bypass CVE-2025-99999 SEC-123"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        # Should not warn about CVE
        assert not any('CVE' in warn for warn in result['warnings'])


class TestTicketReferences:
    """Test ticket reference validation."""
    
    def test_missing_ticket_reference_warns(self):
        """Test commits without ticket reference get warning."""
        msg = "feat(auth): add new feature"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        # Should warn about missing ticket
        assert any('ticket reference' in warn.lower() for warn in result['warnings'])
    
    def test_valid_ticket_formats(self):
        """Test various valid ticket formats."""
        valid_tickets = [
            "feat(auth): add feature EHR-123",
            "fix(payment): bug fix PAY-456",
            "security(api): patch SEC-789",
            "feat(device): enhancement DEV-111",
            "fix(compliance): update COMP-222"
        ]
        
        for msg in valid_tickets:
            result = validate_commit_message(msg, "config/git-policy.yaml")
            # Should not warn about missing ticket
            ticket_warnings = [w for w in result['warnings'] if 'ticket' in w.lower()]
            assert len(ticket_warnings) == 0, f"Unexpected ticket warning for: {msg}"


class TestBreakingChanges:
    """Test breaking change detection and requirements."""
    
    def test_breaking_change_footer(self):
        """Test breaking change detection via BREAKING CHANGE footer."""
        msg = """feat(api): update authentication
        
BREAKING CHANGE: API v1 endpoints removed
        
Migrates all endpoints to v2. Clients must update.
EHR-789"""
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['metadata']['requires_dual_approval'] is True
    
    def test_breaking_change_exclamation(self):
        """Test breaking change detection via ! symbol."""
        msg = "refactor(core)!: restructure data models EHR-999"
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['metadata']['breaking'] is True


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_commit_message(self):
        """Test empty commit message fails."""
        msg = ""
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is False
        assert any('empty' in err.lower() for err in result['errors'])
    
    def test_whitespace_only_message(self):
        """Test whitespace-only message fails."""
        msg = "   \n   \n   "
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is False
    
    def test_subject_too_long(self):
        """Test subject line exceeding 100 characters."""
        msg = "feat(auth): " + "a" * 100  # 113 total chars
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        # Should fail format validation
        assert result['valid'] is False
    
    def test_multiline_commit_message(self):
        """Test multiline commit message with valid subject."""
        msg = """fix(phi): correct encryption at rest EHR-123

This commit addresses the encryption vulnerability discovered
during the security audit. All PHI fields now use AES-256-GCM
encryption as required by HIPAA standards.

Related to: COMP-456, SEC-789"""
        result = validate_commit_message(msg, "config/git-policy.yaml")
        
        assert result['valid'] is True
        assert result['metadata']['type'] == 'fix'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
