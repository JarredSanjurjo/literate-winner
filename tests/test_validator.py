from datetime import datetime, timezone

from src.models.enums import Priority, ProcessingStatus, RequestType
from src.models.schemas import ClassificationOutput
from src.services.validator import validate_output


def test_validator_allows_optional_confidence_but_warns() -> None:
    output = ClassificationOutput(
        request_id="REQ-123",
        request_type=RequestType.OPERATIONAL_REQUEST,
        business_domain="hospitality",
        priority=Priority.HIGH,
        summary="Operations team requests a room allocation update.",
        entities={},
        risk_flags=[],
        recommended_next_action="Review room allocation and confirm changes.",
        confidence=None,
        status=ProcessingStatus.VALIDATED,
        processed_at=datetime.now(timezone.utc),
        prompt_version="classification_v1",
    )

    result = validate_output(output)

    assert result.is_valid is True
    assert "confidence not provided" in result.warnings
