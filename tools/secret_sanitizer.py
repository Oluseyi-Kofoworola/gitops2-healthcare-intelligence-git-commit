#!/usr/bin/env python3
"""
Secret Sanitization for AI Input Processing
Prevents PII/secrets from being sent to public LLMs
WHY: Feeding diffs to AI could leak patient data, API keys, credentials
"""

import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretSeverity(Enum):
    """Severity levels for detected secrets"""
    CRITICAL = "CRITICAL"  # Active credentials, PHI
    HIGH = "HIGH"          # PII, potential secrets
    MEDIUM = "MEDIUM"      # Suspicious patterns
    LOW = "LOW"            # Informational


@dataclass
class SecretMatch:
    """Detected secret or PII"""
    pattern_name: str
    severity: SecretSeverity
    matched_text: str
    line_number: int
    context: str
    file_path: Optional[str] = None


# HIPAA PHI Detection Patterns (WHY: 18 HIPAA identifiers must be protected)
PHI_PATTERNS = {
    # Names with context
    "patient_name": (
        r"(?i)(patient|subscriber|guarantor)[\s_-]*(name|full[\s_-]*name)[\s:=]+[A-Z][a-z]+ [A-Z][a-z]+",
        SecretSeverity.CRITICAL
    ),
    
    # Social Security Numbers
    "ssn": (
        r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
        SecretSeverity.CRITICAL
    ),
    
    # Medical Record Numbers (MRN)
    "mrn": (
        r"(?i)(mrn|medical[\s_-]*record[\s_-]*number|patient[\s_-]*id)[\s:=]+[A-Z0-9]{6,12}",
        SecretSeverity.CRITICAL
    ),
    
    # Date of Birth patterns
    "dob": (
        r"(?i)(dob|date[\s_-]*of[\s_-]*birth|birthdate)[\s:=]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        SecretSeverity.CRITICAL
    ),
    
    # Email addresses (potential PHI in healthcare context)
    "email_phi": (
        r"(?i)(patient|subscriber)[\s_-]*email[\s:=]+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        SecretSeverity.HIGH
    ),
    
    # Phone numbers (potential PHI)
    "phone": (
        r"(?i)(patient|subscriber|emergency)[\s_-]*(phone|tel|mobile)[\s:=]+\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        SecretSeverity.HIGH
    ),
    
    # Credit card numbers (financial PHI)
    "credit_card": (
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        SecretSeverity.CRITICAL
    ),
    
    # IP addresses (can be PHI per HIPAA)
    "ip_address": (
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        SecretSeverity.MEDIUM
    ),
}


# API Keys and Credentials (WHY: prevent credential leakage to public LLMs)
CREDENTIAL_PATTERNS = {
    "aws_access_key": (
        r"(?i)(aws|amazon)[\s_-]*(access[\s_-]*key|key[\s_-]*id)[\s:=]+[A-Z0-9]{20}",
        SecretSeverity.CRITICAL
    ),
    
    "aws_secret": (
        r"(?i)(aws|amazon)[\s_-]*secret[\s:=]+[A-Za-z0-9/+=]{40}",
        SecretSeverity.CRITICAL
    ),
    
    "azure_key": (
        r"(?i)azure[\s_-]*(key|secret|password)[\s:=]+[A-Za-z0-9/+=]{32,}",
        SecretSeverity.CRITICAL
    ),
    
    "github_token": (
        r"(?i)gh[pousr]_[A-Za-z0-9]{36,}",
        SecretSeverity.CRITICAL
    ),
    
    "openai_key": (
        r"sk-[A-Za-z0-9]{48}",
        SecretSeverity.CRITICAL
    ),
    
    "generic_api_key": (
        r"(?i)(api|private)[\s_-]*(key|token|secret)[\s:=]+['\"]?[A-Za-z0-9/+=_-]{32,}['\"]?",
        SecretSeverity.HIGH
    ),
    
    "jwt_token": (
        r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
        SecretSeverity.HIGH
    ),
    
    "connection_string": (
        r"(?i)(connection[\s_-]*string|conn[\s_-]*str)[\s:=]+.*(password|pwd)=[^;\s]+",
        SecretSeverity.CRITICAL
    ),
    
    "private_key_header": (
        r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
        SecretSeverity.CRITICAL
    ),
}


