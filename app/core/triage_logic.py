from __future__ import annotations


RED_FLAG_KEYWORDS = {"bleeding", "seizure", "unconscious", "severe pain", "difficulty breathing"}
URGENT_KEYWORDS = {"fever", "dehydration", "vomiting", "diarrhea", "wound"}


def run_basic_triage(complaint: str) -> dict:
    normalized = complaint.lower()

    if any(keyword in normalized for keyword in RED_FLAG_KEYWORDS):
        return {
            "priority": "Emergency",
            "summary": "Red-flag symptoms detected. Immediate referral is advised.",
            "actions": [
                "Stabilize the patient if possible.",
                "Arrange urgent transport to the nearest facility.",
                "Escalate to supervising clinician immediately.",
            ],
        }

    if any(keyword in normalized for keyword in URGENT_KEYWORDS):
        return {
            "priority": "Urgent",
            "summary": "Symptoms need same-day review and monitoring.",
            "actions": [
                "Record vitals and symptom duration.",
                "Review protocol checklist for the presenting complaint.",
                "Refer for same-day facility review if symptoms worsen.",
            ],
        }

    return {
        "priority": "Routine",
        "summary": "No urgent keywords found in the starter ruleset.",
        "actions": [
            "Continue routine assessment.",
            "Document history and home-care advice.",
            "Schedule follow-up if symptoms persist.",
        ],
    }
