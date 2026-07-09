"""
OpenRouter LLM Provider for the AI Research Agent.

Implements the BaseLLMProvider interface for OpenRouter API.
"""

import time
from typing import Any, Optional

import requests

from .base import BaseLLMProvider
from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter LLM provider implementation.
    
    Uses the OpenRouter API to generate text responses.
    Supports retry logic and proper error handling.
    """
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key (reads from config if not provided)
            model_name: Model name to use (reads from config if not provided)
            max_retries: Maximum number of retry attempts
        """
        # Get API key from config if not provided
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model_name = model_name or settings.MODEL_NAME
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("No OpenRouter API key configured")
        
        logger.info(f"OpenRouterProvider initialized with model: {self.model_name}")
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text using OpenRouter API.
        
        Args:
            prompt: The input prompt to generate from
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text as string
            
        Raises:
            ValueError: If API key is not configured
            requests.RequestException: If API call fails
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 1000),
        }
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.time()
                
                response = requests.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 429:
                    # Rate limited - wait and retry
                    logger.warning(f"Rate limited (429) on attempt {attempt}/{self.max_retries}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise requests.RequestException(f"Rate limited after {self.max_retries} attempts")
                
                if response.status_code == 401:
                    # Unauthorized - don't retry
                    logger.error("Unauthorized (401) - check API key")
                    raise requests.RequestException("Invalid API key")
                
                if response.status_code >= 500:
                    # Server error - retry
                    logger.warning(f"Server error ({response.status_code}) on attempt {attempt}/{self.max_retries}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    raise requests.RequestException(f"Server error: {response.status_code}")
                
                response.raise_for_status()
                
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                logger.success(
                    f"OpenRouter response: model={self.model_name}, "
                    f"time={response_time:.2f}s, attempt={attempt}"
                )
                
                return content
                
            except requests.Timeout as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt}/{self.max_retries}")
            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Request failed on attempt {attempt}/{self.max_retries}: {e}")
            
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)
        
        raise requests.RequestException(f"Failed after {self.max_retries} attempts: {last_error}")
    
    def health_check(self) -> bool:
        """
        Check if OpenRouter API is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return False
        
        try:
            # Simple health check with a short prompt
            self.generate("Hello", max_tokens=10)
            logger.info("OpenRouter health check: OK")
            return True
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return False