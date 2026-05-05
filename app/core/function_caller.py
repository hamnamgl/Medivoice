from __future__ import annotations

from app.core.image_analyzer import analyze_image
from app.core.triage_logic import assess_severity


FUNCTION_REGISTRY = {
    "assess_severity": assess_severity,
    "analyze_image": analyze_image,
}


def call_registered_function(name: str, payload: dict | None = None) -> dict:
    request_payload = payload or {}
    function = FUNCTION_REGISTRY.get(name)
    if function is None:
        return {
            "function": name,
            "payload": request_payload,
            "status": "unknown_function",
            "error": f"Function '{name}' registered nahi hai.",
        }

    try:
        result = function(**request_payload)
    except TypeError as exc:
        return {
            "function": name,
            "payload": request_payload,
            "status": "invalid_payload",
            "error": str(exc),
        }

    return {
        "function": name,
        "payload": request_payload,
        "status": "success",
        "result": result,
    }
