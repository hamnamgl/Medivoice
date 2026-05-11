from __future__ import annotations

import json

import ollama

from app.core.triage_logic import assess_severity

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "assess_triage",
            "description": (
                "Assess the severity of a patient's symptoms and recommend "
                "an action: HOME CARE, REFER TO CLINIC, or EMERGENCY."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptom_text": {
                        "type": "string",
                        "description": "The symptom description from the CHW in any language.",
                    }
                },
                "required": ["symptom_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_referral",
            "description": "Look up the nearest health facility for a given region or country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region or country name e.g. 'punjab', 'lagos', 'nairobi'",
                    }
                },
                "required": ["region"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_drug_dosage",
            "description": "Get the correct dosage for a common essential medicine by patient weight.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "Name of the drug e.g. paracetamol, amoxicillin, ORS",
                    },
                    "weight_kg": {
                        "type": "number",
                        "description": "Patient weight in kilograms",
                    },
                },
                "required": ["drug_name", "weight_kg"],
            },
        },
    },
]

REFERRAL_DB = {
    "punjab": "District Headquarters Hospital, Rawalpindi - 0.4 km from Saddar",
    "sindh": "Civil Hospital Karachi - Karachi City Centre",
    "lagos": "Lagos Island General Hospital - Lagos Island",
    "nairobi": "Kenyatta National Hospital - Upper Hill, Nairobi",
    "addis": "Black Lion Hospital - Addis Ababa",
    "dhaka": "Dhaka Medical College Hospital - Bakshi Bazar",
    "default": "Nearest government health facility - ask local CHW supervisor",
}

DRUG_DB = {
    "paracetamol": lambda kg: f"{round(kg * 15)} mg every 6 hours (max 4 doses/day)",
    "amoxicillin": lambda kg: f"{round(kg * 25)} mg every 8 hours for 5 days",
    "ors": lambda kg: "200ml after every loose stool (no weight restriction)",
    "zinc": lambda kg: "20mg once daily for 10 days (children >6 months)",
    "ibuprofen": lambda kg: f"{round(kg * 10)} mg every 8 hours with food",
}

SYSTEM_PROMPT = """You are Medi, a warm caring AI health assistant for community health workers globally.

LANGUAGE: Always respond in exact same language user wrote in. Never switch.

PERSONALITY:
- Warm, empathetic: "Oh that sounds tough"
- Max 2 short sentences
- Never repeat questions already answered

CLINICAL FLOW — 4 TURNS MAX:
Turn 1: Acknowledge + duration
Turn 2: ONE symptom question
Turn 3: ONE danger sign
Turn 4: Verdict + reasoning

VERDICT format:
HOME CARE: [reason]
REFER TO CLINIC: [reason]
EMERGENCY: [reason]

Never ask rating scales. Never ask food/sleep/stress unless relevant."""


def execute_function(name: str, arguments: dict) -> str:
    """Gemma 4 ne jo function call kiya usse execute karo."""
    if name == "assess_triage":
        result = assess_severity(arguments.get("symptom_text", ""))
        return json.dumps(result, ensure_ascii=False)

    if name == "lookup_referral":
        region = arguments.get("region", "").lower()
        for key in REFERRAL_DB:
            if key in region:
                return REFERRAL_DB[key]
        return REFERRAL_DB["default"]

    if name == "get_drug_dosage":
        drug = arguments.get("drug_name", "").lower()
        weight = float(arguments.get("weight_kg", 10))
        if drug in DRUG_DB:
            return DRUG_DB[drug](weight)
        return f"Dosage information for '{drug}' not available. Consult supervisor."

    return f"Unknown function: {name}"


def run_agent(user_message: str, history: list = None) -> dict:
    if history is None:
        history = []

    history.append({"role": "user", "content": user_message})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    models_to_try = ["gemma3:4b", "gemma4:e4b"]
    full_response = ""
    tool_used = None
    tool_result = None

    for model in models_to_try:
        try:
            response = ollama.chat(
                model=model,
                messages=messages,
                tools=TOOLS,
                options={"temperature": 0.1, "num_predict": 150},
            )

            msg = response.get("message", {})
            if not isinstance(msg, dict):
                msg = {
                    "content": getattr(msg, "content", ""),
                    "tool_calls": getattr(msg, "tool_calls", None),
                }

            tool_calls = msg.get("tool_calls") or []

            if tool_calls:
                for tool_call in tool_calls:
                    fn = tool_call.get("function", {})
                    fn_name = fn.get("name", "")
                    fn_args = fn.get("arguments", {})
                    if isinstance(fn_args, str):
                        fn_args = json.loads(fn_args)

                    tool_used = fn_name
                    tool_result = execute_function(fn_name, fn_args)

                    messages_with_tool = messages + [
                        {"role": "assistant", "content": "", "tool_calls": tool_calls},
                        {"role": "tool", "content": str(tool_result), "name": fn_name},
                    ]

                    final_response = ollama.chat(
                        model=model,
                        messages=messages_with_tool,
                        options={"temperature": 0.1, "num_predict": 100},
                    )
                    final_msg = final_response.get("message", {})
                    full_response = (
                        final_msg.get("content", "")
                        if isinstance(final_msg, dict)
                        else getattr(final_msg, "content", "")
                    )
                    break
            else:
                full_response = msg.get("content", "")

            if full_response.strip():
                break

        except Exception:
            try:
                full_response = ""
                import time

                start = time.time()
                print("Medi: ", end="", flush=True)
                for chunk in ollama.chat(
                    model=model,
                    messages=messages,
                    options={"temperature": 0.1, "num_predict": 80},
                    stream=True,
                ):
                    chunk_msg = chunk.get("message", {})
                    token = (
                        chunk_msg.get("content", "")
                        if isinstance(chunk_msg, dict)
                        else getattr(chunk_msg, "content", "")
                    )
                    if token:
                        print(token, end="", flush=True)
                        full_response += token
                    if time.time() - start > 20 and len(full_response) > 10:
                        break
                print()
                if full_response.strip():
                    break
            except Exception:
                continue

    import re

    full_response = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()
    full_response = re.sub(r"\*\*|\*|##|#", "", full_response).strip()

    history.append({"role": "assistant", "content": full_response})

    return {
        "response": full_response,
        "tool_used": tool_used,
        "tool_result": tool_result,
        "history": history,
    }


if __name__ == "__main__":
    print("MediVoice Function Calling Test\n" + "=" * 40)

    tests = [
        "Bachche ko 3 din se tez bukhar hai aur woh kuch nahi kha raha",
        "Patient Punjab mein hai, hospital kahan hai?",
        "15kg bachche ko paracetamol kitni deni hai?",
        "Mareez behosh ho gaya hai",
    ]

    conversation_history = []
    for test in tests:
        print(f"\nCHW: {test}")
        result = run_agent(test, conversation_history)
        conversation_history = result["history"]
        print(f"Tool: {result['tool_used']}")
        print(f"Medi: {result['response']}")
        print("-" * 40)
