"""Preprocessing utilities for canonical intake normalization."""

from __future__ import annotations

import re

from src.models.schemas import CanonicalIntake


WHITESPACE_RE = re.compile(r"[ \t]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def clean_text(raw_text: str) -> str:
    """Normalize whitespace while preserving paragraph structure."""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def build_normalized_content(intake: CanonicalIntake) -> str:
    """Build cleaned content for downstream processing."""

    return clean_text(intake.raw_content)


def normalize_intake(intake: CanonicalIntake) -> CanonicalIntake:
    """Return a copy of the intake with normalized content updated."""

    return intake.model_copy(update={"normalized_content": build_normalized_content(intake)})
