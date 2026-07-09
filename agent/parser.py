"""
Parser module for the AI Research Agent.

Validates and parses LLM responses into structured Pydantic models.
Handles malformed responses and provides detailed error reporting.

Responsibilities:
- Parse LLM JSON responses
- Validate against Pydantic models
- Handle malformed responses
- Extract structured data
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from pydantic import ValidationError

from .logger import get_logger
from .models import AppResearch, Category, AuthMethod, VerificationStatus

logger = get_logger(__name__)


class ParseResult:
    """Represents the result of parsing an LLM response."""

    def __init__(
        self,
        success: bool,
        data: Optional[AppResearch] = None,
        error: Optional[str] = None,
        raw_response: Optional[str] = None,
    ):
        """
        Initialize parse result.

        Args:
            success: Whether parsing succeeded
            data: Parsed AppResearch object if successful
            error: Error message if failed
            raw_response: Raw LLM response
        """
        self.success = success
        self.data = data
        self.error = error
        self.raw_response = raw_response

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data.dict() if self.data else None,
            "error": self.error,
            "raw_response": self.raw_response,
        }


class ResponseParser:
    """
    Parses LLM responses into structured data.
    
    Handles JSON extraction, validation, and error recovery.
    """

    def __init__(self):
        """Initialize response parser."""
        self.max_retries = 3

    def parse(self, llm_response: str, app_name: Optional[str] = None) -> ParseResult:
        """
        Parse LLM response into AppResearch object.
        
        Args:
            llm_response: Raw LLM response string
            app_name: Optional app name to inject if missing from response
            
        Returns:
            ParseResult object
        """
        logger.debug("Parsing LLM response")
        
        # Step 1: Extract JSON from response
        json_str = self._extract_json(llm_response)
        if not json_str:
            return ParseResult(
                success=False,
                error="No valid JSON found in response",
                raw_response=llm_response,
            )
        
        # Step 2: Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return ParseResult(
                success=False,
                error=f"Invalid JSON: {str(e)}",
                raw_response=llm_response,
            )
        
        # Inject app name if provided and missing
        if app_name and "name" not in data:
            data["name"] = app_name
        
        # Step 3: Validate and create AppResearch object
        try:
            app_research = self._validate_and_create(data)
            logger.success(f"Successfully parsed response")
            return ParseResult(
                success=True,
                data=app_research,
                raw_response=llm_response,
            )
        except ValidationError as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return ParseResult(
                success=False,
                error=error_msg,
                raw_response=llm_response,
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return ParseResult(
                success=False,
                error=error_msg,
                raw_response=llm_response,
            )

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON from LLM response text.
        
        Handles various formats:
        - Pure JSON
        - JSON wrapped in markdown code blocks
        - JSON with surrounding text
        
        Args:
            text: Raw LLM response text
            
        Returns:
            Extracted JSON string or None
        """
        if not text:
            return None
        
        # Try to find JSON in markdown code blocks
        json_patterns = [
            r"```json\s*(\{.*?\})\s*```",  # ```json {...} ```
            r"```\s*(\{.*?\})\s*```",  # ``` {...} ```
            r"(\{[^{}]*\})",  # Simple JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                # Try each match
                for match in matches:
                    try:
                        # Validate it's proper JSON
                        json.loads(match)
                        return match
                    except json.JSONDecodeError:
                        continue
        
        # If no pattern matched, try parsing the whole text
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        return None

    def _validate_and_create(self, data: Dict[str, Any]) -> AppResearch:
        """
        Validate data and create AppResearch object.
        
        Args:
            data: Dictionary with research data
            
        Returns:
            AppResearch object
            
        Raises:
            ValidationError: If data is invalid
        """
        # Normalize category
        if "category" in data:
            data["category"] = self._normalize_category(data["category"])
        
        # Normalize auth_methods
        if "auth_methods" in data:
            data["auth_methods"] = self._normalize_auth_methods(data["auth_methods"])
        
        # Ensure confidence_score is present
        if "confidence_score" not in data:
            data["confidence_score"] = 0.5
        
        # Set default verification_status
        if "verification_status" not in data:
            data["verification_status"] = VerificationStatus.PENDING
        
        # Create AppResearch object
        return AppResearch(**data)

    def _normalize_category(self, category: Any) -> str:
        """
        Normalize category value.
        
        Args:
            category: Category value from LLM
            
        Returns:
            Normalized category string
        """
        if isinstance(category, Category):
            return category.value
        
        if not isinstance(category, str):
            category = str(category)
        
        # Convert to lowercase and replace spaces with underscores
        category_normalized = category.lower().replace(" ", "_").replace("-", "_")
        
        # Validate against allowed categories
        valid_categories = [c.value for c in Category]
        if category_normalized not in valid_categories:
            logger.warning(f"Invalid category '{category}', defaulting to 'other'")
            return Category.OTHER
        
        return category_normalized

    def _normalize_auth_methods(self, auth_methods: Any) -> list:
        """
        Normalize authentication methods.
        
        Args:
            auth_methods: Auth methods from LLM
            
        Returns:
            List of normalized auth method strings
        """
        if not auth_methods:
            return [AuthMethod.UNKNOWN]
        
        if isinstance(auth_methods, str):
            # Handle comma-separated string
            auth_methods = [a.strip() for a in auth_methods.split(",")]
        
        if not isinstance(auth_methods, list):
            auth_methods = [str(auth_methods)]
        
        normalized = []
        valid_methods = [m.value for m in AuthMethod]
        
        for method in auth_methods:
            if isinstance(method, AuthMethod):
                normalized.append(method.value)
                continue
            
            method_str = str(method).lower().replace(" ", "_").replace("-", "_")
            
            if method_str in valid_methods:
                normalized.append(method_str)
            else:
                logger.warning(f"Invalid auth method '{method}', skipping")
        
        return normalized if normalized else [AuthMethod.UNKNOWN]

    def parse_with_retry(
        self,
        llm_response: str,
        max_attempts: int = 3,
        app_name: Optional[str] = None,
    ) -> ParseResult:
        """
        Parse LLM response with retry logic.
        
        Args:
            llm_response: Raw LLM response
            max_attempts: Maximum retry attempts
            app_name: Optional app name to inject if missing
            
        Returns:
            ParseResult object
        """
        for attempt in range(1, max_attempts + 1):
            logger.debug(f"Parse attempt {attempt}/{max_attempts}")
            
            result = self.parse(llm_response, app_name=app_name)
            
            if result.success:
                return result
            
            if attempt < max_attempts:
                logger.warning(
                    f"Parse attempt {attempt} failed: {result.error}. "
                    f"Retrying..."
                )
                # Try to fix common issues
                llm_response = self._attempt_fix(llm_response, result.error)
        
        # All attempts failed
        return result

    def _attempt_fix(self, text: str, error: str) -> str:
        """
        Attempt to fix common parsing errors.
        
        Args:
            text: Original text
            error: Error message
            
        Returns:
            Fixed text
        """
        # Remove common LLM artifacts
        text = text.strip()
        
        # Remove markdown code blocks if present
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        
        # Remove common prefixes/suffixes
        text = re.sub(r"^(Here is|Sure,|Certainly,|Here's).*?:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*\.\s*$", "", text)
        
        return text

    def validate_existing_data(self, data: Dict[str, Any]) -> Tuple[bool, list]:
        """
        Validate existing research data.
        
        Args:
            data: Dictionary with research data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            AppResearch(**data)
            return True, []
        except ValidationError as e:
            for error in e.errors():
                errors.append(f"{error['loc'][0]}: {error['msg']}")
            return False, errors


class DataEnricher:
    """
    Enriches parsed data with additional information.
    
    Adds metadata, timestamps, and computed fields.
    """

    @staticmethod
    def enrich(app_research: AppResearch) -> AppResearch:
        """
        Enrich AppResearch object with additional data.
        
        Args:
            app_research: AppResearch object to enrich
            
        Returns:
            Enriched AppResearch object
        """
        from datetime import datetime
        
        # Add timestamp if not present
        if not app_research.researched_at:
            app_research.researched_at = datetime.utcnow()
        
        # Update timestamp
        app_research.updated_at = datetime.utcnow()
        
        # Set default verification status
        if not app_research.verification_status:
            app_research.verification_status = VerificationStatus.PENDING
        
        return app_research

    @staticmethod
    def calculate_completeness(app_research: AppResearch) -> float:
        """
        Calculate data completeness score.
        
        Args:
            app_research: AppResearch object
            
        Returns:
            Completeness score (0.0-1.0)
        """
        fields = [
            "name",
            "category",
            "description",
            "auth_methods",
            "self_serve",
            "api_surface",
            "mcp_support",
            "buildability",
            "main_blocker",
            "evidence_url",
            "confidence_score",
        ]
        
        populated = sum(1 for field in fields if getattr(app_research, field) is not None)
        
        # Special handling for lists
        if app_research.auth_methods and len(app_research.auth_methods) > 0:
            populated += 0.5  # Bonus for having auth methods
        
        return min(populated / len(fields), 1.0)