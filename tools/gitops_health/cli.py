#!/usr/bin/env python3
"""
GitOps Health CLI - Main Command Line Interface

Unified CLI for AI-native healthcare engineering intelligence.
Commands: commit, compliance, risk, forensics, audit, sanitize
"""

import click
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from pathlib import Path

from .risk import RiskScorer
from .compliance import ComplianceChecker, run_compliance_check
from .bisect import IntelligentBisect, run_bisect
from .commitgen import CommitGenerator, run_commit_generator
from .sanitize import PHISanitizer, run_sanitizer
from .audit import AuditExporter, run_audit_export
from .config import load_config
from .logging import setup_logging

console = Console()


@click.group()
@click.version_option(version="2.0.0")
@click.option("--config", type=click.Path(), help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config, verbose):
    """GitOps Health - AI-Native Healthcare Engineering Intelligence"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["logger"] = setup_logging(verbose)


# ============================================================================
# COMMIT COMMANDS
# ============================================================================


@cli.group()
def commit():
    """Commit message generation and validation"""
    pass


@commit.command("generate")
@click.option("--context", is_flag=True, help="Include AI analysis of changes")
@click.option("--template", type=click.Choice(["feat", "fix", "docs", "style", "refactor", "test", "chore"]))
@click.option("--scope", help="Commit scope (e.g., payment, auth)")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.option("--dry-run", is_flag=True, help="Preview without committing")
@click.option("--output", "-o", type=click.Path(), help="Save to file")
@click.pass_context
def commit_generate(ctx, context, template, scope, interactive, dry_run, output):
    """Generate AI-powered commit messages"""
    try:
        generator = CommitGenerator(ctx.obj["config"])
        
        if interactive:
            message = generator.generate_interactive()
        else:
            message = generator.generate(
                context=context,
                template=template,
                scope=scope
            )
        
        if output:
            Path(output).write_text(message)
            console.print(f"✅ Commit message saved to {output}", style="green")
        else:
            console.print("\n[bold]Generated Commit Message:[/bold]")
            console.print(f"\n{message}\n", style="cyan")
        
        if not dry_run and click.confirm("Commit with this message?"):
            import subprocess
            subprocess.run(["git", "commit", "-m", message])
            console.print("✅ Committed successfully", style="green")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


# ============================================================================
# COMPLIANCE COMMANDS
# ============================================================================


@cli.group()
def compliance():
    """Compliance analysis and validation"""
    pass


@compliance.command("analyze")
@click.option("--frameworks", default="HIPAA,FDA,SOX", help="Comma-separated frameworks")
@click.option("--commit", default="HEAD", help="Commit to analyze")
@click.option("--since", help="Analyze commits since date")
@click.option("--branch", help="Analyze entire branch")
@click.option("--output", "-o", type=click.Choice(["json", "yaml", "html", "pdf"]), default="json")
@click.option("--severity", type=click.Choice(["low", "medium", "high", "critical"]), default="low")
@click.option("--fail-on-violations", is_flag=True, help="Exit 1 if violations found")
@click.pass_context
def compliance_analyze(ctx, frameworks, commit, since, branch, output, severity, fail_on_violations):
    """Analyze commits for compliance violations"""
    try:
        analyzer = ComplianceAnalyzer(
            ctx.obj["config"],
            frameworks=frameworks.split(",")
        )
        
        result = analyzer.analyze(
            commit=commit,
            since=since,
            branch=branch,
            min_severity=severity
        )
        
        # Display results
        table = Table(title="Compliance Analysis Results")
        table.add_column("Framework", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Violations", style="red")
        
        for framework, data in result.frameworks.items():
            status_icon = "✅" if data.status == "PASS" else "❌"
            table.add_row(
                framework,
                f"{status_icon} {data.status}",
                str(len(data.violations))
            )
        
        console.print(table)
        
        # Show violations
        if result.has_violations():
            console.print("\n[bold red]Violations Found:[/bold red]")
            for violation in result.violations:
                console.print(f"  • {violation.framework}: {violation.message}", style="red")
                console.print(f"    Severity: {violation.severity}", style="yellow")
                console.print(f"    Remediation: {violation.remediation}\n", style="blue")
        
        # Save output
        result.save(output)
        
        if fail_on_violations and result.has_violations():
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


# ============================================================================
# RISK COMMANDS
# ============================================================================


@cli.group()
def risk():
    """Risk scoring and assessment"""
    pass


@risk.command("score")
@click.option("--commit", default="HEAD", help="Commit to score")
@click.option("--explain", is_flag=True, help="Show detailed breakdown")
@click.option("--recommend-strategy", is_flag=True, help="Suggest deployment strategy")
@click.option("--historical", is_flag=True, help="Include historical analysis")
@click.option("--output", "-o", type=click.Choice(["json", "text", "table"]), default="text")
@click.pass_context
def risk_score(ctx, commit, explain, recommend_strategy, historical, output):
    """Calculate risk score for commits"""
    try:
        scorer = RiskScorer(ctx.obj["config"])
        result = scorer.score_commit(commit, include_history=historical)
        
        if output == "text":
            console.print(f"\n[bold]Risk Score: {result.overall_score}/100[/bold]", style="cyan")
            console.print(f"Category: {result.category}", style="yellow")
            console.print(f"Deployment Strategy: {result.deployment_strategy}\n", style="green")
            
            if explain:
                table = Table(title="Risk Factors")
                table.add_column("Factor", style="cyan")
                table.add_column("Score", style="yellow")
                table.add_column("Weight", style="green")
                
                for factor in result.factors:
                    table.add_row(factor.name, str(factor.score), str(factor.weight))
                
                console.print(table)
        
        elif output == "json":
            import json
            console.print(json.dumps(result.to_dict(), indent=2))
        
        if recommend_strategy:
            console.print(f"\n💡 Recommended Deployment Strategy: [bold]{result.deployment_strategy}[/bold]")
            console.print("\nRecommendations:")
            for rec in result.recommendations:
                console.print(f"  • {rec}", style="blue")
                
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


# ============================================================================
# FORENSICS COMMANDS
# ============================================================================


@cli.group()
def forensics():
    """Intelligent forensics and debugging"""
    pass


@forensics.command("bisect")
@click.option("--good", required=True, help="Known good commit/tag")
@click.option("--bad", default="HEAD", help="Known bad commit/tag")
@click.option("--test-command", required=True, help="Command to test each commit")
@click.option("--parallel", "-j", default=1, type=int, help="Parallel test jobs")
@click.option("--timeout", default=300, type=int, help="Test timeout (seconds)")
@click.option("--ml-guidance/--no-ml-guidance", default=True, help="Use ML prioritization")
@click.option("--output", "-o", type=click.Path(), help="Save detailed report")
@click.pass_context
def forensics_bisect(ctx, good, bad, test_command, parallel, timeout, ml_guidance, output):
    """AI-powered git bisect for regression identification"""
    try:
        bisect = IntelligentBisect(ctx.obj["config"])
        
        console.print(f"\n🔍 Intelligent Bisect Started", style="bold blue")
        console.print(f"Range: {good} (good) → {bad} (bad)")
        console.print(f"Test: {test_command}\n")
        
        result = bisect.find_regression(
            good_commit=good,
            bad_commit=bad,
            test_command=test_command,
            parallel_jobs=parallel,
            timeout=timeout,
            ml_guidance=ml_guidance
        )
        
        if result.culprit_found:
            console.print(f"\n🎯 [bold green]Regression Found![/bold green]")
            console.print(f"Culprit Commit: {result.culprit_commit.short_hash}")
            console.print(f"Author: {result.culprit_commit.author}")
            console.print(f"Date: {result.culprit_commit.date}")
            console.print(f"Message: {result.culprit_commit.message}\n")
            
            console.print(f"[bold]Root Cause:[/bold]")
            console.print(f"  {result.root_cause}\n")
            
            console.print(f"[bold]Remediation Options:[/bold]")
            for i, option in enumerate(result.remediation_options, 1):
                recommended = " ⭐" if option.recommended else ""
                console.print(f"  {i}. {option.name}{recommended}")
                console.print(f"     {option.description}")
                console.print(f"     Time: {option.estimated_time}\n")
            
            console.print(f"📊 Bisect Stats:")
            console.print(f"  Steps taken: {result.steps_taken}")
            console.print(f"  Traditional steps: {result.traditional_steps_estimate}")
            console.print(f"  Time saved: {result.time_saved}")
            console.print(f"  Efficiency: {result.efficiency_gain}%\n")
        else:
            console.print("❌ Regression not found in range", style="red")
        
        if output:
            result.save_report(output)
            console.print(f"📄 Detailed report saved to {output}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


# ============================================================================
# AUDIT COMMANDS
# ============================================================================


@cli.group()
def audit():
    """Audit trail generation and export"""
    pass


@audit.command("export")
@click.option("--framework", type=click.Choice(["HIPAA", "FDA", "SOX"]), required=True)
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD, default: today)")
@click.option("--format", "-f", type=click.Choice(["json", "csv", "pdf", "xlsx"]), default="pdf")
@click.option("--include-evidence", is_flag=True, help="Include supporting evidence")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file")
@click.pass_context
def audit_export(ctx, framework, start_date, end_date, format, include_evidence, output):
    """Export compliance audit trail"""
    try:
        exporter = AuditExporter(ctx.obj["config"])
        
        console.print(f"\n📋 Generating {framework} audit trail...")
        console.print(f"Period: {start_date} to {end_date or 'today'}\n")
        
        result = exporter.export(
            framework=framework,
            start_date=start_date,
            end_date=end_date,
            format=format,
            include_evidence=include_evidence,
            output_path=output
        )
        
        console.print(f"✅ Audit trail exported to {output}", style="green")
        console.print(f"\nRecords included: {result.record_count}")
        console.print(f"Evidence files: {result.evidence_count}")
        console.print(f"File size: {result.file_size}\n")
        
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


# ============================================================================
# SANITIZE COMMANDS
# ============================================================================


@cli.command("sanitize")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Preview without modifying")
@click.option("--replace-with", type=click.Choice(["synthetic", "redacted", "placeholder"]), default="synthetic")
@click.option("--preserve-format", is_flag=True, help="Keep original data format")
@click.option("--output-report", "-o", type=click.Path(), help="Save sanitization report")
@click.pass_context
def sanitize(ctx, files, dry_run, replace_with, preserve_format, output_report):
    """Remove PHI from files before committing"""
    try:
        sanitizer = PHISanitizer(ctx.obj["config"])
        
        for file in files:
            console.print(f"\n🧹 Sanitizing: {file}")
            
            result = sanitizer.sanitize_file(
                file_path=file,
                dry_run=dry_run,
                replacement_strategy=replace_with,
                preserve_format=preserve_format
            )
            
            if result.phi_found:
                console.print(f"\nPHI Detected:")
                for detection in result.detections:
                    console.print(f"  - Line {detection.line}: {detection.phi_type}", style="yellow")
                    if not dry_run:
                        console.print(f"    {detection.original} → {detection.replacement}", style="green")
                
                if not dry_run:
                    console.print(f"\n✅ Sanitized {result.count} PHI instances", style="green")
                    console.print(f"Original backed up to: {result.backup_path}")
                else:
                    console.print(f"\n⚠️  Dry run - no changes made", style="yellow")
            else:
                console.print("✅ No PHI detected", style="green")
        
        if output_report:
            sanitizer.save_report(output_report)
            console.print(f"\n📄 Report saved to {output_report}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


# ============================================================================
# MAIN ENTRYPOINT
# ============================================================================


def main():
    """Main entry point for CLI"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n\n⚠️  Operation cancelled by user", style="yellow")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
