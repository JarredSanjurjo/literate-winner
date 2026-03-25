"""Prompt loading and message construction."""

from __future__ import annotations

from pathlib import Path

from src.models.schemas import CanonicalIntake


PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(version: str) -> str:
    """Load a prompt asset by version name."""

    prompt_path = PROMPTS_DIR / f"{version}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"prompt version not found: {version}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_input_text(intake: CanonicalIntake) -> str:
    """Build the request payload sent to the model."""

    lines = [
        f"request_id: {intake.request_id}",
        f"source_type: {intake.source_type}",
        f"source_name: {intake.source_name}",
    ]
    if intake.business_domain_hint:
        lines.append(f"business_domain_hint: {intake.business_domain_hint}")

    if intake.metadata:
        lines.append(f"metadata: {intake.metadata}")

    lines.extend(
        [
            "",
            "request_content:",
            intake.normalized_content,
        ]
    )
    return "\n".join(lines).strip()


def build_messages(intake: CanonicalIntake, prompt_version: str) -> list[dict[str, str]]:
    """Build a simple chat-style message payload for the classifier."""

    return [
        {"role": "system", "content": load_prompt(prompt_version)},
        {"role": "user", "content": build_input_text(intake)},
    ]
