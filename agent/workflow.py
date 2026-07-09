"""
Agent Workflow Engine for the AI Research Agent.

Orchestrates the research pipeline by coordinating all components.
Uses dependency injection and documentation cache.
"""

import time
import re
from typing import Any, Dict, Optional, List
from urllib.parse import urljoin, urlparse

from .logger import get_logger
from .models import AppResearch
from .web_research import WebResearchService
from .llm.base import BaseLLMProvider
from .prompt_builder import PromptBuilder
from .parser import ResponseParser
from .confidence import ConfidenceEstimator
from .verifier import VerificationEngine
from .cache import DocumentationCache

logger = get_logger(__name__)

# Priority-ordered URL path patterns for discovering developer documentation
DOCS_PATTERNS = [
    "/docs",
    "/api",
    "/documentation",
    "/developers",
    "/developer",
    "/api-docs",
    "/api/docs",
    "/reference",
    "/openapi",
    "/rest",
    "/graphql",
    "/dev",
    "/portal",
]

# Domain-level documentation subdomain patterns (priority order)
DOCS_SUBDOMAINS = [
    "developer.",
    "developers.",
    "docs.",
    "api.",
    "dev.",
]

# Keywords to search for in homepage HTML when standard patterns fail
DOCS_LINK_KEYWORDS = [
    "developer", "developers", "docs", "documentation",
    "api", "api reference", "api docs", "reference",
    "openapi", "rest api", "graphql", "dev portal",
]


