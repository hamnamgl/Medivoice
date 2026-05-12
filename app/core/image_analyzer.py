from __future__ import annotations

import base64
from pathlib import Path

import ollama

from app.core.language_detector import detect_language

IMAGE_MODELS = ["gemma4:e4b", "gemma3:4b"]


def _build_image_prompt(question: str | None, language: str) -> str:
    base_prompts = {
        "English": (
            "You are MediVoice image triage assistant. "
            "Respond in the same language as the user. "
            "Describe only visible findings, then give exactly one verdict: "
            "HOME CARE, REFER TO CLINIC, or EMERGENCY. "
            "Format: Visible signs: ... Action: ... "
            "Do not claim a diagnosis with certainty."
        ),
        "Roman Urdu": (
            "Aap MediVoice image triage assistant hain. "
            "Roman Urdu mein jawab dein. "
            "Sirf jo nazar aa raha hai woh batayein, phir aik action dein: "
            "HOME CARE, REFER TO CLINIC, ya EMERGENCY. "
            "Format: Nazar aane wali baat: ... Action: ..."
        ),
        "Urdu": (
            "آپ MediVoice image triage assistant ہیں۔ "
            "جو زبان صارف نے استعمال کی ہے اسی میں جواب دیں۔ "
            "صرف نظر آنے والی علامات بیان کریں، پھر ایک action دیں: "
            "HOME CARE، REFER TO CLINIC، یا EMERGENCY۔"
        ),
        "Hausa": (
            "Kai ne MediVoice mai taimakon tantance hoto. "
            "Amsa da Hausa. "
            "Fadi abin da ake gani kawai, sannan ka bada hukunci daya: "
            "HOME CARE, REFER TO CLINIC, ko EMERGENCY."
        ),
        "Swahili": (
            "Wewe ni msaidizi wa MediVoice wa kuchambua picha. "
            "Jibu kwa Kiswahili. "
            "Eleza kinachoonekana tu, kisha toa uamuzi mmoja: "
            "HOME CARE, REFER TO CLINIC, au EMERGENCY."
        ),
    }
    base = base_prompts.get(language, base_prompts["English"])
    if question:
        return f"{base} User question: {question}"
    return (
        f"{base} Check for wound, rash, swelling, bleeding, burn, infection signs, "
        "and whether urgent referral is needed."
    )


def analyze_image(image_path: str, question: str | None = None) -> str:
    """
    Image ko Gemma 4 vision se analyze karo.
    image_path: local file path
    question: CHW ka sawal image ke baare mein
    """
    file_path = Path(image_path)
    if not file_path.exists():
        return "Image file nahi mili"

    with file_path.open("rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    language = detect_language(question or "")
    prompt = _build_image_prompt(question, language)

    for model in IMAGE_MODELS:
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_data],
                    }
                ],
            )
            return response["message"]["content"]
        except Exception:
            continue

    return "Could not analyze image right now. Please try again."


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        result = analyze_image(sys.argv[1])
        print(result)
    else:
        print("Usage: python image_analyzer.py <image_path>")
