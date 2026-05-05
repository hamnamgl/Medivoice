from app.core.triage_logic import assess_severity, run_basic_triage


def test_triage_detects_emergency_keywords():
    result = assess_severity("The patient is unconscious and bleeding.")
    assert result["level"] == "EMERGENCY"


def test_triage_detects_refer_keywords():
    result = assess_severity("bachche ko tez bukhar hai 3 din se")
    assert result["level"] == "REFER"


def test_run_basic_triage_maps_assessment_shape():
    result = run_basic_triage("thodi si khansi hai")
    assert result["priority"] == "HOME CARE"
