#!/usr/bin/env python3
"""
AI-Assisted Git Bisect for Healthcare Incident Response

Intelligently narrows down problem commits by analyzing commit metadata
to prioritize testing commits that are most likely to be the culprit.

Instead of testing commits in chronological order (like standard git bisect),
this tool uses HIPAA, PHI-Impact, and Clinical-Safety metadata to create
a smarter testing order.

Use Cases:
- PHI access incident → prioritize commits with PHI-Impact: Direct
- Auth failure → prioritize commits touching auth-service
- Performance regression → prioritize high-risk changes

HIPAA: Not Applicable
PHI-Impact: None
Clinical-Safety: None
"""

import subprocess
import json
import re
import sys
import argparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CommitInfo:
    """Information about a commit."""
    sha: str
    short_sha: str
    message: str
    author: str
    date: str
    files_changed: List[str]
    metadata: Dict[str, str]
    priority_score: int = 0


class IntelligentBisect:
    """
    Smart git bisect using commit metadata for incident response.
    
    Prioritization logic:
    1. Commits with matching incident context (e.g., PHI-related)
    2. High-risk commits (declared Risk-Level: High)
    3. Commits touching relevant services
    4. Recent commits (temporal proximity)
    """
    
    def __init__(self):
        self.commits_cache = {}
    
    def get_commit_message(self, commit_sha: str) -> str:
        """Get full commit message."""
        try:
            return subprocess.check_output(
                ['git', 'log', '-1', '--format=%B', commit_sha],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
        except subprocess.CalledProcessError:
            return ""
    
    def get_commit_files(self, commit_sha: str) -> List[str]:
        """Get list of files changed in commit."""
        try:
            output = subprocess.check_output(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_sha],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            return output.split('\n') if output else []
        except subprocess.CalledProcessError:
            return []
    
    def extract_commit_metadata(self, commit_sha: str) -> Dict[str, str]:
        """
        Extract structured metadata from commit message.
        
        Parses fields like:
        - HIPAA: Applicable/Not Applicable
        - PHI-Impact: Direct/Indirect/None
        - Clinical-Safety: Critical/Important/Minor/None
        - Risk-Level: High/Medium/Low
        - Service: service-name
        """
        msg = self.get_commit_message(commit_sha)
        metadata = {}
        
        # Parse HIPAA
        if re.search(r'HIPAA:\s*(Applicable|COMPLIANT)', msg, re.IGNORECASE):
            metadata['hipaa'] = 'applicable'
        elif re.search(r'HIPAA:\s*Not\s*Applicable', msg, re.IGNORECASE):
            metadata['hipaa'] = 'not_applicable'
        
        # Parse PHI-Impact
        phi_match = re.search(r'PHI-Impact:\s*(\w+)', msg, re.IGNORECASE)
        if phi_match:
            metadata['phi_impact'] = phi_match.group(1).lower()
        
        # Parse Clinical-Safety
        safety_match = re.search(r'Clinical-Safety:\s*([\w\s]+)', msg, re.IGNORECASE)
        if safety_match:
            metadata['clinical_safety'] = safety_match.group(1).strip().lower()
        
        # Parse Risk-Level
        risk_match = re.search(r'Risk-Level:\s*(\w+)', msg, re.IGNORECASE)
        if risk_match:
            metadata['risk_level'] = risk_match.group(1).lower()
        
        # Parse Service
        service_match = re.search(r'Service:\s*([\w-]+)', msg, re.IGNORECASE)
        if service_match:
            metadata['service'] = service_match.group(1).lower()
        
        return metadata
    
    def get_commit_info(self, commit_sha: str) -> CommitInfo:
        """Get comprehensive commit information."""
        if commit_sha in self.commits_cache:
            return self.commits_cache[commit_sha]
        
        # Get commit details
        try:
            output = subprocess.check_output(
                ['git', 'log', '-1', '--format=%H|%h|%s|%an|%ai', commit_sha],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            sha, short_sha, message, author, date = output.split('|', 4)
            
            commit = CommitInfo(
                sha=sha,
                short_sha=short_sha,
                message=message,
                author=author,
                date=date,
                files_changed=self.get_commit_files(commit_sha),
                metadata=self.extract_commit_metadata(commit_sha)
            )
            
            self.commits_cache[commit_sha] = commit
            return commit
            
        except (subprocess.CalledProcessError, ValueError):
            return CommitInfo(
                sha=commit_sha,
                short_sha=commit_sha[:8],
                message="",
                author="",
                date="",
                files_changed=[],
                metadata={}
            )
    
    def calculate_priority_score(self, commit: CommitInfo, 
                                 incident_context: Dict) -> int:
        """
        Calculate priority score (0-100) for commit based on incident context.
        
        Higher score = more likely to be the culprit.
        """
        score = 0
        
        # 1. PHI-related incidents (30 points)
        if incident_context.get('involves_phi'):
            phi_impact = commit.metadata.get('phi_impact', 'none')
            if phi_impact == 'direct':
                score += 30
            elif phi_impact in ['indirect', 'high']:
                score += 20
        
        # 2. Clinical safety incidents (30 points)
        if incident_context.get('clinical_incident'):
            safety = commit.metadata.get('clinical_safety', 'none')
            if safety == 'critical':
                score += 30
            elif safety == 'important':
                score += 20
            elif safety == 'minor':
                score += 10
        
        # 3. Service-specific incidents (25 points)
        incident_service = incident_context.get('service')
        if incident_service:
            commit_service = commit.metadata.get('service')
            if commit_service == incident_service:
                score += 25
            
            # Check if commit touched the service's files
            service_path = f'services/{incident_service}'
            if any(service_path in f for f in commit.files_changed):
                score += 15
        
        # 4. Declared high-risk commits (15 points)
        if commit.metadata.get('risk_level') == 'high':
            score += 15
        
        # 5. Auth/Security incidents (20 points)
        if incident_context.get('security_incident'):
            if any('auth' in f for f in commit.files_changed):
                score += 20
            if 'security' in commit.message.lower():
                score += 10
        
        return min(score, 100)
    
    def get_commits_in_range(self, good_commit: str, bad_commit: str) -> List[str]:
        """Get all commits between good and bad."""
        try:
            output = subprocess.check_output(
                ['git', 'rev-list', f'{good_commit}..{bad_commit}'],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            return output.split('\n') if output else []
            
        except subprocess.CalledProcessError:
            return []
    
    def suggest_bisect_strategy(self, good_commit: str, bad_commit: str,
                                incident_context: Dict) -> List[CommitInfo]:
        """
        Suggest commits to test first based on incident context.
        
        Returns commits sorted by priority (highest first).
        """
        commit_shas = self.get_commits_in_range(good_commit, bad_commit)
        
        if not commit_shas:
            return []
        
        # Get commit info and calculate scores
        commits_with_scores = []
        for sha in commit_shas:
            commit = self.get_commit_info(sha)
            commit.priority_score = self.calculate_priority_score(commit, incident_context)
            commits_with_scores.append(commit)
        
        # Sort by priority score (descending)
        commits_with_scores.sort(key=lambda c: c.priority_score, reverse=True)
        
        return commits_with_scores
    
    def generate_bisect_script(self, commits: List[CommitInfo], 
                               test_command: str) -> str:
        """Generate a bash script for automated bisect testing."""
        script = [
            "#!/bin/bash",
            "# Intelligent bisect script generated by git_intelligent_bisect.py",
            "# Tests commits in priority order based on incident metadata",
            "",
            "set -e",
            "",
            "echo '🔍 Starting intelligent bisect...'",
            ""
        ]
        
        for i, commit in enumerate(commits[:10], 1):  # Top 10
            script.append(f"echo ''")
            script.append(f"echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'")
            script.append(f"echo '🔍 Testing commit {i}/10: {commit.short_sha}'")
            script.append(f"echo '   {commit.message}'")
            script.append(f"echo '   Priority Score: {commit.priority_score}/100'")
            script.append(f"echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'")
            script.append(f"")
            script.append(f"git checkout {commit.sha} --quiet")
            script.append(f"")
            script.append(f"if {test_command}; then")
            script.append(f"    echo '✅ Test passed - not the culprit'")
            script.append(f"else")
            script.append(f"    echo '❌ Test failed - THIS IS THE CULPRIT!'")
            script.append(f"    echo ''")
            script.append(f"    echo 'Culprit commit: {commit.sha}'")
            script.append(f"    echo 'Message: {commit.message}'")
            script.append(f"    echo 'Author: {commit.author}'")
            script.append(f"    echo 'Date: {commit.date}'")
            script.append(f"    exit 1")
            script.append(f"fi")
            script.append(f"")
        
        script.append("echo ''")
        script.append("echo '✅ All tested commits passed. Culprit may be in untested commits.'")
        
        return '\n'.join(script)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='AI-assisted git bisect for healthcare incident response',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # PHI access incident
  python git_intelligent_bisect.py --good v1.0.0 --bad HEAD \\
    --involves-phi --service phi-service
  
  # Auth failure incident
  python git_intelligent_bisect.py --good HEAD~20 --bad HEAD \\
    --security-incident --service auth-service
  
  # Clinical safety incident
  python git_intelligent_bisect.py --good HEAD~30 --bad HEAD \\
    --clinical-incident
        """
    )
    
    parser.add_argument('--good', required=True, help='Known good commit')
    parser.add_argument('--bad', required=True, help='Known bad commit')
    parser.add_argument('--involves-phi', action='store_true', 
                       help='Incident involves PHI access')
    parser.add_argument('--clinical-incident', action='store_true',
                       help='Clinical safety incident')
    parser.add_argument('--security-incident', action='store_true',
                       help='Security/auth incident')
    parser.add_argument('--service', help='Service name (e.g., phi-service)')
    parser.add_argument('--top', type=int, default=10,
                       help='Number of top commits to show (default: 10)')
    parser.add_argument('--generate-script', metavar='FILE',
                       help='Generate automated bisect script')
    parser.add_argument('--test-command', default='make test',
                       help='Test command for automated script (default: make test)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Build incident context
    incident_context = {
        'involves_phi': args.involves_phi,
        'clinical_incident': args.clinical_incident,
        'security_incident': args.security_incident,
        'service': args.service
    }
    
    # Create bisect analyzer
    bisect = IntelligentBisect()
    
    try:
        # Get prioritized commits
        commits = bisect.suggest_bisect_strategy(
            args.good, args.bad, incident_context
        )
        
        if not commits:
            print("❌ No commits found in range", file=sys.stderr)
            sys.exit(1)
        
        # Output based on format
        if args.format == 'json':
            output = {
                'incident_context': incident_context,
                'total_commits': len(commits),
                'top_suspects': [
                    {
                        'sha': c.sha,
                        'short_sha': c.short_sha,
                        'message': c.message,
                        'author': c.author,
                        'date': c.date,
                        'priority_score': c.priority_score,
                        'metadata': c.metadata,
                        'files_changed': c.files_changed
                    }
                    for c in commits[:args.top]
                ]
            }
            print(json.dumps(output, indent=2))
        
        else:  # text format
            print("\n🔍 Intelligent Bisect Analysis")
            print("=" * 70)
            print(f"\nRange: {args.good[:8]}..{args.bad[:8]}")
            print(f"Total commits in range: {len(commits)}")
            
            # Show incident context
            print("\n📋 Incident Context:")
            if args.involves_phi:
                print("  • PHI-related incident")
            if args.clinical_incident:
                print("  • Clinical safety incident")
            if args.security_incident:
                print("  • Security/auth incident")
            if args.service:
                print(f"  • Service: {args.service}")
            
            # Show top suspects
            print(f"\n🎯 Top {min(args.top, len(commits))} Suspected Commits (by priority):")
            print("=" * 70)
            
            for i, commit in enumerate(commits[:args.top], 1):
                print(f"\n{i}. {commit.short_sha} - Score: {commit.priority_score}/100")
                print(f"   {commit.message}")
                print(f"   Author: {commit.author} | Date: {commit.date}")
                
                if commit.metadata:
                    print(f"   Metadata: {', '.join(f'{k}={v}' for k, v in commit.metadata.items())}")
                
                if commit.files_changed:
                    key_files = [f for f in commit.files_changed 
                                if any(p in f for p in ['services/', 'policies/', '.github/'])]
                    if key_files:
                        print(f"   Key files: {', '.join(key_files[:3])}")
            
            print("\n" + "=" * 70)
            print("\n💡 Suggested Testing Order:")
            print("   Test these commits in the order shown above.")
            print("   Start with #1 (highest priority score).\n")
        
        # Generate automated script if requested
        if args.generate_script:
            script_content = bisect.generate_bisect_script(commits, args.test_command)
            with open(args.generate_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            print(f"\n✅ Automated bisect script generated: {args.generate_script}")
            print(f"   Run: chmod +x {args.generate_script} && ./{args.generate_script}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
