from __future__ import annotations

import base64
from pathlib import Path

import ollama


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

    prompt = question or (
        "Is image mein kya dikhai de raha hai? "
        "Agar yeh koi wound, rash, ya medical condition hai toh "
        "batao kya action lena chahiye. Simple words mein jawab do."
    )

    response = ollama.chat(
        model="gemma4:e4b",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_data],
            }
        ],
    )

    return response["message"]["content"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        result = analyze_image(sys.argv[1])
        print(result)
    else:
        print("Usage: python image_analyzer.py <image_path>")
