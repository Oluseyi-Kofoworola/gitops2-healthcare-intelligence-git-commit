"""
AI Readiness Scanner CLI

Scans repository for AI-readiness compliance:
- PHI logging violations
- Encryption at rest/transit
- AI prompt safety
- Third-party dependency audits

Usage:
    python -m src.ai_readiness.cli --format markdown
    python -m src.ai_readiness.cli --format json > report.json
"""

import sys
import os
import json
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
import yaml

console = Console()


@click.command()
@click.option('--format', type=click.Choice(['markdown', 'json'], case_sensitive=False), default='markdown')
@click.option('--manifest', default='.ai/manifest.yml', help='Path to AI manifest')
@click.option('--fail-on', type=click.Choice(['critical', 'high', 'medium'], case_sensitive=False), 
              default='critical', help='Exit with error on this severity or higher')
def main(format, manifest, fail_on):
    """
    Scan repository for AI readiness and PHI compliance.
    
    This checks:
    - No PHI in log statements
    - Encryption at rest for sensitive data
    - AI prompt safety (no PHI in context)
    - Third-party dependency compliance
    """
    console.print(Panel.fit(
        "[bold magenta]AI Readiness Scanner[/bold magenta]\n"
        "[dim]Healthcare PHI Compliance Engine[/dim]",
        border_style="magenta"
    ))
    
    # Load AI manifest
    if not os.path.exists(manifest):
        console.print(f"[red]Error:[/red] AI manifest not found: {manifest}", style="bold")
        sys.exit(1)
    
    with open(manifest, 'r') as f:
        ai_config = yaml.safe_load(f)
    
    console.print(f"\n[cyan]Loaded AI manifest:[/cyan] {manifest}")
    console.print(f"[cyan]Project:[/cyan] {ai_config['project']['name']}\n")
    
    # Run all checks
    results = run_all_checks(ai_config)
    
    # Display results
    if format == 'markdown':
        display_markdown_report(results)
    else:
        print(json.dumps(results, indent=2))
    
    # Determine exit code
    severity_levels = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
    fail_level = severity_levels[fail_on]
    
    max_severity = 0
    for check in results['checks']:
        if not check['passed']:
            max_severity = max(max_severity, severity_levels[check['severity']])
    
    if max_severity >= fail_level:
        console.print(f"\n[red]❌ AI readiness check failed (severity >= {fail_on})[/red]\n")
        sys.exit(1)
    
    console.print("\n[green]✅ AI readiness check passed![/green]\n")
    sys.exit(0)


def run_all_checks(ai_config: dict) -> dict:
    """Run all AI readiness checks."""
    checks = []
    
    phi_paths = ai_config.get('data_classification', {}).get('phi_sensitive_paths', [])
    
    # Check 1: PHI in logging
    console.print("[cyan]🔍 Running check:[/cyan] PHI logging violations...")
    phi_log_result = check_phi_logging(phi_paths)
    checks.append(phi_log_result)
    
    # Check 2: Encryption at rest
    console.print("[cyan]🔍 Running check:[/cyan] Encryption at rest...")
    encryption_result = check_encryption_at_rest(phi_paths)
    checks.append(encryption_result)
    
    # Check 3: AI prompt safety
    console.print("[cyan]🔍 Running check:[/cyan] AI prompt safety...")
    prompt_safety_result = check_ai_prompt_safety(phi_paths)
    checks.append(prompt_safety_result)
    
    # Check 4: Third-party dependencies
    console.print("[cyan]🔍 Running check:[/cyan] Third-party dependencies...")
    dependency_result = check_third_party_dependencies()
    checks.append(dependency_result)
    
    return {
        'summary': {
            'total_checks': len(checks),
            'passed': sum(1 for c in checks if c['passed']),
            'failed': sum(1 for c in checks if not c['passed']),
        },
        'checks': checks
    }


def check_phi_logging(phi_paths: list) -> dict:
    """Check for PHI in log statements."""
    violations = []
    forbidden_log_terms = ['patient_id', 'ssn', 'medical_record_number', 'mrn', 'dob', 'credit_card']
    
    # Scan Python files in PHI paths
    for path_pattern in phi_paths:
        for py_file in Path('.').rglob('*.py'):
            if any(pattern.replace('**', '') in str(py_file) for pattern in phi_paths):
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if 'log' in line.lower() or 'print' in line.lower():
                            for term in forbidden_log_terms:
                                if term in line.lower():
                                    violations.append(f"{py_file}:{line_num} - {line.strip()}")
    
    return {
        'name': 'phi_logging_check',
        'description': 'Ensure no PHI in log statements',
        'severity': 'critical',
        'passed': len(violations) == 0,
        'violations': violations[:10],  # Limit to 10
        'total_violations': len(violations)
    }


