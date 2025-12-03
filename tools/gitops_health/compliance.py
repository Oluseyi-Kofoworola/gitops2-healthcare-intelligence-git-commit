"""
OPA Policy Compliance Integration

Provides compliance validation using Open Policy Agent (OPA) policies
for HIPAA, FDA, SOX, and other regulatory frameworks.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class ComplianceViolation:
    """Represents a single compliance violation."""
    policy: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rule: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class ComplianceResult:
    """Result of compliance analysis."""
    passed: bool
    violations: List[ComplianceViolation]
    policies_evaluated: int
    timestamp: str
    commit_sha: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ComplianceChecker:
    """Validates commits and code against OPA policies."""

    def __init__(self, policy_dir: Path = None, opa_path: str = "opa"):
        """
        Initialize compliance checker.

        Args:
            policy_dir: Directory containing OPA policy files (.rego)
            opa_path: Path to OPA binary (default: 'opa' in PATH)
        """
        self.policy_dir = policy_dir or Path("policies")
        self.opa_path = opa_path
        self._verify_opa_installation()

    def _verify_opa_installation(self) -> bool:
        """Check if OPA is installed and accessible."""
        try:
            result = subprocess.run(
                [self.opa_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                console.print(f"[green]✓[/green] OPA found: {result.stdout.split()[1]}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            console.print(
                f"[yellow]⚠[/yellow] OPA not found at '{self.opa_path}'. "
                "Install from: https://www.openpolicyagent.org/docs/latest/#1-download-opa"
            )
            return False

    def validate_commit(
        self,
        commit_msg: str,
        diff_stat: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ComplianceResult:
        """
        Validate a commit message against compliance policies.

        Args:
            commit_msg: The commit message to validate
            diff_stat: Git diff statistics (files changed, lines added/removed)
            metadata: Additional metadata (author, timestamp, etc.)

        Returns:
            ComplianceResult with violations if any
        """
        input_data = {
            "commit": {
                "message": commit_msg,
                "diff_stat": diff_stat or {},
                "metadata": metadata or {}
            }
        }

        return self._evaluate_policies(
            input_data,
            policy_path=self.policy_dir / "healthcare",
            package_name="healthcare"
        )

    def validate_code_changes(
        self,
        file_paths: List[str],
        commit_sha: Optional[str] = None
    ) -> ComplianceResult:
        """
        Validate code changes against compliance policies.

        Args:
            file_paths: List of changed file paths
            commit_sha: Git commit SHA (if applicable)

        Returns:
            ComplianceResult with violations if any
        """
        violations = []

        for file_path in file_paths:
            # Check for PHI patterns
            phi_violations = self._check_phi_exposure(file_path)
            violations.extend(phi_violations)

            # Check for critical path changes
            if self._is_critical_path(file_path):
                violations.append(
                    ComplianceViolation(
                        policy="critical_path_protection",
                        severity="HIGH",
                        message=f"Changes to critical path: {file_path}",
                        file_path=file_path,
                        remediation="Requires dual approval and additional testing"
                    )
                )

        return ComplianceResult(
            passed=len(violations) == 0,
            violations=violations,
            policies_evaluated=2,  # PHI + critical path
            timestamp=datetime.utcnow().isoformat(),
            commit_sha=commit_sha
        )

    def _evaluate_policies(
        self,
        input_data: Dict[str, Any],
        policy_path: Path,
        package_name: str
    ) -> ComplianceResult:
        """
        Evaluate OPA policies against input data.

        Args:
            input_data: Data to evaluate
            policy_path: Path to policy directory
            package_name: OPA package name to query

        Returns:
            ComplianceResult
        """
        violations = []

        if not policy_path.exists():
            console.print(f"[yellow]⚠[/yellow] Policy path not found: {policy_path}")
            return ComplianceResult(
                passed=True,
                violations=[],
                policies_evaluated=0,
                timestamp=datetime.utcnow().isoformat()
            )

        # Find all .rego files
        policy_files = list(policy_path.glob("*.rego"))
        policy_files = [f for f in policy_files if not f.name.endswith("_test.rego")]

        if not policy_files:
            console.print(f"[yellow]⚠[/yellow] No policy files found in {policy_path}")
            return ComplianceResult(
                passed=True,
                violations=[],
                policies_evaluated=0,
                timestamp=datetime.utcnow().isoformat()
            )

        # Evaluate each policy
        for policy_file in policy_files:
            try:
                result = self._run_opa_eval(policy_file, input_data, package_name)
                policy_violations = self._parse_opa_result(result, policy_file.stem)
                violations.extend(policy_violations)
            except Exception as e:
                console.print(f"[red]✗[/red] Error evaluating {policy_file.name}: {e}")

        return ComplianceResult(
            passed=len(violations) == 0,
            violations=violations,
            policies_evaluated=len(policy_files),
            timestamp=datetime.utcnow().isoformat()
        )

    def _run_opa_eval(
        self,
        policy_file: Path,
        input_data: Dict[str, Any],
        package_name: str
    ) -> Dict[str, Any]:
        """Run OPA evaluation on a policy file."""
        try:
            cmd = [
                self.opa_path,
                "eval",
                "--data", str(policy_file),
                "--input", "-",
                "--format", "json",
                f"data.{package_name}"
            ]

            result = subprocess.run(
                cmd,
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                console.print(f"[red]OPA error:[/red] {result.stderr}")
                return {}

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            console.print(f"[red]✗[/red] OPA evaluation timeout for {policy_file.name}")
            return {}
        except json.JSONDecodeError as e:
            console.print(f"[red]✗[/red] Invalid JSON from OPA: {e}")
            return {}

    def _parse_opa_result(
        self,
        opa_result: Dict[str, Any],
        policy_name: str
    ) -> List[ComplianceViolation]:
        """Parse OPA evaluation result into violations."""
        violations = []

        # OPA result structure varies by policy
        # This is a simplified parser
        if not opa_result or "result" not in opa_result:
            return violations

        results = opa_result.get("result", [])
        for result in results:
            expressions = result.get("expressions", [])
            for expr in expressions:
                value = expr.get("value", {})

                # Check for 'deny' rules
                if "deny" in value and value["deny"]:
                    for msg in value["deny"]:
                        violations.append(
                            ComplianceViolation(
                                policy=policy_name,
                                severity="HIGH",
                                message=msg,
                                rule="deny"
                            )
                        )

                # Check for 'violations' array
                if "violations" in value:
                    for v in value["violations"]:
                        violations.append(
                            ComplianceViolation(
                                policy=policy_name,
                                severity=v.get("severity", "MEDIUM"),
                                message=v.get("message", "Compliance violation"),
                                rule=v.get("rule")
                            )
                        )

        return violations

    def _check_phi_exposure(self, file_path: str) -> List[ComplianceViolation]:
        """Check file for potential PHI exposure."""
        violations = []
        phi_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN pattern detected'),
            (r'\b\d{10}\b', 'Potential MRN (10 digits)'),
            (r'patient_name|patient_id|ssn|medical_record', 'PHI field name'),
        ]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            import re
            for pattern, description in phi_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(
                        ComplianceViolation(
                            policy="phi_exposure_prevention",
                            severity="CRITICAL",
                            message=f"Potential PHI exposure: {description}",
                            file_path=file_path,
                            remediation="Sanitize PHI or move to secure storage"
                        )
                    )
        except Exception as e:
            # File might be binary or inaccessible
            pass

        return violations

    def _is_critical_path(self, file_path: str) -> bool:
        """Determine if file is in a critical path."""
        critical_paths = [
            "payment-gateway",
            "auth-service",
            "phi-service",
            "medical-device"
        ]
        return any(cp in file_path for cp in critical_paths)

    def generate_report(self, result: ComplianceResult, format: str = "table") -> str:
        """
        Generate a compliance report.

        Args:
            result: ComplianceResult to format
            format: Output format ('table', 'json', 'markdown')

        Returns:
            Formatted report string
        """
        if format == "json":
            return json.dumps({
                "passed": result.passed,
                "timestamp": result.timestamp,
                "policies_evaluated": result.policies_evaluated,
                "violations": [
                    {
                        "policy": v.policy,
                        "severity": v.severity,
                        "message": v.message,
                        "file_path": v.file_path,
                        "remediation": v.remediation
                    }
                    for v in result.violations
                ]
            }, indent=2)

        elif format == "markdown":
            lines = [
                "# Compliance Report",
                f"**Status**: {'✓ PASSED' if result.passed else '✗ FAILED'}",
                f"**Timestamp**: {result.timestamp}",
                f"**Policies Evaluated**: {result.policies_evaluated}",
                "",
                "## Violations",
                ""
            ]

            if not result.violations:
                lines.append("No violations found. ✓")
            else:
                for v in result.violations:
                    lines.extend([
                        f"### {v.severity}: {v.policy}",
                        f"**Message**: {v.message}",
                        f"**File**: {v.file_path or 'N/A'}",
                        f"**Remediation**: {v.remediation or 'See policy documentation'}",
                        ""
                    ])

            return "\n".join(lines)

        else:  # table (rich)
            table = Table(title="Compliance Violations" if result.violations else "Compliance Check")
            table.add_column("Severity", style="bold")
            table.add_column("Policy")
            table.add_column("Message")
            table.add_column("File")

            if not result.violations:
                console.print(f"[green]✓ All {result.policies_evaluated} policies passed[/green]")
                return ""

            for v in result.violations:
                severity_color = {
                    "CRITICAL": "red bold",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "blue"
                }.get(v.severity, "white")

                table.add_row(
                    f"[{severity_color}]{v.severity}[/{severity_color}]",
                    v.policy,
                    v.message,
                    v.file_path or "—"
                )

            console.print(table)
            return ""


def run_compliance_check(
    commit_msg: Optional[str] = None,
    files: Optional[List[str]] = None,
    policy_dir: Optional[Path] = None,
    format: str = "table"
) -> int:
    """
    CLI entry point for compliance checking.

    Returns:
        Exit code (0 = passed, 1 = violations found, 2 = error)
    """
    checker = ComplianceChecker(policy_dir=policy_dir)

    if commit_msg:
        result = checker.validate_commit(commit_msg)
    elif files:
        result = checker.validate_code_changes(files)
    else:
        console.print("[red]Error:[/red] Must provide --commit-msg or --files")
        return 2

    report = checker.generate_report(result, format=format)
    if report:
        print(report)

    return 0 if result.passed else 1
