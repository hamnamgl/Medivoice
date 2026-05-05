from __future__ import annotations

import os
import tempfile
import wave

import numpy as np
import pyttsx3
import sounddevice as sd
import whisper

tts_engine = None
whisper_model = None


def get_tts_engine():
    global tts_engine
    if tts_engine is None:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty("rate", 150)
    return tts_engine


def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("small")
    return whisper_model


def speak(text: str) -> None:
    """Text ko voice mein convert karo."""
    current_engine = get_tts_engine()
    current_engine.say(text)
    current_engine.runAndWait()


def listen(duration: int = 6, samplerate: int = 16000) -> str:
    """Microphone se voice sun ke text return karo - fully offline."""
    print("Bol rahe hain... (listening)")

    audio_data = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype=np.int16,
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio_data.tobytes())

        result = get_whisper_model().transcribe(tmp_path)
        text = result["text"].strip()
        detected_lang = result.get("language", "unknown")
        print(f"Suna ({detected_lang}): {text}")
        return text
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


class VoiceHandler:
    def transcribe(self, audio_path: str | None = None) -> str:
        return listen()

    def synthesize(self, text: str, language: str = "ur-PK") -> dict:
        speak(text)
        return {"text": text, "language": language, "status": "spoken"}


if __name__ == "__main__":
    speak("MediVoice taiyaar hai. Apni baat karein.")
    result = listen()
    print(f"Result: {result}")
