"""Database models for requests, outputs, logs, and reviews."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, Integer, Float, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class RequestRecord(Base):
    """Persisted raw and normalized request input."""

    __tablename__ = "requests"

    request_id: Mapped[str] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(index=True)
    source_name: Mapped[str]
    business_domain_hint: Mapped[str | None]
    raw_content: Mapped[str] = mapped_column(Text)
    normalized_content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    processed_outputs: Mapped[list["ProcessedOutputRecord"]] = relationship(back_populates="request")
    run_logs: Mapped[list["RunLogRecord"]] = relationship(back_populates="request")
    review_items: Mapped[list["ReviewQueueRecord"]] = relationship(back_populates="request")


class ProcessedOutputRecord(Base):
    """Persisted structured output returned by the classifier."""

    __tablename__ = "processed_outputs"
    __table_args__ = (
        Index("ix_processed_outputs_request_type", "request_type"),
        Index("ix_processed_outputs_status", "status"),
        Index("ix_processed_outputs_priority", "priority"),
    )

    output_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.request_id"))
    request_type: Mapped[str]
    business_domain: Mapped[str]
    priority: Mapped[str]
    summary: Mapped[str] = mapped_column(Text)
    entities_json: Mapped[str] = mapped_column(Text)
    risk_flags_json: Mapped[str] = mapped_column(Text)
    recommended_next_action: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str]
    processed_at: Mapped[datetime]
    prompt_version: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    request: Mapped[RequestRecord] = relationship(back_populates="processed_outputs")


class RunLogRecord(Base):
    """Per-stage execution log for audit and debugging."""

    __tablename__ = "run_logs"
    __table_args__ = (Index("ix_run_logs_request_id", "request_id"),)

    run_id: Mapped[str] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.request_id"))
    stage: Mapped[str]
    status: Mapped[str]
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
    processing_time_ms: Mapped[int | None]
    error_message: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    request: Mapped[RequestRecord] = relationship(back_populates="run_logs")


class ReviewQueueRecord(Base):
    """Manual review queue entries for uncertain or failed items."""

    __tablename__ = "review_queue"
    __table_args__ = (Index("ix_review_queue_review_status", "review_status"),)

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.request_id"))
    review_reason: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str]
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    resolved_at: Mapped[datetime | None]

    request: Mapped[RequestRecord] = relationship(back_populates="review_items")
