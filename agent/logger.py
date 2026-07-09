"""
Logging utility for the AI Research Agent.

Provides a centralized logging setup using Rich for beautiful console output.
Supports multiple log levels: info, warning, error, success.
"""

import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
import logging


# Custom theme for Rich console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "debug": "dim",
})


class Logger:
    """
    Centralized logging utility with Rich console output.
    
    Provides structured logging with color-coded output levels.
    Supports both console and file logging.
    """

    def __init__(
        self,
        name: str = "composio-research-agent",
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
    ):
        """
        Initialize the logger.
        
        Args:
            name: Logger name for identification
            level: Logging level (default: INFO)
            log_file: Optional file path for logging to file
        """
        self.name = name
        self.level = level
        self.log_file = log_file

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Remove existing handlers
        self.logger.handlers.clear()

        # Console handler with Rich
        console = Console(theme=custom_theme, stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        console_handler.setLevel(level)

        # Format for console
        console_format = logging.Formatter(
            "%(message)s",
            datefmt="[%X]",
        )
        console_handler.setFormatter(console_format)

        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if self.log_file:
            self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Setup file handler for logging to file."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(self.level)

        # Format for file (no Rich markup)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)

        self.logger.addHandler(file_handler)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(f"[info]ℹ️  {message}[/info]", **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(f"[warning]⚠️  {message}[/warning]", **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(f"[error]❌ {message}[/error]", **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Log success message."""
        self.logger.info(f"[success]✅ {message}[/success]", **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(f"[debug]🐛 {message}[/debug]", **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(f"[error]🚨 {message}[/error]", **kwargs)

    def get_logger(self) -> logging.Logger:
        """
        Get the underlying logger instance.
        
        Returns:
            Standard Python logger instance
        """
        return self.logger


# Global logger instance
_logger: Optional[Logger] = None


def get_logger(
    name: str = "composio-research-agent",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> Logger:
    """
    Get or create the global logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = Logger(name=name, level=level, log_file=log_file)
    return _logger


def setup_logger(
    name: str = "composio-research-agent",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> Logger:
    """
    Setup and return a new logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Configured Logger instance
    """
    return Logger(name=name, level=level, log_file=log_file)