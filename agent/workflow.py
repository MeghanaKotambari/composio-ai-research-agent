"""
Agent Workflow Engine for the AI Research Agent.

Orchestrates the research pipeline by coordinating all components.
Does NOT know about specific implementations - uses dependency injection.
"""

import time
from typing import Any, Dict, Optional

from .logger import get_logger
from .models import AppResearch
from .web_research import WebResearchService
from .llm.base import BaseLLMProvider
from .prompt_builder import PromptBuilder
from .parser import ResponseParser, DataEnricher
from .confidence import ConfidenceEstimator
from .verifier import VerificationEngine

logger = get_logger(__name__)


class ResearchWorkflow:
    """
    Workflow engine that coordinates the research pipeline.
    
    Orchestrates each step of the research process without knowing
    the specific implementations of web research or LLM providers.
    """
    
    def __init__(
        self,
        web_research: WebResearchService,
        llm_provider: BaseLLMProvider,
    ) -> None:
        """
        Initialize the workflow with dependency injection.
        
        Args:
            web_research: WebResearchService instance for fetching documentation
            llm_provider: BaseLLMProvider instance for LLM calls
        """
        self.web_research = web_research
        self.llm_provider = llm_provider
        self.prompt_builder = PromptBuilder()
        self.parser = ResponseParser()
        self.confidence_estimator = ConfidenceEstimator()
        self.verifier = VerificationEngine()
        
        logger.info("ResearchWorkflow initialized")
    
    def locate_source(self, app: Dict[str, Any]) -> str:
        """
        Locate the documentation source URL for an application.
        
        Args:
            app: App dictionary with name and website
            
        Returns:
            Documentation URL
        """
        app_name = app.get("name", "Unknown")
        website_url = app.get("website", "")
        
        logger.info(f"Locating source for {app_name}")
        
        # Use website URL as fallback (documentation finder can be added later)
        return website_url
    
    def fetch_documentation(self, url: str) -> Dict[str, Any]:
        """
        Fetch documentation from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with url, title, text, and status
        """
        logger.info(f"Fetching documentation from {url}")
        
        result = self.web_research.research_source(url)
        
        logger.success(f"Fetched documentation: {len(result.get('text', ''))} chars")
        return result
    
    def prepare_context(self, text: str) -> str:
        """
        Prepare context text for the LLM.
        
        Args:
            text: Raw text content
            
        Returns:
            Prepared context string
        """
        logger.debug("Preparing context")
        
        # Context is already cleaned by web_research, just return it
        return text
    
    def build_prompt(self, app: Dict[str, Any], context: str) -> str:
        """
        Build the LLM prompt for research.
        
        Args:
            app: App dictionary with name and website
            context: Prepared context text
            
        Returns:
            Formatted prompt string
        """
        app_name = app.get("name", "Unknown")
        website_url = app.get("website", "")
        
        logger.info(f"Building prompt for {app_name}")
        
        prompt = self.prompt_builder.build_research_prompt(
            app_name=app_name,
            website_url=website_url,
            content=context,
        )
        
        return prompt
    
    def call_llm(self, prompt: str) -> str:
        """
        Call the LLM provider with a prompt.
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            LLM response string
        """
        logger.info("Calling LLM")
        
        start_time = time.time()
        response = self.llm_provider.generate(prompt)
        elapsed = time.time() - start_time
        
        logger.success(f"LLM response received in {elapsed:.2f}s")
        return response
    
    def parse_response(self, llm_response: str, app_name: str) -> Optional[AppResearch]:
        """
        Parse LLM response into AppResearch object.
        
        Args:
            llm_response: Raw LLM response
            app_name: Application name
            
        Returns:
            AppResearch object if successful, None otherwise
        """
        logger.info("Parsing LLM response")
        
        result = self.parser.parse(llm_response, app_name=app_name)
        
        if result.success and result.data:
            logger.success("Response parsed successfully")
            return result.data
        
        logger.error(f"Failed to parse response: {result.error}")
        return None
    
    def estimate_confidence(self, app_research: AppResearch) -> float:
        """
        Estimate confidence score for research result.
        
        Args:
            app_research: AppResearch object to score
            
        Returns:
            Confidence score (0.0-1.0)
        """
        logger.info("Estimating confidence")
        
        confidence = self.confidence_estimator.calculate(app_research)
        
        logger.info(f"Confidence score: {confidence:.0%}")
        return confidence
    
    def verify_result(self, app: Dict[str, Any], app_research: AppResearch) -> Dict[str, Any]:
        """
        Verify research result against documentation.
        
        Args:
            app: App dictionary
            app_research: AppResearch object to verify
            
        Returns:
            Verification result dictionary
        """
        logger.info(f"Verifying {app_research.name}")
        
        # Fetch documentation for verification
        doc_result = self.fetch_documentation(app.get("website", ""))
        
        verification = self.verifier.verify(
            app_research,
            doc_result.get("text", ""),
        )
        
        return verification
    
    def save_result(self, app_research: AppResearch) -> None:
        """
        Save the research result.
        
        Args:
            app_research: AppResearch object to save
        """
        logger.info(f"Saving result for {app_research.name}")
        
        # This is a placeholder - actual saving is done by ResearchAgent
        logger.success(f"Result ready for {app_research.name}")
    
    def execute(self, app: Dict[str, Any]) -> Optional[AppResearch]:
        """
        Execute the complete research workflow for an application.
        
        Includes verification loop:
        1. Research
        2. Verify
        3. Low score? -> Refetch + Rerun
        4. Manual review flag
        
        Args:
            app: App dictionary with name and website
            
        Returns:
            AppResearch object if successful, None otherwise
        """
        app_name = app.get("name", "Unknown")
        
        logger.info(f"Starting workflow for {app_name}")
        start_time = time.time()
        
        # Step 1: Locate source
        url = self.locate_source(app)
        
        # Step 2: Fetch documentation
        doc_result = self.fetch_documentation(url)
        
        if doc_result.get("status") != 200:
            logger.error(f"Failed to fetch documentation: {doc_result.get('text', 'Unknown error')}")
            return None
        
        # Step 3: Prepare context
        context = self.prepare_context(doc_result.get("text", ""))
        
        # Step 4: Build prompt
        prompt = self.build_prompt(app, context)
        
        # Step 5: Call LLM
        llm_response = self.call_llm(prompt)
        
        # Step 6: Parse response
        app_research = self.parse_response(llm_response, app_name)
        
        if not app_research:
            return None
        
        # Step 7: Estimate confidence
        confidence = self.estimate_confidence(app_research)
        app_research.confidence_score = confidence
        
        # Step 8: Verify result
        verification = self.verify_result(app, app_research)
        
        # Step 9: Verification loop - retry if low score
        if verification.get("verification_score", 0) < 40:
            logger.warning(f"Low verification score ({verification.get('verification_score')}), retrying with improved context")
            app_research = self._retry_with_verification(app, context, app_research)
            
            if app_research:
                verification = self.verify_result(app, app_research)
        
        # Step 10: Set manual review flag
        if verification.get("manual_review_required", False):
            app_research.verification_status = "manual_review"
            logger.warning(f"Manual review required for {app_name}")
        
        # Step 11: Retry if confidence is low
        if app_research.confidence_score < 0.7:
            logger.warning(f"Low confidence ({app_research.confidence_score:.0%}), retrying...")
            app_research = self._retry_with_refinement(app, context, app_research)
        
        # Step 12: Enrich data
        app_research = DataEnricher.enrich(app_research)
        
        # Step 13: Save result
        self.save_result(app_research)
        
        elapsed = time.time() - start_time
        logger.success(f"Workflow complete for {app_name} in {elapsed:.2f}s")
        
        return app_research
    
    def _retry_with_verification(
        self,
        app: Dict[str, Any],
        context: str,
        previous_result: AppResearch,
    ) -> Optional[AppResearch]:
        """
        Retry research with improved context for better verification.
        
        Args:
            app: App dictionary
            context: Context text
            previous_result: Previous result
            
        Returns:
            Improved AppResearch object if successful, original otherwise
        """
        app_name = app.get("name", "Unknown")
        
        logger.info(f"Retrying with improved context for {app_name}")
        
        # Build improvement prompt
        improvement_prompt = f"""Improve the research for {app_name} based on verification feedback.
        
Previous result had low verification score. Focus on finding:
- Authentication methods in documentation
- API surface details
- Self-serve availability
- MCP support
- Evidence URLs
        
Documentation:
{context[:2000]}
        
Return improved JSON:"""
        
        # Call LLM with improvement
        llm_response = self.call_llm(improvement_prompt)
        
        # Parse improved response
        improved = self.parse_response(llm_response, app_name)
        
        if improved:
            return improved
        
        return previous_result
    
    def _retry_with_refinement(
        self,
        app: Dict[str, Any],
        context: str,
        previous_result: AppResearch,
    ) -> Optional[AppResearch]:
        """
        Retry research with refinement prompt.
        
        Args:
            app: App dictionary
            context: Context text
            previous_result: Previous low-confidence result
            
        Returns:
            Refined AppResearch object if successful, original otherwise
        """
        app_name = app.get("name", "Unknown")
        
        logger.info(f"Refining research for {app_name}")
        
        # Build refinement prompt
        refinement_prompt = self.prompt_builder.build_refinement_prompt(
            app_name=app_name,
            previous_result=previous_result.dict(),
            additional_content=context,
        )
        
        # Call LLM with refinement
        llm_response = self.call_llm(refinement_prompt)
        
        # Parse refined response
        refined = self.parse_response(llm_response, app_name)
        
        if refined:
            return refined
        
        return previous_result