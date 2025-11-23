#!/usr/bin/env python3
"""
Healthcare Commit Template Generator
Generates AI audit-ready commit messages for healthcare platforms
Security: Input validation, safe YAML loading, encoding specification
Enterprise: Token limit protection, secret sanitization
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Optional dependency: PyYAML is required for this script to function
try:
    import yaml
except ImportError:
    print(
        "Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr
    )
    sys.exit(1)

# Import enterprise safety modules
try:
    from token_limit_guard import check_token_limit, TokenLimitExceededError, get_git_diff
    from secret_sanitizer import SecretSanitizer
    ENTERPRISE_SAFETY_ENABLED = True
except ImportError:
    logger.warning("Enterprise safety modules not found - running without protection")
    ENTERPRISE_SAFETY_ENABLED = False

# Configure secure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HealthcareCommitGenerator:
    """Secure healthcare commit template generator with input validation"""

    def __init__(self, config_path: Path):
        self.config = self._load_config_safely(config_path)
        self.default_model = os.getenv(
            "AI_MODEL_DEFAULT",
            (self.config.get("ai_agents", {}) or {}).get("default_model", "gpt-4"),
        )

    def _load_config_safely(self, config_path: Path) -> Dict[str, Any]:
        """Safely load YAML configuration with validation"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        if not config_path.is_file():
            raise ValueError(f"Configuration path is not a file: {config_path}")

        # Check file size (prevent DoS)
        if config_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("Configuration file too large (>10MB)")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                # Use safe_load to prevent code injection
                config = yaml.safe_load(f)
                if not isinstance(config, dict):
                    raise ValueError("Configuration must be a dictionary")
                return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}") from e
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 encoding in config file: {e}") from e

    def generate_commit_template(
        self, commit_type: str, scope: str, files: List[str], description: str
    ) -> str:
        """Generate healthcare-compliant commit message template with enterprise safety"""
        
        # ENTERPRISE SAFETY CHECK 1: Token Limit Protection
        if ENTERPRISE_SAFETY_ENABLED:
            diff_text = get_git_diff("HEAD")
            if diff_text:
                estimated, max_tokens, is_safe = check_token_limit(diff_text, self.default_model)
                if not is_safe:
                    logger.error(
                        f"⚠️  LARGE CHANGESET: {estimated:,} tokens exceeds {max_tokens:,} limit"
                    )
                    raise TokenLimitExceededError(
                        f"Diff too large for {self.default_model}.\n"
                        f"Options:\n"
                        f"  1. Split into smaller commits (<100 files)\n"
                        f"  2. Use --summary mode for high-level commit\n"
                        f"  3. Switch to GPT-4 Turbo (128K context)"
                    )
                logger.info(f"✅ Token usage safe: {estimated:,}/{max_tokens:,} ({estimated/max_tokens*100:.1f}%)")
        
        # ENTERPRISE SAFETY CHECK 2: Secret Sanitization
        if ENTERPRISE_SAFETY_ENABLED:
            sanitizer = SecretSanitizer()
            for file_path in files:
                if sanitizer.is_sensitive_file(file_path):
                    logger.error(f"⛔ Sensitive file detected: {file_path}")
                    raise ValueError(
                        f"Cannot process sensitive file: {file_path}\n"
                        f"Exclude .env, .key, secrets.* files from AI processing"
                    )
            
            # Check diff for secrets/PHI before AI processing
            if diff_text:
                is_safe, matches = sanitizer.validate_for_ai_processing(diff_text)
                if not is_safe:
                    report = sanitizer.generate_safety_report(matches)
                    logger.error("⛔ Secrets detected in diff")
                    raise ValueError(
                        f"Cannot generate AI commit - secrets detected:\n{report}\n"
                        f"Remove secrets before proceeding."
                    )
                if matches:
                    logger.warning(f"⚠️  {len(matches)} potential secrets detected (proceeding with caution)")

        compliance_domains = self._detect_compliance_domains(files)
        risk_level = self._assess_risk_level(commit_type, files)

        template = f"{commit_type}({scope}): {description}\n\n"

        # Business Impact
        template += (
            f"Business Impact: {self._generate_business_impact(commit_type, scope)}\n"
        )

        # Compliance Mapping
        if compliance_domains:
            template += f"Compliance: {', '.join(compliance_domains)}\n"
            for domain in compliance_domains:
                template += self._generate_compliance_section(domain, files)

        # Risk Assessment
        template += f"Risk Level: {risk_level}\n"
        template += f"Clinical Safety: {self._assess_clinical_safety(files)}\n"

        # Testing & Validation
        template += f"Testing: {self._generate_testing_requirements(commit_type, compliance_domains)}\n"
        template += f"Validation: {self._generate_validation_requirements(compliance_domains)}\n"

        # Monitoring & Rollback
        template += f"Monitoring: {self._generate_monitoring_plan(files)}\n"
        template += f"Rollback: {self._generate_rollback_plan(risk_level)}\n"

        # Audit Trail
        template += f"Audit Trail: Commit {datetime.now().isoformat()} - {len(files)} files modified\n"
        template += f"Reviewers: {self._suggest_reviewers(compliance_domains)}\n"

        # AI Model
        template += f"AI Model: {self.default_model}\n"  # WHY: surfaces active AI model for audit traceability

        return template

    def _detect_compliance_domains(self, files: List[str]) -> List[str]:
        """Detect which compliance domains are affected"""
        domains = set()

        for file_path in files:
            for path, meta in self.config.get("critical_paths", {}).items():
                if file_path.startswith(path):
                    domains.update(meta.get("compliance_domains", []))

        return sorted(list(domains))

    def _assess_risk_level(self, commit_type: str, files: List[str]) -> str:
        """Assess risk level based on commit type and files"""
        if commit_type in ["security", "breaking"]:
            return "HIGH"

        phi_files = [
            f
            for f in files
            if any(p in f.lower() for p in ["phi", "patient", "medical"])
        ]
        if phi_files:
            return "HIGH"

        device_files = [f for f in files if "medical-device" in f]
        if device_files:
            return "CRITICAL"

        return "MEDIUM" if commit_type == "feat" else "LOW"

    def _assess_clinical_safety(self, files: List[str]) -> str:
        """Assess clinical safety impact"""
        clinical_files = [
            f
            for f in files
            if any(
                p in f.lower()
                for p in ["clinical", "diagnostic", "therapeutic", "patient-care"]
            )
        ]
        if clinical_files:
            return "REQUIRES_CLINICAL_REVIEW"
        return "NO_CLINICAL_IMPACT"

    def _generate_compliance_section(self, domain: str, files: List[str]) -> str:
        """Generate compliance-specific documentation"""
        requirements = self.config.get("compliance_requirements", {}).get(domain, {})

        section = f"\n{domain} Compliance:\n"
        for field in requirements.get("mandatory_fields", []):
            section += f"  {field}: [TO_BE_COMPLETED]\n"

        # Add file-specific compliance notes if relevant
        if files and any(
            f
            for f in files
            if any(pattern in f.lower() for pattern in ["patient", "phi", "medical"])
        ):
            section += f"  Files Modified: {len(files)} healthcare-related files\n"

        return section

    def _generate_business_impact(self, commit_type: str, scope: str) -> str:
        """Generate business impact statement"""
        impact_map = {
            "feat": f"New functionality in {scope} domain",
            "fix": f"Bug resolution in {scope} affecting user experience",
            "security": f"Security enhancement in {scope} - CRITICAL for patient data protection",
            "perf": f"Performance optimization in {scope}",
            "breaking": f"Breaking change in {scope} - REQUIRES COORDINATED DEPLOYMENT",
        }
        return impact_map.get(commit_type, f"Changes to {scope} domain")

    def _generate_testing_requirements(
        self, commit_type: str, compliance_domains: List[str]
    ) -> str:
        """Generate testing requirements based on compliance"""
        tests = ["Unit tests", "Integration tests"]

        if "HIPAA" in compliance_domains:
            tests.extend(["PHI encryption validation", "Access control verification"])

        if "FDA" in compliance_domains:
            tests.extend(["Clinical safety validation", "FDA compliance verification"])

        if commit_type == "security":
            tests.extend(["Penetration testing", "Vulnerability scanning"])

        return ", ".join(tests)

    def _generate_validation_requirements(self, compliance_domains: List[str]) -> str:
        """Generate validation requirements"""
        validations = []

        if "HIPAA" in compliance_domains:
            validations.append("HIPAA risk assessment completed")

        if "FDA" in compliance_domains:
            validations.append("FDA change control process followed")

        if "SOX" in compliance_domains:
            validations.append("SOX control testing performed")

        return (
            ", ".join(validations) if validations else "Standard validation completed"
        )

    def _generate_monitoring_plan(self, files: List[str]) -> str:
        """Generate monitoring requirements"""
        if any("api" in f for f in files):
            return "API response times, error rates, authentication metrics"
        elif any("database" in f for f in files):
            return "Database performance, query execution times, connection pools"
        else:
            return "Application metrics, system health, user experience"

    def _generate_rollback_plan(self, risk_level: str) -> str:
        """Generate rollback strategy based on risk"""
        rollback_map = {
            "CRITICAL": "Immediate rollback capability, database backup verified, clinical team notified",
            "HIGH": "Automated rollback triggered if error rate > 0.1%, feature flag available",
            "MEDIUM": "Standard rollback process, monitoring alerts configured",
            "LOW": "Standard deployment rollback available",
        }
        return rollback_map.get(risk_level, "Standard rollback available")

    def _suggest_reviewers(self, compliance_domains: List[str]) -> str:
        """Suggest required reviewers based on compliance domains"""
        reviewers = ["@engineering-team"]

        if "HIPAA" in compliance_domains:
            reviewers.extend(["@privacy-officer", "@security-team"])

        if "FDA" in compliance_domains:
            reviewers.extend(["@clinical-affairs", "@regulatory-team"])

        if "SOX" in compliance_domains:
            reviewers.extend(["@finance-team", "@audit-team"])

        return ", ".join(reviewers)


