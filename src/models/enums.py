"""Shared enums for source types, taxonomy, and statuses."""

from __future__ import annotations

from enum import Enum


class StringEnum(str, Enum):
    """Shared base class for string-backed enums."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return the enum values as plain strings."""
        return [member.value for member in cls]


class Provider(StringEnum):
    """Supported model providers for the application."""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"


class SourceType(StringEnum):
    """Supported input source types for v1."""

    PASTED_TEXT = "pasted_text"
    TEXT_FILE = "text_file"
    CSV = "csv"
    JSON = "json"
    EMAIL_TEXT = "email_text"


class RequestType(StringEnum):
    """Initial v1 request taxonomy."""

    CLIENT_INSTRUCTION = "client_instruction"
    OPERATIONAL_REQUEST = "operational_request"
    BOOKING_CHANGE = "booking_change"
    SCHEDULE_CHANGE = "schedule_change"
    ISSUE_OR_INCIDENT = "issue_or_incident"
    DATA_UPDATE = "data_update"
    INFORMATION_REQUEST = "information_request"
    RISK_OR_ESCALATION = "risk_or_escalation"
    UNKNOWN = "unknown"


class Priority(StringEnum):
    """Allowed request priorities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProcessingStatus(StringEnum):
    """Pipeline statuses for processed outputs."""

    VALIDATED = "validated"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"


class ReviewStatus(StringEnum):
    """Statuses for review queue items."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
