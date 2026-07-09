"""
Data models for the AI Research Agent.

Defines Pydantic models for representing researched applications
with proper typing and validation.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator


class AuthMethod(str, Enum):
    """Supported authentication methods."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    JWT = "jwt"
    BEARER_TOKEN = "bearer_token"
    OAUTH1 = "oauth1"
    NONE = "none"
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    """Verification status for research data."""
    PENDING = "pending"
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class Category(str, Enum):
    """SaaS application categories."""
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    CRM = "crm"
    ECOMMERCE = "ecommerce"
    DEVELOPER_TOOLS = "developer_tools"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    HR = "hr"
    FINANCE = "finance"
    PROJECT_MANAGEMENT = "project_management"
    CLOUD_INFRASTRUCTURE = "cloud_infrastructure"
    DATABASE = "database"
    AI_ML = "ai_ml"
    SECURITY = "security"
    PAYMENT = "payment"
    SOCIAL = "social"
    MEDIA = "media"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    OTHER = "other"


class AppResearch(BaseModel):
    """
    Represents a researched SaaS application with comprehensive metadata.
    
    This model captures all relevant information about a SaaS application
    for analysis and dashboard presentation.
    """

    # Basic Information
    name: str = Field(
        ...,
        description="Application name",
        min_length=1,
        max_length=200,
    )
    category: Category = Field(
        ...,
        description="Primary category of the application",
    )
    description: str = Field(
        ...,
        description="One-line description of the application",
        min_length=10,
        max_length=500,
    )

    # Authentication
    auth_methods: List[AuthMethod] = Field(
        default_factory=list,
        description="List of supported authentication methods",
    )

    # Access Model
    self_serve: Optional[bool] = Field(
        None,
        description="Whether the app offers self-serve signup (True) or is gated (False)",
    )

    # API Surface
    api_surface: Optional[str] = Field(
        None,
        description="Description of API capabilities and endpoints",
        max_length=1000,
    )

    # MCP Support
    mcp_support: Optional[bool] = Field(
        None,
        description="Whether the app has MCP (Model Context Protocol) support",
    )

    # Buildability for AI Agents
    buildability: Optional[str] = Field(
        None,
        description="Assessment of how buildable the app is for AI agents (high/medium/low)",
    )

    # Blockers
    main_blocker: Optional[str] = Field(
        None,
        description="Main blocker for AI agent integration",
        max_length=500,
    )

    # Evidence
    evidence_url: Optional[HttpUrl] = Field(
        None,
        description="URL providing evidence for the research findings",
    )

    # Confidence and Verification
    confidence_score: float = Field(
        ...,
        description="Confidence score from 0.0 to 1.0",
        ge=0.0,
        le=1.0,
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="Current verification status",
    )

    # Additional Notes
    notes: Optional[str] = Field(
        None,
        description="Additional research notes and observations",
        max_length=2000,
    )

    # Metadata
    researched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when research was conducted",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when data was last updated",
    )

    @validator("description")
    def validate_description(cls, v: str) -> str:
        """Ensure description is properly formatted."""
        return v.strip()

    @validator("auth_methods")
    def validate_auth_methods(cls, v: List[AuthMethod]) -> List[AuthMethod]:
        """Ensure at least one auth method if list is provided."""
        if v and len(v) == 0:
            return [AuthMethod.UNKNOWN]
        return v

    @validator("confidence_score")
    def validate_confidence_score(cls, v: float) -> float:
        """Ensure confidence score is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return round(v, 2)

    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v),
        }


class ResearchBatch(BaseModel):
    """
    Represents a batch of researched applications.
    
    Used for bulk operations and reporting.
    """

    batch_id: str = Field(
        ...,
        description="Unique identifier for the research batch",
    )
    apps: List[AppResearch] = Field(
        default_factory=list,
        description="List of researched applications",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when batch was created",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional batch metadata",
    )

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }