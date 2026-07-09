"""
Verification Engine for the AI Research Agent.

Validates whether extracted research is supported by official documentation.
All verification is deterministic - no LLM calls.
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urlparse

from .logger import get_logger
from .models import AppResearch, AuthMethod, VerificationStatus
from .config import settings

logger = get_logger(__name__)


class VerificationEngine:
    """
    Deterministic verification engine for research data.
    
    Validates extracted information against documentation text
    without using LLM. All checks are based on keyword matching.
    """
    
    # Keywords for auth method detection
    AUTH_KEYWORDS = {
        AuthMethod.API_KEY: ["api key", "apikey", "api-key", "secret key", "access key"],
        AuthMethod.OAUTH2: ["oauth2", "oauth 2", "oauth", "authorization code", "access token"],
        AuthMethod.BASIC_AUTH: ["basic auth", "basic authentication", "username password"],
        AuthMethod.JWT: ["jwt", "json web token", "bearer token"],
        AuthMethod.BEARER_TOKEN: ["bearer token", "bearer", "token authentication"],
        AuthMethod.OAUTH1: ["oauth1", "oauth 1"],
    }
    
    # Keywords for API surface detection
    API_KEYWORDS = ["rest", "graphql", "webhook", "sdk", "openapi", "api reference", "api docs"]
    
    # Keywords for self-serve detection
    SELF_SERVE_POSITIVE = ["sign up", "get started", "free trial", "developer portal", "create account"]
    SELF_SERVE_NEGATIVE = ["contact sales", "enterprise only", "request access", "gated", "sales team"]
    
    # Keywords for MCP detection
    MCP_KEYWORDS = ["mcp", "model context protocol", "agent", "tool calling", "function calling"]
    
    def __init__(self) -> None:
        """Initialize verification engine."""
        self.verified_dir = settings.VERIFIED_OUTPUT_DIR
        self.verified_dir.mkdir(parents=True, exist_ok=True)
    
    def verify_auth(
        self,
        auth_methods: List[str],
        documentation_text: str,
    ) -> Dict[str, Any]:
        """
        Verify authentication methods against documentation.
        
        Checks if OAuth, API Key, Bearer, Basic Auth, Token
        appear in documentation text.
        
        Args:
            auth_methods: List of claimed auth methods
            documentation_text: Documentation to search
            
        Returns:
            Dictionary with verification results
        """
        doc_lower = documentation_text.lower()
        verified = []
        failed = []
        
        for method in auth_methods:
            # Check if method keywords appear in documentation
            keywords = self.AUTH_KEYWORDS.get(method, [])
            found = any(kw in doc_lower for kw in keywords)
            
            if found:
                verified.append(method)
                logger.info(f"Verified auth method: {method}")
            else:
                failed.append(method)
                logger.warning(f"Auth method not found in docs: {method}")
        
        return {
            "verified": verified,
            "failed": failed,
            "score": len(verified) * 20,
        }
    
    def verify_api_surface(
        self,
        api_surface: Optional[str],
        documentation_text: str,
    ) -> Dict[str, Any]:
        """
        Verify API surface claims against documentation.
        
        Looks for REST, GraphQL, Webhook, SDK, OpenAPI keywords.
        
        Args:
            api_surface: Claimed API surface description
            documentation_text: Documentation to search
            
        Returns:
            Dictionary with verification results
        """
        if not api_surface:
            return {"verified": False, "score": 0, "warnings": ["No API surface claimed"]}
        
        doc_lower = documentation_text.lower()
        found_keywords = []
        
        for keyword in self.API_KEYWORDS:
            if keyword in doc_lower:
                found_keywords.append(keyword)
        
        verified = len(found_keywords) > 0
        
        if verified:
            logger.info(f"Verified API surface with keywords: {found_keywords}")
        else:
            logger.warning("No API keywords found in documentation")
        
        return {
            "verified": verified,
            "keywords_found": found_keywords,
            "score": 20 if verified else 0,
        }
    
    def verify_self_serve(
        self,
        self_serve: Optional[bool],
        documentation_text: str,
    ) -> Dict[str, Any]:
        """
        Verify self-serve claim against documentation.
        
        Detects phrases like Sign Up, Get Started, Developer Portal,
        Free Trial, Contact Sales, Enterprise Only, Request Access.
        
        Args:
            self_serve: Claimed self-serve status
            documentation_text: Documentation to search
            
        Returns:
            Dictionary with verification results
        """
        doc_lower = documentation_text.lower()
        
        has_positive = any(kw in doc_lower for kw in self.SELF_SERVE_POSITIVE)
        has_negative = any(kw in doc_lower for kw in self.SELF_SERVE_NEGATIVE)
        
        # Determine actual status
        if has_positive and not has_negative:
            actual = True
        elif has_negative and not has_positive:
            actual = False
        elif has_positive and has_negative:
            actual = True  # Assume self-serve if both present
        else:
            actual = None  # Cannot determine
        
        verified = (self_serve == actual) or (self_serve is not None and actual is None)
        
        if verified:
            logger.info(f"Self-serve claim verified: {self_serve}")
        else:
            logger.warning(f"Self-serve claim mismatch: claimed {self_serve}, found {actual}")
        
        return {
            "verified": verified,
            "actual": actual,
            "score": 20 if verified else 0,
        }
    
    def verify_mcp(
        self,
        mcp_support: Optional[bool],
        documentation_text: str,
    ) -> Dict[str, Any]:
        """
        Verify MCP support claim against documentation.
        
        Searches for MCP, Model Context Protocol, Agent, Tool Calling.
        
        Args:
            mcp_support: Claimed MCP support status
            documentation_text: Documentation to search
            
        Returns:
            Dictionary with verification results
        """
        doc_lower = documentation_text.lower()
        
        found_keywords = [kw for kw in self.MCP_KEYWORDS if kw in doc_lower]
        
        # MCP is supported if keywords found
        actual = len(found_keywords) > 0
        
        verified = mcp_support == actual or mcp_support is None
        
        if verified:
            logger.info(f"MCP claim verified: {mcp_support}")
        else:
            logger.warning(f"MCP claim mismatch: claimed {mcp_support}, found {actual}")
        
        return {
            "verified": verified,
            "keywords_found": found_keywords,
            "score": 20 if verified else 0,
        }
    
    def verify_evidence(
        self,
        evidence_url: Optional[str],
        app_name: str,
    ) -> Dict[str, Any]:
        """
        Verify evidence URL matches official documentation domain.
        
        Args:
            evidence_url: URL to verify
            app_name: Application name for context
            
        Returns:
            Dictionary with verification results
        """
        if not evidence_url:
            return {
                "verified": False,
                "score": -20,
                "warnings": ["No evidence URL provided"],
            }
        
        # Convert HttpUrl to string if needed
        url_str = str(evidence_url)
        
        try:
            parsed = urlparse(url_str)
            domain = parsed.netloc.lower()
            
            # Check if it's a known documentation domain
            is_doc_domain = any(
                kw in domain for kw in ["docs.", "developer.", "api.", "documentation."]
            ) or "github.com" in domain
            
            if is_doc_domain:
                logger.info(f"Evidence URL verified: {evidence_url}")
                return {"verified": True, "score": 20}
            
            logger.warning(f"Evidence URL may not be official docs: {evidence_url}")
            return {
                "verified": True,
                "score": 10,
                "warnings": ["Evidence URL not from official docs domain"],
            }
            
        except Exception as e:
            logger.error(f"Failed to parse evidence URL: {e}")
            return {
                "verified": False,
                "score": -20,
                "warnings": [f"Invalid URL: {str(e)}"],
            }
    
    def verify(
        self,
        app: AppResearch,
        documentation_text: str,
    ) -> Dict[str, Any]:
        """
        Main verification method.
        
        Runs all verification checks and returns comprehensive results.
        
        Args:
            app: AppResearch object to verify
            documentation_text: Documentation to cross-reference
            
        Returns:
            Dictionary with:
            - verified_fields: List of verified field names
            - failed_fields: List of failed field names
            - warnings: List of warning messages
            - verification_score: Total score (max 100)
            - manual_review_required: Boolean
        """
        logger.info(f"Starting verification for {app.name}")
        
        verified_fields = []
        failed_fields = []
        warnings = []
        total_score = 0
        
        # Verify auth methods
        auth_result = self.verify_auth(app.auth_methods, documentation_text)
        if auth_result["verified"]:
            verified_fields.append("auth_methods")
            total_score += auth_result["score"]
        else:
            failed_fields.append("auth_methods")
            if auth_result["failed"]:
                warnings.append(f"Auth methods not found: {auth_result['failed']}")
        
        # Verify API surface
        api_result = self.verify_api_surface(app.api_surface, documentation_text)
        if api_result["verified"]:
            verified_fields.append("api_surface")
            total_score += api_result["score"]
        else:
            failed_fields.append("api_surface")
        
        # Verify self-serve
        self_serve_result = self.verify_self_serve(app.self_serve, documentation_text)
        if self_serve_result["verified"]:
            verified_fields.append("self_serve")
            total_score += self_serve_result["score"]
        else:
            failed_fields.append("self_serve")
        
        # Verify MCP
        mcp_result = self.verify_mcp(app.mcp_support, documentation_text)
        if mcp_result["verified"]:
            verified_fields.append("mcp_support")
            total_score += mcp_result["score"]
        else:
            failed_fields.append("mcp_support")
        
        # Verify evidence
        evidence_result = self.verify_evidence(app.evidence_url, app.name)
        if evidence_result["verified"]:
            verified_fields.append("evidence_url")
            total_score += evidence_result["score"]
        else:
            failed_fields.append("evidence_url")
        
        if evidence_result.get("warnings"):
            warnings.extend(evidence_result["warnings"])
        
        # Determine if manual review is required
        manual_review = len(failed_fields) > 2 or total_score < 40
        
        result = {
            "verified_fields": verified_fields,
            "failed_fields": failed_fields,
            "warnings": warnings,
            "verification_score": min(total_score, 100),
            "manual_review_required": manual_review,
        }
        
        # Log summary
        if manual_review:
            logger.warning(f"Manual review required for {app.name}")
        else:
            logger.success(f"Verification complete for {app.name}: {total_score}/100")
        
        return result
    
    def save_verification_report(
        self,
        app_name: str,
        verification_result: Dict[str, Any],
    ) -> Path:
        """
        Save verification report to output/verified/.
        
        Args:
            app_name: Application name
            verification_result: Verification result dictionary
            
        Returns:
            Path to saved report
        """
        safe_name = "".join(c if c.isalnum() else "_" for c in app_name)
        report_path = self.verified_dir / f"{safe_name}_verification.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(verification_result, f, indent=2)
        
        logger.info(f"Saved verification report to {report_path}")
        return report_path