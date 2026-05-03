from app.core.language_detector import detect_language


def test_detect_language_returns_urdu_for_common_tokens():
    assert detect_language("Bacha ko bukhar hai") == "Urdu"