# Sensitive File Patterns (WHY: files that should never be processed by AI)
SENSITIVE_FILE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"secrets\.yaml$",
    r"secrets\.json$",
    r"\.pem$",
    r"\.key$",
    r"\.pfx$",
    r"id_rsa",
    r"id_ed25519",
    r"\.kdbx$",  # KeePass
    r"vault\.db$",
    r"credentials\.json$",
    r"service-account.*\.json$",
]


class SecretSanitizer:
    """Sanitize text before sending to AI models"""
    
    def __init__(self, enable_phi_detection: bool = True, enable_credential_detection: bool = True):
        self.enable_phi = enable_phi_detection
        self.enable_creds = enable_credential_detection
        self.patterns: Dict[str, Tuple[str, SecretSeverity]] = {}
        
        if enable_phi_detection:
            self.patterns.update(PHI_PATTERNS)
        
        if enable_credential_detection:
            self.patterns.update(CREDENTIAL_PATTERNS)
    
    def is_sensitive_file(self, file_path: str) -> bool:
        """Check if file should be excluded from AI processing"""
        for pattern in SENSITIVE_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def scan_text(self, text: str, file_path: Optional[str] = None) -> List[SecretMatch]:
        """
        Scan text for secrets and PII
        
        Returns:
            List of detected secrets/PII
        """
        matches = []
        lines = text.splitlines()
        
        for pattern_name, (pattern, severity) in self.patterns.items():
            for line_num, line in enumerate(lines, 1):
                for match in re.finditer(pattern, line):
                    matches.append(SecretMatch(
                        pattern_name=pattern_name,
                        severity=severity,
                        matched_text=match.group(0)[:50],  # Truncate for logging
                        line_number=line_num,
                        context=line[:100],  # Context for debugging
                        file_path=file_path
                    ))
        
        return matches
    
    def sanitize_text(self, text: str, redaction_char: str = "█") -> Tuple[str, List[SecretMatch]]:
        """
        Sanitize text by redacting secrets/PII
        
        Returns:
            (sanitized_text, detected_secrets)
        """
        matches = self.scan_text(text)
        sanitized = text
        
        # Sort matches by position (reverse) to maintain string indices
        sorted_matches = sorted(matches, key=lambda m: text.find(m.matched_text), reverse=True)
        
        for match in sorted_matches:
            # Replace with redaction
            redaction = f"[REDACTED_{match.pattern_name.upper()}]"
            sanitized = sanitized.replace(match.matched_text, redaction)
        
        return sanitized, matches
    
    def validate_for_ai_processing(self, text: str, file_path: Optional[str] = None) -> Tuple[bool, List[SecretMatch]]:
        """
        Validate if text is safe for AI processing
        
        Returns:
            (is_safe, detected_secrets)
        """
        # Check file path first
        if file_path and self.is_sensitive_file(file_path):
            logger.error(f"Sensitive file detected: {file_path}")
            return False, []
        
        # Scan for secrets
        matches = self.scan_text(text, file_path)
        
        # Check for critical/high severity secrets
        critical_matches = [m for m in matches if m.severity in [SecretSeverity.CRITICAL, SecretSeverity.HIGH]]
        
        if critical_matches:
            logger.error(f"Found {len(critical_matches)} critical/high severity secrets")
            for match in critical_matches[:5]:  # Log first 5
                logger.error(
                    f"  {match.severity.value}: {match.pattern_name} at line {match.line_number}"
                )
            return False, matches
        
        # Warn on medium severity
        medium_matches = [m for m in matches if m.severity == SecretSeverity.MEDIUM]
        if medium_matches:
            logger.warning(f"Found {len(medium_matches)} medium severity patterns (proceeding with caution)")
        
        return True, matches
    
    def generate_safety_report(self, matches: List[SecretMatch]) -> str:
        """Generate human-readable safety report"""
        if not matches:
            return "✅ No secrets or PII detected - SAFE for AI processing"
        
        report = f"⚠️  SECURITY SCAN RESULTS: {len(matches)} potential issues detected\n\n"
        
        # Group by severity
        by_severity = {}
        for match in matches:
            by_severity.setdefault(match.severity, []).append(match)
        
        for severity in [SecretSeverity.CRITICAL, SecretSeverity.HIGH, SecretSeverity.MEDIUM, SecretSeverity.LOW]:
            if severity in by_severity:
                report += f"\n{severity.value} ({len(by_severity[severity])} matches):\n"
                for match in by_severity[severity][:10]:  # Limit to 10 per severity
                    report += f"  - {match.pattern_name} at line {match.line_number}\n"
                    if match.file_path:
                        report += f"    File: {match.file_path}\n"
                
                if len(by_severity[severity]) > 10:
                    report += f"  ... and {len(by_severity[severity]) - 10} more\n"
        
        # Recommendations
        report += "\n📋 RECOMMENDATIONS:\n"
        if any(m.severity == SecretSeverity.CRITICAL for m in matches):
            report += "  ❌ BLOCK AI PROCESSING - Critical secrets detected\n"
            report += "  1. Remove secrets from code\n"
            report += "  2. Rotate compromised credentials\n"
            report += "  3. Use environment variables or secret managers\n"
        elif any(m.severity == SecretSeverity.HIGH for m in matches):
            report += "  ⚠️  CAUTION - High severity PII detected\n"
            report += "  1. Review if PII is necessary in code\n"
            report += "  2. Consider using synthetic test data\n"
            report += "  3. Enable redaction mode for AI processing\n"
        else:
            report += "  ℹ️  PROCEED WITH CAUTION - Medium/low severity patterns\n"
        
        return report


