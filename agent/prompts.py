"""
Prompt templates for the AI Research Agent.

This module contains structured prompt templates for LLM interactions.
Prompts are organized by research task and designed for future LLM integration.

NOTE: This is a placeholder module. Prompt engineering will be implemented
when integrating with specific LLM providers (OpenAI, Anthropic, etc.).
"""

from typing import Dict, List, Optional


class PromptTemplates:
    """
    Collection of prompt templates for various research tasks.
    
    Each template is designed to be used with different LLM providers
    and can be customized based on the specific research requirements.
    """

    # ============================================================================
    # Application Research Prompts
    # ============================================================================

    RESEARCH_APP_PROMPT = """
    Analyze the following SaaS application and extract structured information.

    Application: {app_name}
    Website: {website_url}

    Provide the following information in JSON format:
    {{
        "category": "one of: productivity, communication, crm, ecommerce, developer_tools, analytics, marketing, hr, finance, project_management, cloud_infrastructure, database, ai_ml, security, payment, social, media, education, healthcare, other",
        "description": "one-line description (10-500 characters)",
        "auth_methods": ["list of: api_key, oauth2, basic_auth, jwt, bearer_token, oauth1, none, unknown"],
        "self_serve": true/false/null,
        "api_surface": "description of API capabilities",
        "mcp_support": true/false/null,
        "buildability": "high/medium/low/null",
        "main_blocker": "main blocker for AI agent integration or null",
        "confidence_score": 0.0-1.0
    }}

    Base your analysis on:
    - Official documentation
    - API references
    - Developer portals
    - Public information

    Be accurate and conservative. If information is unclear, mark confidence_score lower.
    """

    CATEGORIZE_PROMPT = """
    Categorize the following SaaS application based on its primary function.

    Application: {app_name}
    Description: {description}
    Features: {features}

    Select the most appropriate category from:
    - productivity
    - communication
    - crm
    - ecommerce
    - developer_tools
    - analytics
    - marketing
    - hr
    - finance
    - project_management
    - cloud_infrastructure
    - database
    - ai_ml
    - security
    - payment
    - social
    - media
    - education
    - healthcare
    - other

    Provide the category and a brief justification (max 100 words).
    """

    AUTH_ANALYSIS_PROMPT = """
    Analyze the authentication methods supported by this application.

    Application: {app_name}
    Documentation URLs: {doc_urls}

    Identify all authentication methods from:
    - API Key
    - OAuth 2.0
    - OAuth 1.0
    - JWT
    - Basic Auth
    - Bearer Token
    - None (public API)
    - Unknown

    For each method found, provide:
    - Method name
    - Implementation complexity (high/medium/low)
    - Security level (high/medium/low)
    - Documentation quality (high/medium/low)
    """

    BUILDABILITY_ASSESSMENT_PROMPT = """
    Assess how buildable this application is for AI agents.

    Application: {app_name}
    API Documentation: {api_docs}
    SDKs Available: {sdks}
    API Surface: {api_surface}

    Evaluate based on:
    1. API completeness and documentation quality
    2. Authentication complexity
    3. Rate limits and restrictions
    4. SDK availability and quality
    5. Community support and examples
    6. MCP support (if applicable)

    Provide assessment as: high/medium/low
    Include specific reasons for the rating.
    """

    # ============================================================================
    # Verification Prompts
    # ============================================================================

    VERIFY_RESEARCH_PROMPT = """
    Verify the following research data for accuracy.

    Application: {app_name}
    Research Data: {research_data}
    Evidence URL: {evidence_url}

    Check for:
    1. Accuracy of category assignment
    2. Validity of authentication methods
    3. Correctness of API surface description
    4. Appropriateness of buildability rating
    5. Confidence score justification

    Provide verification result:
    {{
        "status": "verified/needs_review/failed",
        "issues": ["list of issues found or empty"],
        "suggestions": ["list of improvements or empty"],
        "confidence": 0.0-1.0
    }}
    """

    CROSS_REFERENCE_PROMPT = """
    Cross-reference research data with multiple sources.

    Application: {app_name}
    Primary Source: {primary_url}
    Research Data: {research_data}

    Compare findings from:
    - Official documentation
    - API references
    - Developer forums
    - Community discussions

    Identify any discrepancies and provide corrected data.
    """

    # ============================================================================
    # Analysis Prompts
    # ============================================================================

    CATEGORY_ANALYSIS_PROMPT = """
    Analyze the distribution of applications across categories.

    Data: {category_data}

    Provide insights on:
    1. Most common categories
    2. Underrepresented categories
    3. Category trends
    4. Recommendations for research focus
    """

    AUTH_STATISTICS_PROMPT = """
    Analyze authentication method patterns across applications.

    Data: {auth_data}

    Provide statistics on:
    1. Most common auth methods
    2. Auth method trends by category
    3. Security implications
    4. Integration complexity patterns
    """

    BUILDABILITY_ANALYSIS_PROMPT = """
    Analyze buildability patterns across applications.

    Data: {buildability_data}

    Provide insights on:
    1. High buildability applications
    2. Common blockers
    3. Category-specific patterns
    4. Recommendations for AI agent development
    """

    # ============================================================================
    # Helper Methods
    # ============================================================================

    @classmethod
    def get_research_prompt(
        cls,
        app_name: str,
        website_url: str,
    ) -> str:
        """
        Get formatted research prompt for an application.
        
        Args:
            app_name: Name of the application
            website_url: Website URL
            
        Returns:
            Formatted prompt string
        """
        return cls.RESEARCH_APP_PROMPT.format(
            app_name=app_name,
            website_url=website_url,
        )

    @classmethod
    def get_verification_prompt(
        cls,
        app_name: str,
        research_data: Dict,
        evidence_url: Optional[str] = None,
    ) -> str:
        """
        Get formatted verification prompt.
        
        Args:
            app_name: Name of the application
            research_data: Research data to verify
            evidence_url: URL providing evidence
            
        Returns:
            Formatted prompt string
        """
        return cls.VERIFY_RESEARCH_PROMPT.format(
            app_name=app_name,
            research_data=research_data,
            evidence_url=evidence_url or "N/A",
        )

    @classmethod
    def get_buildability_prompt(
        cls,
        app_name: str,
        api_docs: str = "",
        sdks: str = "",
        api_surface: str = "",
    ) -> str:
        """
        Get formatted buildability assessment prompt.
        
        Args:
            app_name: Name of the application
            api_docs: API documentation details
            sdks: Available SDKs
            api_surface: API surface description
            
        Returns:
            Formatted prompt string
        """
        return cls.BUILDABILITY_ASSESSMENT_PROMPT.format(
            app_name=app_name,
            api_docs=api_docs or "Not specified",
            sdks=sdks or "None found",
            api_surface=api_surface or "Not specified",
        )


