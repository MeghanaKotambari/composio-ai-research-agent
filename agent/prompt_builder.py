"""
Prompt Builder module for the AI Research Agent.

Generates structured prompts for LLM to extract SaaS application information.
Prompts are designed to return JSON ONLY for easy parsing.

Responsibilities:
- Build research prompts
- Structure LLM requests
- Ensure JSON-only responses
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from .logger import get_logger
from .models import Category, AuthMethod

logger = get_logger(__name__)


class PromptBuilder:
    """
    Builds structured prompts for SaaS application research.
    
    Generates prompts that instruct the LLM to return JSON ONLY
    with specific fields for structured data extraction.
    """

    def __init__(self):
        """Initialize prompt builder."""
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for the LLM.
        
        Returns:
            System prompt string
        """
        return """You are an expert SaaS application researcher. Your task is to analyze 
applications and extract structured information in JSON format ONLY.

CRITICAL RULES:
1. Return ONLY valid JSON, no additional text or explanations
2. Follow the exact schema provided
3. Be accurate and conservative in your assessments
4. If information is unclear, mark confidence_score lower
5. Base your analysis on official documentation, API references, and public information

Your response must be valid JSON that can be parsed directly."""

    def build_research_prompt(
        self,
        app_name: str,
        website_url: str,
        content: str,
    ) -> str:
        """
        Build research prompt for a single application.
        
        Args:
            app_name: Name of the application
            website_url: Website URL
            content: Extracted web content
            
        Returns:
            Formatted prompt string
        """
        # Truncate content to fit within token limits (keep first 3000 chars)
        content_truncated = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""Analyze the following SaaS application and extract structured information.

Application: {app_name}
Website: {website_url}

Web Content:
{content_truncated}

Provide the following information in JSON format ONLY:
{{
    "category": "one of: productivity, communication, crm, ecommerce, developer_tools, analytics, marketing, hr, finance, project_management, cloud_infrastructure, database, ai_ml, security, payment, social, media, education, healthcare, other",
    "description": "one-line description (10-500 characters)",
    "auth_methods": ["list of: api_key, oauth2, basic_auth, jwt, bearer_token, oauth1, none, unknown"],
    "self_serve": true or false,
    "api_surface": "description of API capabilities and endpoints (max 500 chars)",
    "mcp_support": true or false or null,
    "buildability": "high, medium, or low",
    "main_blocker": "main blocker for AI agent integration or null",
    "evidence_url": "URL providing evidence or null"
}}

Return ONLY the JSON object, no other text."""

        return prompt

    def build_refinement_prompt(
        self,
        app_name: str,
        previous_result: Dict[str, Any],
        additional_content: str,
    ) -> str:
        """
        Build refinement prompt to improve previous results.
        
        Args:
            app_name: Name of the application
            previous_result: Previous research result
            additional_content: Additional web content
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Refine and improve the following research data for {app_name} using additional information.

Previous Data:
{previous_result}

Additional Information:
{additional_content[:2000]}

Review and update the JSON with any corrections or improvements. Return ONLY the updated JSON object."""

        return prompt

    def build_verification_prompt(
        self,
        app_name: str,
        research_data: Dict[str, Any],
        evidence_url: str,
    ) -> str:
        """
        Build verification prompt to validate research data.
        
        Args:
            app_name: Name of the application
            research_data: Research data to verify
            evidence_url: URL providing evidence
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Verify the following research data for accuracy.

Application: {app_name}
Evidence URL: {evidence_url}

Research Data:
{research_data}

Check for:
1. Accuracy of category assignment
2. Validity of authentication methods
3. Correctness of API surface description
4. Appropriateness of buildability rating
5. Confidence score justification

Provide verification result in JSON format ONLY:
{{
    "status": "verified, needs_review, or failed",
    "issues": ["list of issues found or empty"],
    "suggestions": ["list of improvements or empty"],
    "confidence": 0.0-1.0
}}

Return ONLY the JSON object."""

        return prompt

    def get_messages(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Format prompts for LLM API call.
        
        Args:
            user_prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        return messages

    def build_llm_request(
        self,
        app_name: str,
        website_url: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Build complete LLM request object.
        
        Args:
            app_name: Name of the application
            website_url: Website URL
            content: Extracted web content
            
        Returns:
            Dictionary containing complete LLM request
        """
        user_prompt = self.build_research_prompt(app_name, website_url, content)
        messages = self.get_messages(user_prompt)
        
        return {
            "messages": messages,
            "temperature": 0.3,  # Low temperature for consistent JSON
            "max_tokens": 1000,
            "response_format": "json",
        }


class PromptManager:
    """
    Manages prompt templates and building.
    
    Provides centralized access to all prompt-related functionality.
    """

    def __init__(self):
        """Initialize prompt manager."""
        self.builder = PromptBuilder()

    def get_research_prompt(self, app_name: str, website_url: str, content: str) -> str:
        """
        Get research prompt for an application.
        
        Args:
            app_name: Application name
            website_url: Website URL
            content: Web content
            
        Returns:
            Formatted prompt string
        """
        return self.builder.build_research_prompt(app_name, website_url, content)

    def get_verification_prompt(
        self,
        app_name: str,
        research_data: Dict[str, Any],
        evidence_url: str,
    ) -> str:
        """
        Get verification prompt.
        
        Args:
            app_name: Application name
            research_data: Research data
            evidence_url: Evidence URL
            
        Returns:
            Formatted prompt string
        """
        return self.builder.build_verification_prompt(
            app_name, research_data, evidence_url
        )

    def get_llm_request(
        self,
        app_name: str,
        website_url: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Get complete LLM request.
        
        Args:
            app_name: Application name
            website_url: Website URL
            content: Web content
            
        Returns:
            LLM request dictionary
        """
        return self.builder.build_llm_request(app_name, website_url, content)