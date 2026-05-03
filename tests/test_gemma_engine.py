from app.core.gemma_engine import GemmaEngine


def test_gemma_engine_returns_placeholder_text():
    response = GemmaEngine().generate("Patient has fever")
    assert "Patient has fever" in response.text
