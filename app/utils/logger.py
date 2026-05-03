from __future__ import annotations

from datetime import datetime


def build_visit_log(patient_name: str, summary: str) -> dict:
    return {
        "patient_name": patient_name,
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
