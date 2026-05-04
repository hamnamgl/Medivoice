import app.core.gemma_engine as gemma_module
from app.core.gemma_engine import GemmaEngine


class DummyOllama:
    def chat(self, *, model, messages):
        return {"message": {"content": f"{model}: {messages[-1]['content']} -> REFER TO CLINIC"}}


def test_gemma_engine_returns_ollama_response(monkeypatch):
    monkeypatch.setattr(gemma_module, "import_module", lambda name: DummyOllama())
    engine = GemmaEngine()

    response = engine.generate("Patient has fever")

    assert response.source == "ollama"
    assert "Patient has fever" in response.text


def test_gemma_engine_reset_clears_history(monkeypatch):
    monkeypatch.setattr(gemma_module, "import_module", lambda name: DummyOllama())
    engine = GemmaEngine()
    engine.chat("Short cough")

    engine.reset()

    assert engine.conversation_history == []