def check_encryption_at_rest(phi_paths: list) -> dict:
    """Check for encryption configuration in PHI services."""
    violations = []
    
    # Look for encryption configuration
    encryption_keywords = ['encrypt', 'aes', 'crypto', 'cipher']
    found_encryption = False
    
    for path_pattern in phi_paths:
        # Combine Python and Go files
        py_files = list(Path('.').rglob('*.py'))
        go_files = list(Path('.').rglob('*.go'))
        all_files = py_files + go_files
        
        for code_file in all_files:
            if any(pattern.replace('**', '') in str(code_file) for pattern in phi_paths):
                with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in encryption_keywords):
                        found_encryption = True
                        break
    
    if not found_encryption:
        violations.append("No encryption implementation found in PHI-sensitive paths")
    
    return {
        'name': 'encryption_at_rest',
        'description': 'Verify PHI storage uses approved encryption',
        'severity': 'critical',
        'passed': found_encryption,
        'violations': violations,
        'total_violations': len(violations)
    }


def check_ai_prompt_safety(phi_paths: list) -> dict:
    """Check for PHI in AI tool prompts/context."""
    violations = []
    ai_tool_keywords = ['openai', 'copilot', 'gpt', 'llm', 'ai_prompt']
    phi_keywords = ['patient', 'medical_record', 'ssn', 'dob']
    
    # Scan for AI tool usage near PHI keywords
    for code_file in Path('.').rglob('*.py'):
        with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            if any(ai_tool in content for ai_tool in ai_tool_keywords):
                if any(phi_kw in content for phi_kw in phi_keywords):
                    violations.append(f"{code_file} - AI tool usage near PHI keywords")
    
    return {
        'name': 'ai_prompt_safety',
        'description': 'Check for PHI in AI tool prompts',
        'severity': 'high',
        'passed': len(violations) == 0,
        'violations': violations[:10],
        'total_violations': len(violations)
    }


def check_third_party_dependencies() -> dict:
    """Audit third-party dependencies for compliance."""
    violations = []
    
    # Check if requirements.txt exists
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            deps = f.readlines()
            # Placeholder: In real implementation, cross-reference with approved list
            if len(deps) > 50:
                violations.append(f"High dependency count ({len(deps)}) - recommend audit")
    
    return {
        'name': 'third_party_dependencies',
        'description': 'Audit dependencies for HIPAA compliance',
        'severity': 'medium',
        'passed': len(violations) == 0,
        'violations': violations,
        'total_violations': len(violations)
    }


def display_markdown_report(results: dict):
    """Display results in rich markdown format."""
    
    # Summary table
    summary_table = Table(title="\n📊 AI Readiness Summary", box=None)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="bold")
    
    summary_table.add_row("Total Checks", str(results['summary']['total_checks']))
    summary_table.add_row("Passed", f"[green]{results['summary']['passed']}[/green]")
    summary_table.add_row("Failed", f"[red]{results['summary']['failed']}[/red]")
    
    console.print(summary_table)
    
    # Individual check results
    console.print("\n[bold cyan]📋 Check Details:[/bold cyan]\n")
    
    for check in results['checks']:
        status = "[green]✅ PASS[/green]" if check['passed'] else "[red]❌ FAIL[/red]"
        severity_color = {
            'critical': 'red',
            'high': 'orange1',
            'medium': 'yellow',
            'low': 'blue'
        }.get(check['severity'], 'white')
        
        console.print(f"{status} [{severity_color}][{check['severity'].upper()}][/{severity_color}] {check['name']}")
        console.print(f"    {check['description']}")
        
        if check['violations']:
            console.print(f"    [red]Violations ({check['total_violations']}):[/red]")
            for violation in check['violations'][:5]:  # Show first 5
                console.print(f"      • {violation}")
            if check['total_violations'] > 5:
                console.print(f"      ... and {check['total_violations'] - 5} more")
        console.print()


if __name__ == '__main__':
    main()
