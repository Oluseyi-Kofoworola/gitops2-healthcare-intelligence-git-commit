"""
AI-Powered Commit Message Generator

Uses OpenAI/Anthropic APIs and local heuristics to generate conventional
commit messages from git diffs and file changes.
"""

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from rich.console import Console
from rich.panel import Panel

console = Console()


@dataclass
class CommitSuggestion:
    """A suggested commit message."""
    type: str  # feat, fix, docs, etc.
    scope: Optional[str]
    subject: str
    body: Optional[str] = None
    breaking: bool = False
    confidence: float = 0.0
    reasoning: Optional[str] = None


class CommitGenerator:
    """
    Generates conventional commit messages using AI and heuristics.
    """

    CONVENTIONAL_TYPES = [
        "feat",     # New feature
        "fix",      # Bug fix
        "docs",     # Documentation
        "style",    # Formatting, missing semicolons, etc.
        "refactor", # Code change that neither fixes a bug nor adds a feature
        "perf",     # Performance improvement
        "test",     # Adding tests
        "build",    # Build system or dependencies
        "ci",       # CI configuration
        "chore",    # Other changes that don't modify src or test files
        "revert",   # Revert a previous commit
    ]

    CRITICAL_SCOPES = [
        "payment",  # Payment gateway changes
        "auth",     # Authentication/authorization
        "phi",      # PHI/PII handling
        "infra",    # Infrastructure
        "security", # Security-related
    ]

    def __init__(
        self,
        repo_path: Path = None,
        use_ai: bool = True,
        api_key: Optional[str] = None,
        model: str = "gpt-4"
    ):
        """
        Initialize commit generator.

        Args:
            repo_path: Path to git repository
            use_ai: Use AI (OpenAI/Anthropic) for generation
            api_key: API key for AI service
            model: AI model name
        """
        self.repo_path = repo_path or Path.cwd()
        self.use_ai = use_ai
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate_from_diff(
        self,
        diff: Optional[str] = None,
        staged_only: bool = True
    ) -> List[CommitSuggestion]:
        """
        Generate commit message from git diff.

        Args:
            diff: Git diff string (if None, will get from repo)
            staged_only: Only include staged changes

        Returns:
            List of suggested commit messages (ranked by confidence)
        """
        # Get diff if not provided
        if diff is None:
            diff = self._get_git_diff(staged_only)

        if not diff:
            console.print("[yellow]No changes to commit[/yellow]")
            return []

        # Get changed files
        files = self._get_changed_files(staged_only)

        # Generate suggestions
        suggestions = []

        # Try AI generation first
        if self.use_ai and self.api_key:
            ai_suggestion = self._generate_with_ai(diff, files)
            if ai_suggestion:
                suggestions.append(ai_suggestion)

        # Always generate heuristic-based suggestions as fallback
        heuristic_suggestions = self._generate_with_heuristics(diff, files)
        suggestions.extend(heuristic_suggestions)

        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:3]  # Return top 3

    def _get_git_diff(self, staged_only: bool) -> str:
        """Get git diff output."""
        try:
            cmd = ["git", "diff"]
            if staged_only:
                cmd.append("--cached")

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error getting diff:[/red] {e.stderr}")
            return ""

    def _get_changed_files(self, staged_only: bool) -> List[str]:
        """Get list of changed files."""
        try:
            cmd = ["git", "diff", "--name-only"]
            if staged_only:
                cmd.append("--cached")

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return [f for f in result.stdout.strip().split("\n") if f]

        except subprocess.CalledProcessError:
            return []

    def _generate_with_ai(
        self,
        diff: str,
        files: List[str]
    ) -> Optional[CommitSuggestion]:
        """
        Generate commit message using OpenAI API.

        Args:
            diff: Git diff string
            files: List of changed files

        Returns:
            CommitSuggestion or None if API call fails
        """
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)

            # Truncate diff if too large (GPT-4 token limit)
            max_diff_length = 8000
            if len(diff) > max_diff_length:
                diff = diff[:max_diff_length] + "\n... (truncated)"

            prompt = f"""Generate a conventional commit message for the following changes.

Changed files:
{chr(10).join(f'- {f}' for f in files)}

Git diff:
```
{diff}
```

Requirements:
1. Follow Conventional Commits format: type(scope): subject
2. Valid types: {', '.join(self.CONVENTIONAL_TYPES)}
3. Critical scopes: {', '.join(self.CRITICAL_SCOPES)}
4. Subject: imperative mood, lowercase, no period, max 50 chars
5. Body (optional): explain WHAT and WHY, not HOW
6. Mark as BREAKING CHANGE if API or behavior changes

Respond with JSON:
{{
  "type": "feat|fix|docs|etc",
  "scope": "payment|auth|phi|etc or null",
  "subject": "add new feature",
  "body": "Optional explanation",
  "breaking": false,
  "reasoning": "Why you chose this commit type"
}}"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at writing conventional commit messages for enterprise software."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            return CommitSuggestion(
                type=data["type"],
                scope=data.get("scope"),
                subject=data["subject"],
                body=data.get("body"),
                breaking=data.get("breaking", False),
                confidence=0.9,  # High confidence for AI
                reasoning=data.get("reasoning")
            )

        except ImportError:
            console.print("[yellow]OpenAI package not installed. Run: pip install openai[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]AI generation failed:[/yellow] {e}")
            return None

    def _generate_with_heuristics(
        self,
        diff: str,
        files: List[str]
    ) -> List[CommitSuggestion]:
        """
        Generate commit messages using rule-based heuristics.

        Args:
            diff: Git diff string
            files: List of changed files

        Returns:
            List of CommitSuggestions
        """
        suggestions = []

        # Analyze files to determine type and scope
        commit_type = self._infer_type(files, diff)
        scope = self._infer_scope(files)
        subject = self._generate_subject(files, diff, commit_type)

        # Primary suggestion
        suggestions.append(
            CommitSuggestion(
                type=commit_type,
                scope=scope,
                subject=subject,
                confidence=0.7,
                reasoning=f"Inferred from file patterns and diff content"
            )
        )

        # Alternative suggestion (different type)
        alt_type = self._get_alternative_type(commit_type, diff)
        if alt_type != commit_type:
            suggestions.append(
                CommitSuggestion(
                    type=alt_type,
                    scope=scope,
                    subject=subject.replace(commit_type, alt_type),
                    confidence=0.5,
                    reasoning=f"Alternative interpretation"
                )
            )

        return suggestions

    def _infer_type(self, files: List[str], diff: str) -> str:
        """Infer commit type from files and diff."""
        # Documentation files
        if any("README" in f or ".md" in f or "docs/" in f for f in files):
            return "docs"

        # Test files
        if any("test" in f or "spec" in f for f in files):
            return "test"

        # CI/CD files
        if any(".github" in f or ".gitlab" in f or "Jenkinsfile" in f for f in files):
            return "ci"

        # Build/dependency files
        if any(f in ["package.json", "requirements.txt", "go.mod", "Cargo.toml"] for f in files):
            return "build"

        # Check diff for bug fix indicators
        bug_keywords = ["fix", "bug", "issue", "error", "crash", "regression"]
        if any(kw in diff.lower() for kw in bug_keywords):
            return "fix"

        # Check for feature indicators
        feature_keywords = ["add", "implement", "create", "new"]
        if any(kw in diff.lower() for kw in feature_keywords):
            return "feat"

        # Default to chore
        return "chore"

    def _infer_scope(self, files: List[str]) -> Optional[str]:
        """Infer scope from file paths."""
        # Check for critical scopes
        for scope in self.CRITICAL_SCOPES:
            if any(scope in f.lower() for f in files):
                return scope

        # Infer from directory structure
        common_prefixes = set()
        for f in files:
            parts = Path(f).parts
            if len(parts) > 1:
                common_prefixes.add(parts[0])

        # If all files share a common prefix, use it
        if len(common_prefixes) == 1:
            prefix = common_prefixes.pop()
            if prefix not in [".", "..", "src", "lib"]:
                return prefix

        return None

    def _generate_subject(self, files: List[str], diff: str, commit_type: str) -> str:
        """Generate commit subject line."""
        # Extract meaningful action from diff
        if commit_type == "feat":
            verb = "add"
        elif commit_type == "fix":
            verb = "fix"
        elif commit_type == "docs":
            verb = "update"
        elif commit_type == "test":
            verb = "add"
        else:
            verb = "update"

        # Generate object
        if len(files) == 1:
            # Single file change
            file_name = Path(files[0]).stem
            object = file_name.replace("_", " ").replace("-", " ")
        else:
            # Multiple files
            object = f"{len(files)} files"

        subject = f"{verb} {object}"

        # Truncate to 50 chars
        if len(subject) > 50:
            subject = subject[:47] + "..."

        return subject

    def _get_alternative_type(self, primary_type: str, diff: str) -> str:
        """Get alternative commit type."""
        if primary_type == "feat":
            return "refactor"
        elif primary_type == "fix":
            return "refactor"
        else:
            return "chore"

    def format_message(self, suggestion: CommitSuggestion) -> str:
        """
        Format a CommitSuggestion into a complete commit message.

        Args:
            suggestion: CommitSuggestion to format

        Returns:
            Formatted commit message string
        """
        # Subject line
        parts = [suggestion.type]
        if suggestion.scope:
            parts.append(f"({suggestion.scope})")
        parts.append(f": {suggestion.subject}")
        
        message = "".join(parts)

        # Body
        if suggestion.body:
            message += f"\n\n{suggestion.body}"

        # Breaking change footer
        if suggestion.breaking:
            message += "\n\nBREAKING CHANGE: This commit introduces breaking changes."

        return message

    def interactive_select(
        self,
        suggestions: List[CommitSuggestion]
    ) -> Optional[CommitSuggestion]:
        """
        Display suggestions and let user select one.

        Args:
            suggestions: List of suggestions to choose from

        Returns:
            Selected CommitSuggestion or None
        """
        if not suggestions:
            return None

        console.print("\n[cyan]Suggested commit messages:[/cyan]\n")

        for i, suggestion in enumerate(suggestions, 1):
            formatted = self.format_message(suggestion)
            confidence_bar = "█" * int(suggestion.confidence * 10)
            
            console.print(Panel(
                f"{formatted}\n\n"
                f"[dim]Confidence: {confidence_bar} {suggestion.confidence:.0%}[/dim]\n"
                f"[dim]Reasoning: {suggestion.reasoning}[/dim]",
                title=f"Option {i}",
                border_style="cyan" if i == 1 else "dim"
            ))

        # Get user selection
        while True:
            choice = console.input(f"\nSelect option [1-{len(suggestions)}], or [c]ustom, or [q]uit: ").lower()
            
            if choice == "q":
                return None
            elif choice == "c":
                custom = console.input("Enter custom commit message: ")
                # Parse custom message (simple implementation)
                return CommitSuggestion(
                    type="chore",
                    scope=None,
                    subject=custom,
                    confidence=1.0
                )
            elif choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                return suggestions[int(choice) - 1]
            else:
                console.print("[red]Invalid choice. Try again.[/red]")


def run_commit_generator(
    staged_only: bool = True,
    use_ai: bool = True,
    auto_commit: bool = False,
    repo_path: Optional[Path] = None
) -> int:
    """
    CLI entry point for commit generator.

    Returns:
        Exit code (0 = success, 1 = no changes, 2 = error)
    """
    try:
        generator = CommitGenerator(
            repo_path=repo_path,
            use_ai=use_ai
        )

        suggestions = generator.generate_from_diff(staged_only=staged_only)

        if not suggestions:
            return 1

        if auto_commit and suggestions:
            # Use top suggestion
            selected = suggestions[0]
        else:
            # Interactive selection
            selected = generator.interactive_select(suggestions)

        if not selected:
            console.print("[yellow]Commit cancelled[/yellow]")
            return 1

        # Format and display final message
        message = generator.format_message(selected)
        console.print("\n[green]Final commit message:[/green]")
        console.print(Panel(message, border_style="green"))

        if auto_commit:
            # Execute git commit
            try:
                subprocess.run(
                    ["git", "commit", "-m", message],
                    cwd=repo_path or Path.cwd(),
                    check=True
                )
                console.print("[green]✓ Committed successfully[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Commit failed:[/red] {e}")
                return 2
        else:
            console.print("\nTo commit, run:")
            console.print(f"  [cyan]git commit -m '{message.split(chr(10))[0]}'[/cyan]")

        return 0

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 2
