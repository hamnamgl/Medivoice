from app.core.language_detector import detect_language


def test_detect_language_returns_roman_urdu_for_common_tokens():
    assert detect_language("Bacha ko bukhar hai") == "Roman Urdu"


def test_detect_language_returns_urdu_for_script_text():
    assert detect_language("بچے کو بخار ہے") == "Urdu"


def test_detect_language_returns_hausa_for_common_tokens():
    assert detect_language("Yaro na da zazzabi") == "Hausa"
