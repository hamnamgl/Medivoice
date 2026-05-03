from __future__ import annotations


def detect_language(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["bukhar", "bacha", "dard"]):
        return "Urdu"
    if any(token in lowered for token in ["zazzabi", "ciwo", "jariri"]):
        return "Hausa"
    if any(token in lowered for token in ["homa", "mtoto", "kidonda"]):
        return "Swahili"
    return "English"
