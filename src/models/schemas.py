"""Pydantic schemas for intake, outputs, and workflow results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import Priority, ProcessingStatus, RequestType, ReviewStatus, SourceType


class BaseSchema(BaseModel):
    """Shared base model with strict field handling."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class CanonicalIntake(BaseSchema):
    """Normalized representation of any supported input source."""

    request_id: str
    source_type: SourceType
    source_name: str
    business_domain_hint: str | None = None
    raw_content: str
    normalized_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime

    @field_validator("request_id", "source_name", "raw_content", "normalized_content")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be blank")
        return value


class ClassificationOutput(BaseSchema):
    """Structured output produced by the classification pipeline."""

    request_id: str
    request_type: RequestType
    business_domain: str
    priority: Priority
    summary: str
    entities: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)
    recommended_next_action: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: ProcessingStatus = ProcessingStatus.VALIDATED
    processed_at: datetime
    prompt_version: str

    @field_validator("request_id", "business_domain", "summary", "recommended_next_action", "prompt_version")
    @classmethod
    def _required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field must not be blank")
        return value

    @field_validator("risk_flags")
    @classmethod
    def _normalize_risk_flags(cls, value: list[str]) -> list[str]:
        return [flag.strip() for flag in value if flag.strip()]


class ValidationResult(BaseSchema):
    """Result of schema and business validation checks."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReviewDecision(BaseSchema):
    """Decision describing whether manual review is required."""

    review_required: bool
    reasons: list[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.OPEN


class ProcessingResult(BaseSchema):
    """Final outcome of processing a single request."""

    request_id: str
    status: ProcessingStatus
    run_id: str | None = None
    validation_result: ValidationResult | None = None
    review_decision: ReviewDecision | None = None
    message: str | None = None
