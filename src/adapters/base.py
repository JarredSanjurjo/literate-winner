"""Base interface for source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.models.enums import SourceType
from src.models.schemas import CanonicalIntake


class BaseAdapter(ABC):
    """Common interface for all supported source adapters."""

    source_type: SourceType

    @abstractmethod
    def can_handle(self, input_ref: str | Path) -> bool:
        """Return True when this adapter can handle the given input."""

    @abstractmethod
    def load_many(
        self,
        input_ref: str | Path,
        *,
        business_domain_hint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[CanonicalIntake]:
        """Load one or more canonical intake records from the source."""

    def load(
        self,
        input_ref: str | Path,
        *,
        business_domain_hint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CanonicalIntake:
        """Load a single intake record and reject multi-record sources."""

        records = self.load_many(
            input_ref,
            business_domain_hint=business_domain_hint,
            metadata=metadata,
        )
        if len(records) != 1:
            raise ValueError("expected exactly one record")
        return records[0]
