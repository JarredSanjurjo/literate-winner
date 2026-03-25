"""Adapter for JSON-based request ingestion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.adapters.base import BaseAdapter
from src.models.enums import SourceType
from src.models.schemas import CanonicalIntake
from src.utils.ids import generate_request_id
from src.utils.timestamps import utc_now


TEXT_PRIORITY_KEYS = ("raw_content", "content", "body", "message", "description", "summary", "text")


def _build_content(payload: dict[str, Any]) -> str:
    """Create normalized content from a JSON object."""

    for key in TEXT_PRIORITY_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    lines: list[str] = []
    for key, value in payload.items():
        if value in (None, "", [], {}):
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


class JsonAdapter(BaseAdapter):
    """Adapter for JSON files or raw JSON strings."""

    source_type = SourceType.JSON

    def can_handle(self, input_ref: str | Path) -> bool:
        path = Path(input_ref)
        return path.exists() and path.is_file() and path.suffix.lower() == ".json"

    def load_many(
        self,
        input_ref: str | Path,
        *,
        business_domain_hint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[CanonicalIntake]:
        base_metadata = dict(metadata or {})
        path = Path(input_ref)

        if path.exists() and path.is_file():
            raw_json = path.read_text(encoding="utf-8")
            base_metadata.setdefault("file_name", path.name)
            base_metadata.setdefault("file_path", str(path))
            source_name = path.name
        else:
            raw_json = str(input_ref)
            source_name = "manual_json_input"

        parsed = json.loads(raw_json)
        payloads = parsed if isinstance(parsed, list) else [parsed]

        records: list[CanonicalIntake] = []
        for item_index, payload in enumerate(payloads, start=1):
            if not isinstance(payload, dict):
                raise ValueError("json payload items must be objects")

            normalized_content = _build_content(payload)
            item_metadata = dict(base_metadata)
            item_metadata["item_number"] = item_index
            item_metadata["source_json"] = payload

            records.append(
                CanonicalIntake(
                    request_id=generate_request_id(),
                    source_type=SourceType.JSON,
                    source_name=source_name,
                    business_domain_hint=business_domain_hint,
                    raw_content=normalized_content,
                    normalized_content=normalized_content,
                    metadata=item_metadata,
                    received_at=utc_now(),
                )
            )

        return records
