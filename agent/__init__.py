"""
Composio AI Research Agent

A modular, AI-powered research system for analyzing SaaS applications.
"""

__version__ = "0.2.0"
__author__ = "Composio AI Product Ops"

from .models import AppResearch, ResearchBatch
from .config import Settings
from .research_agent import ResearchAgent, ResearchService
from .llm_client import LLMClient, LLMProvider, MockLLMProvider
from .web_research import WebResearcher, DocumentationFinder, WebResearchService
from .prompt_builder import PromptBuilder, PromptManager
from .parser import ResponseParser, DataEnricher
from .confidence import ConfidenceEstimator
from .storage import ResearchStorage

__all__ = [
    "AppResearch",
    "ResearchBatch",
    "Settings",
    "ResearchAgent",
    "ResearchService",
    "LLMClient",
    "LLMProvider",
    "MockLLMProvider",
    "WebResearcher",
    "DocumentationFinder",
    "WebResearchService",
    "PromptBuilder",
    "PromptManager",
    "ResponseParser",
    "DataEnricher",
    "ConfidenceEstimator",
    "ResearchStorage",
]
