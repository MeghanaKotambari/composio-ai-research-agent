"""
Mock LLM Provider for the AI Research Agent.

Returns predefined JSON responses for local development and testing.
"""

import json
from typing import Any, Optional

from .base import BaseLLMProvider
from ..logger import get_logger

logger = get_logger(__name__)


class MockProvider(BaseLLMProvider):
    """
    Mock LLM provider for testing and development.
    
    Returns predefined JSON responses without making actual API calls.
    Useful for local development, testing, and CI/CD pipelines.
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
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a mock response.
        
        Args:
            prompt: The input prompt (ignored)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Predefined JSON string with mock research data
        """
        logger.info("MockProvider generating response")
        
        # Return a predefined JSON response for testing
        mock_response = {
            "name": "MockApp",
            "category": "other",
            "description": "A mock application for testing purposes",
            "auth_methods": ["api_key"],
            "self_serve": True,
            "api_surface": "REST API with JSON endpoints",
            "mcp_support": False,
            "buildability": "high",
            "main_blocker": None,
            "evidence_url": "https://example.com",
            "confidence_score": 0.85,
            "notes": "This is mock data for testing"
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