# Integration wrapper for healthcare tools
def safe_ai_processing(func):
    """
    Decorator to add secret sanitization to AI processing functions
    WHY: Automatic protection for all AI workflows
    """
    def wrapper(*args, **kwargs):
        sanitizer = SecretSanitizer()
        
        # Extract text input (assuming first string arg or 'text' kwarg)
        text_input = None
        for arg in args:
            if isinstance(arg, str) and len(arg) > 100:  # Likely the text payload
                text_input = arg
                break
        
        if not text_input and 'text' in kwargs:
            text_input = kwargs['text']
        
        if text_input:
            is_safe, matches = sanitizer.validate_for_ai_processing(text_input)
            
            if not is_safe:
                raise ValueError(
                    f"⛔ BLOCKED: Secrets detected in input\n"
                    f"{sanitizer.generate_safety_report(matches)}\n"
                    f"AI processing aborted to prevent data leakage."
                )
            
            if matches:
                logger.warning(f"Detected {len(matches)} potential secrets (proceeding with caution)")
        
        return func(*args, **kwargs)
    
    return wrapper


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    # Test cases
    test_cases = [
        ("Safe text with no secrets", "feat(auth): add login validation\nUpdated auth service"),
        ("PHI - SSN", "Patient SSN: 123-45-6789 processed"),
        ("PHI - MRN", "MRN: MED123456 updated in database"),
        ("Credential - AWS", "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"),
        ("Credential - OpenAI", "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGH"),
        ("Sensitive file", ".env file content"),
    ]
    
    sanitizer = SecretSanitizer()
    
    print("🔒 SECRET SANITIZATION DEMO\n" + "="*60 + "\n")
    
    for name, text in test_cases:
        print(f"\nTest: {name}")
        print(f"Input: {text[:80]}...")
        
        is_safe, matches = sanitizer.validate_for_ai_processing(text)
        
        if matches:
            print(f"Status: {'✅ SAFE' if is_safe else '⛔ BLOCKED'}")
            print(f"Matches: {len(matches)}")
            for match in matches:
                print(f"  - {match.severity.value}: {match.pattern_name}")
        else:
            print("Status: ✅ SAFE (no issues)")
        
        # Show sanitized version
        if matches:
            sanitized, _ = sanitizer.sanitize_text(text)
            print(f"Sanitized: {sanitized[:80]}...")
