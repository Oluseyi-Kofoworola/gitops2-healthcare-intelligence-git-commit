#!/usr/bin/env python3
"""
GitOps 2.0 Commit Message Validator
Enforces healthcare compliance metadata in commit messages
"""

import re
import sys
from typing import Tuple, List, Optional

# Required fields for all commits
REQUIRED_FIELDS = ["HIPAA", "PHI-Impact", "Clinical-Safety", "Regulation", "Service"]

# Valid values for each field
VALID_VALUES = {
    "HIPAA": ["Applicable", "Not Applicable"],
    "PHI-Impact": ["Direct", "Indirect", "None"],
    "Clinical-Safety": ["Critical", "High", "Medium", "Low"],
    "Regulation": ["HIPAA", "GDPR", "FDA-21CFR11", "SOC2", "None"],
}

# Valid commit type prefixes
VALID_TYPES = ["feat", "fix", "sec", "audit", "refactor", "docs", "test", "perf", "chore"]


def validate_commit_format(msg: str) -> Tuple[bool, Optional[str]]:
    """
    Validate commit message follows <type>(<scope>): <summary> format
    """
    first_line = msg.split('\n')[0]
    pattern = r'^(' + '|'.join(VALID_TYPES) + r')\([^)]+\): .{10,}'
    
    if not re.match(pattern, first_line):
        return False, (
            f"Invalid commit format. Expected: <type>(<scope>): <summary>\n"
            f"Valid types: {', '.join(VALID_TYPES)}\n"
            f"Example: feat(auth-service): add MFA support"
        )
    
    return True, None


def validate_required_fields(msg: str) -> Tuple[bool, Optional[str]]:
    """
    Ensure all required compliance fields are present
    """
    missing_fields = []
    
    for field in REQUIRED_FIELDS:
        if f"{field}:" not in msg:
            missing_fields.append(field)
    
    if missing_fields:
        return False, (
            f"Missing required compliance fields: {', '.join(missing_fields)}\n\n"
            f"Required fields:\n"
            f"  HIPAA: Applicable | Not Applicable\n"
            f"  PHI-Impact: Direct | Indirect | None\n"
            f"  Clinical-Safety: Critical | High | Medium | Low\n"
            f"  Regulation: HIPAA | GDPR | FDA-21CFR11 | SOC2 | None\n"
            f"  Service: <service-name>\n\n"
            f"💡 Tip: Use GitHub Copilot to generate compliant commit messages:\n"
            f"   @workspace Generate a commit message for my staged changes"
        )
    
    return True, None


def validate_field_values(msg: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that field values are from allowed sets
    """
    errors = []
    
    for field, valid_values in VALID_VALUES.items():
        # Extract field value from commit message
        pattern = f"{field}:\\s*(.+?)(?:\\n|$)"
        match = re.search(pattern, msg)
        
        if match:
            value = match.group(1).strip()
            if value not in valid_values:
                errors.append(
                    f"  • {field}: '{value}' is invalid. Must be one of: {', '.join(valid_values)}"
                )
    
    if errors:
        return False, "Invalid field values:\n" + "\n".join(errors)
    
    return True, None


def validate_service_exists(msg: str) -> Tuple[bool, Optional[str]]:
    """
    Check that Service field has a value (not empty)
    """
    pattern = r"Service:\s*(.+?)(?:\n|$)"
    match = re.search(pattern, msg)
    
    if match:
        service = match.group(1).strip()
        if not service or service.lower() == "none":
            return False, "Service field cannot be empty. Specify the affected service."
    
    return True, None


def validate_phi_safety_consistency(msg: str) -> Tuple[bool, Optional[str]]:
    """
    Warn if PHI-Impact is Direct but Clinical-Safety is Low
    (This is a warning, not a hard failure)
    """
    phi_match = re.search(r"PHI-Impact:\s*(.+?)(?:\n|$)", msg)
    safety_match = re.search(r"Clinical-Safety:\s*(.+?)(?:\n|$)", msg)
    
    if phi_match and safety_match:
        phi_impact = phi_match.group(1).strip()
        clinical_safety = safety_match.group(1).strip()
        
        if phi_impact == "Direct" and clinical_safety == "Low":
            return False, (
                "⚠️  Inconsistency detected:\n"
                "   PHI-Impact: Direct is typically paired with Clinical-Safety: High or Critical\n"
                "   Are you sure Clinical-Safety should be Low?"
            )
    
    return True, None


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_commit_msg.py <commit-msg-file>")
        sys.exit(1)
    
    commit_msg_file = sys.argv[1]
    
    try:
        with open(commit_msg_file, 'r', encoding='utf-8') as f:
            commit_msg = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find commit message file: {commit_msg_file}")
        sys.exit(1)
    
    # Skip validation for merge commits
    if commit_msg.startswith("Merge "):
        print("ℹ️  Merge commit detected - skipping compliance validation")
        sys.exit(0)
    
    print("🔍 Validating commit message compliance...")
    
    # Run all validations
    validations = [
        ("Format", validate_commit_format),
        ("Required Fields", validate_required_fields),
        ("Field Values", validate_field_values),
        ("Service Name", validate_service_exists),
        ("PHI/Safety Consistency", validate_phi_safety_consistency),
    ]
    
    failed_validations = []
    
    for name, validator in validations:
        valid, error = validator(commit_msg)
        if not valid:
            failed_validations.append((name, error))
    
    if failed_validations:
        print("\n❌ Commit validation FAILED\n")
        print("=" * 70)
        
        for i, (name, error) in enumerate(failed_validations, 1):
            print(f"\n{i}. {name} Error:")
            print(f"{error}")
        
        print("\n" + "=" * 70)
        print("\n📖 View full schema: .github/gitops-copilot-instructions.md")
        print("💡 Use GitHub Copilot to auto-generate compliant messages")
        print()
        sys.exit(1)
    
    print("✅ Commit message is compliant!")
    print("   All required compliance metadata present and valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