class DocumentationDiscovery:
    """
    Discovers official developer documentation URLs for SaaS applications.

    Priority order:
    1. developer.domain.com (top priority)
    2. developers.domain.com
    3. docs.domain.com
    4. api.domain.com
    5. dev.domain.com
    6. domain.com/developer
    7. domain.com/developers
    8. domain.com/docs
    9. domain.com/api
    10. Official docs links found in homepage HTML
    11. Original website URL (fallback)
    """

    def __init__(self, web_research: WebResearchService, cache: DocumentationCache) -> None:
        """
        Initialize documentation discovery.

        Args:
            web_research: WebResearchService for fetching pages
            cache: DocumentationCache for caching results
        """
        self.web_research = web_research
        self.cache = cache

    def discover(self, app_name: str, website_url: str) -> str:
        """
        Discover the best documentation URL for an application.

        Tries subdomain patterns first, then path patterns.
        If those fail, scans the homepage for documentation links.
        Falls back to the original website URL.

        Args:
            app_name: Application name
            website_url: Main website URL

        Returns:
            Best documentation URL found
        """
        logger.info(f"Discovering documentation for {app_name} from {website_url}")

        base = self._get_base_url(website_url)

        # Phase 1: Try common documentation subdomains (priority order)
        doc_subdomain = self._try_subdomains(base)
        if doc_subdomain:
            logger.success(f"Found docs subdomain for {app_name}: {doc_subdomain}")
            return doc_subdomain

        # Phase 2: Try common documentation URL paths
        doc_path = self._try_paths(base)
        if doc_path:
            logger.success(f"Found docs path for {app_name}: {doc_path}")
            return doc_path

        # Phase 3: Scan homepage HTML for documentation links
        homepage_doc = self._scan_homepage_for_docs(website_url)
        if homepage_doc:
            logger.success(f"Found docs link in homepage for {app_name}: {homepage_doc}")
            return homepage_doc

        # Phase 4: Use the original website URL as fallback
        logger.warning(f"No documentation found for {app_name}, using website URL")
        return website_url

    def _get_base_url(self, url: str) -> str:
        """Extract base URL (scheme + netloc) from a URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _try_subdomains(self, base_url: str) -> Optional[str]:
        """
        Try common documentation subdomains in priority order.

        Args:
            base_url: Base URL like https://example.com

        Returns:
            Working documentation URL if found, None otherwise
        """
        parsed = urlparse(base_url)
        domain = parsed.netloc

        for prefix in DOCS_SUBDOMAINS:
            docs_url = f"{parsed.scheme}://{prefix}{domain}"
            if self._url_exists(docs_url):
                return docs_url

        return None

    def _try_paths(self, base_url: str) -> Optional[str]:
        """
        Try common documentation URL paths in priority order.

        Args:
            base_url: Base URL like https://example.com

        Returns:
            Working documentation URL if found, None otherwise
        """
        for pattern in DOCS_PATTERNS:
            docs_url = urljoin(base_url.rstrip("/") + "/", pattern.lstrip("/"))
            if self._url_exists(docs_url):
                return docs_url

        return None

    def _scan_homepage_for_docs(self, website_url: str) -> Optional[str]:
        """
        Scan the homepage HTML for links that point to documentation.

        Searches for links containing keywords like 'developer', 'docs', 'api'.

        Args:
            website_url: The homepage URL to scan

        Returns:
            Documentation URL if found, None otherwise
        """
        try:
            html = self.web_research.fetch_page(website_url)
        except Exception:
            return None

        # Parse HTML and find all links
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        base = self._get_base_url(website_url)

        doc_links: List[str] = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            text = link.get_text(strip=True).lower()

            # Convert relative URLs to absolute
            if href.startswith("/"):
                href = urljoin(base, href)
            elif href.startswith("#"):
                continue
            elif not href.startswith("http"):
                continue

            href_lower = href.lower()

            # Check if link text or URL contains documentation keywords
            for keyword in DOCS_LINK_KEYWORDS:
                if keyword in text or keyword in href_lower:
                    doc_links.append(href)
                    break

        # Check each found link to see if it's a valid documentation page
        for link in doc_links:
            if self._url_exists(link):
                return link

        return None

    def _url_exists(self, url: str) -> bool:
        """
        Check if a URL returns a valid response.

        Quick check with short timeout.
        Uses cache to avoid redundant checks.

        Args:
            url: URL to check

        Returns:
            True if URL returns HTTP 200 with content, False otherwise
        """
        cached = self.cache.get(url)
        if cached:
            return cached.get("status") == 200 and len(cached.get("text", "")) > 500

        try:
            import requests
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                result = self.web_research.research_source(url)
                self.cache.set(url, result)
                return len(result.get("text", "")) > 500
            return False
        except Exception:
            self.cache.set(url, {"url": url, "title": "", "text": "", "status": 0})
            return False


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
        self.cache = DocumentationCache()
        self.doc_discovery = DocumentationDiscovery(web_research, self.cache)
        self.prompt_builder = PromptBuilder()
        self.parser = ResponseParser()
        self.confidence_estimator = ConfidenceEstimator()
        self.verifier = VerificationEngine()

        logger.info("ResearchWorkflow initialized")

    def locate_source(self, app: Dict[str, Any]) -> str:
        """
        Locate the official documentation URL for an application.

        Uses DocumentationDiscovery before falling back to website URL.

        Args:
            app: App dictionary with name and website

        Returns:
            Documentation URL
        """
        app_name = app.get("name", "Unknown")
        website_url = app.get("website", "")

        logger.info(f"Locating documentation for {app_name}")

        docs_url = self.doc_discovery.discover(app_name, website_url)

        logger.info(f"Documentation URL for {app_name}: {docs_url}")
        return docs_url

    def fetch_documentation(self, url: str) -> Dict[str, Any]:
        """
        Fetch documentation from a URL, using cache.

        Args:
            url: URL to fetch

        Returns:
            Dictionary with url, title, text, and status
        """
        logger.info(f"Fetching documentation from {url}")

        cached = self.cache.get(url)
        if cached:
            logger.info(f"Using cached documentation for {url}")
            return cached

        result = self.web_research.research_source(url)
        self.cache.set(url, result)

        logger.success(f"Fetched documentation: {len(result.get('text', ''))} chars")
        return result

    def prepare_context(self, text: str) -> str:
        """Prepare context text for the LLM."""
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

        return self.prompt_builder.build_research_prompt(
            app_name=app_name,
            website_url=website_url,
            content=context,
        )

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

        Preserves the original app name in the parsed result.

        Args:
            llm_response: Raw LLM response
            app_name: Application name from apps.json

        Returns:
            AppResearch object if successful, None otherwise
        """
        logger.info("Parsing LLM response")

        result = self.parser.parse(llm_response, app_name=app_name)

        if result.success and result.data:
            # CRITICAL: Ensure the app name is never "Unknown" or null
            # The parser already injects the original name, but double-check
            if not result.data.name or result.data.name == "Unknown":
                result.data.name = app_name
            logger.success("Response parsed successfully")
            return result.data

        logger.error(f"Failed to parse response: {result.error}")
        return None

    def estimate_confidence(self, app_research: AppResearch) -> float:
        """
        Estimate confidence score for research result.

        Confidence depends ONLY on:
        - Evidence quality (has evidence_url, is real docs URL)
        - Required fields completeness
        - Verification score
        - Documentation completeness

        Retry count does NOT increase confidence.

        Args:
            app_research: AppResearch object to score

        Returns:
            Confidence score (0.0-1.0)
        """
        logger.info("Estimating confidence")

        confidence = self.confidence_estimator.calculate(app_research)

        logger.info(f"Confidence score: {confidence:.0%}")
        return confidence

    def verify_result(
        self,
        app: Dict[str, Any],
        app_research: AppResearch,
        docs_url: str,
    ) -> Dict[str, Any]:
        """
        Verify research result using cached documentation.

        Does NOT fetch documentation again. Reuses cached content.

        Args:
            app: App dictionary
            app_research: AppResearch object to verify
            docs_url: Documentation URL (used to retrieve cached content)

        Returns:
            Verification result dictionary with reasons
        """
        logger.info(f"Verifying {app_research.name}")

        doc_result = self.cache.get(docs_url)

        if not doc_result:
            logger.warning(f"Documentation not cached for {docs_url}, fetching...")
            doc_result = self.fetch_documentation(docs_url)

        verification = self.verifier.verify(
            app_research,
            doc_result.get("text", ""),
        )

        return verification

    def execute(self, app: Dict[str, Any]) -> Optional[AppResearch]:
        """
        Execute the complete research workflow for an application.

        Pipeline:
        1. Discover documentation URL
        2. Fetch documentation (with cache)
        3. Extract text
        4. Build prompt
        5. Call LLM
        6. Parse response (preserves original app name)
        7. Estimate confidence (retry does NOT increase confidence)
        8. Verify using cached docs
        9. Retry if low verification (preserves name, docs_url, category)

        Args:
            app: App dictionary with name and website

        Returns:
            AppResearch object if successful, None otherwise
        """
        app_name = app.get("name", "Unknown")
        app_category = app.get("category", None)

        logger.info(f"Starting workflow for {app_name}")
        start_time = time.time()

        # Step 1: Discover documentation URL (not just homepage)
        docs_url = self.locate_source(app)

        # Step 2: Fetch documentation (with caching)
        doc_result = self.fetch_documentation(docs_url)

        if doc_result.get("status") != 200:
            logger.error(f"Failed to fetch documentation: {doc_result.get('text', 'Unknown error')}")
            return None

        # Step 3: Prepare context
        context = doc_result.get("text", "")

        # Step 4: Build prompt
        prompt = self.build_prompt(app, context)

        # Step 5: Call LLM
        llm_response = self.call_llm(prompt)

        # Step 6: Parse response (preserves original app name)
        app_research = self.parse_response(llm_response, app_name)

        if not app_research:
            return None

        # Step 7: Estimate confidence
        confidence = self.estimate_confidence(app_research)
        app_research.confidence_score = confidence

        # Step 8: Verify result using cached documentation
        verification = self.verify_result(app, app_research, docs_url)

        # Step 9: Verification loop - retry if low score
        verification_score = verification.get("verification_score", 0)
        if verification_score < 40:
            logger.warning(
                f"Low verification score ({verification_score}), "
                f"retrying with improved context"
            )
            improved = self._retry_with_verification(
                app, context, app_research, app_name, app_category, docs_url
            )

            if improved:
                app_research = improved
                # Re-verify using cached docs
                verification = self.verify_result(app, app_research, docs_url)
                # Re-estimate confidence (retry does NOT boost confidence)
                confidence = self.estimate_confidence(app_research)
                app_research.confidence_score = confidence

        # Step 10: Set manual review flag
        if verification.get("manual_review_required", False):
            app_research.verification_status = "manual_review"
            logger.warning(f"Manual review required for {app_name}")

        # Step 11: Set evidence_url from the documentation URL (never placeholder)
        if docs_url and docs_url != app.get("website", ""):
            app_research.evidence_url = docs_url

        # Step 12: Preserve category from apps.json if LLM didn't set it
        if app_category and (not app_research.category or app_research.category == "other"):
            app_research.category = app_category

        # Step 13: Final name sanity check
        if not app_research.name or app_research.name == "Unknown":
            app_research.name = app_name

        elapsed = time.time() - start_time
        logger.success(f"Workflow complete for {app_name} in {elapsed:.2f}s")

        return app_research

    def _retry_with_verification(
        self,
        app: Dict[str, Any],
        context: str,
        previous_result: AppResearch,
        app_name: str,
        app_category: Optional[str],
        docs_url: str,
    ) -> Optional[AppResearch]:
        """
        Retry research with improved context for better verification.

        CRITICAL: Preserves app name, documentation URL, and category.
        Only replaces fields that were regenerated by the LLM.

        Args:
            app: App dictionary
            context: Context text
            previous_result: Previous result (preserved for fallback)
            app_name: Original app name (never overwritten)
            app_category: Original category (never overwritten)
            docs_url: Original documentation URL (never overwritten)

        Returns:
            Improved AppResearch object if successful, original otherwise
        """
        logger.info(f"Retrying with improved context for {app_name}")

        # Build improvement prompt that asks for specific missing fields
        improvement_prompt = (
            f"Research the application '{app_name}' using the following documentation.\n\n"
            f"Previous result had low verification score. Focus on finding:\n"
            f"- Authentication methods (OAuth, API Key, JWT, Basic Auth, etc.)\n"
            f"- API surface details (REST, GraphQL, Webhooks, SDK)\n"
            f"- Self-serve availability (sign up, free trial vs contact sales)\n"
            f"- MCP support (Model Context Protocol, function calling)\n"
            f"- Buildability assessment (high, medium, low)\n\n"
            f"Documentation:\n"
            f"{context[:3000]}\n\n"
            f"Return complete JSON:"
        )

        llm_response = self.call_llm(improvement_prompt)
        improved = self.parse_response(llm_response, app_name)

        if improved:
            # Preserve original fields that should never be overwritten
            improved.name = app_name
            if app_category:
                improved.category = app_category

            # Merge: only replace fields that were regenerated
            if not improved.description or improved.description == "Unknown":
                improved.description = previous_result.description
            if not improved.auth_methods or len(improved.auth_methods) == 0:
                improved.auth_methods = previous_result.auth_methods
            if not improved.api_surface:
                improved.api_surface = previous_result.api_surface
            if improved.self_serve is None:
                improved.self_serve = previous_result.self_serve
            if improved.mcp_support is None:
                improved.mcp_support = previous_result.mcp_support
            if not improved.buildability:
                improved.buildability = previous_result.buildability
            if not improved.main_blocker:
                improved.main_blocker = previous_result.main_blocker

            return improved

        return previous_result