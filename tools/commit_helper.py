#!/usr/bin/env python3
"""
Interactive Commit Message Helper for Healthcare GitOps 2.0

Provides a user-friendly CLI interface to guide developers through creating
compliant commit messages with all required metadata fields.

Features:
- Interactive questionnaire for all metadata fields
- Context-aware suggestions based on changed files
- Validation of input values
- Generated message preview
- Direct git commit execution
"""

import os
import sys
import subprocess
from typing import List, Dict, Optional, Set
from pathlib import Path

try:
    import questionary
    from questionary import Style
except ImportError:
    print("❌ Error: questionary package not installed")
    print("Install with: pip install questionary")
    sys.exit(1)


# Custom style for healthcare theme
custom_style = Style([
    ('qmark', 'fg:#00d4aa bold'),           # Question mark
    ('question', 'bold'),                    # Question text
    ('answer', 'fg:#00d4aa bold'),          # User answer
    ('pointer', 'fg:#00d4aa bold'),         # List pointer
    ('highlighted', 'fg:#00d4aa bold'),     # Highlighted choice
    ('selected', 'fg:#00d4aa'),             # Selected choice
    ('separator', 'fg:#6c6c6c'),            # Separator
    ('instruction', 'fg:#858585'),          # Instructions
])


def get_changed_files() -> List[str]:
    """Get list of staged files for the commit."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        return [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []


def analyze_changed_files(files: List[str]) -> Dict[str, any]:
    """Analyze changed files to provide context-aware suggestions."""
    context = {
        'has_phi_service': False,
        'has_auth_service': False,
        'has_payment_service': False,
        'has_medical_device': False,
        'has_policies': False,
        'has_infrastructure': False,
        'has_docs': False,
        'has_tests': False,
        'suggested_risk': 'LOW',
        'suggested_phi_impact': 'None',
        'suggested_clinical_safety': 'None',
        'suggested_hipaa': False,
    }
    
    for file in files:
        file_lower = file.lower()
        
        # Service detection
        if 'phi-service' in file_lower:
            context['has_phi_service'] = True
            context['suggested_risk'] = 'HIGH'
            context['suggested_phi_impact'] = 'Direct'
            context['suggested_hipaa'] = True
        
        if 'auth-service' in file_lower or 'jwt' in file_lower:
            context['has_auth_service'] = True
            if context['suggested_risk'] != 'HIGH':
                context['suggested_risk'] = 'MEDIUM'
            context['suggested_hipaa'] = True
        
        if 'payment' in file_lower:
            context['has_payment_service'] = True
            if context['suggested_risk'] != 'HIGH':
                context['suggested_risk'] = 'MEDIUM'
        
        if 'medical-device' in file_lower:
            context['has_medical_device'] = True
            context['suggested_risk'] = 'HIGH'
            context['suggested_clinical_safety'] = 'Critical'
        
        # Other areas
        if 'policies/' in file or '.rego' in file_lower:
            context['has_policies'] = True
            if context['suggested_risk'] == 'LOW':
                context['suggested_risk'] = 'MEDIUM'
        
        if 'infra/' in file or 'terraform/' in file or '.bicep' in file_lower:
            context['has_infrastructure'] = True
        
        if 'docs/' in file or 'README' in file:
            context['has_docs'] = True
        
        if 'test' in file_lower or '_test.' in file_lower:
            context['has_tests'] = True
    
    return context


def get_commit_type() -> str:
    """Prompt for commit type."""
    return questionary.select(
        "Select commit type:",
        choices=[
            'feat: ✨ New feature',
            'fix: 🐛 Bug fix',
            'docs: 📚 Documentation',
            'style: 💎 Code style/formatting',
            'refactor: ♻️ Code refactoring',
            'perf: ⚡ Performance improvement',
            'test: 🧪 Tests',
            'build: 🔧 Build system',
            'ci: 🤖 CI/CD',
            'chore: 🔨 Maintenance',
            'security: 🔒 Security fix',
        ],
        style=custom_style
    ).ask()


def get_scope(context: Dict) -> Optional[str]:
    """Prompt for commit scope."""
    suggested_scopes = []
    
    if context['has_phi_service']:
        suggested_scopes.append('phi-service')
    if context['has_auth_service']:
        suggested_scopes.append('auth-service')
    if context['has_payment_service']:
        suggested_scopes.append('payment-gateway')
    if context['has_medical_device']:
        suggested_scopes.append('medical-device')
    if context['has_policies']:
        suggested_scopes.append('policies')
    if context['has_infrastructure']:
        suggested_scopes.append('infrastructure')
    if context['has_docs']:
        suggested_scopes.append('docs')
    if context['has_tests']:
        suggested_scopes.append('tests')
    
    choices = suggested_scopes + ['(custom)', '(no scope)']
    
    scope = questionary.select(
        "Select scope:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if scope == '(custom)':
        scope = questionary.text("Enter custom scope:", style=custom_style).ask()
    elif scope == '(no scope)':
        scope = None
    
    return scope


def get_description() -> str:
    """Prompt for commit description."""
    return questionary.text(
        "Enter short description (imperative mood, lowercase):",
        validate=lambda text: len(text) > 0 and len(text) <= 72,
        style=custom_style
    ).ask()


def get_risk_level(context: Dict) -> str:
    """Prompt for risk level."""
    default = context['suggested_risk']
    
    risk = questionary.select(
        f"Select risk level (suggested: {default}):",
        choices=['LOW', 'MEDIUM', 'HIGH'],
        default=default,
        style=custom_style
    ).ask()
    
    return risk


def get_phi_impact(context: Dict) -> str:
    """Prompt for PHI impact level."""
    default = context['suggested_phi_impact']
    
    impact = questionary.select(
        f"Select PHI impact (suggested: {default}):",
        choices=['None', 'Indirect', 'Direct'],
        default=default,
        style=custom_style
    ).ask()
    
    return impact


def get_clinical_safety(context: Dict) -> str:
    """Prompt for clinical safety level."""
    default = context['suggested_clinical_safety']
    
    safety = questionary.select(
        f"Select clinical safety (suggested: {default}):",
        choices=['None', 'Important', 'Critical'],
        default=default,
        style=custom_style
    ).ask()
    
    return safety


def get_compliance_codes() -> List[str]:
    """Prompt for compliance codes."""
    codes = questionary.checkbox(
        "Select applicable compliance codes:",
        choices=[
            'HIPAA-164.312(a)(1): Access Control',
            'HIPAA-164.312(a)(2)(i): Unique User ID',
            'HIPAA-164.312(e)(1): Transmission Security',
            'HIPAA-164.312(e)(2)(ii): Encryption',
            'SOX-404: Internal Controls',
            'SOX-302: CEO/CFO Certification',
            'FDA-21CFR11: Electronic Records',
            'FDA-CFR-820.30: Design Controls',
            '(none)',
        ],
        style=custom_style
    ).ask()
    
    if '(none)' in codes:
        return []
    
    # Extract just the code part (e.g., "HIPAA-164.312(a)(1)")
    return [code.split(':')[0].strip() for code in codes]


def get_hipaa_required(context: Dict) -> bool:
    """Prompt for HIPAA applicability."""
    default = 'Yes' if context['suggested_hipaa'] else 'No'
    
    result = questionary.select(
        f"Is HIPAA applicable? (suggested: {default}):",
        choices=['Yes', 'No'],
        default=default,
        style=custom_style
    ).ask()
    
    return result == 'Yes'


def get_audit_trail() -> str:
    """Prompt for audit trail ticket."""
    ticket = questionary.text(
        "Enter audit trail ticket (e.g., JIRA-1234, or leave empty):",
        style=custom_style
    ).ask()
    
    return ticket if ticket else 'N/A'


def get_body() -> Optional[str]:
    """Prompt for extended commit body."""
    add_body = questionary.confirm(
        "Add extended description (body)?",
        default=False,
        style=custom_style
    ).ask()
    
    if add_body:
        body = questionary.text(
            "Enter extended description:",
            multiline=True,
            style=custom_style
        ).ask()
        return body
    
    return None


def build_commit_message(
    commit_type: str,
    scope: Optional[str],
    description: str,
    risk_level: str,
    phi_impact: str,
    clinical_safety: str,
    compliance_codes: List[str],
    hipaa_required: bool,
    audit_trail: str,
    body: Optional[str]
) -> str:
    """Build the final commit message."""
    # Extract type prefix (before colon and emoji)
    type_prefix = commit_type.split(':')[0]
    
    # Build subject line
    if scope:
        subject = f"{type_prefix}({scope}): {description}"
    else:
        subject = f"{type_prefix}: {description}"
    
    # Build metadata section
    metadata = [
        "",
        f"Risk Level: {risk_level}",
        f"PHI-Impact: {phi_impact}",
        f"Clinical-Safety: {clinical_safety}",
    ]
    
    if compliance_codes:
        metadata.append(f"Compliance: {', '.join(compliance_codes)}")
    
    metadata.append(f"HIPAA-Required: {'Yes' if hipaa_required else 'No'}")
    metadata.append(f"Audit-Trail: {audit_trail}")
    
    # Combine all parts
    parts = [subject]
    
    if body:
        parts.append("")
        parts.append(body)
    
    parts.extend(metadata)
    
    return '\n'.join(parts)


def preview_commit_message(message: str) -> None:
    """Display a preview of the commit message."""
    print("\n" + "="*60)
    print("📝 COMMIT MESSAGE PREVIEW")
    print("="*60)
    print(message)
    print("="*60 + "\n")


def execute_commit(message: str) -> bool:
    """Execute the git commit with the generated message."""
    try:
        subprocess.run(
            ['git', 'commit', '-m', message],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing commit: {e}")
        return False


def main():
    """Main interactive flow."""
    print("\n🏥 Healthcare GitOps 2.0 - Interactive Commit Helper\n")
    
    # Check if there are staged changes
    changed_files = get_changed_files()
    
    if not changed_files:
        print("❌ No staged changes found. Stage your changes first with: git add <files>")
        sys.exit(1)
    
    print(f"✅ Found {len(changed_files)} staged file(s):\n")
    for file in changed_files[:10]:  # Show first 10
        print(f"   • {file}")
    if len(changed_files) > 10:
        print(f"   ... and {len(changed_files) - 10} more")
    print()
    
    # Analyze context
    context = analyze_changed_files(changed_files)
    
    # Interactive prompts
    try:
        commit_type = get_commit_type()
        scope = get_scope(context)
        description = get_description()
        risk_level = get_risk_level(context)
        phi_impact = get_phi_impact(context)
        clinical_safety = get_clinical_safety(context)
        compliance_codes = get_compliance_codes()
        hipaa_required = get_hipaa_required(context)
        audit_trail = get_audit_trail()
        body = get_body()
        
        # Build message
        message = build_commit_message(
            commit_type,
            scope,
            description,
            risk_level,
            phi_impact,
            clinical_safety,
            compliance_codes,
            hipaa_required,
            audit_trail,
            body
        )
        
        # Preview
        preview_commit_message(message)
        
        # Confirm
        proceed = questionary.confirm(
            "Proceed with this commit?",
            default=True,
            style=custom_style
        ).ask()
        
        if proceed:
            if execute_commit(message):
                print("✅ Commit created successfully!")
            else:
                print("❌ Commit failed")
                sys.exit(1)
        else:
            print("❌ Commit cancelled")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)


if __name__ == '__main__':
    main()
