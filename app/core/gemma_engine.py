from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GemmaResponse:
    text: str
    source: str = "stub"


class GemmaEngine:
    """Minimal local-model interface placeholder."""

    def __init__(self, model_name: str = "gemma3") -> None:
        self.model_name = model_name

    def generate(self, prompt: str) -> GemmaResponse:
        cleaned = prompt.strip() or "No prompt provided."
        return GemmaResponse(
            text=f"[{self.model_name}] Placeholder response for: {cleaned}",
            source="local-stub",
        )
