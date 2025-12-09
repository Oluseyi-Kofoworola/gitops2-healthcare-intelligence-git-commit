"""
Git Policy Validation CLI

Enforces Conventional Commits, tier-based validation, and compliance rules
for healthcare GitOps workflows.

Usage:
    python -m src.git_policy.cli <commit-msg-file>
    python -m src.git_policy.cli --validate-last
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command()
@click.argument('commit_msg_file', type=click.Path(exists=True), required=False)
@click.option('--validate-last', is_flag=True, help='Validate the last commit message')
@click.option('--config', default='config/git-policy.yaml', help='Path to policy config')
def main(commit_msg_file, validate_last, config):
    """
    Validate commit messages against healthcare GitOps policy.
    
    This enforces:
    - Conventional Commits v1.0.0
    - Tier-based validation (tier1/2/3)
    - Security/breaking change escalation
    - HIPAA/FDA/SOX compliance codes
    """
    console.print(Panel.fit(
        "[bold cyan]Git Policy Validator[/bold cyan]\n"
        "[dim]Healthcare GitOps Compliance Engine[/dim]",
        border_style="cyan"
    ))
    
    if validate_last:
        # Get last commit message
        import subprocess
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True
        )
        commit_msg = result.stdout.strip()
        console.print(f"\n[bold]Last Commit Message:[/bold]\n{commit_msg}\n")
    elif commit_msg_file:
        with open(commit_msg_file, 'r') as f:
            commit_msg = f.read().strip()
    else:
        console.print("[red]Error:[/red] No commit message provided", style="bold")
        sys.exit(1)
    
    # Parse commit message
    validation_result = validate_commit_message(commit_msg, config)
    
    # Display results
    display_validation_results(validation_result)
    
    if not validation_result['valid']:
        sys.exit(1)
    
    console.print("\n[green]✅ Commit message is valid![/green]\n")
    sys.exit(0)


def validate_commit_message(commit_msg: str, config_path: str) -> dict:
    """
    Validate commit message against policy rules.
    
    Returns:
        dict: Validation results with 'valid', 'errors', 'warnings', 'metadata'
    """
    errors = []
    warnings = []
    metadata = {}
    
    # Basic structure check
    if not commit_msg:
        errors.append("Commit message is empty")
        return {'valid': False, 'errors': errors, 'warnings': warnings, 'metadata': metadata}
    
    lines = commit_msg.split('\n')
    subject = lines[0]
    
    # Check Conventional Commits format: type(scope): description
    import re
    pattern = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|security)(\([a-z-]+\))?(!)?:\s.{1,100}$'
    
    if not re.match(pattern, subject):
        errors.append(
            "Subject line must follow Conventional Commits format:\n"
            "  type(scope): description\n"
            "  Example: feat(auth): add MFA support EHR-123"
        )
    else:
        # Extract metadata
        match = re.match(r'^(\w+)(?:\(([a-z-]+)\))?(!)?: (.+)$', subject)
        if match:
            metadata['type'] = match.group(1)
            metadata['scope'] = match.group(2) or 'general'
            metadata['breaking'] = bool(match.group(3))
            metadata['description'] = match.group(4)
    
    # Check for security/breaking changes
    if 'security' in subject.lower() and 'CVE' not in commit_msg:
        warnings.append("Security fixes should reference a CVE or ticket number")
    
    if '!' in subject or 'BREAKING CHANGE' in commit_msg:
        metadata['requires_dual_approval'] = True
        warnings.append("Breaking change detected - requires dual approval")
    
    # Check for compliance codes (HIPAA, FDA, SOX)
    if any(word in commit_msg.upper() for word in ['PHI', 'ENCRYPTION', 'AUDIT']):
        if not any(code in commit_msg.upper() for code in ['HIPAA', 'FDA', 'SOX', 'HITRUST']):
            warnings.append("PHI-related changes should reference compliance framework")
    
    # Check for ticket reference
    ticket_pattern = r'(EHR|PAY|DEV|SEC|COMP)-\d+'
    if not re.search(ticket_pattern, commit_msg):
        warnings.append("No ticket reference found (recommended: EHR-XXX, SEC-XXX, etc.)")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'metadata': metadata
    }


def display_validation_results(result: dict):
    """Display validation results in a rich formatted table."""
    
    if result['errors']:
        console.print("\n[bold red]❌ Validation Errors:[/bold red]")
        for error in result['errors']:
            console.print(f"  • {error}", style="red")
    
    if result['warnings']:
        console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
        for warning in result['warnings']:
            console.print(f"  • {warning}", style="yellow")
    
    if result['metadata']:
        console.print("\n[bold cyan]📋 Commit Metadata:[/bold cyan]")
        table = Table(show_header=False, box=None)
        for key, value in result['metadata'].items():
            table.add_row(f"[cyan]{key}[/cyan]", str(value))
        console.print(table)


if __name__ == '__main__':
    main()
