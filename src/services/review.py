"""Review queue routing and management."""

from __future__ import annotations

from src.models.schemas import ReviewDecision, ValidationResult
from src.services.storage import StorageService


class ReviewService:
    """Create and persist review queue items."""

    def __init__(self, storage_service: StorageService) -> None:
        self.storage_service = storage_service

    def from_validation(self, validation_result: ValidationResult) -> ReviewDecision:
        """Create a review decision from validation errors."""

        reasons = validation_result.errors or ["validation failed"]
        return ReviewDecision(review_required=True, reasons=reasons)

    def enqueue(self, request_id: str, review_decision: ReviewDecision) -> None:
        """Persist all review reasons for a request."""

        for reason in review_decision.reasons:
            self.storage_service.enqueue_review(
                request_id=request_id,
                reason=reason,
                review_status=str(review_decision.review_status),
            )

    def enqueue_system_failure(self, request_id: str, error_message: str) -> None:
        """Create a review queue item for a pipeline failure."""

        self.storage_service.enqueue_review(request_id=request_id, reason=f"system failure: {error_message}")
