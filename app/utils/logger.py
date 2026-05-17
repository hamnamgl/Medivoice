from __future__ import annotations

from datetime import datetime


def build_visit_log(
    patient_name: str,
    summary: str,
    *,
    severity: str | None = None,
    language: str | None = None,
    tool_used: str | None = None,
    explanation: dict | None = None,
) -> dict:
    return {
        "patient_name": patient_name,
        "summary": summary,
        "severity": severity,
        "language": language,
        "tool_used": tool_used,
        "explanation": explanation or {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
