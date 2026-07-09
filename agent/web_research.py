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