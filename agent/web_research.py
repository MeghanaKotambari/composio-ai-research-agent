"""
Web Research module for the AI Research Agent.

Handles web page fetching, content extraction, and text cleaning.
Supports both requests and Playwright for different use cases.

Responsibilities:
- Fetch web pages
- Extract readable text
- Clean and normalize content
- Handle errors and retries
"""

from typing import Optional, Dict, Any
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .logger import get_logger
from .utils import is_valid_url, normalize_url, retry as custom_retry

logger = get_logger(__name__)


class WebResearchService:
    """
    Web research service for fetching and extracting documentation content.
    
    Fetches official documentation pages and extracts clean readable text
    for later LLM processing. Does not perform any LLM operations.
    """
    
    # Default user agent for requests
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Maximum text length to extract (approximately 12000 characters)
    MAX_TEXT_LENGTH = 12000
    
    def __init__(
        self,
        timeout: int = 20,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Initialize web research service.
        
        Args:
            timeout: Request timeout in seconds (default: 20)
            max_retries: Maximum number of retry attempts (default: 3)
            user_agent: Custom user agent string (uses default if None)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        
        logger.info("WebResearchService initialized")
    
    def fetch_page(self, url: str) -> str:
        """
        Download webpage using requests with retry logic.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If fetch fails after retries
            requests.Timeout: If request times out
        """
        if not self._validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        url = normalize_url(url)
        logger.info(f"Fetching page: {url}")
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Detect and log redirects
                if response.url != url:
                    logger.info(f"Redirect detected: {url} -> {response.url}")
                
                logger.success(f"Successfully fetched {url} ({len(response.text)} bytes)")
                return response.text
                
            except requests.Timeout as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt}/{self.max_retries} for {url}")
            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Request failed on attempt {attempt}/{self.max_retries} for {url}: {e}")
            
            if attempt < self.max_retries:
                continue
        
        raise requests.RequestException(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        return is_valid_url(url)
    
    def extract_text(self, html: str) -> str:
        """
        Extract readable text from HTML using BeautifulSoup.
        
        Removes non-content elements and normalizes whitespace.
        Limits output to approximately the first 12000 characters.
        
        Args:
            html: HTML content to extract from
            
        Returns:
            Cleaned text content
        """
        logger.debug("Extracting text from HTML")
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unwanted elements that don't contain useful content
        for element in soup(["script", "style", "svg", "noscript", "iframe", "footer", "nav", "header"]):
            element.decompose()
        
        # Get text content
        text = soup.get_text(separator="\n")
        
        # Clean and normalize whitespace
        text = self._clean_text(text)
        
        # Limit to approximately 12000 characters to avoid huge prompts
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]
            logger.debug(f"Text truncated to {self.MAX_TEXT_LENGTH} characters")
        
        logger.debug(f"Extracted {len(text)} characters of text")
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text with normalized whitespace
        """
        if not text:
            return ""
        
        # Split into lines
        lines = text.split("\n")
        
        # Remove empty lines and excessive whitespace
        cleaned_lines = []
        for line in lines:
            line = " ".join(line.split())  # Normalize whitespace
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join with single newlines
        cleaned_text = "\n".join(cleaned_lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        while "\n\n\n" in cleaned_text:
            cleaned_text = cleaned_text.replace("\n\n\n", "\n\n")
        
        return cleaned_text.strip()
    
    def research_source(self, url: str) -> Dict[str, Any]:
        """
        Complete research workflow for a single source.
        
        Fetches page and extracts clean text.
        
        Args:
            url: URL to research
            
        Returns:
            Dictionary containing:
            - url: Original URL
            - title: Page title (if found)
            - text: Extracted text content
            - status: HTTP status code (200 for success)
        """
        logger.info(f"Researching source: {url}")
        
        result = {
            "url": url,
            "title": "",
            "text": "",
            "status": 0,
        }
        
        try:
            html = self.fetch_page(url)
            
            # Extract title from HTML
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text(strip=True)
            
            # Extract text content
            result["text"] = self.extract_text(html)
            result["status"] = 200
            
            logger.success(f"Research complete for {url} ({len(result['text'])} chars)")
            
        except Exception as e:
            logger.error(f"Failed to research {url}: {e}")
            result["status"] = 0
            result["text"] = f"Error: {str(e)}"
        
        return result
    
    def close(self) -> None:
        """Close the session and free resources."""
        self.session.close()
        logger.debug("WebResearchService session closed")
    
    def __enter__(self) -> "WebResearchService":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class WebResearcher:
    """
    Web research module for fetching and extracting web content.
    
    Supports both simple HTTP requests and browser automation (Playwright).
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize web researcher.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    @custom_retry(max_attempts=3, delay=1.0, backoff=2.0)
    def fetch_page(self, url: str) -> str:
        """
        Fetch web page content using requests.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            requests.RequestException: If fetch fails after retries
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        url = normalize_url(url)
        logger.info(f"Fetching page: {url}")
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        logger.success(f"Successfully fetched {url} ({len(response.text)} bytes)")
        return response.text

    def extract_text(self, html: str, url: str) -> str:
        """
        Extract readable text from HTML.
        
        Removes scripts, styles, and other non-content elements.
        
        Args:
            html: HTML content
            url: Source URL (for resolving relative links)
            
        Returns:
            Cleaned text content
        """
        logger.debug("Extracting text from HTML")
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Get text content
        text = soup.get_text(separator="\n")
        
        # Clean whitespace
        text = self._clean_text(text)
        
        logger.debug(f"Extracted {len(text)} characters of text")
        return text

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Split into lines
        lines = text.split("\n")
        
        # Remove empty lines and excessive whitespace
        cleaned_lines = []
        for line in lines:
            line = " ".join(line.split())  # Normalize whitespace
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join with single newlines
        cleaned_text = "\n".join(cleaned_lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        while "\n\n\n" in cleaned_text:
            cleaned_text = cleaned_text.replace("\n\n\n", "\n\n")
        
        return cleaned_text.strip()

    def research_page(self, url: str) -> Dict[str, Any]:
        """
        Complete research workflow for a single page.
        
        Fetches page and extracts clean text.
        
        Args:
            url: URL to research
            
        Returns:
            Dictionary containing:
            - url: Original URL
            - content: Extracted text content
            - success: Whether research succeeded
            - error: Error message if failed
        """
        result = {
            "url": url,
            "content": "",
            "success": False,
            "error": None,
        }
        
        try:
            html = self.fetch_page(url)
            content = self.extract_text(html, url)
            
            result["content"] = content
            result["success"] = True
            
            logger.success(f"Research complete for {url} ({len(content)} chars)")
            
        except Exception as e:
            error_msg = f"Failed to research {url}: {str(e)}"
            logger.error(error_msg)
            result["error"] = str(e)
        
        return result

    def research_with_playwright(self, url: str) -> Dict[str, Any]:
        """
        Research page using Playwright (for JavaScript-heavy sites).
        
        Args:
            url: URL to research
            
        Returns:
            Dictionary with research results
        """
        # TODO: Implement Playwright-based research
        # This is a placeholder for future implementation
        logger.warning("Playwright research not yet implemented, falling back to requests")
        return self.research_page(url)

    def close(self) -> None:
        """Close the session and free resources."""
        self.session.close()
        logger.debug("Web researcher session closed")

    def __enter__(self) -> "WebResearcher":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class DocumentationFinder:
    """
    Finds official documentation URLs for SaaS applications.
    
    Uses common patterns and search strategies to locate docs.
    """

    def __init__(self, web_researcher: Optional[WebResearcher] = None):
        """
        Initialize documentation finder.
        
        Args:
            web_researcher: WebResearcher instance for fetching pages
        """
        self.web_researcher = web_researcher or WebResearcher()

    def find_docs_url(self, app_name: str, website_url: str) -> Optional[str]:
        """
        Find official documentation URL for an application.
        
        Args:
            app_name: Application name
            website_url: Main website URL
            
        Returns:
            Documentation URL if found, None otherwise
        """
        logger.info(f"Finding documentation for {app_name}")
        
        # Common documentation URL patterns
        patterns = [
            "/docs",
            "/documentation",
            "/developers",
            "/developer",
            "/api",
            "/api-docs",
            "/api/docs",
            "/reference",
            "/guide",
        ]
        
        base_url = self._get_base_url(website_url)
        
        # Try common patterns
        for pattern in patterns:
            docs_url = urljoin(base_url, pattern)
            if self._is_valid_docs_page(docs_url):
                logger.success(f"Found docs at {docs_url}")
                return docs_url
        
        # TODO: Implement search-based discovery
        # Use search engines to find documentation
        
        logger.warning(f"No documentation found for {app_name}")
        return None

    def _get_base_url(self, url: str) -> str:
        """
        Get base URL (scheme + netloc).
        
        Args:
            url: Full URL
            
        Returns:
            Base URL
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _is_valid_docs_page(self, url: str) -> bool:
        """
        Check if URL is a valid documentation page.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid docs page, False otherwise
        """
        try:
            result = self.web_researcher.fetch_page(url)
            # Simple heuristic: check if page contains documentation-like content
            return len(result) > 1000  # At least 1KB of content
        except Exception:
            return False

    def close(self) -> None:
        """Close resources."""
        if self.web_researcher:
            self.web_researcher.close()

    def __enter__(self) -> "DocumentationFinder":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()