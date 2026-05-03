from __future__ import annotations


class VoiceHandler:
    def transcribe(self, audio_path: str) -> str:
        return f"Transcription placeholder for {audio_path}"

    def synthesize(self, text: str, language: str = "en") -> dict:
        return {"text": text, "language": language, "status": "queued"}
