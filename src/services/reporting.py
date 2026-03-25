"""Reporting queries and export helpers."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from sqlalchemy import select

from src.models.db_models import ProcessedOutputRecord, RequestRecord, ReviewQueueRecord, RunLogRecord
from src.services.storage import StorageService


class ReportingService:
    """Read-oriented reporting queries for the workflow application."""

    def __init__(self, storage_service: StorageService) -> None:
        self.storage_service = storage_service

    def get_processed_requests(self) -> pd.DataFrame:
        """Return processed outputs joined to their request source type."""

        with self.storage_service.session() as session:
            rows = session.execute(
                select(ProcessedOutputRecord, RequestRecord.source_type).join(
                    RequestRecord, ProcessedOutputRecord.request_id == RequestRecord.request_id
                )
            ).all()

        records: list[dict[str, Any]] = []
        for output, source_type in rows:
            records.append(
                {
                    "request_id": output.request_id,
                    "request_type": output.request_type,
                    "business_domain": output.business_domain,
                    "priority": output.priority,
                    "status": output.status,
                    "source_type": source_type,
                    "summary": output.summary,
                    "confidence": output.confidence,
                    "prompt_version": output.prompt_version,
                    "processed_at": output.processed_at,
                }
            )

        return pd.DataFrame(records)

    def get_review_queue(self) -> pd.DataFrame:
        """Return review queue items."""

        with self.storage_service.session() as session:
            rows = session.scalars(select(ReviewQueueRecord)).all()

        records = [
            {
                "review_id": row.review_id,
                "request_id": row.request_id,
                "review_reason": row.review_reason,
                "review_status": row.review_status,
                "reviewer_notes": row.reviewer_notes,
                "created_at": row.created_at,
                "resolved_at": row.resolved_at,
            }
            for row in rows
        ]
        return pd.DataFrame(records)

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """Return aggregate dashboard metrics."""

        processed = self.get_processed_requests()
        reviews = self.get_review_queue()

        with self.storage_service.session() as session:
            run_logs = session.scalars(select(RunLogRecord)).all()

        processing_times = [row.processing_time_ms for row in run_logs if row.processing_time_ms is not None]
        average_processing_time_ms = (
            round(sum(processing_times) / len(processing_times), 2) if processing_times else None
        )

        metrics = {
            "total_requests": int(len(processed.index)),
            "validated_requests": int((processed["status"] == "validated").sum()) if not processed.empty else 0,
            "review_required_requests": (
                int((processed["status"] == "review_required").sum()) if not processed.empty else 0
            ),
            "failed_requests": int((processed["status"] == "failed").sum()) if not processed.empty else 0,
            "review_queue_items": int(len(reviews.index)),
            "request_type_breakdown": (
                processed["request_type"].value_counts().to_dict() if not processed.empty else {}
            ),
            "source_type_breakdown": (
                processed["source_type"].value_counts().to_dict() if not processed.empty else {}
            ),
            "average_processing_time_ms": average_processing_time_ms,
        }
        return metrics

    def get_request_detail(self, request_id: str) -> dict[str, Any] | None:
        """Return a request detail object with source, outputs, and review records."""

        with self.storage_service.session() as session:
            request = session.get(RequestRecord, request_id)
            if request is None:
                return None

            outputs = session.scalars(
                select(ProcessedOutputRecord).where(ProcessedOutputRecord.request_id == request_id)
            ).all()
            review_items = session.scalars(
                select(ReviewQueueRecord).where(ReviewQueueRecord.request_id == request_id)
            ).all()

        return {
            "request_id": request.request_id,
            "source_type": request.source_type,
            "source_name": request.source_name,
            "business_domain_hint": request.business_domain_hint,
            "raw_content": request.raw_content,
            "normalized_content": request.normalized_content,
            "metadata": json.loads(request.metadata_json),
            "outputs": [
                {
                    "request_type": output.request_type,
                    "business_domain": output.business_domain,
                    "priority": output.priority,
                    "summary": output.summary,
                    "entities": json.loads(output.entities_json),
                    "risk_flags": json.loads(output.risk_flags_json),
                    "recommended_next_action": output.recommended_next_action,
                    "confidence": output.confidence,
                    "status": output.status,
                    "processed_at": output.processed_at,
                    "prompt_version": output.prompt_version,
                }
                for output in outputs
            ],
            "review_items": [
                {
                    "review_reason": item.review_reason,
                    "review_status": item.review_status,
                    "reviewer_notes": item.reviewer_notes,
                    "created_at": item.created_at,
                    "resolved_at": item.resolved_at,
                }
                for item in review_items
            ],
        }

    def export_validated_records(self) -> pd.DataFrame:
        """Return validated records ready for CSV export."""

        processed = self.get_processed_requests()
        if processed.empty:
            return processed
        return processed[processed["status"] == "validated"].copy()
