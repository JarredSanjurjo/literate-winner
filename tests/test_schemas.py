from datetime import datetime, timezone

from src.models.enums import Priority, ProcessingStatus, RequestType, SourceType
from src.models.schemas import CanonicalIntake, ClassificationOutput


def test_canonical_intake_accepts_valid_payload() -> None:
    intake = CanonicalIntake(
        request_id="REQ-123",
        source_type=SourceType.PASTED_TEXT,
        source_name="manual_input",
        raw_content="Example request",
        normalized_content="Example request",
        received_at=datetime.now(timezone.utc),
    )

    assert intake.request_id == "REQ-123"
    assert intake.source_type == SourceType.PASTED_TEXT.value


def test_classification_output_accepts_optional_confidence() -> None:
    output = ClassificationOutput(
        request_id="REQ-123",
        request_type=RequestType.INFORMATION_REQUEST,
        business_domain="operations",
        priority=Priority.MEDIUM,
        summary="Customer asks for implementation status.",
        entities={},
        risk_flags=[],
        recommended_next_action="Prepare and send a status summary.",
        confidence=None,
        status=ProcessingStatus.VALIDATED,
        processed_at=datetime.now(timezone.utc),
        prompt_version="classification_v1",
    )

    assert output.confidence is None
