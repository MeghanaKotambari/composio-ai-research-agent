"""
Mock LLM Provider for the AI Research Agent.

Analyzes documentation text to generate realistic, data-driven JSON responses.
"""

import json
import re
from typing import Any, Optional, List, Dict

from .base import BaseLLMProvider
from ..logger import get_logger

logger = get_logger(__name__)


class MockProvider(BaseLLMProvider):
    """
    Mock LLM provider that analyzes documentation to generate realistic results.
    
    Instead of returning category templates, this provider extracts keywords
    from the documentation text to determine auth methods, API types, etc.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        """
        Initialize mock provider.
        
        Args:
            api_key: Ignored (for interface compatibility)
            model_name: Ignored (for interface compatibility)
        """
        super().__init__(api_key, model_name)
        logger.info("MockProvider initialized")
    
    def _extract_keywords(self, text: str) -> Dict[str, Any]:
        """
        Extract relevant keywords from documentation text.
        
        Args:
            text: Documentation text to analyze
            
        Returns:
            Dictionary with extracted keywords
        """
        text_lower = text.lower()
        
        # Auth method detection
        auth_methods = []
        if "oauth" in text_lower or "oauth2" in text_lower:
            auth_methods.append("oauth2")
        if "api key" in text_lower or "apikey" in text_lower or "api-key" in text_lower:
            auth_methods.append("api_key")
        if "bearer token" in text_lower or "bearer_token" in text_lower:
            auth_methods.append("bearer_token")
        if "personal access token" in text_lower or "pat" in text_lower:
            auth_methods.append("api_key")
        if "bot token" in text_lower or "bot_token" in text_lower:
            auth_methods.append("bot_token")
        if "jwt" in text_lower:
            auth_methods.append("jwt")
        
        # API type detection
        api_types = []
        if "rest api" in text_lower or "restful" in text_lower:
            api_types.append("rest")
        if "graphql" in text_lower:
            api_types.append("graphql")
        if "webhook" in text_lower:
            api_types.append("webhook")
        if "sdk" in text_lower or "client library" in text_lower:
            api_types.append("sdk")
        if "openapi" in text_lower or "openapi.json" in text_lower:
            api_types.append("openapi")
        
        # Self-serve detection
        self_serve = True
        if "contact sales" in text_lower or "enterprise only" in text_lower:
            self_serve = False
        if "gated" in text_lower or "request access" in text_lower:
            self_serve = False
        
        # MCP detection
        mcp_support = "mcp" in text_lower or "model context protocol" in text_lower
        
        # Buildability detection
        buildability = "medium"
        if "excellent documentation" in text_lower or "comprehensive api" in text_lower:
            buildability = "high"
        if "beta" in text_lower or "limited access" in text_lower or "invite only" in text_lower:
            buildability = "low"
        if "enterprise only" in text_lower or "partner" in text_lower:
            buildability = "blocked"
        
        # Blocker detection
        blockers = []
        if "rate limit" in text_lower:
            blockers.append("Rate Limits")
        if "enterprise only" in text_lower:
            blockers.append("Enterprise Only")
        if "partner" in text_lower:
            blockers.append("Partner Approval")
        if "no public api" in text_lower:
            blockers.append("No Public API")
        if "beta" in text_lower:
            blockers.append("Beta API")
        if "invite only" in text_lower:
            blockers.append("Invite Only")
        if "manual setup" in text_lower:
            blockers.append("Manual Setup")
        
        return {
            "auth_methods": auth_methods if auth_methods else ["api_key"],
            "api_types": api_types if api_types else ["rest"],
            "self_serve": self_serve,
            "mcp_support": mcp_support,
            "buildability": buildability,
            "blockers": blockers,
        }
    
    def _calculate_confidence(self, keywords: Dict[str, Any], has_evidence: bool) -> float:
        """
        Calculate confidence score based on extracted keywords.
        
        Weights:
        - Documentation Quality: 30%
        - Verification Score: 30%
        - Required Fields: 20%
        - Evidence Quality: 10%
        - Retry Penalty: 5%
        - Manual Review Penalty: 5%
        
        Args:
            keywords: Extracted keywords
            has_evidence: Whether evidence URL exists
            
        Returns:
            Confidence score between 0.45 and 0.98
        """
        # Base score
        score = 0.45
        
        # Documentation quality (30% weight)
        if keywords["auth_methods"]:
            score += 0.15
        if keywords["api_types"]:
            score += 0.10
        if len(keywords["api_types"]) > 1:
            score += 0.05
        
        # Verification score (30% weight)
        if has_evidence:
            score += 0.15
        if keywords["self_serve"]:
            score += 0.10
        if not keywords["blockers"]:
            score += 0.05
        
        # Required fields (20% weight)
        if keywords["auth_methods"]:
            score += 0.10
        if keywords["api_types"]:
            score += 0.10
        
        # Evidence quality (10% weight)
        if has_evidence:
            score += 0.10
        
        # Manual review penalty (5% weight)
        if keywords["buildability"] == "blocked":
            score -= 0.05
        if keywords["buildability"] == "low":
            score -= 0.02
        
        return min(max(score, 0.45), 0.98)
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a response by analyzing documentation text.
        
        Args:
            prompt: The input prompt containing the app name, category, and documentation
            **kwargs: Additional parameters (ignored)
            
        Returns:
            JSON string with research data
        """
        logger.info("MockProvider generating response")
        
        # Extract app name and category from prompt
        app_name = "Unknown"
        app_category = "other"
        documentation_text = ""
        
        for line in prompt.split("\n"):
            line_lower = line.lower().strip()
            if line_lower.startswith("application:"):
                app_name = line.split(":", 1)[1].strip()
            elif line_lower.startswith("category:"):
                app_category = line.split(":", 1)[1].strip()
            elif line_lower.startswith("documentation:"):
                # Get documentation text (everything after "Documentation:")
                doc_start = prompt.find("Documentation:")
                if doc_start != -1:
                    documentation_text = prompt[doc_start + 15:].strip()
        
        # Extract keywords from documentation
        keywords = self._extract_keywords(documentation_text)
        
        # Build API surface description
        api_surface = ", ".join(keywords["api_types"]) if keywords["api_types"] else "REST API"
        if "webhook" in keywords["api_types"]:
            api_surface += " with webhooks"
        if "sdk" in keywords["api_types"]:
            api_surface += " and SDK"
        
        # Build main blocker
        main_blocker = keywords["blockers"][0] if keywords["blockers"] else None
        
        # Calculate confidence
        has_evidence = "https://" in documentation_text
        confidence = self._calculate_confidence(keywords, has_evidence)
        
        # Build realistic response
        mock_response = {
            "name": app_name,
            "category": app_category,
            "description": f"SaaS platform for {app_category.replace('_', ' ')} workflows",
            "auth_methods": keywords["auth_methods"],
            "self_serve": keywords["self_serve"],
            "api_surface": api_surface,
            "mcp_support": keywords["mcp_support"],
            "buildability": keywords["buildability"],
            "main_blocker": main_blocker,
            "evidence_url": None,  # Will be set by workflow
            "confidence_score": round(confidence, 2),
            "notes": None
        }
        
        return json.dumps(mock_response, indent=2)
    
    def health_check(self) -> bool:
        """
        Check if mock provider is healthy.
        
        Returns:
            Always True for mock provider
        """
        logger.info("MockProvider health check: OK")
        return True