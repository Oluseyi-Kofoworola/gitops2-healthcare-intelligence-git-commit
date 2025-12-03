"""
Audit Trail Export Module

Generates tamper-proof audit trails for compliance reporting.
Exports git history, CI/CD events, and policy decisions in
HIPAA/SOX/FDA-compliant formats.
"""

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class AuditEvent:
    """A single audit event."""
    timestamp: str
    event_type: str  # COMMIT, DEPLOY, POLICY_CHECK, ACCESS, etc.
    actor: str  # User or system that triggered event
    action: str  # What happened
    resource: str  # What was affected (file, service, etc.)
    outcome: str  # SUCCESS, FAILURE, BLOCKED
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: Optional[str] = None  # Cryptographic hash for integrity

    def __post_init__(self):
        """Calculate hash for tamper detection."""
        if not self.hash:
            self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of event data."""
        # Create deterministic string representation
        data = f"{self.timestamp}|{self.event_type}|{self.actor}|{self.action}|{self.resource}|{self.outcome}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify event hasn't been tampered with."""
        expected_hash = self._calculate_hash()
        return self.hash == expected_hash


@dataclass
class AuditTrail:
    """Complete audit trail."""
    start_date: str
    end_date: str
    events: List[AuditEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    chain_hash: Optional[str] = None  # Hash of entire chain

    def add_event(self, event: AuditEvent):
        """Add event to trail."""
        self.events.append(event)
        self._update_chain_hash()

    def _update_chain_hash(self):
        """Update chain hash for blockchain-like integrity."""
        if not self.events:
            self.chain_hash = ""
            return

        # Chain hash includes all event hashes
        combined = "".join(e.hash for e in self.events)
        self.chain_hash = hashlib.sha256(combined.encode()).hexdigest()

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify integrity of entire trail.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Verify each event
        for i, event in enumerate(self.events):
            if not event.verify_integrity():
                errors.append(f"Event {i} failed integrity check: {event.action}")

        # Verify chain hash
        old_hash = self.chain_hash
        self._update_chain_hash()
        if old_hash != self.chain_hash:
            errors.append("Chain hash mismatch - trail may have been modified")

        return len(errors) == 0, errors


class AuditExporter:
    """
    Exports audit trails from git history and external sources.
    """

    def __init__(self, repo_path: Path = None):
        """
        Initialize audit exporter.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = repo_path or Path.cwd()

    def export_git_history(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None
    ) -> AuditTrail:
        """
        Export git commit history as audit trail.

        Args:
            since: Start date (ISO format or git date)
            until: End date (ISO format or git date)
            author: Filter by author

        Returns:
            AuditTrail with commit events
        """
        # Build git log command
        cmd = [
            "git", "log",
            "--format=%H|%an|%ae|%ai|%s",
            "--name-status"
        ]

        if since:
            cmd.append(f"--since={since}")
        if until:
            cmd.append(f"--until={until}")
        if author:
            cmd.append(f"--author={author}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            events = self._parse_git_log(result.stdout)

            trail = AuditTrail(
                start_date=since or "beginning",
                end_date=until or "now",
                metadata={
                    "source": "git",
                    "repository": str(self.repo_path),
                    "total_commits": len(events)
                }
            )

            for event in events:
                trail.add_event(event)

            return trail

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error reading git log:[/red] {e.stderr}")
            return AuditTrail(start_date="", end_date="")

    def _parse_git_log(self, log_output: str) -> List[AuditEvent]:
        """Parse git log output into audit events."""
        events = []
        lines = log_output.strip().split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line:
                i += 1
                continue

            # Parse commit line
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 5:
                    commit_sha = parts[0]
                    author_name = parts[1]
                    author_email = parts[2]
                    timestamp = parts[3]
                    subject = "|".join(parts[4:])  # Re-join in case subject had |

                    # Parse file changes
                    files_changed = []
                    i += 1
                    while i < len(lines) and lines[i] and not "|" in lines[i]:
                        file_line = lines[i].strip()
                        if file_line:
                            files_changed.append(file_line)
                        i += 1

                    # Create audit event
                    event = AuditEvent(
                        timestamp=timestamp,
                        event_type="COMMIT",
                        actor=f"{author_name} <{author_email}>",
                        action=subject,
                        resource=commit_sha[:8],
                        outcome="SUCCESS",
                        metadata={
                            "commit_sha": commit_sha,
                            "files_changed": files_changed
                        }
                    )
                    events.append(event)
                    continue

            i += 1

        return events

    def export_deployment_events(
        self,
        ci_logs_path: Optional[Path] = None
    ) -> AuditTrail:
        """
        Export deployment events from CI/CD logs.

        Args:
            ci_logs_path: Path to CI/CD log files

        Returns:
            AuditTrail with deployment events
        """
        trail = AuditTrail(
            start_date=datetime.utcnow().isoformat(),
            end_date=datetime.utcnow().isoformat(),
            metadata={"source": "ci_cd"}
        )

        # This is a placeholder - in production, integrate with actual CI/CD
        # systems (GitHub Actions, GitLab CI, Jenkins, etc.)
        
        if ci_logs_path and ci_logs_path.exists():
            # Parse CI logs (format depends on CI system)
            try:
                with open(ci_logs_path, 'r') as f:
                    # Simplified parser - customize for your CI system
                    for line in f:
                        if "deploy" in line.lower():
                            event = AuditEvent(
                                timestamp=datetime.utcnow().isoformat(),
                                event_type="DEPLOY",
                                actor="CI/CD System",
                                action=line.strip(),
                                resource="production",
                                outcome="SUCCESS"
                            )
                            trail.add_event(event)
            except Exception as e:
                console.print(f"[yellow]Warning parsing CI logs:[/yellow] {e}")

        return trail

    def export_policy_decisions(
        self,
        policy_logs_path: Optional[Path] = None
    ) -> AuditTrail:
        """
        Export policy check results.

        Args:
            policy_logs_path: Path to policy decision logs

        Returns:
            AuditTrail with policy events
        """
        trail = AuditTrail(
            start_date=datetime.utcnow().isoformat(),
            end_date=datetime.utcnow().isoformat(),
            metadata={"source": "policy_engine"}
        )

        # Placeholder for OPA decision logs
        # In production, query OPA decision log API
        
        return trail

    def merge_trails(self, *trails: AuditTrail) -> AuditTrail:
        """
        Merge multiple audit trails into one.

        Args:
            *trails: Variable number of AuditTrail objects

        Returns:
            Combined AuditTrail
        """
        all_events = []
        for trail in trails:
            all_events.extend(trail.events)

        # Sort by timestamp
        all_events.sort(key=lambda e: e.timestamp)

        # Determine date range
        if all_events:
            start_date = all_events[0].timestamp
            end_date = all_events[-1].timestamp
        else:
            start_date = end_date = datetime.utcnow().isoformat()

        merged = AuditTrail(
            start_date=start_date,
            end_date=end_date,
            metadata={"merged_from": len(trails)}
        )

        for event in all_events:
            merged.add_event(event)

        return merged

    def export_to_json(
        self,
        trail: AuditTrail,
        output_path: Path,
        pretty: bool = True
    ):
        """
        Export audit trail to JSON.

        Args:
            trail: AuditTrail to export
            output_path: Output file path
            pretty: Pretty-print JSON
        """
        data = {
            "start_date": trail.start_date,
            "end_date": trail.end_date,
            "total_events": len(trail.events),
            "chain_hash": trail.chain_hash,
            "metadata": trail.metadata,
            "events": [asdict(e) for e in trail.events]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2 if pretty else None)

        console.print(f"[green]✓[/green] Exported {len(trail.events)} events to {output_path}")

    def export_to_csv(
        self,
        trail: AuditTrail,
        output_path: Path
    ):
        """
        Export audit trail to CSV.

        Args:
            trail: AuditTrail to export
            output_path: Output file path
        """
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Timestamp",
                "Event Type",
                "Actor",
                "Action",
                "Resource",
                "Outcome",
                "Hash"
            ])

            # Events
            for event in trail.events:
                writer.writerow([
                    event.timestamp,
                    event.event_type,
                    event.actor,
                    event.action,
                    event.resource,
                    event.outcome,
                    event.hash
                ])

        console.print(f"[green]✓[/green] Exported {len(trail.events)} events to {output_path}")

    def export_to_markdown(
        self,
        trail: AuditTrail,
        output_path: Path
    ):
        """
        Export audit trail to Markdown report.

        Args:
            trail: AuditTrail to export
            output_path: Output file path
        """
        lines = [
            "# Audit Trail Report",
            "",
            f"**Period**: {trail.start_date} to {trail.end_date}",
            f"**Total Events**: {len(trail.events)}",
            f"**Chain Hash**: `{trail.chain_hash}`",
            "",
            "## Integrity Verification",
            ""
        ]

        is_valid, errors = trail.verify_integrity()
        if is_valid:
            lines.append("✓ **Status**: VERIFIED - Audit trail integrity confirmed")
        else:
            lines.append("✗ **Status**: COMPROMISED - Integrity check failed")
            lines.append("")
            lines.append("**Errors**:")
            for error in errors:
                lines.append(f"- {error}")

        lines.extend([
            "",
            "## Event Summary",
            ""
        ])

        # Count by type
        type_counts = {}
        outcome_counts = {}
        for event in trail.events:
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1
            outcome_counts[event.outcome] = outcome_counts.get(event.outcome, 0) + 1

        lines.append("### By Event Type")
        lines.append("")
        for event_type, count in sorted(type_counts.items()):
            lines.append(f"- **{event_type}**: {count}")

        lines.append("")
        lines.append("### By Outcome")
        lines.append("")
        for outcome, count in sorted(outcome_counts.items()):
            lines.append(f"- **{outcome}**: {count}")

        lines.extend([
            "",
            "## Event Details",
            ""
        ])

        for i, event in enumerate(trail.events[:100], 1):  # Limit to first 100
            lines.extend([
                f"### Event {i}: {event.event_type}",
                f"- **Timestamp**: {event.timestamp}",
                f"- **Actor**: {event.actor}",
                f"- **Action**: {event.action}",
                f"- **Resource**: {event.resource}",
                f"- **Outcome**: {event.outcome}",
                f"- **Hash**: `{event.hash}`",
                ""
            ])

        if len(trail.events) > 100:
            lines.append(f"*... and {len(trail.events) - 100} more events*")

        with open(output_path, 'w') as f:
            f.write("\n".join(lines))

        console.print(f"[green]✓[/green] Exported markdown report to {output_path}")

    def generate_summary(self, trail: AuditTrail):
        """
        Print summary table to console.

        Args:
            trail: AuditTrail to summarize
        """
        # Summary table
        table = Table(title="Audit Trail Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Period", f"{trail.start_date} to {trail.end_date}")
        table.add_row("Total Events", str(len(trail.events)))
        table.add_row("Chain Hash", trail.chain_hash[:16] + "..." if trail.chain_hash else "N/A")

        # Integrity check
        is_valid, _ = trail.verify_integrity()
        integrity_status = "[green]✓ VERIFIED[/green]" if is_valid else "[red]✗ COMPROMISED[/red]"
        table.add_row("Integrity", integrity_status)

        console.print(table)

        # Event type breakdown
        type_table = Table(title="Events by Type")
        type_table.add_column("Event Type", style="yellow")
        type_table.add_column("Count", justify="right")

        type_counts = {}
        for event in trail.events:
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1

        for event_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            type_table.add_row(event_type, str(count))

        console.print(type_table)


def run_audit_export(
    output_path: Path,
    since: Optional[str] = None,
    until: Optional[str] = None,
    format: str = "json",
    repo_path: Optional[Path] = None
) -> int:
    """
    CLI entry point for audit export.

    Returns:
        Exit code (0 = success, 1 = no events, 2 = error)
    """
    try:
        exporter = AuditExporter(repo_path=repo_path)

        console.print("[cyan]Exporting audit trail...[/cyan]")
        
        # Export git history
        trail = exporter.export_git_history(since=since, until=until)

        if not trail.events:
            console.print("[yellow]No events found in specified date range[/yellow]")
            return 1

        # Generate summary
        exporter.generate_summary(trail)

        # Export to file
        if format == "json":
            exporter.export_to_json(trail, output_path)
        elif format == "csv":
            exporter.export_to_csv(trail, output_path)
        elif format == "markdown":
            exporter.export_to_markdown(trail, output_path)
        else:
            console.print(f"[red]Unknown format: {format}[/red]")
            return 2

        return 0

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        return 2
