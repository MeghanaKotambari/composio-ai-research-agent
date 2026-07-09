"""
Configuration management for the AI Research Agent.

Uses python-dotenv to load environment variables.
Prepares configuration for future API integrations without requiring specific providers.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """
    Application settings loaded from environment variables.
    
    This class provides a centralized configuration management system
    that can be extended with additional API keys and settings as needed.
    """

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize settings from environment variables.
        
        Args:
            env_file: Optional path to .env file. Defaults to .env in project root.
        """
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from project root
            project_root = Path(__file__).parent.parent
            env_path = project_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)

        # Application settings
        self.APP_NAME: str = os.getenv("APP_NAME", "Composio AI Research Agent")
        self.APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

        # Output directories
        self.OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
        self.RAW_OUTPUT_DIR: Path = self.OUTPUT_DIR / "raw"
        self.VERIFIED_OUTPUT_DIR: Path = self.OUTPUT_DIR / "verified"
        self.REPORTS_DIR: Path = self.OUTPUT_DIR / "reports"
        self.CHARTS_DIR: Path = self.OUTPUT_DIR / "charts"

        # Research settings
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
        self.REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

        # LLM Provider settings
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")

        # Future API keys (placeholders for extensibility)
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
        self.SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")
        self.OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
        self.PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

        # Ensure output directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create output directories if they don't exist."""
        for directory in [
            self.RAW_OUTPUT_DIR,
            self.VERIFIED_OUTPUT_DIR,
            self.REPORTS_DIR,
            self.CHARTS_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Retrieve API key for a specific provider.
        
        Args:
            provider: Name of the API provider (e.g., 'openai', 'anthropic')
            
        Returns:
            API key if configured, None otherwise
        """
        key_mapping = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "google": self.GOOGLE_API_KEY,
            "serper": self.SERPER_API_KEY,
            "openrouter": self.OPENROUTER_API_KEY,
        }
        return key_mapping.get(provider.lower())

    def __repr__(self) -> str:
        """String representation of settings (hiding sensitive keys)."""
        return (
            f"Settings(APP_NAME={self.APP_NAME}, "
            f"DEBUG={self.DEBUG}, "
            f"OUTPUT_DIR={self.OUTPUT_DIR})"
        )


# Global settings instance
settings = Settings()