def main():
    parser = argparse.ArgumentParser(
        description="Generate healthcare-compliant commit messages"
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["feat", "fix", "security", "perf", "breaking", "chore", "docs"],
    )
    parser.add_argument(
        "--scope", required=True, help="Commit scope (e.g., phi, auth, clinical)"
    )
    parser.add_argument("--description", required=True, help="Commit description")
    parser.add_argument(
        "--files", nargs="+", required=True, help="List of modified files"
    )
    parser.add_argument(
        "--config", default="config/git-forensics-config.yaml", help="Config file path"
    )

    args = parser.parse_args()

    try:
        # Validate input parameters
        if len(args.description) > 200:
            raise ValueError("Description must be less than 200 characters")

        if len(args.files) > 100:
            raise ValueError("Too many files specified (max 100)")

        # Validate file paths to prevent directory traversal
        for file_path in args.files:
            if ".." in file_path or file_path.startswith("/"):
                raise ValueError(f"Invalid file path: {file_path}")

        config_path = Path(args.config)
        generator = HealthcareCommitGenerator(config_path)

        template = generator.generate_commit_template(
            args.type, args.scope, args.files, args.description
        )

        print(template)

    except (ValueError, FileNotFoundError) as e:
        logger.error("Error generating commit template: %s", str(e))
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error("YAML error: %s", str(e))
        sys.exit(1)
    except UnicodeDecodeError as e:
        logger.error("Encoding error: %s", str(e))
        sys.exit(1)
    except OSError as e:
        logger.error("OS error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
