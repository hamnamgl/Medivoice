from __future__ import annotations


def call_registered_function(name: str, payload: dict | None = None) -> dict:
    return {
        "function": name,
        "payload": payload or {},
        "status": "not_implemented",
    }
