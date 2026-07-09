"""
LLM Factory for the AI Research Agent.

Creates and manages LLM provider instances based on configuration.
"""

from typing import Optional

from .base import BaseLLMProvider
from .mock import MockProvider
from .openrouter import OpenRouterProvider
from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """
    Factory for creating LLM provider instances.
    
    Supports multiple providers and can be extended to add new ones.
    Reads configuration from environment variables.
    """
    
    # Supported provider types
    PROVIDER_MOCK = "mock"
    PROVIDER_OPENROUTER = "openrouter"
    PROVIDER_OPENAI = "openai"
    PROVIDER_ANTHROPIC = "anthropic"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_GROQ = "groq"
    
    @classmethod
    def create(
        cls,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ('mock', 'openrouter', 'openai', 'anthropic', 'gemini', 'groq')
            api_key: API key (reads from config if not provided)
            model_name: Model name (reads from config if not provided)
            
        Returns:
            BaseLLMProvider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_type = provider_type or settings.LLM_PROVIDER or cls.PROVIDER_MOCK
        
        logger.info(f"Creating LLM provider: {provider_type}")
        
        if provider_type == cls.PROVIDER_MOCK:
            return MockProvider(api_key=api_key, model_name=model_name)
        
        elif provider_type == cls.PROVIDER_OPENROUTER:
            return OpenRouterProvider(
                api_key=api_key,
                model_name=model_name,
            )
        
        elif provider_type == cls.PROVIDER_OPENAI:
            # Placeholder for future implementation
            logger.warning(f"Provider '{provider_type}' not yet implemented, using mock")
            return MockProvider(api_key=api_key, model_name=model_name)
        
        elif provider_type == cls.PROVIDER_ANTHROPIC:
            # Placeholder for future implementation
            logger.warning(f"Provider '{provider_type}' not yet implemented, using mock")
            return MockProvider(api_key=api_key, model_name=model_name)
        
        elif provider_type == cls.PROVIDER_GEMINI:
            # Placeholder for future implementation
            logger.warning(f"Provider '{provider_type}' not yet implemented, using mock")
            return MockProvider(api_key=api_key, model_name=model_name)
        
        elif provider_type == cls.PROVIDER_GROQ:
            # Placeholder for future implementation
            logger.warning(f"Provider '{provider_type}' not yet implemented, using mock")
            return MockProvider(api_key=api_key, model_name=model_name)
        
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """
        Get list of available provider types.
        
        Returns:
            List of supported provider type strings
        """
        return [
            cls.PROVIDER_MOCK,
            cls.PROVIDER_OPENROUTER,
            cls.PROVIDER_OPENAI,
            cls.PROVIDER_ANTHROPIC,
            cls.PROVIDER_GEMINI,
            cls.PROVIDER_GROQ,
        ]