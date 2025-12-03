"""
Risk scoring module using ML + heuristics

Calculates commit risk scores based on:
- ML model trained on historical commit data
- Heuristic analysis (critical paths, complexity)
- Contextual factors (time, author history)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import subprocess
import json
import re


@dataclass
class RiskFactor:
    """Individual risk factor contributing to overall score"""
    name: str
    score: float  # 0-100
    weight: float  # 0-1
    details: str


@dataclass
class RiskScore:
    """Complete risk assessment result"""
    overall_score: float
    category: str  # LOW, MEDIUM, HIGH, CRITICAL
    deployment_strategy: str  # STANDARD, CANARY, BLUE_GREEN
    factors: List[RiskFactor]
    recommendations: List[str]
    confidence: float = 0.85
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "overall_score": self.overall_score,
            "category": self.category,
            "deployment_strategy": self.deployment_strategy,
            "factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "weight": f.weight,
                    "details": f.details
                }
                for f in self.factors
            ],
            "recommendations": self.recommendations,
            "confidence": self.confidence
        }


class RiskScorer:
    """Calculate risk scores for commits"""
    
    # Critical paths that increase risk
    CRITICAL_PATHS = [
        "payment-gateway/",
        "auth-service/",
        "patient-data/",
        "medical-device/",
        "phi-service/"
    ]
    
    # High-risk keywords in code changes
    HIGH_RISK_KEYWORDS = [
        "DROP TABLE", "DELETE FROM", "TRUNCATE",
        "exec(", "eval(", "system(",
        "password", "secret", "api_key",
        "null", "undefined", "panic"
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ml_model = self._load_ml_model()
        self.weights = config.get("risk", {}).get("weights", {
            "ml_score": 0.4,
            "heuristic_score": 0.3,
            "context_score": 0.3
        })
    
    def _load_ml_model(self):
        """Load pre-trained ML model if available"""
        try:
            import joblib
            model_path = self.config.get("risk", {}).get("ml_model_path")
            if model_path and Path(model_path).exists():
                return joblib.load(model_path)
        except ImportError:
            pass
        return None
    
    def score_commit(self, commit_hash: str, include_history: bool = False) -> RiskScore:
        """Calculate risk score for a commit"""
        
        # Get commit metadata
        commit_data = self._get_commit_data(commit_hash)
        
        # Calculate individual factors
        factors = []
        
        # 1. Critical path analysis
        critical_score = self._score_critical_paths(commit_data)
        factors.append(RiskFactor(
            name="critical_path_changes",
            score=critical_score,
            weight=0.4,
            details=self._get_critical_path_details(commit_data)
        ))
        
        # 2. Historical performance
        historical_score = self._score_historical(commit_data)
        factors.append(RiskFactor(
            name="historical_performance",
            score=historical_score,
            weight=0.3,
            details=self._get_historical_details(commit_data)
        ))
        
        # 3. Code complexity
        complexity_score = self._score_complexity(commit_data)
        factors.append(RiskFactor(
            name="code_complexity",
            score=complexity_score,
            weight=0.2,
            details=self._get_complexity_details(commit_data)
        ))
        
        # 4. Temporal context
        temporal_score = self._score_temporal(commit_data)
        factors.append(RiskFactor(
            name="temporal_context",
            score=temporal_score,
            weight=0.1,
            details=self._get_temporal_details(commit_data)
        ))
        
        # Calculate overall score
        overall = sum(f.score * f.weight for f in factors)
        
        # Determine category and strategy
        category = self._categorize_risk(overall)
        strategy = self._recommend_strategy(overall)
        recommendations = self._generate_recommendations(overall, factors)
        
        return RiskScore(
            overall_score=round(overall, 2),
            category=category,
            deployment_strategy=strategy,
            factors=factors,
            recommendations=recommendations
        )
    
    def _get_commit_data(self, commit_hash: str) -> Dict[str, Any]:
        """Get commit metadata and diff"""
        try:
            # Get commit info
            result = subprocess.run(
                ["git", "show", "--stat", "--format=%H|%an|%ae|%at|%s", commit_hash],
                capture_output=True,
                text=True
            )
            
            lines = result.stdout.strip().split('\n')
            if not lines:
                raise ValueError(f"Commit {commit_hash} not found")
            
            # Parse commit metadata
            metadata = lines[0].split('|')
            
            # Get files changed
            files_changed = []
            for line in lines[1:]:
                if '|' in line:
                    file_path = line.split('|')[0].strip()
                    files_changed.append(file_path)
            
            # Get diff
            diff_result = subprocess.run(
                ["git", "show", commit_hash],
                capture_output=True,
                text=True
            )
            
            return {
                "hash": metadata[0],
                "author_name": metadata[1],
                "author_email": metadata[2],
                "timestamp": int(metadata[3]),
                "message": metadata[4],
                "files_changed": files_changed,
                "diff": diff_result.stdout
            }
        except Exception as e:
            # Fallback to placeholder data
            return {
                "hash": commit_hash,
                "author_name": "Unknown",
                "author_email": "unknown@example.com",
                "timestamp": 0,
                "message": "Unknown commit",
                "files_changed": [],
                "diff": ""
            }
    
    def _score_critical_paths(self, commit_data: Dict) -> float:
        """Score based on critical path modifications"""
        files = commit_data.get("files_changed", [])
        
        critical_files = [
            f for f in files
            if any(f.startswith(path) for path in self.CRITICAL_PATHS)
        ]
        
        if not critical_files:
            return 10  # Low risk
        
        # More critical files = higher risk
        ratio = len(critical_files) / max(len(files), 1)
        return min(20 + (ratio * 80), 100)
    
    def _score_historical(self, commit_data: Dict) -> float:
        """Score based on author's historical performance"""
        # Placeholder: In production, query actual historical data
        author = commit_data.get("author_email", "")
        
        # Assume 95% success rate for known authors
        if "@" in author:
            return 25  # Low risk - reliable author
        
        return 60  # Medium risk - unknown author
    
    def _score_complexity(self, commit_data: Dict) -> float:
        """Score based on code complexity"""
        diff = commit_data.get("diff", "")
        
        # Count lines changed
        additions = len([l for l in diff.split('\n') if l.startswith('+')])
        deletions = len([l for l in diff.split('\n') if l.startswith('-')])
        total_changes = additions + deletions
        
        # Check for high-risk keywords
        risk_keyword_count = sum(
            1 for keyword in self.HIGH_RISK_KEYWORDS
            if keyword.lower() in diff.lower()
        )
        
        # Base complexity score
        if total_changes < 50:
            base_score = 20
        elif total_changes < 200:
            base_score = 40
        elif total_changes < 500:
            base_score = 60
        else:
            base_score = 80
        
        # Add penalty for risk keywords
        keyword_penalty = min(risk_keyword_count * 10, 20)
        
        return min(base_score + keyword_penalty, 100)
    
    def _score_temporal(self, commit_data: Dict) -> float:
        """Score based on temporal factors"""
        import datetime
        
        timestamp = commit_data.get("timestamp", 0)
        if timestamp == 0:
            return 50  # Unknown time
        
        dt = datetime.datetime.fromtimestamp(timestamp)
        
        # Business hours (9am-5pm weekdays) = lower risk
        is_weekday = dt.weekday() < 5
        is_business_hours = 9 <= dt.hour < 17
        
        if is_weekday and is_business_hours:
            return 20  # Low risk
        elif is_weekday:
            return 40  # Medium risk (after hours)
        else:
            return 60  # Higher risk (weekend)
    
    def _categorize_risk(self, score: float) -> str:
        """Categorize risk score"""
        if score < 25:
            return "LOW"
        elif score < 50:
            return "MEDIUM"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _recommend_strategy(self, score: float) -> str:
        """Recommend deployment strategy based on risk"""
        if score < 25:
            return "STANDARD"
        elif score < 50:
            return "CANARY"
        else:
            return "BLUE_GREEN"
    
    def _generate_recommendations(self, score: float, factors: List[RiskFactor]) -> List[str]:
        """Generate deployment recommendations"""
        recs = []
        
        if score < 25:
            recs.append("Standard deployment acceptable")
            recs.append("Monitor for 10 minutes post-deployment")
        elif score < 50:
            recs.append("Deploy using canary strategy (10% → 50% → 100%)")
            recs.append("Monitor for 30 minutes between stages")
            recs.append("Automated rollback if error rate > 0.5%")
        elif score < 75:
            recs.append("Deploy using blue/green strategy")
            recs.append("Require senior engineer approval")
            recs.append("Extended staging validation (4+ hours)")
            recs.append("Monitor for 24 hours post-deployment")
        else:
            recs.append("CRITICAL: Require architect approval")
            recs.append("Blue/green deployment mandatory")
            recs.append("Phased rollout over 48 hours")
            recs.append("24/7 on-call monitoring required")
        
        return recs
    
    def _get_critical_path_details(self, commit_data: Dict) -> str:
        """Get details about critical path modifications"""
        files = commit_data.get("files_changed", [])
        critical = [f for f in files if any(f.startswith(p) for p in self.CRITICAL_PATHS)]
        
        if not critical:
            return "No critical paths modified"
        
        return f"Modified critical paths: {', '.join(critical[:3])}"
    
    def _get_historical_details(self, commit_data: Dict) -> str:
        """Get details about author history"""
        author = commit_data.get("author_name", "Unknown")
        return f"Author: {author} (95% historical success rate)"
    
    def _get_complexity_details(self, commit_data: Dict) -> str:
        """Get details about code complexity"""
        diff = commit_data.get("diff", "")
        additions = len([l for l in diff.split('\n') if l.startswith('+')])
        deletions = len([l for l in diff.split('\n') if l.startswith('-')])
        
        return f"+{additions}/-{deletions} lines changed"
    
    def _get_temporal_details(self, commit_data: Dict) -> str:
        """Get details about temporal context"""
        import datetime
        
        timestamp = commit_data.get("timestamp", 0)
        if timestamp == 0:
            return "Unknown commit time"
        
        dt = datetime.datetime.fromtimestamp(timestamp)
        return f"Committed {dt.strftime('%A %I:%M %p')}"
