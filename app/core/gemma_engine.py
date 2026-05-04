from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass
class GemmaResponse:
    text: str
    source: str = "stub"


SYSTEM_PROMPT = """You are MediVoice, an AI clinical decision support assistant
for community health workers (CHWs) in low-resource settings.

STRICT RULES:
1. Always respond in the SAME language the user speaks in
2. Use simple non-technical words only
3. Ask ONE question at a time
4. Never diagnose - only assess severity and recommend action
5. Always end with one of these: HOME CARE / REFER TO CLINIC / EMERGENCY
6. Be brief and clear - user may be semi-literate

You help CHWs assess: fever, cough, diarrhea, malnutrition, pregnancy danger signs, wounds."""


class GemmaEngine:
    """Small Ollama-backed chat wrapper for local clinical support flows."""

    def __init__(self, model_name: str = "gemma4:e4b", system_prompt: str = SYSTEM_PROMPT) -> None:
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.conversation_history: list[dict[str, str]] = []

    def _load_ollama(self) -> Any:
        try:
            return import_module("ollama")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Ollama Python package is not installed. Add it to the environment first."
            ) from exc

    def chat(self, user_message: str) -> GemmaResponse:
        cleaned = user_message.strip()
        if not cleaned:
            return GemmaResponse(text="Please share the patient's problem.", source="validation")

        self.conversation_history.append({"role": "user", "content": cleaned})
        ollama = self._load_ollama()
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
            ],
        )

        assistant_message = response["message"]["content"]
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        return GemmaResponse(text=assistant_message, source="ollama")

    def generate(self, prompt: str) -> GemmaResponse:
        return self.chat(prompt)

    def reset(self) -> None:
        self.conversation_history.clear()