class PromptBuilder:
    """
    Builder class for constructing complex prompts.
    
    Provides a fluent interface for building prompts with dynamic content.
    """

    def __init__(self, template: str):
        """
        Initialize prompt builder.
        
        Args:
            template: Base prompt template
        """
        self.template = template
        self.context: Dict[str, str] = {}

    def add_context(self, key: str, value: str) -> "PromptBuilder":
        """
        Add context variable to prompt.
        
        Args:
            key: Variable name
            value: Variable value
            
        Returns:
            Self for method chaining
        """
        self.context[key] = value
        return self

    def add_contexts(self, **kwargs: str) -> "PromptBuilder":
        """
        Add multiple context variables.
        
        Args:
            **kwargs: Key-value pairs of context variables
            
        Returns:
            Self for method chaining
        """
        self.context.update(kwargs)
        return self

    def build(self) -> str:
        """
        Build the final prompt with all context.
        
        Returns:
            Formatted prompt string
        """
        try:
            return self.template.format(**self.context)
        except KeyError as e:
            raise ValueError(f"Missing context variable: {e}")

    def reset(self) -> "PromptBuilder":
        """
        Reset context and return builder.
        
        Returns:
            Self for method chaining
        """
        self.context = {}
        return self


# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPTS = {
    "research_assistant": """
    You are an expert SaaS application researcher. Your role is to analyze
    applications and extract structured, accurate information. Be thorough,
    conservative in your assessments, and always provide evidence for claims.
    When uncertain, lower your confidence score rather than guessing.
    """,

    "verifier": """
    You are a quality assurance specialist for research data. Your role is to
    verify the accuracy of research findings, identify discrepancies, and ensure
    data quality. Be critical but fair, and provide constructive feedback.
    """,

    "analyst": """
    You are a data analyst specializing in SaaS applications. Your role is to
    analyze research data, identify patterns, and provide actionable insights.
    Focus on trends, anomalies, and recommendations for AI agent development.
    """,
}


def get_system_prompt(role: str) -> str:
    """
    Get system prompt for a specific role.
    
    Args:
        role: Role name (research_assistant, verifier, analyst)
        
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS["research_assistant"])


# ============================================================================
# Prompt Management
# ============================================================================


class PromptManager:
    """
    Manager class for organizing and accessing prompts.
    
    Provides centralized access to all prompt templates and utilities.
    """

    def __init__(self):
        """Initialize prompt manager."""
        self.templates = PromptTemplates()
        self.system_prompts = SYSTEM_PROMPTS

    def get_template(self, template_name: str) -> str:
        """
        Get a specific prompt template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Prompt template string
            
        Raises:
            AttributeError: If template doesn't exist
        """
        return getattr(self.templates, template_name.upper())

    def list_templates(self) -> List[str]:
        """
        List all available prompt templates.
        
        Returns:
            List of template names
        """
        return [
            attr for attr in dir(self.templates)
            if attr.isupper() and not attr.startswith("_")
        ]

    def build_prompt(
        self,
        template_name: str,
        **context: str,
    ) -> str:
        """
        Build a prompt from a template with context.
        
        Args:
            template_name: Name of the template
            **context: Context variables for formatting
            
        Returns:
            Formatted prompt string
        """
        template = self.get_template(template_name)
        builder = PromptBuilder(template)
        builder.add_contexts(**context)
        return builder.build()