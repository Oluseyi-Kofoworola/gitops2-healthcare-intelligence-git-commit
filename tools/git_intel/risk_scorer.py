#!/usr/bin/env python3
"""
Risk Scorer - Production Ready
Calculates deployment risk scores based on commit metadata and determines deployment strategy.

Features:
- Multi-factor risk assessment (compliance, scope, clinical impact)
- Adaptive deployment strategies (direct, canary, manual approval)
- JSON output for CI/CD integration
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class RiskScorer:
    """Calculate risk scores and determine deployment strategies"""
    
    # Risk weights
    WEIGHTS = {
        'compliance_domains': 2.0,
        'phi_impact': 3.0,
        'clinical_safety': 4.0,
        'scope': 1.5,
        'files_modified': 0.5
    }
    
    # Risk thresholds
    THRESHOLDS = {
        'low': 3.0,
        'medium': 7.0,
        'high': 10.0
    }
    
    def score_commit(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk score from commit metadata.
        
        Args:
            metadata: Commit metadata dictionary
            
        Returns:
            Risk assessment with score and deployment strategy
        """
        score = 0.0
        factors = []
        
        # Compliance domain risk
        compliance_count = len(metadata.get('compliance_domains', []))
        compliance_score = min(compliance_count * 1.5, 5.0)
        score += compliance_score * self.WEIGHTS['compliance_domains']
        factors.append({
            'factor': 'compliance_domains',
            'value': compliance_count,
            'contribution': compliance_score * self.WEIGHTS['compliance_domains']
        })
        
        # PHI impact risk
        phi_impact = metadata.get('phi_impact', 'NONE')
        phi_score = {
            'NONE': 0.0,
            'INDIRECT': 2.0,
            'DIRECT': 5.0
        }.get(phi_impact, 0.0)
        score += phi_score * self.WEIGHTS['phi_impact']
        factors.append({
            'factor': 'phi_impact',
            'value': phi_impact,
            'contribution': phi_score * self.WEIGHTS['phi_impact']
        })
        
        # Clinical safety risk
        clinical_safety = metadata.get('clinical_safety', 'NO_CLINICAL_IMPACT')
        clinical_score = {
            'NO_CLINICAL_IMPACT': 0.0,
            'CLINICAL_VALIDATION_NEEDED': 3.0,
            'REQUIRES_CLINICAL_REVIEW': 5.0
        }.get(clinical_safety, 0.0)
        score += clinical_score * self.WEIGHTS['clinical_safety']
        factors.append({
            'factor': 'clinical_safety',
            'value': clinical_safety,
            'contribution': clinical_score * self.WEIGHTS['clinical_safety']
        })
        
        # Scope risk
        scope = metadata.get('scope', '')
        scope_score = {
            'auth': 4.0,
            'phi': 5.0,
            'payment': 4.0,
            'medical-device': 5.0
        }.get(scope, 1.0)
        score += scope_score * self.WEIGHTS['scope']
        factors.append({
            'factor': 'scope',
            'value': scope,
            'contribution': scope_score * self.WEIGHTS['scope']
        })
        
        # Files modified risk
        files_modified = metadata.get('files_modified', 1)
        files_score = min(files_modified * 0.5, 3.0)
        score += files_score * self.WEIGHTS['files_modified']
        factors.append({
            'factor': 'files_modified',
            'value': files_modified,
            'contribution': files_score * self.WEIGHTS['files_modified']
        })
        
        # Normalize to 0-10 scale
        max_possible = 10.0
        normalized_score = min(score, max_possible)
        
        # Determine risk level
        if normalized_score < self.THRESHOLDS['low']:
            risk_level = 'LOW'
        elif normalized_score < self.THRESHOLDS['medium']:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        # Determine deployment strategy
        deployment_strategy = self._get_deployment_strategy(normalized_score, metadata)
        
        return {
            'risk_score': round(normalized_score, 1),
            'risk_level': risk_level,
            'factors': factors,
            'deployment_strategy': deployment_strategy,
            'metadata': metadata
        }
    
    def _get_deployment_strategy(self, score: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Determine deployment strategy based on risk score"""
        
        if score < self.THRESHOLDS['low']:
            return {
                'type': 'DIRECT',
                'description': 'Direct deployment to production',
                'steps': [
                    'Deploy to production',
                    'Monitor for 1 hour',
                    'Auto-rollback if error rate > 1%'
                ],
                'approval_required': False,
                'monitoring_duration_hours': 1
            }
        
        elif score < self.THRESHOLDS['medium']:
            return {
                'type': 'CANARY',
                'description': 'Gradual canary deployment',
                'steps': [
                    'Deploy to 10% of traffic',
                    'Monitor for 4 hours',
                    'Deploy to 50% if healthy',
                    'Monitor for 12 hours',
                    'Deploy to 100% if healthy'
                ],
                'approval_required': False,
                'monitoring_duration_hours': 24,
                'rollback_threshold_error_rate': 0.1
            }
        
        else:
            return {
                'type': 'MANUAL_APPROVAL',
                'description': 'High-risk deployment requiring manual approval',
                'steps': [
                    'Security team review required',
                    'Compliance officer approval required',
                    'Deploy to staging environment',
                    'Full regression test suite',
                    'Deploy to 5% canary',
                    'Monitor for 48 hours',
                    'Manual approval for full rollout'
                ],
                'approval_required': True,
                'approvers': metadata.get('approvers', ['security-team', 'compliance-officer']),
                'monitoring_duration_hours': 48
            }


def main():
    parser = argparse.ArgumentParser(description='Calculate deployment risk scores')
    parser.add_argument('command', choices=['score'], help='Command to execute')
    parser.add_argument('--metadata', required=True, help='Path to commit metadata JSON')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Load metadata
    try:
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file not found: {args.metadata}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in metadata file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Calculate risk score
    scorer = RiskScorer()
    assessment = scorer.score_commit(metadata)
    
    # Output
    output_json = json.dumps(assessment, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Risk assessment written to: {args.output}")
    else:
        print(output_json)
    
    # Print human-readable summary to stderr
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Risk Score: {assessment['risk_score']}/10 ({assessment['risk_level']})", file=sys.stderr)
    print(f"Deployment Strategy: {assessment['deployment_strategy']['type']}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)


if __name__ == '__main__':
    main()
