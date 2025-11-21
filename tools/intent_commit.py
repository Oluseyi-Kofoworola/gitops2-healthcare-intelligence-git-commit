#!/usr/bin/env python3
"""Intent-driven commit helper for GitOps 2.0 demo.

This script turns business intent into a Conventional Commit-style message
with rich, machine-readable metadata, aligned to the GitOps 2.0 manifesto.

Usage (from repo root):

  python tools/intent_commit.py \
    --type feat \
    --scope payment \
    --subject "add SOX controls for high-value transactions" \
    --goal "improve SOX audit readiness" \
    --metric "audit-findings-resolved < 2 days" \
    --owner "finance-platform" \
    --risk "high" \
    --rollback "disable sox_high_value_guard feature flag" \
    --testing "unit, integration, compliance" \
    --monitoring "payment_sox_violations, payment_error_rate" \
    --compliance "HIPAA, SOX" \
    --reviewers "@payments-team,@compliance-team"

By default it prints the message to stdout so it can be piped into `git commit`.
"""

import argparse
import json
import textwrap
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "git-forensics-config.yaml"

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # Optional dependency


def _get_default_model() -> str:
    # env override takes precedence
    model = os.getenv("AI_MODEL_DEFAULT")
    if model:
        return model
    # fallback to config if available
    if yaml and CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                ai_agents = cfg.get("ai_agents", {}) or {}
                return ai_agents.get("default_model", "gpt-4")
        except (OSError, ValueError, TypeError):
            return "gpt-4"
    return "gpt-4"


def simulate_policy_check(args: argparse.Namespace) -> dict:
    """Simulate policy-driven governance by checking risk and compliance."""
    policy_results = {
        "policy_passed": True,
        "risk_assessment": args.risk or "medium",
        "compliance_domains": args.compliance.split(",") if args.compliance else [],
        "governance_notes": "Commit aligns with enterprise policies for healthcare compliance."
    }
    return policy_results


def simulate_ai_forensics(args: argparse.Namespace) -> dict:
    """Simulate AI-driven forensics and regression detection."""
    # Simulate detecting potential regressions based on scope and risk
    regressions = []
    if args.risk in ["high", "critical"]:
        regressions.append("Potential latency regression in payment processing.")
    if "payment" in (args.scope or ""):
        regressions.append("Monitor for SOX audit trail integrity.")
    
    forensics_results = {
        "regressions_detected": regressions,
        "forensics_summary": "AI analysis indicates no critical regressions; rollback plan validated.",
        "regression_log": "Logged potential issues for monitoring."
    }
    return forensics_results


def generate_business_summary(args: argparse.Namespace) -> str:
    """Generate business-aligned PR/commit summary."""
    summary = f"Business Impact: {args.goal or 'Enhance service capabilities'}.\n"
    summary += f"Success Metrics: {args.metric or 'Improved performance and compliance'}.\n"
    summary += f"Ownership: {args.owner or 'Platform team'}.\n"
    summary += f"Compliance Alignment: {args.compliance or 'General standards'}."
    return summary


def build_commit_message(args: argparse.Namespace) -> str:
    commit_type = args.type or "feat"
    scope = args.scope or "general"
    subject = args.subject or "update service behavior"

    header = f"{commit_type}({scope}): {subject}"

    lines = [header, ""]

    if args.goal:
        lines.append(f"Goal: {args.goal}")
    if args.metric:
        lines.append(f"Metric: {args.metric}")
    if args.owner:
        lines.append(f"Owner: {args.owner}")
    if args.risk:
        lines.append(f"Risk-Level: {args.risk}")
    if args.compliance:
        lines.append(f"Compliance: {args.compliance}")
    if args.testing:
        lines.append(f"Testing: {args.testing}")
    if args.monitoring:
        lines.append(f"Monitoring: {args.monitoring}")
    if args.rollback:
        lines.append(f"Rollback: {args.rollback}")
    if args.reviewers:
        lines.append(f"Reviewers: {args.reviewers}")

    # Add AI-simulated elements for full alignment
    policy = simulate_policy_check(args)
    forensics = simulate_ai_forensics(args)
    business_summary = generate_business_summary(args)

    lines.append("")
    lines.append("Policy Governance:")
    lines.append(f"- Passed: {policy['policy_passed']}")
    lines.append(f"- Risk: {policy['risk_assessment']}")
    lines.append(f"- Notes: {policy['governance_notes']}")

    lines.append("")
    lines.append("AI Forensics & Regression:")
    lines.append(f"- Regressions: {', '.join(forensics['regressions_detected']) or 'None detected'}")
    lines.append(f"- Summary: {forensics['forensics_summary']}")

    lines.append("")
    lines.append("Business-Aligned Summary:")
    lines.extend(business_summary.split("\n"))

    lines.append("")
    lines.append(f"AI Model: {_get_default_model()}")

    wrapped = []
    for line in lines:
        if line and not any(line.startswith(prefix) for prefix in ("feat(", "fix(", "chore(", "refactor(", "docs(", "test(", "build(", "perf(", "ci(", "revert(")):
            wrapped.extend(textwrap.wrap(line, width=100) or [""])
        else:
            wrapped.append(line)

    return "\n".join(wrapped).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an intent-driven Conventional Commit message.")
    parser.add_argument("--type", help="Conventional commit type (feat, fix, chore, etc.)")
    parser.add_argument("--scope", help="Conventional commit scope (e.g., payment, auth, infra)")
    parser.add_argument("--subject", help="Short subject line describing the change")

    parser.add_argument("--goal", help="Business or product goal for this change")
    parser.add_argument("--metric", help="Success metric or KPI (e.g., 'p95_latency < 200ms')")
    parser.add_argument("--owner", help="Owning team or group (e.g., 'growth-team')")
    parser.add_argument("--risk", help="Risk level (low, medium, high, critical)")
    parser.add_argument("--rollback", help="Rollback strategy if the change misbehaves")
    parser.add_argument("--testing", help="Testing performed (unit, integration, e2e, etc.)")
    parser.add_argument("--monitoring", help="Key monitors, SLOs, or dashboards to watch")
    parser.add_argument("--compliance", help="Relevant compliance domains (HIPAA, SOX, PCI, etc.)")
    parser.add_argument("--reviewers", help="Suggested reviewers or approvers")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON with all metadata")

    args = parser.parse_args()
    
    if args.json:
        # Output structured JSON for AI-native automation
        policy = simulate_policy_check(args)
        forensics = simulate_ai_forensics(args)
        business_summary = generate_business_summary(args)
        output = {
            "commit_message": build_commit_message(args).strip(),
            "semantic_records": {
                "type": args.type or "feat",
                "scope": args.scope or "general",
                "subject": args.subject or "update service behavior"
            },
            "ai_memory": "Simulated Copilot annotation: This commit enhances compliance and business alignment.",
            "policy_governance": policy,
            "ai_forensics": forensics,
            "business_records": business_summary,
            "intent_engineering": {
                "goal": args.goal,
                "metric": args.metric,
                "risk": args.risk,
                "rollback": args.rollback
            }
        }
        print(json.dumps(output, indent=2))
    else:
        message = build_commit_message(args)
        print(message, end="")


if __name__ == "__main__":
    main()
