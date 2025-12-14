#!/usr/bin/env python3
"""
GitHub Copilot-Style Commit Generator for Healthcare - GitOps 2.0
AI-powered commit message generation with HIPAA, FDA, and SOX compliance

This tool implements the vision from the GitOps 2.0 article:
"GitHub Copilot Enterprise can now generate structured, compliant,
healthcare-aware commit intelligence automatically."

Usage:
    python git_copilot_commit.py --analyze
    python git_copilot_commit.py --analyze --scope phi --compliance HIPAA
    python git_copilot_commit.py --analyze --auto-commit

Author: GitOps 2.0 Healthcare Intelligence Platform
Version: 2.0.0 (Production)
License: MIT
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

# OpenAI for AI-powered analysis
try:
    from openai import OpenAI, OpenAIError, APIError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI library not installed. Install with: pip install openai", file=sys.stderr)
    # Define fallback exception types
    class OpenAIError(Exception):
        pass
    class APIError(OpenAIError):
        pass

# Load configuration
CONFIG_FILE = Path(__file__).parent.parent / ".copilot" / "healthcare-commit-guidelines.yml"


class GitCopilotCommit:
    """
    AI-powered commit message generator for healthcare compliance

    Implements the GitOps 2.0 vision:
    - Analyzes git diff automatically
    - Generates structured, compliant commit messages
    - Includes risk assessment, clinical safety, compliance metadata
    - Zero manual effort from developers
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries
        self.config = self._load_config()

        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key and OPENAI_AVAILABLE:
            print("⚠️  OPENAI_API_KEY not set. Set it with: export OPENAI_API_KEY=your-key", file=sys.stderr)
            sys.exit(1)

        if OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def _load_config(self) -> Dict:
        """Load healthcare commit guidelines configuration"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, IOError) as e:
            print(f"⚠️  Configuration file error: {e}", file=sys.stderr)
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration if file not found"""
        return {
            "risk_patterns": {
                "CRITICAL": ["services/phi-service/**", "services/medical-device/**", "**/*encryption*"],
                "HIGH": ["services/payment-gateway/**", "services/auth-service/**"],
                "MEDIUM": ["services/*/api/**", ".github/workflows/**"],
                "LOW": ["docs/**", "**/*.md"]
            },
            "compliance_mapping": {
                "HIPAA": ["services/phi-service/**", "**/*phi*", "**/*patient*"],
                "FDA": ["services/medical-device/**", "**/*device*"],
                "SOX": ["services/payment-gateway/**", "**/*financial*"]
            }
        }

    def get_git_diff(self, ref: str = "HEAD") -> Tuple[List[str], str]:
        """Get modified files and diff content"""
        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", ref],
                capture_output=True,
                text=True,
                check=True
            )
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

            # Get diff content (limit to 10000 lines for token management)
            result = subprocess.run(
                ["git", "diff", ref],
                capture_output=True,
                text=True,
                check=True
            )
            diff_text = result.stdout[:50000]  # Limit to ~12k tokens

            return files, diff_text
        except subprocess.CalledProcessError:
            print("❌ Git command failed. Make sure you're in a git repository.", file=sys.stderr)
            sys.exit(1)

    def assess_risk_level(self, files: List[str]) -> str:
        """Determine risk level based on modified files"""
        risk_patterns = self.config.get("risk_patterns", {})

        for risk_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            patterns = risk_patterns.get(risk_level, [])
            for file in files:
                for pattern in patterns:
                    # Simple pattern matching (could use fnmatch for wildcards)
                    if self._matches_pattern(file, pattern):
                        return risk_level

        return "MEDIUM"  # Default

    def assess_clinical_safety(self, files: List[str]) -> str:
        """Determine clinical safety impact"""
        critical_patterns = ["services/medical-device/**", "**/*diagnostic*", "**/*clinical-decision*"]
        medium_patterns = ["services/phi-service/**", "**/*patient*"]

        for file in files:
            for pattern in critical_patterns:
                if self._matches_pattern(file, pattern):
                    return "REQUIRES_CLINICAL_REVIEW"

        for file in files:
            for pattern in medium_patterns:
                if self._matches_pattern(file, pattern):
                    return "CLINICAL_VALIDATION_NEEDED"

        return "NO_CLINICAL_IMPACT"

    def detect_compliance_domains(self, files: List[str]) -> List[str]:
        """Detect applicable compliance frameworks"""
        compliance_mapping = self.config.get("compliance_mapping", {})
        domains = set()

        for domain, patterns in compliance_mapping.items():
            for file in files:
                for pattern in patterns:
                    if self._matches_pattern(file, pattern):
                        domains.add(domain)

        return sorted(list(domains))

    def _matches_pattern(self, file: str, pattern: str) -> bool:
        """Simple pattern matching (supports ** wildcards)"""
        import fnmatch
        return fnmatch.fnmatch(file, pattern)

    def suggest_reviewers(self, compliance_domains: List[str], risk_level: str) -> List[str]:
        """Suggest required reviewers based on compliance and risk"""
        reviewer_mapping = self.config.get("reviewer_mapping", {})
        reviewers = set()

        for domain in compliance_domains:
            reviewers.update(reviewer_mapping.get(domain, []))

        if risk_level == "CRITICAL":
            reviewers.update(reviewer_mapping.get("CRITICAL_RISK", []))
        elif risk_level == "HIGH":
            reviewers.update(reviewer_mapping.get("HIGH_RISK", []))

        return sorted(list(reviewers))

    def generate_commit_message(
        self,
        files: List[str],
        diff_text: str,
        scope: Optional[str] = None,
        compliance_hint: Optional[str] = None
    ) -> str:
        """
        Generate AI-powered commit message using OpenAI

        This is the core GitOps 2.0 feature: AI writes the compliance story
        while developers write code.
        """
        if not self.client:
            return self._generate_fallback_message(files, scope)

        # Assess metadata
        risk_level = self.assess_risk_level(files)
        clinical_safety = self.assess_clinical_safety(files)
        compliance_domains = self.detect_compliance_domains(files)

        if compliance_hint:
            compliance_domains.append(compliance_hint)
            compliance_domains = sorted(list(set(compliance_domains)))

        reviewers = self.suggest_reviewers(compliance_domains, risk_level)

        # Construct AI prompt
        system_prompt = """You are an AI assistant specializing in healthcare compliance and GitOps 2.0 engineering.
Generate a structured, machine-readable commit message that serves as a compliance artifact.
The commit must be audit-ready and contain all required regulatory metadata.

Follow this EXACT format:

<type>(<scope>): <description>

Business Impact: <one sentence describing business value>
Risk Level: <risk_level>
Clinical Safety: <clinical_safety>
Compliance: <comma-separated compliance domains>

<Compliance-Specific Sections>

Testing: <required tests>
Validation: <validation status>
Reviewers: <required reviewers>

Audit Trail: <file_count> files modified at <timestamp>
AI Model: <model_name>

Rules:
- Description must be 20-100 characters
- Use conventional commit types: feat, fix, security, perf, breaking, chore, docs, test, refactor
- Be specific and technical
- Focus on WHAT changed and WHY it matters for healthcare
- Include specific compliance framework sections (HIPAA, FDA, SOX) when applicable
"""

        user_prompt = f"""Analyze this git diff and generate a compliant healthcare commit message.

Modified files ({len(files)}):
{chr(10).join(f'- {f}' for f in files[:10])}

Detected metadata:
- Risk Level: {risk_level}
- Clinical Safety: {clinical_safety}
- Compliance Domains: {', '.join(compliance_domains) if compliance_domains else 'None'}
- Required Reviewers: {', '.join(reviewers) if reviewers else 'None'}

Git diff (truncated):
{diff_text[:8000]}

Generate the commit message now following the exact format specified."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for consistency
                max_tokens=1000
            )

            commit_message = response.choices[0].message.content.strip()
            
            # Remove markdown code block formatting if present
            # Handle various markdown formats: ```plaintext, ```, etc.
            if commit_message.startswith("```plaintext"):
                commit_message = commit_message[len("```plaintext"):].lstrip('\n')
            elif commit_message.startswith("```"):
                commit_message = commit_message[3:].lstrip('\n')
            
            if commit_message.endswith("```"):
                commit_message = commit_message[:-3].rstrip('\n')
            
            commit_message = commit_message.strip()

            # Inject actual metadata
            commit_message = commit_message.replace("<risk_level>", risk_level)
            commit_message = commit_message.replace("<clinical_safety>", clinical_safety)
            commit_message = commit_message.replace("<timestamp>", datetime.now(timezone.utc).isoformat())
            commit_message = commit_message.replace("<model_name>", self.model)
            commit_message = commit_message.replace("<file_count>", str(len(files)))

            return commit_message

        except ImportError as e:
            print(f"❌ OpenAI library not properly installed: {e}", file=sys.stderr)
            return self._generate_fallback_message(files, scope)
        except AttributeError as e:
            print(f"❌ OpenAI API client error (check API key and version): {e}", file=sys.stderr)
            return self._generate_fallback_message(files, scope)
        except (TimeoutError, ConnectionError) as e:
            print(f"❌ Network error connecting to OpenAI: {e}", file=sys.stderr)
            return self._generate_fallback_message(files, scope)
        except ValueError as e:
            print(f"❌ Invalid parameter or response format: {e}", file=sys.stderr)
            return self._generate_fallback_message(files, scope)
        except KeyError as e:
            print(f"❌ Unexpected response structure from OpenAI: {e}", file=sys.stderr)
            return self._generate_fallback_message(files, scope)
        except Exception as e:
            # Last resort catch-all with detailed logging
            print(f"❌ Unexpected error during AI generation: {type(e).__name__}: {e}", file=sys.stderr)
            return self._generate_fallback_message(files, scope)

    def _generate_fallback_message(self, files: List[str], scope: Optional[str] = None) -> str:
        """Fallback message when AI is unavailable"""
        risk_level = self.assess_risk_level(files)
        clinical_safety = self.assess_clinical_safety(files)
        compliance_domains = self.detect_compliance_domains(files)
        reviewers = self.suggest_reviewers(compliance_domains, risk_level)

        scope = scope or "core"

        return f"""chore({scope}): update healthcare system components

