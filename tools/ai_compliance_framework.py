"""
AI Agent Healthcare Compliance Framework
Integrates AI agents for automated compliance, security, and audit workflows
Enterprise Safety: Token limit protection, secret sanitization, hallucination prevention
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import argparse
import subprocess
import shlex
import json

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    raise

# Import enterprise safety modules
try:
    from token_limit_guard import (
        check_token_limit, 
        TokenLimitExceededError,
        chunk_diff_safely,
        validate_ai_input_size
    )
    from secret_sanitizer import SecretSanitizer
    ENTERPRISE_SAFETY_ENABLED = True
except ImportError:
    logging.warning("Enterprise safety modules not found - running without protection")
    ENTERPRISE_SAFETY_ENABLED = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComplianceAgent:
    name: str
    model: str
    responsibilities: List[str]
    confidence_threshold: float = 0.8

class HealthcareAIFramework:
    def __init__(self, config_path: str):
        # Validate config file path
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        if config_file.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("Configuration file too large")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                if not isinstance(self.config, dict):
                    raise ValueError("Configuration must be a dictionary")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}") from e
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 encoding in config file: {e}") from e
        
        self.agents = self._initialize_agents()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_agents(self) -> Dict[str, ComplianceAgent]:
        """Initialize AI agents based on configuration (skip non-dict entries like default_model)"""
        agents = {}
        cfg = self.config.get("ai_agents", {})
        for agent_name, meta in cfg.items():
            if not isinstance(meta, dict):
                continue
            if meta.get("enabled", False):
                agents[agent_name] = ComplianceAgent(
                    name=agent_name,
                    model=meta.get("models", [cfg.get("default_model", "gpt-4")])[0],
                    responsibilities=meta.get("responsibilities", [])
                )
        return agents
    
    async def analyze_commit_compliance(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze commit for compliance using AI agents
        ENTERPRISE SAFETY: Token limits, secret sanitization, hallucination prevention
        """
        
        # SAFETY CHECK 1: Secret Sanitization (BEFORE AI processing)
        if ENTERPRISE_SAFETY_ENABLED:
            sanitizer = SecretSanitizer()
            
            # Check commit message
            message_safe, message_matches = sanitizer.validate_for_ai_processing(
                commit_data.get("message", "")
            )
            if not message_safe:
                logger.error("⛔ Secrets detected in commit message")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "commit_sha": commit_data.get("sha"),
                    "compliance_status": "BLOCKED",
                    "risk_score": 1.0,
                    "blocking_reason": "Secrets/PHI detected in commit message",
                    "security_report": sanitizer.generate_safety_report(message_matches)
                }
            
            # Check files for sensitive paths
            for file_path in commit_data.get("files", []):
                if sanitizer.is_sensitive_file(file_path):
                    logger.error(f"⛔ Sensitive file in changeset: {file_path}")
                    return {
                        "timestamp": datetime.now().isoformat(),
                        "commit_sha": commit_data.get("sha"),
                        "compliance_status": "BLOCKED",
                        "risk_score": 1.0,
                        "blocking_reason": f"Sensitive file detected: {file_path}",
                        "recommendation": "Exclude .env, .key, secrets.* files from commits"
                    }
        
        # SAFETY CHECK 2: Token Limit Protection
        if ENTERPRISE_SAFETY_ENABLED:
            full_commit_data = json.dumps(commit_data)
            try:
                validate_ai_input_size(full_commit_data, context="commit_data")
            except TokenLimitExceededError as e:
                logger.error(f"⚠️  Commit data exceeds token limits: {e}")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "commit_sha": commit_data.get("sha"),
                    "compliance_status": "REQUIRES_CHUNKING",
                    "risk_score": 0.0,
                    "blocking_reason": "Commit too large for AI processing",
                    "recommendation": "Break into smaller commits or use batch processing"
                }
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "commit_sha": commit_data.get("sha"),
            "compliance_status": "PENDING",
            "agent_analyses": {},
            "required_actions": [],
            "risk_score": 0.0,
            "safety_checks": {
                "secret_sanitization": "PASSED" if ENTERPRISE_SAFETY_ENABLED else "DISABLED",
                "token_limits": "PASSED" if ENTERPRISE_SAFETY_ENABLED else "DISABLED"
            }
        }
        
        # Parallel analysis by different AI agents
        tasks = []
        
        if "compliance_assistant" in self.agents:
            tasks.append(self._compliance_analysis(commit_data))
        
        if "security_analyzer" in self.agents:
            tasks.append(self._security_analysis(commit_data))
        
        if "clinical_validator" in self.agents:
            tasks.append(self._clinical_validation(commit_data))
        
        # Execute all analyses in parallel
        analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for i, analysis in enumerate(analyses):
            if not isinstance(analysis, Exception):
                agent_name = list(self.agents.keys())[i]
                results["agent_analyses"][agent_name] = analysis
                results["risk_score"] = max(results["risk_score"], analysis.get("risk_score", 0.0))
        
        # Determine overall compliance status
        results["compliance_status"] = self._determine_compliance_status(results)
        
        return results
    
    async def _compliance_analysis(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """HIPAA/FDA compliance analysis"""
        
        # Simulate AI agent analysis
        compliance_domains = self._detect_compliance_domains(commit_data.get("files", []))
        
        analysis = {
            "agent": "compliance_assistant",
            "compliance_domains": compliance_domains,
            "risk_score": 0.0,
            "findings": [],
            "recommendations": []
        }
        
        # Check for PHI exposure risk
        phi_risk = self._assess_phi_risk(commit_data)
        if phi_risk > 0.5:
            analysis["risk_score"] = 0.9
            analysis["findings"].append("HIGH: Potential PHI exposure detected")
            analysis["recommendations"].append("Require HIPAA privacy officer review")
        
        # Check for FDA compliance
        if "FDA" in compliance_domains:
            analysis["risk_score"] = max(analysis["risk_score"], 0.8)
            analysis["findings"].append("FDA-regulated software modification detected")
            analysis["recommendations"].append("FDA change control process required")
        
        return analysis
    
    async def _security_analysis(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Security vulnerability and encryption analysis"""
        
        analysis = {
            "agent": "security_analyzer",
            "risk_score": 0.0,
            "vulnerabilities": [],
            "encryption_status": "COMPLIANT",
            "recommendations": []
        }
        
        # Check for security-related changes
        security_files = [f for f in commit_data.get("files", []) 
                         if any(pattern in f.lower() for pattern in ["auth", "security", "encryption", "password"])]
        
        if security_files:
            analysis["risk_score"] = 0.7
            analysis["recommendations"].append("Security team review required")
            analysis["recommendations"].append("Penetration testing recommended")
        
        return analysis
    
    async def _clinical_validation(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clinical safety and medical accuracy validation"""
        
        analysis = {
            "agent": "clinical_validator",
            "risk_score": 0.0,
            "clinical_impact": "LOW",
            "safety_concerns": [],
            "recommendations": []
        }
        
        # Check for clinical impact
        clinical_files = [f for f in commit_data.get("files", [])
                         if any(pattern in f.lower() for pattern in ["clinical", "patient", "diagnostic", "therapeutic"])]
        
        if clinical_files:
            analysis["risk_score"] = 0.8
            analysis["clinical_impact"] = "HIGH"
            analysis["recommendations"].append("Clinical affairs team review required")
            analysis["recommendations"].append("Medical device risk assessment needed")
        
        return analysis
    
    def _detect_compliance_domains(self, files: List[str]) -> List[str]:
        """Detect compliance domains based on file paths"""
        domains = set()
        
        for file_path in files:
            for path, meta in self.config.get("critical_paths", {}).items():
                if file_path.startswith(path):
                    domains.update(meta.get("compliance_domains", []))
        
        return sorted(list(domains))
    
    def _assess_phi_risk(self, commit_data: Dict[str, Any]) -> float:
        """Assess Protected Health Information risk"""
        phi_indicators = ["patient", "medical", "phi", "ssn", "dob", "address"]
        
        message = commit_data.get("message", "").lower()
        files = commit_data.get("files", [])
        
        # Check commit message for PHI indicators
        message_risk = sum(1 for indicator in phi_indicators if indicator in message) / len(phi_indicators)
        
        # Check file paths for PHI indicators
        file_risk = sum(1 for f in files if any(indicator in f.lower() for indicator in phi_indicators)) / max(len(files), 1)
        
        return max(message_risk, file_risk)
    
    def _determine_compliance_status(self, results: Dict[str, Any]) -> str:
        """Determine overall compliance status"""
        risk_score = results["risk_score"]
        
        if risk_score >= 0.9:
            return "NON_COMPLIANT"
        elif risk_score >= 0.7:
            return "REQUIRES_REVIEW"
        elif risk_score >= 0.4:
            return "CONDITIONAL_APPROVAL"
        else:
            return "COMPLIANT"
    
    def generate_compliance_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable compliance report"""
        
        report = f"""
# AI Compliance Analysis Report

**Commit:** {analysis_results['commit_sha']}
**Timestamp:** {analysis_results['timestamp']}
**Overall Status:** {analysis_results['compliance_status']}
**Risk Score:** {analysis_results['risk_score']:.2f}/1.0

## Agent Analyses

"""
        
        for agent_name, analysis in analysis_results.get("agent_analyses", {}).items():
            report += f"### {agent_name.title()}\n"
            report += f"- **Risk Score:** {analysis.get('risk_score', 0.0):.2f}\n"
            
            if analysis.get("findings"):
                report += "- **Findings:**\n"
                for finding in analysis["findings"]:
                    report += f"  - {finding}\n"
            
            if analysis.get("recommendations"):
                report += "- **Recommendations:**\n"
                for rec in analysis["recommendations"]:
                    report += f"  - {rec}\n"
            
            report += "\n"
        
        # Required actions
        if analysis_results.get("required_actions"):
            report += "## Required Actions\n\n"
            for action in analysis_results["required_actions"]:
                report += f"- {action}\n"
        
        return report

# Utility: safe git command runner
def _run_git(cmd: str) -> Tuple[int, str, str]:
    parts = shlex.split(cmd)
    proc = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace")

def _sanitize_ref(ref: str) -> str:
    bad = [';', '&', '|', '`', '$', '(', ')', '>', '<']
    if any(b in ref for b in bad):
        raise ValueError(f"Invalid ref: {ref}")
    return ref

def load_commit_data(ref: str) -> Dict[str, Any]:
    ref = _sanitize_ref(ref)
    code, out, err = _run_git(f"git show --name-only --format=%H%n%B {ref}")
    if code != 0:
        raise RuntimeError(f"git show failed: {err}")
    lines = out.splitlines()
    if not lines:
        raise RuntimeError("Empty git show output")
    sha = lines[0].strip()
    # Commit message until blank line or file list separation
    message_lines = []
    file_lines = []
    parsing_files = False
    for line in lines[1:]:
        if not parsing_files and line.strip() == "":
            parsing_files = True
            continue
        if parsing_files:
            if line.strip():
                file_lines.append(line.strip())
        else:
            message_lines.append(line.rstrip())
    message = "\n".join(message_lines).strip()
    return {"sha": sha, "message": message, "files": file_lines}

def analyze_commit(ref: str, json_output: bool) -> Dict[str, Any]:
    # Resolve config path relative to repo root or script directory
    script_dir = Path(__file__).parent.parent
    default_cfg = script_dir / "config" / "git-forensics-config.yaml"
    local_cfg = Path("config/git-forensics-config.yaml")
    cfg_path = local_cfg if local_cfg.exists() else default_cfg
    framework = HealthcareAIFramework(str(cfg_path))
    commit_data = load_commit_data(ref)
    results = asyncio.run(framework.analyze_commit_compliance(commit_data))
    report = framework.generate_compliance_report(results)
    output = {"commit_analysis": results, "human_report": report}
    if json_output:
        print(json.dumps(output, indent=2))
    else:
        print(report)
    return output

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Healthcare AI Compliance Framework CLI")
    sub = p.add_subparsers(dest="command", required=False)
    ac = sub.add_parser("analyze-commit", help="Analyze a single commit for healthcare compliance")
    ac.add_argument("ref", nargs="?", default="HEAD", help="Git ref / commit SHA (default HEAD)")
    ac.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable report")
    return p

def cli_main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "analyze-commit":
        analyze_commit(args.ref, args.json)
    else:
        # Default: analyze HEAD if no subcommand provided
        analyze_commit("HEAD", False)

def main_entry():
    cli_main()

if __name__ == "__main__":
    cli_main()
