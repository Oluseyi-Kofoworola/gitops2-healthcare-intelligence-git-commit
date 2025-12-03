"""
PHI/PII Sanitization Module

Detects and removes Protected Health Information (PHI) and Personally
Identifiable Information (PII) from code, logs, and git history.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Tuple

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class SensitivePattern:
    """Definition of a sensitive data pattern."""
    name: str
    pattern: Pattern
    category: str  # PHI, PII, CREDENTIALS
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    example: str = ""


@dataclass
class Detection:
    """A detected instance of sensitive data."""
    pattern_name: str
    category: str
    severity: str
    file_path: str
    line_number: int
    line_content: str
    matched_text: str
    sanitized_text: str
    context: str = ""


@dataclass
class SanitizationReport:
    """Report of sanitization operation."""
    timestamp: str
    files_scanned: int
    detections: List[Detection] = field(default_factory=list)
    files_modified: int = 0
    dry_run: bool = True


class PHISanitizer:
    """
    Detects and sanitizes PHI/PII from files and git history.
    """

    # HIPAA-defined PHI identifiers (18 types)
    PHI_PATTERNS = [
        SensitivePattern(
            name="ssn",
            pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            category="PHI",
            severity="CRITICAL",
            description="Social Security Number",
            example="123-45-6789"
        ),
        SensitivePattern(
            name="mrn",
            pattern=re.compile(r'\b(?:MRN|mrn|medical.?record.?number)[\s:=]+\d{6,10}\b', re.IGNORECASE),
            category="PHI",
            severity="CRITICAL",
            description="Medical Record Number",
            example="MRN: 123456789"
        ),
        SensitivePattern(
            name="patient_name",
            pattern=re.compile(r'(?:patient|individual)[\s_]?(?:name|full.?name)[\s:=]+[A-Z][a-z]+ [A-Z][a-z]+', re.IGNORECASE),
            category="PHI",
            severity="HIGH",
            description="Patient Name",
            example="Patient Name: John Doe"
        ),
        SensitivePattern(
            name="email",
            pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            category="PII",
            severity="HIGH",
            description="Email Address",
            example="patient@example.com"
        ),
        SensitivePattern(
            name="phone",
            pattern=re.compile(r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            category="PII",
            severity="MEDIUM",
            description="Phone Number",
            example="(555) 123-4567"
        ),
        SensitivePattern(
            name="ip_address",
            pattern=re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            category="PII",
            severity="MEDIUM",
            description="IP Address",
            example="192.168.1.1"
        ),
        SensitivePattern(
            name="credit_card",
            pattern=re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            category="PII",
            severity="CRITICAL",
            description="Credit Card Number",
            example="4532-1234-5678-9010"
        ),
        SensitivePattern(
            name="api_key",
            pattern=re.compile(r'\b(?:api[_-]?key|apikey|api[_-]?secret)[\s:=]+[\'"]?([A-Za-z0-9_\-]{20,})[\'"]?', re.IGNORECASE),
            category="CREDENTIALS",
            severity="CRITICAL",
            description="API Key",
            example="api_key: sk_live_abcdef123456"
        ),
        SensitivePattern(
            name="password",
            pattern=re.compile(r'\b(?:password|passwd|pwd)[\s:=]+[\'"]?([^\s\'"]{8,})[\'"]?', re.IGNORECASE),
            category="CREDENTIALS",
            severity="CRITICAL",
            description="Password",
            example="password: MySecretPass123"
        ),
        SensitivePattern(
            name="jwt_token",
            pattern=re.compile(r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b'),
            category="CREDENTIALS",
            severity="HIGH",
            description="JWT Token",
            example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        ),
    ]

    def __init__(
        self,
        custom_patterns: Optional[List[SensitivePattern]] = None,
        hash_seed: str = "gitops-health"
    ):
        """
        Initialize sanitizer.

        Args:
            custom_patterns: Additional patterns to detect
            hash_seed: Seed for deterministic hashing
        """
        self.patterns = self.PHI_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        
        self.hash_seed = hash_seed

    def scan_file(self, file_path: Path) -> List[Detection]:
        """
        Scan a file for sensitive data.

        Args:
            file_path: Path to file to scan

        Returns:
            List of detections
        """
        detections = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern_def in self.patterns:
                    matches = pattern_def.pattern.finditer(line)
                    for match in matches:
                        matched_text = match.group(0)
                        sanitized = self._sanitize_text(matched_text, pattern_def.name)

                        detections.append(Detection(
                            pattern_name=pattern_def.name,
                            category=pattern_def.category,
                            severity=pattern_def.severity,
                            file_path=str(file_path),
                            line_number=line_num,
                            line_content=line.strip(),
                            matched_text=matched_text,
                            sanitized_text=sanitized
                        ))

        except Exception as e:
            console.print(f"[yellow]Warning: Could not scan {file_path}: {e}[/yellow]")

        return detections

    def scan_directory(
        self,
        directory: Path,
        exclude_patterns: Optional[List[str]] = None
    ) -> SanitizationReport:
        """
        Recursively scan directory for sensitive data.

        Args:
            directory: Directory to scan
            exclude_patterns: List of glob patterns to exclude

        Returns:
            SanitizationReport
        """
        exclude_patterns = exclude_patterns or [
            "*.git*",
            "*node_modules*",
            "*venv*",
            "*.pyc",
            "*__pycache__*",
            "*.jpg", "*.png", "*.gif",  # Binary files
        ]

        all_detections = []
        files_scanned = 0

        # Collect all files to scan
        files_to_scan = []
        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            # Check exclusions
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue

            files_to_scan.append(file_path)

        # Scan files
        for file_path in files_to_scan:
            detections = self.scan_file(file_path)
            all_detections.extend(detections)
            files_scanned += 1

            if detections:
                console.print(f"[yellow]⚠[/yellow] Found {len(detections)} issue(s) in {file_path}")

        return SanitizationReport(
            timestamp=datetime.utcnow().isoformat(),
            files_scanned=files_scanned,
            detections=all_detections,
            dry_run=True
        )

    def sanitize_file(
        self,
        file_path: Path,
        detections: List[Detection],
        dry_run: bool = True
    ) -> bool:
        """
        Sanitize a file by replacing sensitive data.

        Args:
            file_path: File to sanitize
            detections: List of detections in this file
            dry_run: If True, don't actually modify file

        Returns:
            True if file was modified (or would be in dry run)
        """
        if not detections:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            modified = False
            for detection in detections:
                line_idx = detection.line_number - 1
                if line_idx < len(lines):
                    old_line = lines[line_idx]
                    new_line = old_line.replace(
                        detection.matched_text,
                        detection.sanitized_text
                    )
                    if old_line != new_line:
                        lines[line_idx] = new_line
                        modified = True

            if modified and not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                console.print(f"[green]✓[/green] Sanitized {file_path}")

            return modified

        except Exception as e:
            console.print(f"[red]Error sanitizing {file_path}:[/red] {e}")
            return False

    def _sanitize_text(self, text: str, pattern_name: str) -> str:
        """
        Replace sensitive text with sanitized version.

        Strategies:
        - Hash: Deterministic hash for consistent redaction
        - Mask: Replace with *** or [REDACTED]
        - Placeholder: Replace with example value
        """
        # Use deterministic hashing for consistent redaction
        hash_input = f"{self.hash_seed}:{pattern_name}:{text}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]

        replacements = {
            "ssn": "XXX-XX-XXXX",
            "mrn": f"MRN: [REDACTED-{hash_value}]",
            "patient_name": "Patient Name: [REDACTED]",
            "email": f"user{hash_value}@example.com",
            "phone": "(XXX) XXX-XXXX",
            "ip_address": "XXX.XXX.XXX.XXX",
            "credit_card": "XXXX-XXXX-XXXX-XXXX",
            "api_key": f"[API_KEY_REDACTED_{hash_value}]",
            "password": "[PASSWORD_REDACTED]",
            "jwt_token": f"[JWT_REDACTED_{hash_value[:16]}]",
        }

        return replacements.get(pattern_name, f"[REDACTED-{hash_value}]")

    def generate_report(
        self,
        report: SanitizationReport,
        format: str = "table"
    ) -> str:
        """
        Generate sanitization report.

        Args:
            report: SanitizationReport to format
            format: Output format ('table', 'json', 'markdown')

        Returns:
            Formatted report
        """
        if format == "json":
            return json.dumps({
                "timestamp": report.timestamp,
                "files_scanned": report.files_scanned,
                "total_detections": len(report.detections),
                "by_severity": self._count_by_severity(report.detections),
                "by_category": self._count_by_category(report.detections),
                "detections": [
                    {
                        "pattern": d.pattern_name,
                        "category": d.category,
                        "severity": d.severity,
                        "file": d.file_path,
                        "line": d.line_number,
                        "matched": d.matched_text[:50] + "..." if len(d.matched_text) > 50 else d.matched_text
                    }
                    for d in report.detections
                ]
            }, indent=2)

        elif format == "markdown":
            lines = [
                "# PHI/PII Sanitization Report",
                "",
                f"**Timestamp**: {report.timestamp}",
                f"**Files Scanned**: {report.files_scanned}",
                f"**Total Detections**: {len(report.detections)}",
                "",
                "## Summary by Severity",
                ""
            ]

            severity_counts = self._count_by_severity(report.detections)
            for severity, count in severity_counts.items():
                lines.append(f"- **{severity}**: {count}")

            lines.extend([
                "",
                "## Summary by Category",
                ""
            ])

            category_counts = self._count_by_category(report.detections)
            for category, count in category_counts.items():
                lines.append(f"- **{category}**: {count}")

            lines.extend([
                "",
                "## Detections",
                ""
            ])

            for d in report.detections[:50]:  # Limit to first 50
                lines.extend([
                    f"### {d.severity}: {d.pattern_name}",
                    f"- **File**: `{d.file_path}:{d.line_number}`",
                    f"- **Category**: {d.category}",
                    f"- **Matched**: `{d.matched_text}`",
                    ""
                ])

            if len(report.detections) > 50:
                lines.append(f"... and {len(report.detections) - 50} more detections")

            return "\n".join(lines)

        else:  # table
            # Summary
            console.print(f"\n[cyan]Scanned {report.files_scanned} files[/cyan]")
            console.print(f"[yellow]Found {len(report.detections)} sensitive data instances[/yellow]\n")

            if not report.detections:
                console.print("[green]✓ No sensitive data detected[/green]")
                return ""

            # By severity table
            sev_table = Table(title="By Severity")
            sev_table.add_column("Severity", style="bold")
            sev_table.add_column("Count", justify="right")

            severity_counts = self._count_by_severity(report.detections)
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                if severity in severity_counts:
                    color = {
                        "CRITICAL": "red bold",
                        "HIGH": "red",
                        "MEDIUM": "yellow",
                        "LOW": "blue"
                    }[severity]
                    sev_table.add_row(
                        f"[{color}]{severity}[/{color}]",
                        str(severity_counts[severity])
                    )

            console.print(sev_table)

            # Detections table
            det_table = Table(title="Top Detections")
            det_table.add_column("Severity")
            det_table.add_column("Pattern")
            det_table.add_column("File")
            det_table.add_column("Line", justify="right")

            for d in report.detections[:20]:  # Show top 20
                severity_color = {
                    "CRITICAL": "red bold",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "blue"
                }.get(d.severity, "white")

                det_table.add_row(
                    f"[{severity_color}]{d.severity}[/{severity_color}]",
                    d.pattern_name,
                    Path(d.file_path).name,
                    str(d.line_number)
                )

            console.print(det_table)

            if len(report.detections) > 20:
                console.print(f"\n[dim]... and {len(report.detections) - 20} more detections[/dim]")

            return ""

    def _count_by_severity(self, detections: List[Detection]) -> Dict[str, int]:
        """Count detections by severity."""
        counts = {}
        for d in detections:
            counts[d.severity] = counts.get(d.severity, 0) + 1
        return counts

    def _count_by_category(self, detections: List[Detection]) -> Dict[str, int]:
        """Count detections by category."""
        counts = {}
        for d in detections:
            counts[d.category] = counts.get(d.category, 0) + 1
        return counts


def run_sanitizer(
    path: Path,
    dry_run: bool = True,
    format: str = "table"
) -> int:
    """
    CLI entry point for sanitizer.

    Returns:
        Exit code (0 = clean, 1 = detections found, 2 = error)
    """
    try:
        sanitizer = PHISanitizer()

        if path.is_file():
            detections = sanitizer.scan_file(path)
            report = SanitizationReport(
                timestamp=datetime.utcnow().isoformat(),
                files_scanned=1,
                detections=detections,
                dry_run=dry_run
            )
        else:
            report = sanitizer.scan_directory(path)

        # Generate report
        output = sanitizer.generate_report(report, format=format)
        if output:
            print(output)

        # Sanitize if not dry run
        if not dry_run and report.detections:
            console.print("\n[yellow]Sanitizing files...[/yellow]")
            files_by_path = {}
            for d in report.detections:
                if d.file_path not in files_by_path:
                    files_by_path[d.file_path] = []
                files_by_path[d.file_path].append(d)

            for file_path, file_detections in files_by_path.items():
                sanitizer.sanitize_file(Path(file_path), file_detections, dry_run=False)

        return 1 if report.detections else 0

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 2