Business Impact: System maintenance and updates
Risk Level: {risk_level}
Clinical Safety: {clinical_safety}
Compliance: {', '.join(compliance_domains) if compliance_domains else 'None'}

Testing: Standard validation required
Validation: Pending review
Reviewers: {', '.join(reviewers) if reviewers else '@team'}

Audit Trail: {len(files)} files modified at {datetime.now(timezone.utc).isoformat()}
AI Model: fallback-template

⚠️  This is a fallback message. Enable OpenAI for AI-generated compliance metadata.
"""

    def commit_with_message(self, message: str, auto_commit: bool = False):
        """Create git commit with generated message"""
        if auto_commit:
            try:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", message], check=True)
                print("✅ Commit created successfully!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Commit failed: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("\n" + "="*80)
            print("📋 Generated Commit Message:")
            print("="*80)
            print(message)
            print("="*80)
            print("\nTo commit, run:")
            print(f'  git commit -m "{message}"')
            print("\nOr use --auto-commit flag for automatic commit")


def main():
    parser = argparse.ArgumentParser(
        description="GitOps 2.0 AI-Powered Commit Generator for Healthcare",
        epilog="""
Examples:
  # Generate commit message for current changes
  python git_copilot_commit.py --analyze

  # Generate with specific scope and compliance hint
  python git_copilot_commit.py --analyze --scope phi --compliance HIPAA

  # Generate and commit automatically
  python git_copilot_commit.py --analyze --auto-commit

  # Use specific AI model
  python git_copilot_commit.py --analyze --model gpt-4-turbo
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--analyze", action="store_true", help="Analyze git diff and generate commit message")
    parser.add_argument("--scope", help="Commit scope (phi, auth, device, payment, etc.)")
    parser.add_argument("--compliance", help="Compliance hint (HIPAA, FDA, SOX, GDPR, PCI-DSS)")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--auto-commit", action="store_true", help="Automatically create commit (dangerous!)")
    parser.add_argument("--context", default="healthcare", help="Context for analysis (always healthcare)")

    args = parser.parse_args()

    if not args.analyze:
        parser.print_help()
        sys.exit(0)

    print("🤖 GitOps 2.0 AI Commit Generator")
    print("=" * 80)

    # Initialize generator
    generator = GitCopilotCommit(model=args.model)

    # Get git changes
    print("📊 Analyzing git changes...")
    files, diff_text = generator.get_git_diff()

    if not files:
        print("❌ No changes detected. Stage your changes first with 'git add'.")
        sys.exit(1)

    print(f"✅ Found {len(files)} modified files")

    # Generate commit message
    print(f"🧠 Generating compliant commit message with {args.model}...")
    message = generator.generate_commit_message(
        files=files,
        diff_text=diff_text,
        scope=args.scope,
        compliance_hint=args.compliance
    )

    # Output or commit
    generator.commit_with_message(message, auto_commit=args.auto_commit)


if __name__ == "__main__":
    main()
