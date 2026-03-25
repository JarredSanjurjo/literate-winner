import logging
from datetime import datetime, timezone

from src.config.settings import Settings
from src.main import process_records
from src.models.enums import Priority, ProcessingStatus, RequestType, SourceType
from src.models.schemas import CanonicalIntake, ClassificationOutput
from src.services.review import ReviewService
from src.services.storage import StorageService


class FakeClassifierService:
    def classify(self, intake, prompt_version):
        return ClassificationOutput(
            request_id=intake.request_id,
            request_type=RequestType.OPERATIONAL_REQUEST,
            business_domain="hospitality",
            priority=Priority.HIGH,
            summary="Operations team requests a booking update before Friday.",
            entities={"deadline": "Friday"},
            risk_flags=[],
            recommended_next_action="Review booking allocation and confirm changes.",
            confidence=None,
            status=ProcessingStatus.VALIDATED,
            processed_at=datetime.now(timezone.utc),
            prompt_version=prompt_version,
        )


def test_pipeline_process_records_end_to_end(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'app.db'}")
    storage = StorageService(settings)
    storage.init_db()
    review = ReviewService(storage)
    logger = logging.getLogger("test")

    intake = CanonicalIntake(
        request_id="REQ-123",
        source_type=SourceType.PASTED_TEXT,
        source_name="manual_input",
        raw_content="Please update the booking allocation before Friday.",
        normalized_content="Please update the booking allocation before Friday.",
        metadata={},
        received_at=datetime.now(timezone.utc),
    )

    results = process_records(
        [intake],
        settings=settings,
        classifier_service=FakeClassifierService(),
        storage_service=storage,
        review_service=review,
        logger=logger,
    )

    assert len(results) == 1
    assert results[0].status == ProcessingStatus.VALIDATED.value
    assert len(storage.list_processed_records()) == 1
