"""
AI Agent Healthcare Compliance Framework
Integrates AI agents for automated compliance, security, and audit workflows
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    raise

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
        """Initialize AI agents based on configuration"""
        agents = {}
        
        for agent_name, config in self.config.get("ai_agents", {}).items():
            if config.get("enabled", False):
                agents[agent_name] = ComplianceAgent(
                    name=agent_name,
                    model=config.get("models", ["gpt-4"])[0],
                    responsibilities=config.get("responsibilities", [])
                )
        
        return agents
    
    async def analyze_commit_compliance(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze commit for compliance using AI agents"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "commit_sha": commit_data.get("sha"),
            "compliance_status": "PENDING",
            "agent_analyses": {},
            "required_actions": [],
            "risk_score": 0.0
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

# Example usage for AI agent integration
async def main():
    framework = HealthcareAIFramework("config/git-forensics-config.yaml")
    
    # Example commit data
    commit_data = {
        "sha": "abc123def456",
        "message": "feat(phi): add patient data encryption",
        "files": ["services/phi-service/encryption.py", "lib/security/crypto.py"],
        "author": "developer@healthcare.com"
    }
    
    # Analyze commit compliance
    results = await framework.analyze_commit_compliance(commit_data)
    
    # Generate report
    report = framework.generate_compliance_report(results)
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
