"""
Prompt Builder module for the AI Research Agent.

Generates optimized prompts for extracting structured information from SaaS documentation.
Designed to maximize factual accuracy and minimize hallucinations.
"""

from typing import Dict, List, Optional, Any

from .logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """
    Builds optimized prompts for SaaS application research.
    
    Generates prompts that maximize factual accuracy and minimize hallucinations
    by explicitly instructing the model to use only provided documentation.
    """
    
    # Maximum documentation length to include in prompt
    MAX_DOC_LENGTH = 3000
    
    def __init__(self) -> None:
        """Initialize prompt builder."""
        pass
    
    def build_system_prompt(self) -> str:
        """
        Build the system prompt for the LLM.
        
        Instructs the AI to behave as an expert SaaS API Research Analyst
        with strict rules to prevent hallucinations.
        
        Returns:
            System prompt string
        """
        return """You are an expert SaaS API Research Analyst. Your task is to extract 
structured information from official documentation about SaaS applications.

CRITICAL RULES:
1. Use ONLY the provided documentation. Do not use any external knowledge.
2. Never invent or guess information. If a field cannot be determined, return "Unknown".
3. If information is not explicitly present in the documentation, return "Unknown".
4. Do NOT infer missing values or make assumptions.
5. Prefer official documentation over assumptions.
6. Output VALID JSON only.
7. No markdown formatting.
8. No comments.
9. No explanations.
10. No extra text before or after the JSON.

JSON FORMAT RULES:
- Arrays must always be arrays, even if empty: []
- Strings must always be strings, use "Unknown" for missing: "Unknown"
- Booleans must be true or false, never null: true
- Return only the JSON object, nothing else."""
    
    def build_user_prompt(
        self,
        app_name: str,
        documentation_text: str,
    ) -> str:
        """
        Build the user prompt for extracting SaaS information.
        
        Args:
            app_name: Name of the application to research
            documentation_text: Extracted documentation text
            
        Returns:
            User prompt string
        """
        # Truncate documentation to fit within token limits
        doc_truncated = self._truncate_documentation(documentation_text)
        
        return f"""Extract structured information about the SaaS application "{app_name}" 
from the following documentation.

Documentation:
{doc_truncated}

Extract ONLY the following fields in JSON format:
{{
    "name": "Application name (use '{app_name}' if not found)",
    "category": "one of: productivity, communication, crm, ecommerce, developer_tools, analytics, marketing, hr, finance, project_management, cloud_infrastructure, database, ai_ml, security, payment, social, media, education, healthcare, other",
    "description": "one-line description (10-500 characters)",
    "auth_methods": ["list of: api_key, oauth2, basic_auth, jwt, bearer_token, oauth1, none, unknown"],
    "self_serve": true or false,
    "api_surface": "description of API capabilities and endpoints (max 500 chars)",
    "mcp_support": true or false or null,
    "buildability": "high, medium, or low",
    "main_blocker": "main blocker for AI agent integration or null",
    "evidence_url": "URL providing evidence or null",
    "notes": "additional research notes or null"
}}

Return ONLY the JSON object, no other text."""
    
    def build_messages(
        self,
        app_name: str,
        documentation_text: str,
    ) -> List[Dict[str, str]]:
        """
        Build complete messages for LLM API call.
        
        Args:
            app_name: Name of the application
            documentation_text: Documentation text
            
        Returns:
            List of message dictionaries with system and user prompts
        """
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(app_name, documentation_text)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    
    def _truncate_documentation(self, text: str) -> str:
        """
        Truncate documentation to fit within token limits.
        
        Preserves the beginning and important headings.
        
        Args:
            text: Full documentation text
            
        Returns:
            Truncated text
        """
        if len(text) <= self.MAX_DOC_LENGTH:
            return text
        
        # Keep the first part (usually contains most important info)
        truncated = text[:self.MAX_DOC_LENGTH]
        
        # Try to end at a sentence boundary
        last_period = truncated.rfind(".")
        if last_period > self.MAX_DOC_LENGTH * 0.8:
            truncated = truncated[:last_period + 1]
        
        logger.debug(f"Documentation truncated from {len(text)} to {len(truncated)} chars")
        return truncated
    
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
        # Truncate content to fit within token limits
        content_truncated = self._truncate_documentation(content)
        
        return f"""Analyze the following SaaS application and extract structured information.

Application: {app_name}
Website: {website_url}

Documentation:
{content_truncated}

Extract ONLY the following fields in JSON format:
{{
    "name": "Application name",
    "category": "one of: productivity, communication, crm, ecommerce, developer_tools, analytics, marketing, hr, finance, project_management, cloud_infrastructure, database, ai_ml, security, payment, social, media, education, healthcare, other",
    "description": "one-line description (10-500 characters)",
    "auth_methods": ["list of: api_key, oauth2, basic_auth, jwt, bearer_token, oauth1, none, unknown"],
    "self_serve": true or false,
    "api_surface": "description of API capabilities and endpoints (max 500 chars)",
    "mcp_support": true or false or null,
    "buildability": "high, medium, or low",
    "main_blocker": "main blocker for AI agent integration or null",
    "evidence_url": "URL providing evidence or null",
    "notes": "additional research notes or null"
}}

Return ONLY the JSON object, no other text."""
    
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
        additional_truncated = self._truncate_documentation(additional_content)
        
        return f"""Refine and improve the following research data for {app_name} 
using additional documentation.

Previous Data:
{previous_result}

Additional Documentation:
{additional_truncated}

Review and update the JSON with corrections. If information is still not 
found in the documentation, keep "Unknown". Return ONLY the updated JSON object."""
    
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
        return f"""Verify the following research data for {app_name} against the evidence.

Evidence URL: {evidence_url}

Research Data:
{research_data}

Check for accuracy. If any field is incorrect, fix it. If information 
is not in the evidence, return "Unknown".

Return ONLY the corrected JSON object."""
    
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
                "content": self.build_system_prompt()
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
            "temperature": 0.3,
            "max_tokens": 1000,
        }


class PromptManager:
    """
    Manages prompt templates and building.
    
    Provides centralized access to all prompt-related functionality.
    """
    
    def __init__(self) -> None:
        """Initialize prompt manager."""
        self.builder = PromptBuilder()
    
    def get_research_prompt(
        self,
        app_name: str,
        website_url: str,
        content: str,
    ) -> str:
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