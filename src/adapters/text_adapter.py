"""Adapter for pasted text and text files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.adapters.base import BaseAdapter
from src.models.enums import SourceType
from src.models.schemas import CanonicalIntake
from src.utils.ids import generate_request_id
from src.utils.timestamps import utc_now


class TextAdapter(BaseAdapter):
    """Adapter for plain text file paths and pasted text content."""

    source_type = SourceType.TEXT_FILE

    def can_handle(self, input_ref: str | Path) -> bool:
        path = Path(input_ref)
        return path.exists() and path.is_file() and path.suffix.lower() == ".txt"

    def load_many(
        self,
        input_ref: str | Path,
        *,
        business_domain_hint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[CanonicalIntake]:
        metadata = dict(metadata or {})
        path = Path(input_ref)

        if path.exists() and path.is_file():
            raw_content = path.read_text(encoding="utf-8")
            metadata.setdefault("file_name", path.name)
            metadata.setdefault("file_path", str(path))
            source_type = SourceType.TEXT_FILE
            source_name = path.name
        else:
            raw_content = str(input_ref)
            source_type = SourceType.PASTED_TEXT
            source_name = "manual_input"

        record = CanonicalIntake(
            request_id=generate_request_id(),
            source_type=source_type,
            source_name=source_name,
            business_domain_hint=business_domain_hint,
            raw_content=raw_content,
            normalized_content=raw_content,
            metadata=metadata,
            received_at=utc_now(),
        )
        return [record]
