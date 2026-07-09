"""
LLM Client module for the AI Research Agent.

Provides an abstract interface for LLM providers with a pluggable architecture.
Supports multiple providers (OpenAI, Anthropic, Groq, etc.) through a unified interface.

Design Pattern: Strategy Pattern with Dependency Injection
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .config import settings
from .logger import get_logger
from .models import AppResearch

logger = get_logger(__name__)


class LLMResponse:
    """Represents a response from an LLM provider."""

    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        tokens_used: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize LLM response.

        Args:
            content: Response content (usually JSON string)
            provider: Provider name (e.g., 'openai', 'anthropic')
            model: Model identifier
            tokens_used: Optional token usage statistics
            metadata: Optional additional metadata
        """
        self.content = content
        self.provider = provider
        self.model = model
        self.tokens_used = tokens_used or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
        }


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement this interface to ensure
    consistent behavior across different providers.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM provider.
        
        Args:
            api_key: API key for the provider
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default model for this provider.
        
        Returns:
            Default model identifier
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json",
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            response_format: Expected response format ('json' or 'text')
            
        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate connection to the LLM provider.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.provider_name}(model={self.model})"


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def get_default_model(self) -> str:
        """Get default OpenAI model."""
        return "gpt-4-turbo-preview"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json",
    ) -> LLMResponse:
        """
        Generate response using OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Response format ('json' or 'text')
            
        Returns:
            LLMResponse object
        """
        # TODO: Implement OpenAI API call
        # This is a placeholder implementation
        raise NotImplementedError(
            "OpenAI provider not yet implemented. "
            "Install openai package and implement this method."
        )

    def validate_connection(self) -> bool:
        """Validate OpenAI connection."""
        # TODO: Implement connection validation
        return False


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider implementation."""

    def get_default_model(self) -> str:
        """Get default Anthropic model."""
        return "claude-3-opus-20240229"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json",
    ) -> LLMResponse:
        """
        Generate response using Anthropic API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Response format
            
        Returns:
            LLMResponse object
        """
        # TODO: Implement Anthropic API call
        raise NotImplementedError(
            "Anthropic provider not yet implemented. "
            "Install anthropic package and implement this method."
        )

    def validate_connection(self) -> bool:
        """Validate Anthropic connection."""
        # TODO: Implement connection validation
        return False


class GroqProvider(LLMProvider):
    """Groq LLM provider implementation."""

    def get_default_model(self) -> str:
        """Get default Groq model."""
        return "llama2-70b-4096"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json",
    ) -> LLMResponse:
        """
        Generate response using Groq API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Response format
            
        Returns:
            LLMResponse object
        """
        # TODO: Implement Groq API call
        raise NotImplementedError(
            "Groq provider not yet implemented. "
            "Install groq package and implement this method."
        )

    def validate_connection(self) -> bool:
        """Validate Groq connection."""
        # TODO: Implement connection validation
        return False


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for testing and development.
    
    Returns predefined responses without making actual API calls.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize mock provider."""
        super().__init__(api_key, model)
        self.call_count = 0

    def get_default_model(self) -> str:
        """Get default mock model."""
        return "mock-model-v1"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json",
    ) -> LLMResponse:
        """
        Generate mock response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Response format
            
        Returns:
            LLMResponse with mock data
        """
        self.call_count += 1
        
        # Return a mock JSON response
        mock_response = {
            "category": "developer_tools",
            "description": "A software development tool for version control and collaboration",
            "auth_methods": ["api_key", "oauth2"],
            "self_serve": True,
            "api_surface": "REST API with comprehensive endpoints for repositories, issues, and pull requests",
            "mcp_support": False,
            "buildability": "high",
            "main_blocker": "Rate limits on free tier",
            "confidence_score": 0.85
        }
        
        content = json.dumps(mock_response)
        
        logger.warning(
            f"Using mock LLM provider (call #{self.call_count}). "
            "No actual API call made."
        )
        
        return LLMResponse(
            content=content,
            provider="mock",
            model=self.model,
            tokens_used={"prompt": 100, "completion": 50},
            metadata={"mock": True, "call_number": self.call_count},
        )

    def validate_connection(self) -> bool:
        """Mock connection validation always succeeds."""
        return True


class LLMClient:
    """
    Main LLM client with provider management.
    
    Provides a unified interface for interacting with different LLM providers.
    Uses dependency injection for provider configuration.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        """
        Initialize LLM client.
        
        Args:
            provider: LLM provider instance (if None, uses mock provider)
        """
        self.provider = provider or MockLLMProvider()
        logger.info(f"LLM Client initialized with {self.provider}")

    def set_provider(self, provider: LLMProvider) -> None:
        """
        Set the LLM provider.
        
        Args:
            provider: LLM provider instance
        """
        self.provider = provider
        logger.info(f"LLM provider changed to {provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: str = "json",
    ) -> LLMResponse:
        """
        Generate response using the configured provider.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Response format
            
        Returns:
            LLMResponse object
        """
        logger.debug(f"Generating response with {self.provider}")
        return self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    def validate_connection(self) -> bool:
        """
        Validate connection to the LLM provider.
        
        Returns:
            True if connection is valid, False otherwise
        """
        return self.provider.validate_connection()

    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> LLMProvider:
        """
        Factory method to create LLM providers.
        
        Args:
            provider_type: Type of provider ('openai', 'anthropic', 'groq', 'mock')
            **kwargs: Additional arguments for provider initialization
            
        Returns:
            LLMProvider instance
        """
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "groq": GroqProvider,
            "mock": MockLLMProvider,
        }
        
        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available providers: {list(providers.keys())}"
            )
        
        return provider_class(**kwargs)


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client(provider: Optional[LLMProvider] = None) -> LLMClient:
    """
    Get or create the global LLM client instance.
    
    Args:
        provider: Optional LLM provider instance
        
    Returns:
        LLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(provider=provider)
    return _llm_client


def setup_llm_client(provider_type: str = "mock", **kwargs) -> LLMClient:
    """
    Setup and return a new LLM client instance.
    
    Args:
        provider_type: Type of provider ('openai', 'anthropic', 'groq', 'mock')
        **kwargs: Additional arguments for provider initialization
        
    Returns:
        Configured LLMClient instance
    """
    provider = LLMClient.create_provider(provider_type, **kwargs)
    return LLMClient(provider=provider)