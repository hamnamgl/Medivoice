from app.core.voice_handler import VoiceHandler


def test_voice_handler_synthesize_marks_status():
    result = VoiceHandler().synthesize("Hello", "en")
    assert result["status"] == "queued"
