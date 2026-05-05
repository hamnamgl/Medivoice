from app.core.function_caller import call_registered_function


def test_call_registered_function_runs_triage():
    result = call_registered_function("assess_severity", {"text": "high fever for 3 days"})
    assert result["status"] == "success"
    assert result["result"]["level"] == "REFER"


def test_call_registered_function_handles_unknown_name():
    result = call_registered_function("missing_function", {})
    assert result["status"] == "unknown_function"
