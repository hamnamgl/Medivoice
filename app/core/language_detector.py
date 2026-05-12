from __future__ import annotations

import re

def detect_language(text: str) -> str:
    lowered = text.lower()
    if re.search(r"[\u0600-\u06FF]", text):
        return "Urdu"
    if any(token in lowered for token in ["bukhar", "bacha", "mareez", "dard", "behosh", "ulti", "dast"]):
        return "Roman Urdu"
    if any(token in lowered for token in ["zazzabi", "ciwo", "jariri"]):
        return "Hausa"
    if any(token in lowered for token in ["homa", "mtoto", "kidonda"]):
        return "Swahili"
    if re.search(r"[\u0900-\u097F]", text):
        return "Hindi"
    return "English"
