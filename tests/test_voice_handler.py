import app.core.voice_handler as voice_module
from app.core.voice_handler import VoiceHandler


def test_voice_handler_synthesize_marks_status(monkeypatch):
    monkeypatch.setattr(voice_module, "get_tts_engine", lambda: type("DummyEngine", (), {"say": lambda self, text: None, "runAndWait": lambda self: None})())
    monkeypatch.setattr(voice_module, "speak", lambda text: None)
    result = VoiceHandler().synthesize("Hello", "en")
    assert result["status"] == "spoken"


def test_voice_handler_transcribe_uses_listen(monkeypatch):
    monkeypatch.setattr(voice_module, "listen", lambda duration=5, samplerate=16000: "sample text")
    result = VoiceHandler().transcribe()
    assert result == "sample text"
