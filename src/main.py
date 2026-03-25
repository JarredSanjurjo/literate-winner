"""Main entry point for the classification pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.adapters.base import BaseAdapter
from src.adapters.csv_adapter import CsvAdapter
from src.adapters.email_text_adapter import EmailTextAdapter
from src.adapters.json_adapter import JsonAdapter
from src.adapters.text_adapter import TextAdapter
from src.config.settings import Settings
from src.models.enums import ProcessingStatus, SourceType
from src.models.schemas import CanonicalIntake, ProcessingResult
from src.services.business_rules import apply_rules
from src.services.classifier import ClassificationService
from src.services.logging_service import configure_logging
from src.services.preprocessing import normalize_intake
from src.services.review import ReviewService
from src.services.storage import StorageService
from src.services.validator import validate_output
from src.utils.ids import generate_run_id
from src.utils.timestamps import utc_now


def resolve_adapter(input_ref: str, source_type: str | None = None) -> BaseAdapter:
    """Resolve the appropriate adapter for a given input reference."""

    adapters: dict[str, BaseAdapter] = {
        SourceType.TEXT_FILE.value: TextAdapter(),
        SourceType.PASTED_TEXT.value: TextAdapter(),
        SourceType.CSV.value: CsvAdapter(),
        SourceType.JSON.value: JsonAdapter(),
        SourceType.EMAIL_TEXT.value: EmailTextAdapter(),
    }

    if source_type:
        if source_type not in adapters:
            raise ValueError(f"unsupported source type: {source_type}")
        return adapters[source_type]

    candidates = [EmailTextAdapter(), CsvAdapter(), JsonAdapter(), TextAdapter()]
    for adapter in candidates:
        if adapter.can_handle(input_ref):
            return adapter

    return TextAdapter()


def process_records(
    records: list[CanonicalIntake],
    *,
    settings: Settings,
    classifier_service: ClassificationService,
    storage_service: StorageService,
    review_service: ReviewService,
    logger,
) -> list[ProcessingResult]:
    """Process a collection of canonical intake records."""

    results: list[ProcessingResult] = []
    for intake in records:
        run_id = generate_run_id()
        started_at = utc_now()
        storage_service.save_request(intake)

        try:
            output = classifier_service.classify(intake, settings.prompt_version)
            validation_result = validate_output(output)

            if not validation_result.is_valid:
                review_decision = review_service.from_validation(validation_result)
                review_service.enqueue(intake.request_id, review_decision)
                storage_service.save_run_log(
                    run_id=run_id,
                    request_id=intake.request_id,
                    stage="validation",
                    status=ProcessingStatus.REVIEW_REQUIRED.value,
                    started_at=started_at,
                    completed_at=utc_now(),
                    prompt_version=settings.prompt_version,
                    error_message="; ".join(validation_result.errors),
                )
                results.append(
                    ProcessingResult(
                        request_id=intake.request_id,
                        status=ProcessingStatus.REVIEW_REQUIRED,
                        run_id=run_id,
                        validation_result=validation_result,
                        review_decision=review_decision,
                        message="validation failed and request routed to review",
                    )
                )
                continue

            review_decision = apply_rules(output, settings.confidence_threshold)
            if review_decision.review_required:
                output = output.model_copy(update={"status": ProcessingStatus.REVIEW_REQUIRED})
                review_service.enqueue(intake.request_id, review_decision)
                message = "classification completed and request routed to review"
            else:
                output = output.model_copy(update={"status": ProcessingStatus.VALIDATED})
                message = "classification completed successfully"

            storage_service.save_processed_output(output)
            storage_service.save_run_log(
                run_id=run_id,
                request_id=intake.request_id,
                stage="classification",
                status=str(output.status),
                started_at=started_at,
                completed_at=utc_now(),
                prompt_version=settings.prompt_version,
            )
            results.append(
                ProcessingResult(
                    request_id=intake.request_id,
                    status=output.status,
                    run_id=run_id,
                    validation_result=validation_result,
                    review_decision=review_decision,
                    message=message,
                )
            )
        except Exception as exc:
            logger.exception("Processing failed for request %s", intake.request_id)
            review_service.enqueue_system_failure(intake.request_id, str(exc))
            storage_service.save_run_log(
                run_id=run_id,
                request_id=intake.request_id,
                stage="classification",
                status=ProcessingStatus.FAILED.value,
                started_at=started_at,
                completed_at=utc_now(),
                prompt_version=settings.prompt_version,
                error_message=str(exc),
            )
            results.append(
                ProcessingResult(
                    request_id=intake.request_id,
                    status=ProcessingStatus.FAILED,
                    run_id=run_id,
                    message=str(exc),
                )
            )

    return results


def process_input(
    input_ref: str,
    *,
    source_type: str | None = None,
    business_domain_hint: str | None = None,
    settings: Settings | None = None,
) -> list[ProcessingResult]:
    """Run the full pipeline for a single input reference."""

    settings = settings or Settings.from_env()
    logger = configure_logging(settings.log_level)
    storage_service = StorageService(settings)
    storage_service.init_db()
    review_service = ReviewService(storage_service)
    classifier_service = ClassificationService(settings)

    adapter = resolve_adapter(input_ref, source_type=source_type)
    records = adapter.load_many(input_ref, business_domain_hint=business_domain_hint)
    normalized_records = [normalize_intake(record) for record in records]
    return process_records(
        normalized_records,
        settings=settings,
        classifier_service=classifier_service,
        storage_service=storage_service,
        review_service=review_service,
        logger=logger,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for the pipeline."""

    parser = argparse.ArgumentParser(description="Run the AI workflow classifier.")
    parser.add_argument("input_ref", help="File path or raw text to process")
    parser.add_argument("--source-type", dest="source_type", help="Explicit source type override")
    parser.add_argument("--business-domain", dest="business_domain_hint", help="Optional business domain hint")
    return parser


def main() -> None:
    """Run the application pipeline from the command line."""

    parser = build_parser()
    args = parser.parse_args()
    results = process_input(
        args.input_ref,
        source_type=args.source_type,
        business_domain_hint=args.business_domain_hint,
    )
    for result in results:
        print(f"{result.request_id}: {result.status}")


if __name__ == "__main__":
    main()
