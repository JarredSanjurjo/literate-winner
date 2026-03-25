"""Adapter for email-style free-text requests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.adapters.base import BaseAdapter
from src.models.enums import SourceType
from src.models.schemas import CanonicalIntake
from src.utils.ids import generate_request_id
from src.utils.timestamps import utc_now


class EmailTextAdapter(BaseAdapter):
    """Adapter for copied email-style text requests."""

    source_type = SourceType.EMAIL_TEXT

    def can_handle(self, input_ref: str | Path) -> bool:
        text = str(input_ref)
        lowered = text.lower()
        return "subject:" in lowered or "from:" in lowered or "to:" in lowered

    def load_many(
        self,
        input_ref: str | Path,
        *,
        business_domain_hint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[CanonicalIntake]:
        metadata = dict(metadata or {})
        metadata.setdefault("received_channel", "email_text")

        record = CanonicalIntake(
            request_id=generate_request_id(),
            source_type=SourceType.EMAIL_TEXT,
            source_name="manual_email_input",
            business_domain_hint=business_domain_hint,
            raw_content=str(input_ref),
            normalized_content=str(input_ref),
            metadata=metadata,
            received_at=utc_now(),
        )
        return [record]
