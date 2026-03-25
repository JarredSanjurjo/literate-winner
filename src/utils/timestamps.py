"""Timestamp helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""

    return utc_now().isoformat()
