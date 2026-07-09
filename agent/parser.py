"""
Parser module for the AI Research Agent.

Validates and parses LLM responses into structured Pydantic models.
Handles malformed responses and provides detailed error reporting.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from pydantic import ValidationError

from .logger import get_logger
from .models import AppResearch, Category, AuthMethod, VerificationStatus

logger = get_logger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class ResponseParsingError(Exception):
    """Base exception for response parsing errors."""
    pass


class MalformedJSONError(ResponseParsingError):
    """Raised when JSON cannot be located or extracted from response."""
    pass


class ValidationFailedError(ResponseParsingError):
    """Raised when JSON is valid but fails Pydantic validation."""
    pass


# ============================================================================
# Parse Result
# ============================================================================

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


# ============================================================================
# Response Parser
# ============================================================================

class ResponseParser:
    """
    Parses LLM responses into structured data.
    
    Handles JSON extraction, validation, and error recovery.
    Extremely robust against malformed responses.
    """
    
    def __init__(self) -> None:
        """Initialize response parser."""
        self.max_retries = 3
    
    def parse(self, response: str, app_name: Optional[str] = None) -> ParseResult:
        """
        Main public method to parse LLM response.
        
        Pipeline:
        1. Clean response
        2. Extract JSON
        3. Repair common errors
        4. Parse JSON
        5. Validate
        
        Args:
            response: Raw LLM response string
            app_name: Optional app name to inject if missing
            
        Returns:
            ParseResult object
        """
        logger.debug("Starting response parsing pipeline")
        
        # Step 1: Clean response
        cleaned = self.clean_response(response)
        logger.debug("Response cleaned")
        
        # Step 2: Extract JSON
        try:
            json_str = self.extract_json(cleaned)
        except MalformedJSONError as e:
            logger.error(f"JSON extraction failed: {e}")
            return ParseResult(
                success=False,
                error=str(e),
                raw_response=response,
            )
        
        # Step 3: Repair common errors
        repaired = self.repair_common_errors(json_str)
        if repaired != json_str:
            logger.info("JSON repaired")
        
        # Step 4: Parse JSON
        try:
            data = self.parse_json(repaired)
        except MalformedJSONError as e:
            logger.error(f"JSON parsing failed: {e}")
            return ParseResult(
                success=False,
                error=str(e),
                raw_response=response,
            )
        
        # Inject app name if provided and missing
        if app_name and "name" not in data:
            data["name"] = app_name
        
        # Step 5: Validate
        try:
            app_research = self.validate(data)
            logger.success("Response parsed and validated successfully")
            return ParseResult(
                success=True,
                data=app_research,
                raw_response=response,
            )
        except ValidationFailedError as e:
            logger.error(f"Validation failed: {e}")
            return ParseResult(
                success=False,
                error=str(e),
                raw_response=response,
            )
    
    def clean_response(self, response: str) -> str:
        """
        Clean LLM response by removing artifacts.
        
        Removes:
        - Markdown code fences
        - ```json
        - ```
        - Accidental text before/after JSON
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response string
        """
        if not response:
            return ""
        
        text = response.strip()
        
        # Remove markdown code fences
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        
        # Remove common prefixes
        text = re.sub(r"^(Here is|Sure,|Certainly,|Here's|Here's the JSON).*?:\s*", "", text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_json(self, response: str) -> str:
        """
        Extract JSON from response text.
        
        Locates first { and last } to extract JSON object.
        
        Args:
            response: Cleaned response text
            
        Returns:
            Extracted JSON string
            
        Raises:
            MalformedJSONError: If JSON cannot be located
        """
        if not response:
            raise MalformedJSONError("Empty response")
        
        # Find first { and last }
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        
        if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
            raise MalformedJSONError("No JSON object found in response")
        
        json_str = response[start_idx:end_idx + 1]
        
        if not json_str:
            raise MalformedJSONError("Empty JSON object extracted")
        
        logger.debug(f"Extracted JSON: {len(json_str)} chars")
        return json_str
    
    def parse_json(self, json_string: str) -> Dict[str, Any]:
        """
        Parse JSON string into dictionary.
        
        Args:
            json_string: JSON string to parse
            
        Returns:
            Parsed dictionary
            
        Raises:
            MalformedJSONError: If JSON is invalid
        """
        try:
            data = json.loads(json_string)
            if not isinstance(data, dict):
                raise MalformedJSONError("JSON is not an object")
            return data
        except json.JSONDecodeError as e:
            raise MalformedJSONError(f"Invalid JSON: {str(e)}")
    
    def repair_common_errors(self, json_string: str) -> str:
        """
        Repair common JSON errors conservatively.
        
        Repairs:
        - Trailing commas before } or ]
        - Single quotes to double quotes (for keys and string values)
        - Missing closing braces
        
        Does NOT:
        - Invent values
        - Fix structural issues
        - Add missing fields
        
        Args:
            json_string: JSON string to repair
            
        Returns:
            Repaired JSON string
        """
        if not json_string:
            return json_string
        
        repaired = json_string
        
        # Fix trailing commas (e.g., "key": "value",} -> "key": "value"}
        repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
        
        # Fix single quotes for keys (e.g., {'key': -> {"key":)
        # Only fix if the string uses single quotes consistently
        if "'" in repaired and '"' not in repaired:
            # Replace single quotes with double quotes
            repaired = re.sub(r"'([^']+)'", r'"\1"', repaired)
        
        # Try to fix missing closing braces
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")
        
        if open_braces > 0:
            repaired += "}" * open_braces
        if open_brackets > 0:
            repaired += "]" * open_brackets
        
        return repaired
    
    def validate(self, app_json: Dict[str, Any]) -> AppResearch:
        """
        Validate JSON data against AppResearch model.
        
        Args:
            app_json: Dictionary to validate
            
        Returns:
            Validated AppResearch object
            
        Raises:
            ValidationFailedError: If validation fails
        """
        # Normalize category
        if "category" in app_json:
            app_json["category"] = self._normalize_category(app_json["category"])
        
        # Normalize auth_methods
        if "auth_methods" in app_json:
            app_json["auth_methods"] = self._normalize_auth_methods(app_json["auth_methods"])
        
        # Ensure confidence_score is present
        if "confidence_score" not in app_json:
            app_json["confidence_score"] = 0.5
        
        # Set default verification_status
        if "verification_status" not in app_json:
            app_json["verification_status"] = VerificationStatus.PENDING
        
        try:
            return AppResearch(**app_json)
        except ValidationError as e:
            raise ValidationFailedError(f"Validation error: {str(e)}")
    
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


# ============================================================================
# Data Enricher
# ============================================================================

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


# ============================================================================
# Self-Test
# ============================================================================

def _self_test() -> None:
    """Run self-test with sample malformed responses."""
    parser = ResponseParser()
    
    test_cases = [
        # 1. Valid JSON
        ('{"name": "TestApp", "category": "other", "description": "Test", "auth_methods": ["api_key"], "confidence_score": 0.5}', "Valid JSON"),
        
        # 2. JSON with markdown code fences
        ('```json\n{"name": "TestApp", "category": "other", "description": "Test", "auth_methods": ["api_key"], "confidence_score": 0.5}\n```', "Markdown code fences"),
        
        # 3. JSON with trailing comma
        ('{"name": "TestApp", "category": "other", "description": "Test", "auth_methods": ["api_key",], "confidence_score": 0.5}', "Trailing comma"),
        
        # 4. JSON with single quotes
        ("{'name': 'TestApp', 'category': 'other', 'description': 'Test', 'auth_methods': ['api_key'], 'confidence_score': 0.5}", "Single quotes"),
        
        # 5. No JSON found
        ("I cannot find the information you requested.", "No JSON"),
    ]
    
    print("Running self-test...")
    for response, description in test_cases:
        result = parser.parse(response)
        status = "✓ PASS" if (result.success or "No JSON" in description) else "✗ FAIL"
        print(f"{status}: {description}")
        if result.success:
            print(f"  Parsed: {result.data.name}")
        else:
            print(f"  Error: {result.error}")


if __name__ == "__main__":
    _self_test()