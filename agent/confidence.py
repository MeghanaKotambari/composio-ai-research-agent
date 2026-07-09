"""
Confidence Estimator module for the AI Research Agent.

Calculates confidence scores for research data based on multiple factors.
Provides transparent scoring logic that can be audited and improved.

Responsibilities:
- Calculate confidence scores
- Weight different evidence factors
- Provide scoring rationale
- Support threshold-based filtering
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .logger import get_logger
from .models import AppResearch

logger = get_logger(__name__)


class ConfidenceEstimator:
    """
    Calculates confidence scores for research data.
    
    Uses a weighted scoring system based on multiple factors:
    - Evidence availability
    - Authentication detection
    - API surface detection
    - Blocker identification
    - Buildability justification
    - Data completeness
    """

    # Scoring weights (total = 100)
    WEIGHTS = {
        "evidence_url": 20,      # Evidence URL exists and is valid
        "auth_detected": 20,     # Authentication methods identified
        "api_detected": 20,      # API surface documented
        "blocker_found": 20,     # Main blocker identified
        "buildability_justified": 20,  # Buildability has rationale
    }

    # Thresholds
    HIGH_THRESHOLD = 0.8
    MEDIUM_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.3

    def __init__(self):
        """Initialize confidence estimator."""
        self.scoring_details: Dict[str, Any] = {}

    def calculate(self, app_data: AppResearch) -> float:
        """
        Calculate confidence score for research data.
        
        Args:
            app_data: AppResearch object with research data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        logger.debug(f"Calculating confidence score for {app_data.name}")
        
        scores = {}
        total_weight = 0
        weighted_sum = 0

        # Factor 1: Evidence URL (20 points)
        evidence_score = self._score_evidence_url(app_data)
        scores["evidence_url"] = evidence_score
        weighted_sum += evidence_score * self.WEIGHTS["evidence_url"]
        total_weight += self.WEIGHTS["evidence_url"]

        # Factor 2: Authentication detected (20 points)
        auth_score = self._score_auth_detected(app_data)
        scores["auth_detected"] = auth_score
        weighted_sum += auth_score * self.WEIGHTS["auth_detected"]
        total_weight += self.WEIGHTS["auth_detected"]

        # Factor 3: API surface detected (20 points)
        api_score = self._score_api_detected(app_data)
        scores["api_detected"] = api_score
        weighted_sum += api_score * self.WEIGHTS["api_detected"]
        total_weight += self.WEIGHTS["api_detected"]

        # Factor 4: Blocker identified (20 points)
        blocker_score = self._score_blocker_found(app_data)
        scores["blocker_found"] = blocker_score
        weighted_sum += blocker_score * self.WEIGHTS["blocker_found"]
        total_weight += self.WEIGHTS["blocker_found"]

        # Factor 5: Buildability justified (20 points)
        buildability_score = self._score_buildability_justified(app_data)
        scores["buildability_justified"] = buildability_score
        weighted_sum += buildability_score * self.WEIGHTS["buildability_justified"]
        total_weight += self.WEIGHTS["buildability_justified"]

        # Calculate final score
        final_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Store scoring details for audit
        self.scoring_details = {
            "app_name": app_data.name,
            "scores": scores,
            "weighted_sum": weighted_sum,
            "total_weight": total_weight,
            "final_score": round(final_score, 2),
            "rating": self._get_rating(final_score),
        }
        
        logger.debug(
            f"Confidence score for {app_data.name}: {final_score:.2f} "
            f"({self._get_rating(final_score)})"
        )
        
        return round(final_score, 2)

    def _score_evidence_url(self, app_data: AppResearch) -> float:
        """
        Score evidence URL factor.
        
        Args:
            app_data: AppResearch object
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not app_data.evidence_url:
            return 0.0
        
        # Evidence URL exists
        base_score = 0.5
        
        # Bonus for specific documentation URLs
        url_str = str(app_data.evidence_url).lower()
        if any(term in url_str for term in ["docs", "documentation", "api", "developer"]):
            base_score += 0.3
        
        # Bonus for HTTPS
        if url_str.startswith("https://"):
            base_score += 0.2
        
        return min(base_score, 1.0)

    def _score_auth_detected(self, app_data: AppResearch) -> float:
        """
        Score authentication detection factor.
        
        Args:
            app_data: AppResearch object
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not app_data.auth_methods or len(app_data.auth_methods) == 0:
            return 0.0
        
        # Base score for having auth methods
        base_score = 0.5
        
        # Bonus for multiple auth methods
        if len(app_data.auth_methods) >= 2:
            base_score += 0.2
        
        # Bonus for specific auth methods (more specific = better)
        specific_methods = ["oauth2", "oauth1", "jwt", "api_key"]
        if any(method in app_data.auth_methods for method in specific_methods):
            base_score += 0.3
        
        return min(base_score, 1.0)

    def _score_api_detected(self, app_data: AppResearch) -> float:
        """
        Score API surface detection factor.
        
        Args:
            app_data: AppResearch object
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not app_data.api_surface:
            return 0.0
        
        api_surface = app_data.api_surface.lower()
        base_score = 0.5
        
        # Bonus for detailed API description
        if len(app_data.api_surface) > 100:
            base_score += 0.2
        
        # Bonus for specific API terms
        api_terms = ["rest", "graphql", "endpoint", "api", "sdk", "webhook"]
        if any(term in api_surface for term in api_terms):
            base_score += 0.3
        
        return min(base_score, 1.0)

    def _score_blocker_found(self, app_data: AppResearch) -> float:
        """
        Score blocker identification factor.
        
        Args:
            app_data: AppResearch object
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not app_data.main_blocker:
            return 0.0
        
        # Base score for having a blocker identified
        base_score = 0.6
        
        # Bonus for specific blocker description
        if len(app_data.main_blocker) > 20:
            base_score += 0.2
        
        # Bonus for technical blockers (shows deep analysis)
        technical_terms = ["rate limit", "authentication", "api", "permission", "access"]
        blocker_lower = app_data.main_blocker.lower()
        if any(term in blocker_lower for term in technical_terms):
            base_score += 0.2
        
        return min(base_score, 1.0)

    def _score_buildability_justified(self, app_data: AppResearch) -> float:
        """
        Score buildability justification factor.
        
        Args:
            app_data: AppResearch object
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not app_data.buildability:
            return 0.0
        
        # Base score for having buildability assessment
        base_score = 0.5
        
        # Bonus for specific buildability rating
        if app_data.buildability in ["high", "medium", "low"]:
            base_score += 0.3
        
        # Bonus for consistency with other factors
        # High buildability should correlate with good API and auth
        if app_data.buildability == "high":
            if app_data.api_surface and app_data.auth_methods:
                base_score += 0.2
        
        return min(base_score, 1.0)

    def _get_rating(self, score: float) -> str:
        """
        Get rating label for score.
        
        Args:
            score: Confidence score
            
        Returns:
            Rating string (high, medium, low)
        """
        if score >= self.HIGH_THRESHOLD:
            return "high"
        elif score >= self.MEDIUM_THRESHOLD:
            return "medium"
        elif score >= self.LOW_THRESHOLD:
            return "low"
        else:
            return "very_low"

    def get_scoring_details(self) -> Dict[str, Any]:
        """
        Get detailed scoring breakdown.
        
        Returns:
            Dictionary with scoring details
        """
        return self.scoring_details

    def get_confidence_level(self, score: float) -> str:
        """
        Get confidence level description.
        
        Args:
            score: Confidence score
            
        Returns:
            Confidence level string
        """
        if score >= 0.8:
            return "High confidence - data is reliable"
        elif score >= 0.6:
            return "Medium confidence - data is mostly reliable"
        elif score >= 0.4:
            return "Low confidence - data needs verification"
        else:
            return "Very low confidence - data is unreliable"

    def calculate_batch_statistics(self, apps: List[AppResearch]) -> Dict[str, Any]:
        """
        Calculate confidence statistics for a batch of apps.
        
        Args:
            apps: List of AppResearch objects
            
        Returns:
            Dictionary with batch statistics
        """
        if not apps:
            return {
                "total_apps": 0,
                "average_confidence": 0.0,
                "high_confidence_count": 0,
                "medium_confidence_count": 0,
                "low_confidence_count": 0,
            }
        
        scores = [self.calculate(app) for app in apps]
        
        return {
            "total_apps": len(apps),
            "average_confidence": round(sum(scores) / len(scores), 2),
            "high_confidence_count": sum(1 for s in scores if s >= self.HIGH_THRESHOLD),
            "medium_confidence_count": sum(1 for s in scores if self.MEDIUM_THRESHOLD <= s < self.HIGH_THRESHOLD),
            "low_confidence_count": sum(1 for s in scores if s < self.MEDIUM_THRESHOLD),
            "min_confidence": min(scores),
            "max_confidence": max(scores),
        }

    def should_include_in_dashboard(self, confidence_score: float) -> bool:
        """
        Determine if app should be included in dashboard.
        
        Args:
            confidence_score: Confidence score
            
        Returns:
            True if should be included, False otherwise
        """
        return confidence_score >= self.MEDIUM_THRESHOLD

    def get_improvement_suggestions(self, app_data: AppResearch) -> List[str]:
        """
        Get suggestions for improving confidence score.
        
        Args:
            app_data: AppResearch object
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        if not app_data.evidence_url:
            suggestions.append("Add evidence URL to improve confidence")
        
        if not app_data.auth_methods or len(app_data.auth_methods) == 0:
            suggestions.append("Identify authentication methods")
        
        if not app_data.api_surface:
            suggestions.append("Document API surface and capabilities")
        
        if not app_data.main_blocker:
            suggestions.append("Identify main blocker for AI agent integration")
        
        if not app_data.buildability:
            suggestions.append("Assess buildability for AI agents")
        
        return suggestions