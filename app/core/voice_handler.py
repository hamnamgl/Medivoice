import os
import re
import wave
import tempfile
import asyncio

import edge_tts
import sounddevice as sd
import numpy as np
import whisper

FFMPEG_DIR = r"D:\Projects\medivoice\ffmpeg-master-latest-win64-gpl-shared\bin"
if FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

LANG_VOICES = {
    "en":       "en-US-AriaNeural",
    "ur-roman": "ur-PK-AsadNeural",
    "ur":       "ur-PK-AsadNeural",
    "hi":       "hi-IN-SwaraNeural",
    "ha":       "en-NG-AbeoNeural",
    "sw":       "sw-KE-RafikiNeural",
    "fr":       "fr-FR-DeniseNeural",
    "bn":       "bn-BD-NabanitaNeural",
    "tl":       "fil-PH-BlessicaNeural",
    "am":       "am-ET-MekdesNeural",
    "es":       "es-ES-ElviraNeural",
    "pt":       "pt-BR-FranciscaNeural",
    "id":       "id-ID-GadisNeural",
    "so":       "en-US-AriaNeural",
    "ps":       "ur-PK-AsadNeural",
    "yo":       "en-NG-AbeoNeural",
    "ig":       "en-NG-AbeoNeural",
    "zu":       "en-ZA-LeahNeural",
    "ne":       "ne-NP-HemkalaNeural",
    "my":       "en-US-AriaNeural",
    "km":       "en-US-AriaNeural",
    "ti":       "en-US-AriaNeural",
}

_current_lang = "en"
_whisper_model = None
_tts_file = os.path.join(tempfile.gettempdir(), "medi_tts.mp3")


def set_tts_language(lang_code: str):
    global _current_lang
    _current_lang = lang_code


def get_tts_engine():
    return None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("tiny")
    return _whisper_model


def speak(text: str):
    """edge-tts se text ko voice mein convert karo"""
    try:
        clean = re.sub(r"[\[\]<>#*\-]", "", text).strip()
        if not clean:
            return
        voice = LANG_VOICES.get(_current_lang, "en-US-AriaNeural")

        async def _generate():
            communicate = edge_tts.Communicate(clean, voice)
            await communicate.save(_tts_file)

        asyncio.run(_generate())

        os.system(f'powershell -c "(New-Object Media.SoundPlayer).PlaySync()" 2>nul || '
                  f'start /wait wmplayer "{_tts_file}" 2>nul')

    except Exception as e:
        print(f"  [TTS: {e}]")


def listen(duration: int = 5, samplerate: int = 16000) -> str:
    """Offline STT via Whisper tiny"""
    try:
        print("  Listening... speak now", flush=True)
        audio_data = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio_data.tobytes())

        model = get_whisper_model()
        result = model.transcribe(tmp_path, fp16=False)
        os.unlink(tmp_path)

        text = result["text"].strip()
        lang = result.get("language", "?")
        if text:
            print(f"  Heard ({lang}): {text}")
        return text

    except Exception as e:
        print(f"  [Voice error: {e}]")
        return ""


def synthesize(text: str) -> dict:
    speak(text)
    return {"status": "spoken", "text": text}


def transcribe(audio_path: str) -> str:
    model = get_whisper_model()
    result = model.transcribe(audio_path, fp16=False)
    return result["text"].strip()


class VoiceHandler:
    def transcribe(self, audio_path: str | None = None) -> str:
        if audio_path:
            return transcribe(audio_path)
        return listen()

    def synthesize(self, text: str, language: str = "ur-PK") -> dict:
        result = synthesize(text)
        result["language"] = language
        return result
