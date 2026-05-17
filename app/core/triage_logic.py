from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "protocols"
GENERIC_TRIAGE = json.loads((DATA_DIR / "generic_triage.json").read_text(encoding="utf-8"))

EMERGENCY_KEYWORDS = [
    "bेहosh",
    "बेहोश",
    "بیہوش",
    "خون",
    "سانس نہیں",
    "دورہ",
    "unconscious",
    "not breathing",
    "heavy bleeding",
    "convulsion",
    "suma",
    "jini mai yawa",
    "kupoteza fahamu",
    "damu nyingi",
]

REFER_KEYWORDS = [
    "tez bukhar",
    "تیز بخار",
    "high fever",
    "3 din",
    "teen din",
    "3 days",
    "kha nahi raha",
    "نہیں کھا رہا",
    "not eating",
    "ulti",
    "اُلٹی",
    "vomiting",
    "dast",
    "دست",
    "diarrhea",
    "pregnancy",
    "حمل",
    "hamal",
    "difficulty breathing",
    "fast breathing",
    "chest pain",
    "week",
    "1 week",
    "7 days",
]


def _contains_any(text: str, items: list[str]) -> bool:
    text_lower = text.lower()
    return any(item.lower() in text_lower for item in items)


def _has_long_duration(text: str) -> bool:
    text_lower = text.lower()
    patterns = [
        r"\b[4-9]\s*days?\b",
        r"\b[1-9]\d\s*days?\b",
        r"\b1\s*week\b",
        r"\ba week\b",
        r"\bhaft",
        r"\bhafte\b",
        r"\bweek\b",
    ]
    return any(re.search(pattern, text_lower) for pattern in patterns)


def assess_severity(text: str) -> dict:
    """
    CHW ki baat sun ke severity assess karo.
    Returns: {level, action, message}
    """
    text_lower = text.lower()
    emergency_signs = GENERIC_TRIAGE.get("emergency_signs", [])
    refer_signs = GENERIC_TRIAGE.get("refer_signs", [])

    for keyword in EMERGENCY_KEYWORDS:
        if keyword.lower() in text_lower:
            return {
                "level": "EMERGENCY",
                "action": "FORAN HOSPITAL",
                "message": "Yeh emergency hai. Foran hospital le jayen. Deri mat karein.",
                "matched_rules": [keyword],
                "rule_source": "keyword_emergency",
            }

    if _contains_any(text_lower, emergency_signs):
        matches = [item for item in emergency_signs if item.lower() in text_lower]
        return {
            "level": "EMERGENCY",
            "action": "FORAN HOSPITAL",
            "message": "Danger signs mojood hain. Foran hospital ya emergency care ki zarurat hai.",
            "matched_rules": matches,
            "rule_source": "generic_protocol_emergency",
        }

    for keyword in REFER_KEYWORDS:
        if keyword.lower() in text_lower:
            return {
                "level": "REFER",
                "action": "CLINIC REFER KAREIN",
                "message": "Is case mein clinic jana zaroori hai. Aaj hi le jayen.",
                "matched_rules": [keyword],
                "rule_source": "keyword_refer",
            }

    if _contains_any(text_lower, refer_signs) or _has_long_duration(text_lower):
        matches = [item for item in refer_signs if item.lower() in text_lower]
        if _has_long_duration(text_lower):
            matches.append("long_duration")
        return {
            "level": "REFER",
            "action": "CLINIC REFER KAREIN",
            "message": "Yeh case protocol ke mutabiq clinic review mangta hai. Aaj hi dikhayen.",
            "matched_rules": matches,
            "rule_source": "generic_protocol_refer",
        }

    return {
        "level": "HOME CARE",
        "action": "GHAR PE DEKHBHAL",
        "message": "Abhi ghar pe dekhbhal karein. Agar haalt kharab ho toh clinic jayen.",
        "matched_rules": [],
        "rule_source": "default_home_care",
    }


def run_basic_triage(complaint: str) -> dict:
    result = assess_severity(complaint)
    return {
        "priority": result["level"],
        "summary": result["message"],
        "actions": [result["action"]],
    }


if __name__ == "__main__":
    tests = [
        "bachche ko tez bukhar hai 3 din se",
        "mareez behosh ho gaya",
        "thodi si khansi hai",
    ]
    for test_input in tests:
        result = assess_severity(test_input)
        print(f"Input: {test_input}")
        print(f"Result: {result}\n")
