from datetime import datetime, timezone

from src.models.enums import Priority, ProcessingStatus, RequestType
from src.models.schemas import ClassificationOutput
from src.services.business_rules import apply_rules


def test_unknown_request_routes_to_review() -> None:
    output = ClassificationOutput(
        request_id="REQ-123",
        request_type=RequestType.UNKNOWN,
        business_domain="operations",
        priority=Priority.MEDIUM,
        summary="Unclear request content that needs review.",
        entities={},
        risk_flags=[],
        recommended_next_action="Review manually.",
        confidence=None,
        status=ProcessingStatus.VALIDATED,
        processed_at=datetime.now(timezone.utc),
        prompt_version="classification_v1",
    )

    decision = apply_rules(output, threshold=0.75)

    assert decision.review_required is True
    assert "request type is unknown" in decision.reasons


def test_low_confidence_routes_to_review() -> None:
    output = ClassificationOutput(
        request_id="REQ-123",
        request_type=RequestType.OPERATIONAL_REQUEST,
        business_domain="operations",
        priority=Priority.HIGH,
        summary="Need an urgent workflow update before the deadline.",
        entities={"deadline": "Friday"},
        risk_flags=[],
        recommended_next_action="Escalate to operations lead.",
        confidence=0.4,
        status=ProcessingStatus.VALIDATED,
        processed_at=datetime.now(timezone.utc),
        prompt_version="classification_v1",
    )

    decision = apply_rules(output, threshold=0.75)

    assert decision.review_required is True
