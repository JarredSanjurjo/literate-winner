"""Adapter for CSV-based request ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.adapters.base import BaseAdapter
from src.models.enums import SourceType
from src.models.schemas import CanonicalIntake
from src.utils.ids import generate_request_id
from src.utils.timestamps import utc_now


def _row_to_text(row: dict[str, Any]) -> str:
    """Render a CSV row into a readable text block for classification."""

    lines: list[str] = []
    for key, value in row.items():
        if pd.isna(value):
            continue
        text = str(value).strip()
        if not text:
            continue
        lines.append(f"{key}: {text}")
    return "\n".join(lines)


class CsvAdapter(BaseAdapter):
    """Adapter for CSV rows, treating each row as a separate request."""

    source_type = SourceType.CSV

    def can_handle(self, input_ref: str | Path) -> bool:
        path = Path(input_ref)
        return path.exists() and path.is_file() and path.suffix.lower() == ".csv"

    def load_many(
        self,
        input_ref: str | Path,
        *,
        business_domain_hint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[CanonicalIntake]:
        path = Path(input_ref)
        frame = pd.read_csv(path)
        base_metadata = dict(metadata or {})
        base_metadata.setdefault("file_name", path.name)
        base_metadata.setdefault("file_path", str(path))

        records: list[CanonicalIntake] = []
        for row_index, (_, row) in enumerate(frame.iterrows(), start=1):
            row_dict = row.to_dict()
            normalized_content = _row_to_text(row_dict)
            record_metadata = dict(base_metadata)
            record_metadata["row_number"] = row_index
            record_metadata["row_data"] = {
                key: (None if pd.isna(value) else str(value))
                for key, value in row_dict.items()
            }
            records.append(
                CanonicalIntake(
                    request_id=generate_request_id(),
                    source_type=SourceType.CSV,
                    source_name=path.name,
                    business_domain_hint=business_domain_hint,
                    raw_content=normalized_content,
                    normalized_content=normalized_content,
                    metadata=record_metadata,
                    received_at=utc_now(),
                )
            )

        return records
