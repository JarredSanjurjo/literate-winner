"""LLM classification service."""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from src.config.settings import Settings
from src.models.enums import ProcessingStatus, Provider
from src.models.schemas import CanonicalIntake, ClassificationOutput
from src.services.prompt_manager import build_input_text, load_prompt
from src.utils.timestamps import utc_now


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class ClassificationService:
    """LLM-backed service for request classification."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self.client = client or self._build_client()

    def _build_client(self) -> OpenAI:
        if self.settings.provider != Provider.OPENAI.value:
            raise NotImplementedError(f"provider not implemented: {self.settings.provider}")
        return OpenAI(api_key=self.settings.openai_api_key)

    def classify(self, intake: CanonicalIntake, prompt_version: str) -> ClassificationOutput:
        """Classify one canonical intake record into a structured output."""

        instructions = load_prompt(prompt_version)
        response = self.client.responses.create(
            model=self.settings.model_name,
            instructions=instructions,
            input=build_input_text(intake),
        )
        payload = self._parse_response(response.output_text)
        payload.update(
            {
                "request_id": intake.request_id,
                "processed_at": utc_now(),
                "prompt_version": prompt_version,
                "status": ProcessingStatus.VALIDATED,
            }
        )
        return ClassificationOutput.model_validate(payload)

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """Parse a model response into a JSON dictionary."""

        if not response_text or not response_text.strip():
            raise ValueError("empty model response")

        cleaned = response_text.strip()
        fence_match = JSON_BLOCK_RE.search(cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        return json.loads(cleaned)
