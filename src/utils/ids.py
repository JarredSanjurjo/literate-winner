"""Identifier generation helpers."""

from __future__ import annotations

from uuid import uuid4


def generate_request_id(prefix: str = "REQ") -> str:
    """Generate a readable unique request identifier."""

    return f"{prefix}-{uuid4().hex[:12].upper()}"


def generate_run_id(prefix: str = "RUN") -> str:
    """Generate a readable unique run identifier."""

    return f"{prefix}-{uuid4().hex[:12].upper()}"
