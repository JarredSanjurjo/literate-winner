"""Persistence service for requests, outputs, logs, and reviews."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import Settings
from src.models.db_models import Base, ProcessedOutputRecord, RequestRecord, ReviewQueueRecord, RunLogRecord
from src.models.schemas import CanonicalIntake, ClassificationOutput


def _json_dumps(payload: object) -> str:
    return json.dumps(payload, default=str, sort_keys=True)


class StorageService:
    """Database persistence service for the local-first workflow."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ensure_parent_dir()
        self.engine = create_engine(settings.database_url, future=True)
        self.session_factory = sessionmaker(bind=self.engine, future=True)

    def _ensure_parent_dir(self) -> None:
        database_path = self.settings.database_path
        if database_path is None:
            return
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)

    def save_request(self, intake: CanonicalIntake) -> None:
        with self.session() as session:
            existing = session.get(RequestRecord, intake.request_id)
            if existing is not None:
                return

            session.add(
                RequestRecord(
                    request_id=intake.request_id,
                    source_type=str(intake.source_type),
                    source_name=intake.source_name,
                    business_domain_hint=intake.business_domain_hint,
                    raw_content=intake.raw_content,
                    normalized_content=intake.normalized_content,
                    metadata_json=_json_dumps(intake.metadata),
                    received_at=intake.received_at,
                )
            )

    def save_processed_output(self, output: ClassificationOutput) -> None:
        with self.session() as session:
            session.add(
                ProcessedOutputRecord(
                    request_id=output.request_id,
                    request_type=str(output.request_type),
                    business_domain=output.business_domain,
                    priority=str(output.priority),
                    summary=output.summary,
                    entities_json=_json_dumps(output.entities),
                    risk_flags_json=_json_dumps(output.risk_flags),
                    recommended_next_action=output.recommended_next_action,
                    confidence=output.confidence,
                    status=str(output.status),
                    processed_at=output.processed_at,
                    prompt_version=output.prompt_version,
                )
            )

    def save_run_log(
        self,
        *,
        run_id: str,
        request_id: str,
        stage: str,
        status: str,
        started_at,
        completed_at,
        processing_time_ms: int | None = None,
        error_message: str | None = None,
        prompt_version: str | None = None,
    ) -> None:
        with self.session() as session:
            session.add(
                RunLogRecord(
                    run_id=run_id,
                    request_id=request_id,
                    stage=stage,
                    status=status,
                    started_at=started_at,
                    completed_at=completed_at,
                    processing_time_ms=processing_time_ms,
                    error_message=error_message,
                    prompt_version=prompt_version,
                )
            )

    def enqueue_review(self, request_id: str, reason: str, review_status: str = "open") -> None:
        with self.session() as session:
            session.add(
                ReviewQueueRecord(
                    request_id=request_id,
                    review_reason=reason,
                    review_status=review_status,
                )
            )

    def list_processed_records(self) -> list[ProcessedOutputRecord]:
        with self.session() as session:
            return list(session.scalars(select(ProcessedOutputRecord).order_by(ProcessedOutputRecord.output_id.desc())))

    def list_review_queue(self) -> list[ReviewQueueRecord]:
        with self.session() as session:
            return list(session.scalars(select(ReviewQueueRecord).order_by(ReviewQueueRecord.review_id.desc())))
