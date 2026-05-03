from app.core.triage_logic import run_basic_triage


def test_triage_detects_emergency_keywords():
    result = run_basic_triage("The patient is unconscious and bleeding.")
    assert result["priority"] == "Emergency"
