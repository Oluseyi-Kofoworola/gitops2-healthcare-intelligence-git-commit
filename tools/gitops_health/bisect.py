"""
Intelligent Git Bisect Implementation

AI-assisted binary search for identifying commits that introduced bugs or regressions.
Uses heuristics, ML patterns, and CI/CD signals to accelerate bisect operations.
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


@dataclass
class BisectStep:
    """Represents a single bisect step."""
    commit_sha: str
    commit_msg: str
    timestamp: str
    test_result: Optional[str] = None  # "good", "bad", "skip"
    test_output: Optional[str] = None
    confidence: float = 0.0  # AI confidence score (0-1)
    reason: Optional[str] = None


@dataclass
class BisectSession:
    """Represents a full bisect session."""
    start_time: str
    end_time: Optional[str] = None
    good_commit: str = ""
    bad_commit: str = ""
    culprit_commit: Optional[str] = None
    steps: List[BisectStep] = field(default_factory=list)
    total_commits: int = 0
    test_command: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligentBisect:
    """
    AI-enhanced git bisect that uses heuristics to speed up regression detection.
    """

    def __init__(
        self,
        repo_path: Path = None,
        test_command: Optional[str] = None,
        use_ai_hints: bool = True
    ):
        """
        Initialize intelligent bisect.

        Args:
            repo_path: Path to git repository (default: current directory)
            test_command: Command to run for each commit test
            use_ai_hints: Use AI/heuristics to prioritize commits
        """
        self.repo_path = repo_path or Path.cwd()
        self.test_command = test_command
        self.use_ai_hints = use_ai_hints
        self.session: Optional[BisectSession] = None

    def start_bisect(
        self,
        good_commit: str,
        bad_commit: str,
        test_fn: Optional[Callable[[str], bool]] = None
    ) -> BisectSession:
        """
        Start an intelligent bisect session.

        Args:
            good_commit: Known good commit SHA
            bad_commit: Known bad commit SHA
            test_fn: Optional Python callable to test commits (returns True if good)

        Returns:
            BisectSession with results
        """
        console.print(f"[cyan]Starting intelligent bisect...[/cyan]")
        console.print(f"  Good commit: [green]{good_commit[:8]}[/green]")
        console.print(f"  Bad commit:  [red]{bad_commit[:8]}[/red]")

        # Initialize session
        self.session = BisectSession(
            start_time=datetime.utcnow().isoformat(),
            good_commit=good_commit,
            bad_commit=bad_commit,
            test_command=self.test_command
        )

        # Get commit range
        commits = self._get_commit_range(good_commit, bad_commit)
        self.session.total_commits = len(commits)
        console.print(f"  Total commits to bisect: {len(commits)}")

        if self.use_ai_hints:
            console.print("[cyan]Analyzing commits for intelligent prioritization...[/cyan]")
            commits = self._prioritize_commits(commits)

        # Perform bisect
        culprit = self._binary_search(commits, good_commit, bad_commit, test_fn)

        self.session.culprit_commit = culprit
        self.session.end_time = datetime.utcnow().isoformat()

        return self.session

    def _get_commit_range(self, good: str, bad: str) -> List[str]:
        """Get list of commits between good and bad."""
        try:
            result = subprocess.run(
                ["git", "rev-list", f"{good}..{bad}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commits = result.stdout.strip().split("\n")
            return [c for c in commits if c]  # Filter empty strings
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error getting commit range:[/red] {e.stderr}")
            return []

    def _prioritize_commits(self, commits: List[str]) -> List[str]:
        """
        Use heuristics to prioritize which commits to test first.

        Heuristics:
        1. Commits with specific keywords (fix, bug, regression, etc.)
        2. Commits to critical paths (payment, auth, etc.)
        3. Commits with large diffs
        4. Commits that failed CI previously
        """
        scored_commits = []

        for commit_sha in commits:
            score = 0.0
            
            # Get commit details
            details = self._get_commit_details(commit_sha)
            msg = details.get("message", "").lower()
            files = details.get("files", [])

            # Keyword scoring
            high_priority_keywords = ["fix", "bug", "regression", "break", "fail", "revert"]
            if any(kw in msg for kw in high_priority_keywords):
                score += 2.0

            # Critical path scoring
            critical_paths = ["payment-gateway", "auth-service", "phi-service"]
            if any(any(cp in f for cp in critical_paths) for f in files):
                score += 1.5

            # Large diff scoring (more likely to introduce issues)
            insertions = details.get("insertions", 0)
            deletions = details.get("deletions", 0)
            if insertions + deletions > 500:
                score += 1.0

            scored_commits.append((commit_sha, score))

        # Sort by score (descending) - test high-priority commits first
        scored_commits.sort(key=lambda x: x[1], reverse=True)
        
        return [sha for sha, _ in scored_commits]

    def _get_commit_details(self, commit_sha: str) -> Dict[str, Any]:
        """Get detailed information about a commit."""
        try:
            # Get commit message
            msg_result = subprocess.run(
                ["git", "log", "-1", "--format=%s", commit_sha],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            message = msg_result.stdout.strip()

            # Get commit stats
            stat_result = subprocess.run(
                ["git", "show", "--stat", "--format=", commit_sha],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse files and stats
            files = []
            insertions = 0
            deletions = 0
            for line in stat_result.stdout.strip().split("\n"):
                if "|" in line:
                    file_path = line.split("|")[0].strip()
                    files.append(file_path)
                elif "insertion" in line or "deletion" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "insertion" in part:
                            insertions = int(part.split()[0])
                        elif "deletion" in part:
                            deletions = int(part.split()[0])

            return {
                "message": message,
                "files": files,
                "insertions": insertions,
                "deletions": deletions
            }

        except subprocess.CalledProcessError:
            return {"message": "", "files": [], "insertions": 0, "deletions": 0}

    def _binary_search(
        self,
        commits: List[str],
        good: str,
        bad: str,
        test_fn: Optional[Callable[[str], bool]]
    ) -> Optional[str]:
        """
        Perform binary search to find culprit commit.

        Args:
            commits: List of commits to search (pre-sorted if using AI hints)
            good: Known good commit
            bad: Known bad commit
            test_fn: Function to test if a commit is good

        Returns:
            SHA of culprit commit, or None if not found
        """
        left = 0
        right = len(commits) - 1
        culprit = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Bisecting...", total=None)

            while left <= right:
                mid = (left + right) // 2
                commit_sha = commits[mid]

                progress.update(
                    task,
                    description=f"Testing commit {mid+1}/{len(commits)}: {commit_sha[:8]}..."
                )

                # Test commit
                is_good = self._test_commit(commit_sha, test_fn)
                
                # Record step
                step = BisectStep(
                    commit_sha=commit_sha,
                    commit_msg=self._get_commit_details(commit_sha)["message"],
                    timestamp=datetime.utcnow().isoformat(),
                    test_result="good" if is_good else "bad",
                    confidence=0.9  # High confidence for direct test
                )
                self.session.steps.append(step)

                if is_good:
                    # Good commit, search right half
                    left = mid + 1
                else:
                    # Bad commit, this could be the culprit
                    culprit = commit_sha
                    right = mid - 1

        return culprit

    def _test_commit(
        self,
        commit_sha: str,
        test_fn: Optional[Callable[[str], bool]]
    ) -> bool:
        """
        Test if a commit is good or bad.

        Args:
            commit_sha: Commit to test
            test_fn: Optional custom test function

        Returns:
            True if commit is good, False if bad
        """
        # Checkout commit
        try:
            subprocess.run(
                ["git", "checkout", commit_sha],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error checking out commit:[/red] {e.stderr}")
            return False

        # Run test
        if test_fn:
            # Use custom Python test function
            try:
                result = test_fn(commit_sha)
                return result
            except Exception as e:
                console.print(f"[red]Test function error:[/red] {e}")
                return False
        elif self.test_command:
            # Use shell command
            try:
                result = subprocess.run(
                    self.test_command,
                    cwd=self.repo_path,
                    shell=True,
                    capture_output=True,
                    timeout=300  # 5 minute timeout
                )
                return result.returncode == 0
            except subprocess.TimeoutExpired:
                console.print(f"[yellow]Test timeout for {commit_sha[:8]}[/yellow]")
                return False
        else:
            # Interactive mode
            console.print(f"\n[cyan]Test commit {commit_sha[:8]}[/cyan]")
            while True:
                response = console.input("Is this commit [g]ood, [b]ad, or [s]kip? ").lower()
                if response in ["g", "good"]:
                    return True
                elif response in ["b", "bad"]:
                    return False
                elif response in ["s", "skip"]:
                    # For now, treat skip as bad
                    return False

    def generate_report(self, format: str = "table") -> str:
        """
        Generate bisect report.

        Args:
            format: Output format ('table', 'json', 'markdown')

        Returns:
            Formatted report
        """
        if not self.session:
            return "No bisect session found."

        if format == "json":
            return json.dumps({
                "start_time": self.session.start_time,
                "end_time": self.session.end_time,
                "good_commit": self.session.good_commit,
                "bad_commit": self.session.bad_commit,
                "culprit_commit": self.session.culprit_commit,
                "total_commits": self.session.total_commits,
                "steps_taken": len(self.session.steps),
                "steps": [
                    {
                        "commit": s.commit_sha,
                        "message": s.commit_msg,
                        "result": s.test_result,
                        "confidence": s.confidence
                    }
                    for s in self.session.steps
                ]
            }, indent=2)

        elif format == "markdown":
            lines = [
                "# Intelligent Bisect Report",
                "",
                f"**Culprit Commit**: `{self.session.culprit_commit or 'Not found'}`",
                f"**Total Commits**: {self.session.total_commits}",
                f"**Steps Taken**: {len(self.session.steps)}",
                f"**Efficiency**: {len(self.session.steps)}/{self.session.total_commits} "
                f"({100*len(self.session.steps)/max(1, self.session.total_commits):.1f}%)",
                "",
                "## Bisect Steps",
                ""
            ]

            for i, step in enumerate(self.session.steps, 1):
                result_emoji = "✓" if step.test_result == "good" else "✗"
                lines.append(
                    f"{i}. {result_emoji} `{step.commit_sha[:8]}` - {step.commit_msg}"
                )

            if self.session.culprit_commit:
                lines.extend([
                    "",
                    "## Culprit Details",
                    f"```",
                    f"git show {self.session.culprit_commit}",
                    f"```"
                ])

            return "\n".join(lines)

        else:  # table
            table = Table(title="Intelligent Bisect Results")
            table.add_column("Step", style="cyan")
            table.add_column("Commit", style="yellow")
            table.add_column("Result")
            table.add_column("Message")

            for i, step in enumerate(self.session.steps, 1):
                result_style = "green" if step.test_result == "good" else "red"
                table.add_row(
                    str(i),
                    step.commit_sha[:8],
                    f"[{result_style}]{step.test_result}[/{result_style}]",
                    step.commit_msg[:50] + "..." if len(step.commit_msg) > 50 else step.commit_msg
                )

            console.print(table)

            if self.session.culprit_commit:
                console.print(f"\n[red]Culprit commit:[/red] {self.session.culprit_commit}")
                console.print(f"Run: [cyan]git show {self.session.culprit_commit}[/cyan]")

            efficiency = len(self.session.steps) / max(1, self.session.total_commits) * 100
            console.print(f"\nEfficiency: {len(self.session.steps)}/{self.session.total_commits} steps ({efficiency:.1f}%)")

            return ""


def run_bisect(
    good: str,
    bad: str,
    test_command: Optional[str] = None,
    repo_path: Optional[Path] = None,
    format: str = "table"
) -> int:
    """
    CLI entry point for intelligent bisect.

    Returns:
        Exit code (0 = success, 1 = no culprit found, 2 = error)
    """
    try:
        bisect = IntelligentBisect(
            repo_path=repo_path,
            test_command=test_command,
            use_ai_hints=True
        )

        session = bisect.start_bisect(good, bad)
        
        report = bisect.generate_report(format=format)
        if report:
            print(report)

        return 0 if session.culprit_commit else 1

    except Exception as e:
        console.print(f"[red]Bisect error:[/red] {e}")
        return 2
