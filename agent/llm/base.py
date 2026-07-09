"""
Base LLM Provider interface for the AI Research Agent.

Defines the abstract interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers (OpenRouter, OpenAI, Anthropic, etc.) must
    implement this interface to be compatible with the system.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for authentication
            model_name: Model name to use for generation
        """
        self.api_key = api_key
        self.model_name = model_name
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input prompt to generate from
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text as string
            
        Raises:
            Exception: If generation fails
        """
        ...
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        ...