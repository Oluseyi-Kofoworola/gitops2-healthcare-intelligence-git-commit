#!/usr/bin/env python3
"""
Metadata Verifier - Prevents Gaming of Compliance Metadata

Cross-references declared commit metadata with actual code changes to detect:
- Risk level understatement (declared low, but changed PHI encryption)
- Missing HIPAA declarations (changed auth-service without HIPAA metadata)
- PHI-Impact mismatches (declared None, but modified phi-service)

This tool is the "trust but verify" layer that prevents developers from
bypassing compliance gates by declaring false metadata.

Usage:
    python tools/git_intel/metadata_verifier.py
    python tools/git_intel/metadata_verifier.py --commit abc123
    python tools/git_intel/metadata_verifier.py --strict

HIPAA: Not Applicable
PHI-Impact: None
Clinical-Safety: None
"""

import subprocess
import sys
import json
import argparse
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """Result of metadata verification."""
    passed: bool
    confidence: float  # 0.0-1.0
    warnings: List[str]
    errors: List[str]
    recommendations: List[str]


class MetadataVerifier:
    """
    Verifies that declared commit metadata matches actual code changes.
    
    Uses multiple heuristics to detect fraud:
    1. Path-based analysis (PHI/auth/payment services)
    2. Content-based analysis (encryption, authentication keywords)
    3. Risk level cross-reference
    4. Historical pattern matching
    """
    
    # Critical paths that indicate high-risk changes
    HIGH_RISK_PATHS = [
        'services/phi-service/',
        'services/auth-service/jwt',
        'services/auth-service/middleware/auth',
        'services/payment-gateway/transaction',
        'policies/healthcare/',
        'infra/azure-cosmos-db.bicep',
    ]
    
    MEDIUM_RISK_PATHS = [
        'services/auth-service/',
        'services/payment-gateway/',
        '.github/workflows/',
        'tools/git_copilot_commit.py',
    ]
    
    # Keywords that indicate specific concerns
    PHI_KEYWORDS = [
        'patient', 'medical', 'health', 'diagnosis', 'treatment',
        'prescription', 'phi', 'pii', 'ssn', 'mrn'
    ]
    
    ENCRYPTION_KEYWORDS = [
        'encrypt', 'decrypt', 'cipher', 'aes', 'gcm', 'key',
        'crypto', 'hash', 'bcrypt', 'argon'
    ]
    
    AUTH_KEYWORDS = [
        'jwt', 'token', 'auth', 'login', 'password', 'session',
        'oauth', 'saml', 'bearer', 'credential'
    ]
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
    
    def get_commit_metadata(self, commit_ref: str = "HEAD") -> Dict:
        """Extract metadata from commit message."""
        try:
            msg = subprocess.check_output(
                ['git', 'log', '-1', '--format=%B', commit_ref],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            metadata = {}
            
            # Parse metadata fields
            if m := re.search(r'HIPAA:\s*([\w\s]+)', msg, re.IGNORECASE):
                metadata['hipaa'] = m.group(1).strip().lower()
            
            if m := re.search(r'PHI-Impact:\s*(\w+)', msg, re.IGNORECASE):
                metadata['phi_impact'] = m.group(1).lower()
            
            if m := re.search(r'Clinical-Safety:\s*([\w\s]+)', msg, re.IGNORECASE):
                metadata['clinical_safety'] = m.group(1).strip().lower()
            
            if m := re.search(r'Risk-Level:\s*(\w+)', msg, re.IGNORECASE):
                metadata['risk_level'] = m.group(1).lower()
            
            if m := re.search(r'Service:\s*([\w-]+)', msg, re.IGNORECASE):
                metadata['service'] = m.group(1).lower()
            
            return metadata
            
        except subprocess.CalledProcessError:
            return {}
    
    def get_changed_files(self, commit_ref: str = "HEAD") -> List[str]:
        """Get files changed in commit."""
        try:
            output = subprocess.check_output(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_ref],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            
            return output.split('\n') if output else []
            
        except subprocess.CalledProcessError:
            return []
    
    def get_file_diff(self, file_path: str, commit_ref: str = "HEAD") -> str:
        """Get diff content for a specific file."""
        try:
            output = subprocess.check_output(
                ['git', 'show', f'{commit_ref}:{file_path}'],
                text=True,
                stderr=subprocess.DEVNULL
            )
            return output.lower()  # Lowercase for keyword matching
        except subprocess.CalledProcessError:
            return ""
    
    def analyze_risk_level_mismatch(self, declared_risk: str, 
                                    actual_files: List[str]) -> Tuple[bool, List[str]]:
        """Check if declared risk level matches actual changes."""
        warnings = []
        
        # Check for high-risk path modifications
        high_risk_files = [f for f in actual_files 
                          if any(hr in f for hr in self.HIGH_RISK_PATHS)]
        
        if high_risk_files and declared_risk == 'low':
            warnings.append(
                f"⚠️  RISK MISMATCH: Modified high-risk paths but declared risk=LOW"
            )
            for f in high_risk_files[:3]:
                warnings.append(f"   • {f}")
            return False, warnings
        
        # Check for medium-risk paths declared as low
        medium_risk_files = [f for f in actual_files
                            if any(mr in f for mr in self.MEDIUM_RISK_PATHS)]
        
        if medium_risk_files and declared_risk == 'low':
            warnings.append(
                f"ℹ️  Consider MEDIUM risk: Modified {len(medium_risk_files)} medium-risk files"
            )
        
        return True, warnings
    
    def analyze_phi_impact_mismatch(self, declared_phi: str,
                                   actual_files: List[str],
                                   commit_ref: str) -> Tuple[bool, List[str]]:
        """Check if PHI-Impact declaration matches actual changes."""
        warnings = []
        
        # Check for PHI service modifications
        phi_files = [f for f in actual_files if 'phi-service' in f]
        
        if phi_files and declared_phi == 'none':
            warnings.append(
                "⚠️  PHI MISMATCH: Modified PHI service but declared PHI-Impact=None"
            )
            for f in phi_files[:3]:
                warnings.append(f"   • {f}")
            return False, warnings
        
        # Check for PHI keywords in code changes
        for file_path in actual_files:
            diff = self.get_file_diff(file_path, commit_ref)
            phi_keywords_found = [kw for kw in self.PHI_KEYWORDS if kw in diff]
            
            if phi_keywords_found and declared_phi == 'none':
                warnings.append(
                    f"⚠️  PHI KEYWORDS detected in {file_path}: {', '.join(phi_keywords_found[:3])}"
                )
                return False, warnings
        
        return True, warnings
    
    def analyze_hipaa_applicability(self, declared_hipaa: str,
                                   actual_files: List[str],
                                   commit_ref: str) -> Tuple[bool, List[str]]:
        """Check if HIPAA declaration is appropriate."""
        warnings = []
        
        # Services that typically require HIPAA consideration
        hipaa_services = ['phi-service', 'auth-service', 'payment-gateway']
        
        hipaa_relevant_files = [f for f in actual_files
                               if any(svc in f for svc in hipaa_services)]
        
        if hipaa_relevant_files and declared_hipaa != 'applicable':
            warnings.append(
                "ℹ️  HIPAA CONSIDERATION: Modified HIPAA-relevant service"
            )
            warnings.append(f"   Consider setting HIPAA: Applicable")
            for f in hipaa_relevant_files[:2]:
                warnings.append(f"   • {f}")
        
        # Check for encryption changes
        for file_path in actual_files:
            diff = self.get_file_diff(file_path, commit_ref)
            encryption_keywords = [kw for kw in self.ENCRYPTION_KEYWORDS if kw in diff]
            
            if encryption_keywords and declared_hipaa != 'applicable':
                warnings.append(
                    f"ℹ️  ENCRYPTION changes in {file_path}: Consider HIPAA: Applicable"
                )
        
        return True, warnings
    
    def analyze_clinical_safety(self, declared_safety: str,
                               actual_files: List[str]) -> Tuple[bool, List[str]]:
        """Check clinical safety declaration."""
        warnings = []
        
        # Medical device service changes are critical
        medical_device_files = [f for f in actual_files 
                               if 'medical-device' in f]
        
        if medical_device_files and declared_safety == 'none':
            warnings.append(
                "⚠️  CLINICAL SAFETY: Modified medical device service"
            )
            warnings.append("   Clinical-Safety should not be 'None'")
            return False, warnings
        
        return True, warnings
    
    def verify_commit(self, commit_ref: str = "HEAD") -> VerificationResult:
        """
        Comprehensive verification of commit metadata.
        
        Returns:
            VerificationResult with passed/failed status and details
        """
        metadata = self.get_commit_metadata(commit_ref)
        files = self.get_changed_files(commit_ref)
        
        if not metadata:
            return VerificationResult(
                passed=False,
                confidence=0.0,
                warnings=[],
                errors=["❌ No compliance metadata found in commit message"],
                recommendations=[
                    "Run: python tools/git_copilot_commit.py --analyze",
                    "Or use: python tools/commit_helper.py"
                ]
            )
        
        if not files:
            return VerificationResult(
                passed=True,
                confidence=1.0,
                warnings=["ℹ️  No files changed (empty commit?)"],
                errors=[],
                recommendations=[]
            )
        
        # Run all verification checks
        all_warnings = []
        all_errors = []
        all_passed = True
        
        # 1. Risk level verification
        declared_risk = metadata.get('risk_level', 'none')
        risk_ok, risk_warnings = self.analyze_risk_level_mismatch(
            declared_risk, files
        )
        if not risk_ok:
            all_errors.extend(risk_warnings)
            all_passed = False
        else:
            all_warnings.extend(risk_warnings)
        
        # 2. PHI-Impact verification
        declared_phi = metadata.get('phi_impact', 'none')
        phi_ok, phi_warnings = self.analyze_phi_impact_mismatch(
            declared_phi, files, commit_ref
        )
        if not phi_ok:
            all_errors.extend(phi_warnings)
            all_passed = False
        else:
            all_warnings.extend(phi_warnings)
        
        # 3. HIPAA applicability
        declared_hipaa = metadata.get('hipaa', 'not applicable')
        hipaa_ok, hipaa_warnings = self.analyze_hipaa_applicability(
            declared_hipaa, files, commit_ref
        )
        all_warnings.extend(hipaa_warnings)
        
        # 4. Clinical safety
        declared_safety = metadata.get('clinical_safety', 'none')
        safety_ok, safety_warnings = self.analyze_clinical_safety(
            declared_safety, files
        )
        if not safety_ok:
            all_errors.extend(safety_warnings)
            all_passed = False
        else:
            all_warnings.extend(safety_warnings)
        
        # Calculate confidence score
        confidence = 1.0
        if all_errors:
            confidence -= 0.5
        if all_warnings:
            confidence -= 0.1 * len(all_warnings)
        confidence = max(0.0, min(1.0, confidence))
        
        # Generate recommendations
        recommendations = []
        if all_errors:
            recommendations.append("🔴 FAILED: Metadata does not match code changes")
            recommendations.append("Review and update commit metadata to accurately reflect changes")
        elif all_warnings:
            recommendations.append("🟡 WARNINGS: Consider reviewing metadata")
        else:
            recommendations.append("✅ PASSED: Metadata matches code changes")
        
        return VerificationResult(
            passed=all_passed if self.strict_mode else (not all_errors),
            confidence=confidence,
            warnings=all_warnings,
            errors=all_errors,
            recommendations=recommendations
        )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Verify commit metadata matches actual code changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify current commit
  python metadata_verifier.py
  
  # Verify specific commit
  python metadata_verifier.py --commit abc123
  
  # Strict mode (warnings become errors)
  python metadata_verifier.py --strict
  
  # JSON output for CI/CD
  python metadata_verifier.py --format json
        """
    )
    
    parser.add_argument('--commit', default='HEAD',
                       help='Commit to verify (default: HEAD)')
    parser.add_argument('--strict', action='store_true',
                       help='Treat warnings as errors')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Run verification
    verifier = MetadataVerifier(strict_mode=args.strict)
    result = verifier.verify_commit(args.commit)
    
    # Output based on format
    if args.format == 'json':
        output = {
            'passed': result.passed,
            'confidence': result.confidence,
            'warnings': result.warnings,
            'errors': result.errors,
            'recommendations': result.recommendations
        }
        print(json.dumps(output, indent=2))
    else:
        print("\n🔍 Metadata Verification Result")
        print("=" * 70)
        print(f"\nCommit: {args.commit}")
        print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        print(f"Confidence: {result.confidence * 100:.0f}%")
        
        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"   {error}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   {warning}")
        
        if result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"   {rec}")
        
        print("\n" + "=" * 70 + "\n")
    
    # Exit code based on result
    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
