"""
Unit Tests for Risk Scorer Module

Tests the RiskScorer class and its risk assessment functionality.
"""

import json
from pathlib import Path

import pytest

from gitops_health.risk import RiskScorer, DeploymentStrategy


class TestRiskScorer:
    """Test suite for RiskScorer class."""
    
    def test_scorer_initialization(self, temp_repo):
        """Test RiskScorer can be initialized."""
        scorer = RiskScorer(repo_path=temp_repo)
        assert scorer is not None
        assert scorer.repo_path == temp_repo
    
    def test_critical_path_detection(self, temp_repo):
        """Test detection of critical path changes."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        # Critical paths should increase risk
        critical_files = [
            "services/payment-gateway/handler.go",
            "services/auth-service/auth.go",
            "services/phi-service/patient.go"
        ]
        
        for file in critical_files:
            file_path = temp_repo / file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("// Critical service code\n")
        
        # Add and commit
        import subprocess
        subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "feat(payment): add critical changes"],
            cwd=temp_repo,
            check=True,
            capture_output=True
        )
        
        result = scorer.analyze_commit("HEAD")
        
        # Should detect critical path
        assert result["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]
    
    def test_deployment_strategy_selection(self, temp_repo):
        """Test deployment strategy is recommended based on risk."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        # Low risk - should recommend STANDARD
        # (We'll use the initial commit from temp_repo fixture)
        result = scorer.analyze_commit("HEAD")
        
        # Should have a deployment strategy
        assert "deployment_strategy" in result
        assert result["deployment_strategy"] in [
            DeploymentStrategy.STANDARD,
            DeploymentStrategy.CANARY,
            DeploymentStrategy.BLUE_GREEN
        ]
    
    @pytest.mark.slow
    def test_risk_score_range(self, temp_repo):
        """Test risk scores are within valid range."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        result = scorer.analyze_commit("HEAD")
        
        # Score should be 0-100
        assert 0 <= result["overall_score"] <= 100
    
    def test_risk_factors_present(self, temp_repo):
        """Test that risk factors are analyzed."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        result = scorer.analyze_commit("HEAD")
        
        # Should have factors breakdown
        assert "factors" in result
        assert isinstance(result["factors"], dict)
    
    def test_invalid_commit_handling(self, temp_repo):
        """Test handling of invalid commit SHA."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        with pytest.raises(Exception):
            scorer.analyze_commit("invalid_sha_that_does_not_exist")
    
    def test_json_output_format(self, temp_repo):
        """Test risk score can be serialized to JSON."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        result = scorer.analyze_commit("HEAD")
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["overall_score"] == result["overall_score"]


class TestDeploymentStrategy:
    """Test deployment strategy recommendation logic."""
    
    def test_low_risk_standard_deployment(self, temp_repo):
        """Test low risk commits get STANDARD deployment."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        # Simple documentation change
        readme = temp_repo / "README.md"
        readme.write_text("# Updated README\n")
        
        import subprocess
        subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "docs: update readme"],
            cwd=temp_repo,
            check=True,
            capture_output=True
        )
        
        result = scorer.analyze_commit("HEAD")
        
        # Documentation changes should be low risk
        assert result["risk_level"] == "LOW"
        assert result["deployment_strategy"] == DeploymentStrategy.STANDARD
    
    def test_high_risk_blue_green_deployment(self, temp_repo):
        """Test high risk commits get BLUE_GREEN deployment."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        # Large change to critical service
        payment_service = temp_repo / "services" / "payment-gateway" / "handler.go"
        payment_service.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a large change
        large_code = "package main\n\n" + "\n".join([
            f"func Handler{i}() {{}}" for i in range(100)
        ])
        payment_service.write_text(large_code)
        
        import subprocess
        subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "refactor(payment): major handler refactoring"],
            cwd=temp_repo,
            check=True,
            capture_output=True
        )
        
        result = scorer.analyze_commit("HEAD")
        
        # Should be high risk due to critical path + large change
        assert result["risk_level"] in ["HIGH", "CRITICAL"]
        assert result["deployment_strategy"] in [
            DeploymentStrategy.CANARY,
            DeploymentStrategy.BLUE_GREEN
        ]


@pytest.mark.integration
class TestRiskScorerIntegration:
    """Integration tests for RiskScorer."""
    
    @pytest.mark.requires_git
    def test_real_repository_analysis(self):
        """Test analyzing a real repository."""
        # Use current repository
        repo_path = Path(__file__).parent.parent.parent
        scorer = RiskScorer(repo_path=repo_path)
        
        result = scorer.analyze_commit("HEAD")
        
        # Should successfully analyze
        assert result is not None
        assert "overall_score" in result
        assert "risk_level" in result
    
    def test_multiple_commits_analysis(self, temp_repo):
        """Test analyzing multiple commits in sequence."""
        scorer = RiskScorer(repo_path=temp_repo)
        
        # Create multiple commits
        import subprocess
        for i in range(3):
            file = temp_repo / f"file{i}.txt"
            file.write_text(f"Content {i}\n")
            subprocess.run(["git", "add", "."], cwd=temp_repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"feat: add file {i}"],
                cwd=temp_repo,
                check=True,
                capture_output=True
            )
        
        # Get commit history
        result = subprocess.run(
            ["git", "log", "--format=%H", "-n", "3"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
            check=True
        )
        commits = result.stdout.strip().split("\n")
        
        # Analyze each
        for commit in commits:
            result = scorer.analyze_commit(commit)
            assert result is not None
            assert "overall_score" in result
