"""Deterministic business rules applied after validation."""

from __future__ import annotations

from src.models.enums import RequestType, ReviewStatus
from src.models.schemas import ClassificationOutput, ReviewDecision


def apply_rules(output: ClassificationOutput, threshold: float) -> ReviewDecision:
    """Apply deterministic rules that decide whether review is required."""

    reasons: list[str] = []

    if output.request_type == RequestType.UNKNOWN.value:
        reasons.append("request type is unknown")

    if output.confidence is not None and output.confidence < threshold:
        reasons.append(f"confidence below threshold ({output.confidence:.2f} < {threshold:.2f})")

    if len(output.summary.strip()) < 20:
        reasons.append("summary is too short")

    deadline = output.entities.get("deadline")
    if output.priority == "urgent" and not deadline:
        reasons.append("urgent request missing deadline")

    return ReviewDecision(
        review_required=bool(reasons),
        reasons=reasons,
        review_status=ReviewStatus.OPEN,
    )
