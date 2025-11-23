#!/usr/bin/env python3
"""
Real AI Integration for Healthcare Compliance
Connects to actual LLM APIs (OpenAI, Azure OpenAI, GitHub Copilot)
WHY: Move from conceptual AI references to production-ready LLM integration
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GITHUB_COPILOT = "github_copilot"
    ANTHROPIC = "anthropic"


@dataclass
class AIConfig:
    """AI provider configuration"""
    provider: AIProvider
    api_key: Optional[str] = None
    endpoint: Optional[str] = None  # For Azure OpenAI
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.3  # Lower for more deterministic compliance
    timeout: int = 30


class AIIntegration:
    """
    Production-ready AI integration for healthcare compliance
    Supports multiple LLM providers with fallback strategies
    """
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate AI client"""
        try:
            if self.config.provider == AIProvider.OPENAI:
                self._init_openai()
            elif self.config.provider == AIProvider.AZURE_OPENAI:
                self._init_azure_openai()
            elif self.config.provider == AIProvider.GITHUB_COPILOT:
                self._init_github_copilot()
            elif self.config.provider == AIProvider.ANTHROPIC:
                self._init_anthropic()
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
        except ImportError as e:
            logger.warning(f"AI provider SDK not available: {e}")
            logger.warning("Install with: pip install openai anthropic")
            self.client = None
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.config.api_key or os.getenv("OPENAI_API_KEY")
            )
            logger.info("✅ OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI SDK not installed. Run: pip install openai")
            raise
    
    def _init_azure_openai(self):
        """Initialize Azure OpenAI client"""
        try:
            import openai
            self.client = openai.AzureOpenAI(
                api_key=self.config.api_key or os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=self.config.endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version="2024-02-15-preview"
            )
            logger.info("✅ Azure OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI SDK not installed. Run: pip install openai")
            raise
    
    def _init_github_copilot(self):
        """Initialize GitHub Copilot client"""
        # GitHub Copilot uses OpenAI-compatible API
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.config.api_key or os.getenv("GITHUB_TOKEN"),
                base_url="https://api.githubcopilot.com"
            )
            logger.info("✅ GitHub Copilot client initialized")
        except ImportError:
            logger.error("OpenAI SDK not installed. Run: pip install openai")
            raise
    
    def _init_anthropic(self):
        """Initialize Anthropic (Claude) client"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            )
            logger.info("✅ Anthropic client initialized")
        except ImportError:
            logger.error("Anthropic SDK not installed. Run: pip install anthropic")
            raise
    
    async def analyze_commit_compliance(
        self, 
        commit_message: str, 
        diff: str, 
        files: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze commit for HIPAA/FDA/SOX compliance using real LLM
        
        Returns:
            {
                "compliant": bool,
                "risk_score": float (0.0-1.0),
                "violations": List[str],
                "recommendations": List[str],
                "compliance_codes": List[str],
                "model_used": str
            }
        """
        if not self.client:
            return self._fallback_analysis(commit_message, diff, files)
        
        prompt = self._build_compliance_prompt(commit_message, diff, files)
        
        try:
            if self.config.provider == AIProvider.ANTHROPIC:
                response = await self._call_anthropic(prompt)
            else:
                response = await self._call_openai(prompt)
            
            return self._parse_compliance_response(response)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(commit_message, diff, files)
    
    def _build_compliance_prompt(
        self, 
        commit_message: str, 
        diff: str, 
        files: List[str]
    ) -> str:
        """Build prompt for compliance analysis"""
        return f"""You are a healthcare compliance expert analyzing a Git commit for HIPAA, FDA, and SOX compliance.

COMMIT MESSAGE:
{commit_message}

CHANGED FILES:
{', '.join(files)}

DIFF (first 2000 chars):
{diff[:2000]}

TASK:
1. Identify any compliance violations (HIPAA 164.308/164.310/164.312, FDA 21 CFR Part 11, SOX 302/404)
2. Assess risk level (0.0 = low, 1.0 = critical)
3. Extract compliance codes mentioned
4. Provide actionable recommendations

RESPONSE FORMAT (JSON):
{{
  "compliant": true/false,
  "risk_score": 0.0-1.0,
  "violations": ["violation 1", "violation 2"],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "compliance_codes": ["164.312(e)(1)", "21CFR11.10"],
  "reasoning": "brief explanation"
}}

Respond ONLY with valid JSON."""
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI/Azure OpenAI API"""
        try:
            import openai
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a healthcare compliance expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic (Claude) API"""
        try:
            import anthropic
            response = self.client.messages.create(
                model=self.config.model or "claude-3-5-sonnet-20241022",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def _parse_compliance_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured compliance analysis"""
        try:
            # Extract JSON from response (handles markdown code blocks)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            data = json.loads(response)
            
            # Add model metadata
            data["model_used"] = self.config.model
            data["provider"] = self.config.provider.value
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.error(f"Response: {response[:500]}")
            return self._fallback_analysis("", "", [])
    
    def _fallback_analysis(
        self, 
        commit_message: str, 
        diff: str, 
        files: List[str]
    ) -> Dict[str, Any]:
        """Fallback heuristic analysis when AI is unavailable"""
        logger.warning("Using fallback heuristic analysis (AI unavailable)")
        
        risk_score = 0.0
        violations = []
        recommendations = []
        
        # Heuristic checks
        if any(term in commit_message.lower() for term in ["phi", "patient", "medical"]):
            risk_score = max(risk_score, 0.7)
            violations.append("Potential PHI exposure - verify HIPAA 164.312(e)(1) encryption")
        
        if any(term in commit_message.lower() for term in ["device", "fda", "510k"]):
            risk_score = max(risk_score, 0.8)
            violations.append("FDA-regulated device - verify 21 CFR Part 11 compliance")
        
        if any(term in commit_message.lower() for term in ["financial", "sox", "audit"]):
            risk_score = max(risk_score, 0.6)
            violations.append("Financial system - verify SOX 404 controls")
        
        if not violations:
            violations.append("No obvious violations detected (heuristic analysis only)")
        
        recommendations.append("Use AI-powered analysis for comprehensive compliance review")
        recommendations.append("Manually verify compliance codes against official regulations")
        
        return {
            "compliant": risk_score < 0.5,
            "risk_score": risk_score,
            "violations": violations,
            "recommendations": recommendations,
            "compliance_codes": [],
            "model_used": "heuristic_fallback",
            "provider": "local",
            "reasoning": "Fallback analysis due to AI unavailability"
        }
    
    async def generate_commit_message(
        self, 
        diff: str, 
        files: List[str],
        commit_type: str = "feat"
    ) -> str:
        """
        Generate HIPAA-compliant commit message using AI
        
        Returns:
            Full commit message with compliance metadata
        """
        if not self.client:
            return self._fallback_commit_message(diff, files, commit_type)
        
        prompt = f"""Generate a HIPAA-compliant Git commit message for the following changes.

COMMIT TYPE: {commit_type}
CHANGED FILES: {', '.join(files)}
DIFF (first 2000 chars):
{diff[:2000]}

REQUIREMENTS:
1. Follow Conventional Commits format: type(scope): subject
2. Include compliance metadata (HIPAA:, PHI-Impact:, etc.)
3. Add business impact statement
4. Suggest reviewers based on risk
5. Be concise but comprehensive

RESPONSE FORMAT:
Just the commit message (no explanation, no markdown formatting).
"""
        
        try:
            if self.config.provider == AIProvider.ANTHROPIC:
                message = await self._call_anthropic(prompt)
            else:
                message = await self._call_openai(prompt)
            
            # Clean up markdown if present
            if "```" in message:
                message = message.split("```")[1].strip() if message.count("```") > 1 else message
            
            return message.strip()
            
        except Exception as e:
            logger.error(f"AI commit generation failed: {e}")
            return self._fallback_commit_message(diff, files, commit_type)
    
    def _fallback_commit_message(
        self, 
        diff: str, 
        files: List[str], 
        commit_type: str
    ) -> str:
        """Generate basic commit message without AI"""
        scope = "healthcare" if any("phi" in f or "patient" in f for f in files) else "platform"
        
        message = f"""{commit_type}({scope}): update {len(files)} file(s)

Business Impact: Code changes in {scope} domain
Risk Level: MEDIUM
Testing: Manual verification required

Files Modified: {', '.join(files[:5])}
{"..." if len(files) > 5 else ""}

Reviewers: @engineering-team
Note: Generated without AI assistance - manual review recommended
"""
        return message


# Factory function for easy instantiation
def create_ai_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: str = "gpt-4"
) -> AIIntegration:
    """
    Create AI client with sensible defaults
    
    Usage:
        ai = create_ai_client("openai", api_key="sk-...")
        result = await ai.analyze_commit_compliance(message, diff, files)
    """
    config = AIConfig(
        provider=AIProvider(provider),
        api_key=api_key,
        model=model,
        temperature=0.3,  # Deterministic for compliance
        max_tokens=4000
    )
    return AIIntegration(config)


# Demo usage
async def demo():
    """Demonstrate real AI integration"""
    print("🤖 Real AI Integration Demo\n" + "="*60 + "\n")
    
    # Check for API keys
    providers = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append("openai")
    if os.getenv("AZURE_OPENAI_API_KEY"):
        providers.append("azure_openai")
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append("anthropic")
    
    if not providers:
        print("⚠️  No API keys found. Using fallback heuristic analysis.")
        print("Set OPENAI_API_KEY, AZURE_OPENAI_API_KEY, or ANTHROPIC_API_KEY\n")
        provider = "openai"  # Will use fallback
    else:
        provider = providers[0]
        print(f"✅ Using {provider.upper()} for AI analysis\n")
    
    # Create client
    ai = create_ai_client(provider=provider)
    
    # Test commit analysis
    test_message = """feat(phi): add AES-256 encryption for patient data

HIPAA: 164.312(e)(1)
PHI-Impact: HIGH
"""
    test_diff = """
+func EncryptPHI(data []byte) ([]byte, error) {
+    cipher, _ := aes.NewCipher(key)
+    encrypted := make([]byte, aes.BlockSize+len(data))
+    return encrypted, nil
+}
"""
    test_files = ["services/phi-service/encryption.go"]
    
    print("Analyzing commit...")
    result = await ai.analyze_commit_compliance(test_message, test_diff, test_files)
    
    print(json.dumps(result, indent=2))
    print(f"\n{'✅ COMPLIANT' if result['compliant'] else '❌ NON-COMPLIANT'}")
    print(f"Risk Score: {result['risk_score']:.2f}")
    print(f"Model: {result['model_used']}")


if __name__ == "__main__":
    asyncio.run(demo())
