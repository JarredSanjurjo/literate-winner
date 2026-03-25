from datetime import datetime, timezone

from src.config.settings import Settings
from src.models.enums import Priority, ProcessingStatus, RequestType, SourceType
from src.models.schemas import CanonicalIntake, ClassificationOutput
from src.services.storage import StorageService


def test_storage_saves_requests_outputs_and_reviews(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'app.db'}")
    storage = StorageService(settings)
    storage.init_db()

    intake = CanonicalIntake(
        request_id="REQ-123",
        source_type=SourceType.PASTED_TEXT,
        source_name="manual_input",
        raw_content="Please update the schedule.",
        normalized_content="Please update the schedule.",
        metadata={"submitted_by": "test"},
        received_at=datetime.now(timezone.utc),
    )
    output = ClassificationOutput(
        request_id="REQ-123",
        request_type=RequestType.SCHEDULE_CHANGE,
        business_domain="architecture",
        priority=Priority.HIGH,
        summary="Client requests a schedule change.",
        entities={"deadline": "Friday"},
        risk_flags=[],
        recommended_next_action="Update the plan and confirm timing.",
        confidence=0.9,
        status=ProcessingStatus.VALIDATED,
        processed_at=datetime.now(timezone.utc),
        prompt_version="classification_v1",
    )

    storage.save_request(intake)
    storage.save_processed_output(output)
    storage.enqueue_review(request_id="REQ-123", reason="manual check")

    assert len(storage.list_processed_records()) == 1
    assert len(storage.list_review_queue()) == 1
