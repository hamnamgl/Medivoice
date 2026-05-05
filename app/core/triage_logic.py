from __future__ import annotations

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
]


def assess_severity(text: str) -> dict:
    """
    CHW ki baat sun ke severity assess karo.
    Returns: {level, action, message}
    """
    text_lower = text.lower()

    for keyword in EMERGENCY_KEYWORDS:
        if keyword.lower() in text_lower:
            return {
                "level": "EMERGENCY",
                "action": "FORAN HOSPITAL",
                "message": "Yeh emergency hai. Foran hospital le jayen. Deri mat karein.",
            }

    for keyword in REFER_KEYWORDS:
        if keyword.lower() in text_lower:
            return {
                "level": "REFER",
                "action": "CLINIC REFER KAREIN",
                "message": "Is case mein clinic jana zaroori hai. Aaj hi le jayen.",
            }

    return {
        "level": "HOME CARE",
        "action": "GHAR PE DEKHBHAL",
        "message": "Abhi ghar pe dekhbhal karein. Agar haalt kharab ho toh clinic jayen.",
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
