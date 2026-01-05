#!/usr/bin/env python3
"""
Risk Scoring for Git Commits in Healthcare Applications

Calculates risk scores (0-100) based on:
- File paths modified (PHI services, auth, payments)
- Commit metadata (HIPAA, FDA, clinical safety impact)
- Change patterns (size, complexity, scope)

Used by CI/CD pipelines to determine deployment strategy:
- Low Risk (0-39): Auto-deploy with standard checks
- Medium Risk (40-69): Enhanced scanning, canary rollout
- High Risk (70-100): Dual approval, full audit trail

HIPAA: Not Applicable
PHI-Impact: None
Clinical-Safety: None
"""

import sys
import json
import argparse
import re
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    score: int
    level: str
    reasons: List[str]
    deployment_strategy: str
    approval_required: bool
    audit_level: str


class CommitRiskScorer:
    """
    Calculate risk score for Git commits in healthcare context.
    
    Scoring factors:
    - File paths (40 points max): PHI/auth/payment services
    - Metadata (40 points max): PHI-Impact, Clinical-Safety
    - Change scope (20 points max): Number of files, LoC changed
    """
    
    # High-risk paths (40 points each)
    HIGH_RISK_PATHS = [
        'services/auth-service/',
        'services/phi-service/',
        'services/payment-gateway/transaction',
        'services/medical-device/',
        'policies/healthcare/',
    ]
    
    # Medium-risk paths (20 points each)
    MEDIUM_RISK_PATHS = [
        'services/payment-gateway/',
        '.github/workflows/',
        'infra/',
        'tools/git_copilot_commit.py',
    ]
    
    # Low-risk paths (5 points each)
    LOW_RISK_PATHS = [
        'docs/',
        'README.md',
        'tests/',
    ]
    
    def __init__(self):
        self.max_score = 100
    
    def extract_metadata_from_commit(self, commit_ref: str = "HEAD") -> Dict:
        """Extract structured metadata from commit message."""
        try:
            msg = subprocess.check_output(
                ['git', 'log', '-1', '--format=%B', commit_ref],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            metadata = {}
            
            # Parse HIPAA
            if re.search(r'HIPAA:\s*(Applicable|COMPLIANT)', msg, re.IGNORECASE):
                metadata['hipaa'] = True
            
            # Parse PHI-Impact
            phi_match = re.search(r'PHI-Impact:\s*(\w+)', msg, re.IGNORECASE)
            if phi_match:
                metadata['phi_impact'] = phi_match.group(1).lower()
            
            # Parse Clinical-Safety
            safety_match = re.search(r'Clinical-Safety:\s*(\w+)', msg, re.IGNORECASE)
            if safety_match:
                metadata['clinical_safety'] = safety_match.group(1).lower()
            
            # Parse Risk-Level
            risk_match = re.search(r'Risk-Level:\s*(\w+)', msg, re.IGNORECASE)
            if risk_match:
                metadata['declared_risk'] = risk_match.group(1).lower()
            
            return metadata
            
        except subprocess.CalledProcessError:
            return {}
    
    def get_changed_files(self, commit_ref: str = "HEAD") -> List[str]:
        """Get list of files changed in commit."""
        try:
            output = subprocess.check_output(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_ref],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            return output.split('\n') if output else []
            
        except subprocess.CalledProcessError:
            return []
    
    def score_file_paths(self, files: List[str]) -> Tuple[int, List[str]]:
        """Score based on file paths modified."""
        score = 0
        reasons = []
        
        for file_path in files:
            # Check high-risk paths
            for high_risk in self.HIGH_RISK_PATHS:
                if high_risk in file_path:
                    score += 40
                    reasons.append(f"High-risk path modified: {file_path}")
                    break
            else:
                # Check medium-risk paths
                for medium_risk in self.MEDIUM_RISK_PATHS:
                    if medium_risk in file_path:
                        score += 20
                        reasons.append(f"Medium-risk path modified: {file_path}")
                        break
                else:
                    # Check low-risk paths
                    for low_risk in self.LOW_RISK_PATHS:
                        if low_risk in file_path:
                            score += 5
                            reasons.append(f"Low-risk documentation change: {file_path}")
                            break
        
        return min(score, 40), reasons  # Cap at 40 for file paths
    
    def score_metadata(self, metadata: Dict) -> Tuple[int, List[str]]:
        """Score based on commit metadata."""
        score = 0
        reasons = []
        
        # PHI Impact scoring (0-20 points)
        phi_impact = metadata.get('phi_impact', 'none').lower()
        if phi_impact == 'direct':
            score += 30
            reasons.append("Direct PHI impact declared")
        elif phi_impact == 'indirect':
            score += 15
            reasons.append("Indirect PHI impact")
        elif phi_impact == 'high':
            score += 30
            reasons.append("High PHI impact")
        
        # Clinical Safety scoring (0-30 points)
        clinical_safety = metadata.get('clinical_safety', 'none').lower()
        if clinical_safety == 'critical':
            score += 25
            reasons.append("Critical clinical safety impact")
        elif clinical_safety == 'important':
            score += 15
            reasons.append("Important clinical safety consideration")
        elif clinical_safety == 'minor':
            score += 5
            reasons.append("Minor clinical safety impact")
        
        # HIPAA compliance (bonus, not penalty)
        if metadata.get('hipaa'):
            reasons.append("HIPAA compliance metadata present")
        
        return min(score, 40), reasons  # Cap at 40 for metadata
    
    def score_change_scope(self, files: List[str]) -> Tuple[int, List[str]]:
        """Score based on scope of changes."""
        score = 0
        reasons = []
        
        num_files = len(files)
        
        if num_files > 20:
            score += 20
            reasons.append(f"Large change scope: {num_files} files modified")
        elif num_files > 10:
            score += 15
            reasons.append(f"Moderate change scope: {num_files} files modified")
        elif num_files > 5:
            score += 10
            reasons.append(f"Multiple files modified: {num_files}")
        elif num_files > 0:
            score += 5
            reasons.append(f"Small change: {num_files} file(s)")
        
        return min(score, 20), reasons  # Cap at 20 for scope
    
    def determine_deployment_strategy(self, score: int, level: str) -> Tuple[str, bool, str]:
        """Determine deployment strategy based on risk score."""
        if score >= 70:  # High risk
            return (
                "controlled_rollout",
                True,  # Dual approval required
                "full"  # Full audit trail
            )
        elif score >= 40:  # Medium risk
            return (
                "canary_deployment",
                False,  # Single approval
                "enhanced"  # Enhanced monitoring
            )
        else:  # Low risk
            return (
                "auto_deploy",
                False,  # No approval needed
                "standard"  # Standard monitoring
            )
    
    def score_commit(self, files: Optional[List[str]] = None, 
                    metadata: Optional[Dict] = None,
                    commit_ref: str = "HEAD") -> RiskAssessment:
        """
        Calculate comprehensive risk score for a commit.
        
        Args:
            files: List of changed files (will auto-detect if None)
            metadata: Commit metadata dict (will extract if None)
            commit_ref: Git commit reference (default: HEAD)
        
        Returns:
            RiskAssessment with score, level, and deployment strategy
        """
        # Auto-detect if not provided
        if files is None:
            files = self.get_changed_files(commit_ref)
        
        if metadata is None:
            metadata = self.extract_metadata_from_commit(commit_ref)
        
        # Calculate component scores
        path_score, path_reasons = self.score_file_paths(files)
        meta_score, meta_reasons = self.score_metadata(metadata)
        scope_score, scope_reasons = self.score_change_scope(files)
        
        # Total score
        total_score = path_score + meta_score + scope_score
        total_score = min(total_score, self.max_score)
        
        # Determine risk level
        if total_score >= 70:
            level = 'high'
        elif total_score >= 40:
            level = 'medium'
        else:
            level = 'low'
        
        # Combine all reasons
        all_reasons = path_reasons + meta_reasons + scope_reasons
        
        # Determine deployment strategy
        strategy, approval_req, audit_level = self.determine_deployment_strategy(
            total_score, level
        )
        
        return RiskAssessment(
            score=total_score,
            level=level,
            reasons=all_reasons,
            deployment_strategy=strategy,
            approval_required=approval_req,
            audit_level=audit_level
        )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate risk score for Git commits in healthcare context'
    )
    parser.add_argument(
        '--commit',
        default='HEAD',
        help='Git commit reference (default: HEAD)'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='List of changed files (optional, will auto-detect)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text', 'github'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--output-github-actions',
        action='store_true',
        help='Output GitHub Actions workflow variables'
    )
    
    args = parser.parse_args()
    
    # Create scorer and calculate
    scorer = CommitRiskScorer()
    
    try:
        assessment = scorer.score_commit(
            files=args.files,
            commit_ref=args.commit
        )
        
        # Output based on format
        if args.format == 'json':
            print(json.dumps(asdict(assessment), indent=2))
        
        elif args.format == 'github':
            # GitHub Actions output format
            print(f"::set-output name=score::{assessment.score}")
            print(f"::set-output name=level::{assessment.level}")
            print(f"::set-output name=strategy::{assessment.deployment_strategy}")
            print(f"::set-output name=approval_required::{str(assessment.approval_required).lower()}")
        
        else:  # text format
            print(f"\n🎯 Risk Assessment for Commit: {args.commit}")
            print("=" * 60)
            print(f"\n📊 Risk Score: {assessment.score}/100")
            print(f"🚦 Risk Level: {assessment.level.upper()}")
            print(f"🚀 Deployment Strategy: {assessment.deployment_strategy}")
            print(f"✅ Approval Required: {'Yes' if assessment.approval_required else 'No'}")
            print(f"📝 Audit Level: {assessment.audit_level}")
            
            if assessment.reasons:
                print(f"\n📋 Risk Factors:")
                for reason in assessment.reasons:
                    print(f"  • {reason}")
            
            print("\n" + "=" * 60)
            
            # Deployment guidance
            if assessment.level == 'high':
                print("\n⚠️  HIGH RISK - Required Actions:")
                print("  • Dual approval from security + compliance teams")
                print("  • Full HIPAA/FDA evidence generation")
                print("  • Controlled rollout with extensive monitoring")
                print("  • Complete audit trail documentation")
            elif assessment.level == 'medium':
                print("\n⚠️  MEDIUM RISK - Required Actions:")
                print("  • Single approval from team lead")
                print("  • Enhanced security scanning")
                print("  • Canary deployment to staging first")
                print("  • Standard compliance evidence")
            else:
                print("\n✅ LOW RISK - Standard Process:")
                print("  • Auto-deploy after tests pass")
                print("  • Basic security scanning")
                print("  • Standard monitoring")
        
        # Output for GitHub Actions if requested
        if args.output_github_actions:
            print(f"\n::set-output name=score::{assessment.score}")
            print(f"::set-output name=level::{assessment.level}")
            print(f"::set-output name=strategy::{assessment.deployment_strategy}")
        
        # Exit code based on risk level
        sys.exit(0 if assessment.level != 'high' else 1)
        
    except Exception as e:
        print(f"❌ Error calculating risk score: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
