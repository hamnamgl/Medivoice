from __future__ import annotations

import re
import time
from dataclasses import dataclass
from importlib import import_module

import ollama

SYSTEM_PROMPT = """You are Medi, a warm caring AI health assistant for community health workers globally.

LANGUAGE: Always respond in exact same language user wrote in. Never switch.

PERSONALITY:
- Warm, empathetic, human: "Oh that sounds tough" / "I understand"
- Max 2 short sentences per response
- Never repeat questions already answered
- Never use numbered lists or scales

CLINICAL FLOW — STRICTLY 4 TURNS MAX:
Turn 1: Acknowledge + ask duration only
Turn 2: Ask ONE symptom (fever OR breathing OR eating — pick most relevant)
Turn 3: Ask ONE danger sign (unconscious? severe pain? bleeding?)
Turn 4: Give verdict + brief reasoning

VERDICT — use exactly one of:
HOME CARE: [reason in one line]
REFER TO CLINIC: [reason in one line]
EMERGENCY: [reason in one line]

RULES:
- Never ask rating scales (1-10)
- Never ask about food/sleep/stress unless directly relevant
- Never repeat what user already said
- If user frustrated, apologize briefly and move to verdict"""

FAST_MODEL = "gemma3:4b"
FULL_MODEL = "gemma4:e4b"

conversation_history = []


def _clean_response(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"Thinking Process:.*?\.\.\.done thinking\.", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"\*\*|\*|##|#", "", text).strip()
    return text


def _chat_with_options(client, **request):
    try:
        return client.chat(**request)
    except TypeError:
        request.pop("options", None)
        request.pop("stream", None)
        return client.chat(**request)


def chat(user_message: str) -> str:
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    print("Medi: ", end="", flush=True)
    full_response = ""

    for model in [FAST_MODEL, FULL_MODEL]:
        try:
            start = time.time()
            full_response = ""

            for chunk in ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *conversation_history
                ],
                options={"temperature": 0.1, "num_predict": 80},
                stream=True
            ):
                msg = chunk.get("message", {})
                token = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                if token:
                    print(token, end="", flush=True)
                    full_response += token
                if time.time() - start > 5 and len(full_response) > 10:
                    break

            print()
            if full_response.strip():
                break

        except Exception:
            continue

    full_response = _clean_response(full_response)

    conversation_history.append({
        "role": "assistant",
        "content": full_response
    })

    return full_response


def reset():
    conversation_history.clear()


@dataclass
class GemmaResponse:
    text: str
    source: str = "ollama"


class GemmaEngine:
    def __init__(self, model_name: str = FULL_MODEL, system_prompt: str = SYSTEM_PROMPT) -> None:
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.conversation_history = []

    def chat(self, user_message: str) -> GemmaResponse:
        client = import_module("ollama")
        cleaned = user_message.strip()
        if not cleaned:
            return GemmaResponse(text="Please share the patient's problem.", source="validation")

        self.conversation_history.append({"role": "user", "content": cleaned})
        assistant_message = ""

        for model in [FAST_MODEL, self.model_name]:
            try:
                response = _chat_with_options(
                    client,
                    model=model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        *self.conversation_history,
                    ],
                    options={"temperature": 0.1, "num_predict": 80},
                )
                assistant_message = _clean_response(response["message"]["content"])
                if assistant_message:
                    break
            except Exception:
                continue

        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        return GemmaResponse(text=assistant_message, source="ollama")

    def generate(self, prompt: str) -> GemmaResponse:
        return self.chat(prompt)

    def reset(self) -> None:
        self.conversation_history.clear()
