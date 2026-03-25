"""Schema validation service."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from src.models.schemas import ClassificationOutput, ValidationResult


def validate_output(output: ClassificationOutput) -> ValidationResult:
    """Validate a classification output after schema parsing."""

    errors: list[str] = []
    warnings: list[str] = []

    if not output.summary.strip():
        errors.append("summary must not be blank")

    if not output.recommended_next_action.strip():
        errors.append("recommended_next_action must not be blank")

    if output.confidence is None:
        warnings.append("confidence not provided")

    if not output.entities:
        warnings.append("no entities extracted")

    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)


def validate_output_payload(payload: dict[str, Any]) -> tuple[ClassificationOutput | None, ValidationResult]:
    """Validate a raw payload and return the parsed output when valid."""

    try:
        output = ClassificationOutput.model_validate(payload)
    except ValidationError as exc:
        return None, ValidationResult(
            is_valid=False,
            errors=[error["msg"] for error in exc.errors()],
            warnings=[],
        )

    return output, validate_output(output)
