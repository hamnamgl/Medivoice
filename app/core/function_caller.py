from __future__ import annotations

import json
import re
from pathlib import Path

import ollama

from app.core.triage_logic import assess_severity

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REFERRAL_FILES = {
    "pakistan": DATA_DIR / "referrals" / "pk_facilities.json",
}
DRUGS_FILE = DATA_DIR / "drugs" / "essential_medicines.json"

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

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


REFERRAL_DATA = _load_json(REFERRAL_FILES["pakistan"])
DRUG_DATA = _load_json(DRUGS_FILE)

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

DOSAGE_HINTS = ["dosage", "dose", "kitni", "mg", "medicine", "drug", "paracetamol", "amoxicillin", "ors", "zinc", "ibuprofen", "cotrimoxazole"]
REFERRAL_HINTS = ["hospital", "clinic", "referral", "nearest", "kahan", "where", "facility", "punjab", "sindh", "kpk", "balochistan", "rawalpindi", "lahore", "karachi", "peshawar", "quetta"]


def _format_drug_dose(drug_name: str, weight_kg: float) -> str:
    medicine = DRUG_DATA.get("medicines", {}).get(drug_name)
    if not medicine:
        return f"Dosage information for '{drug_name}' not available. Consult supervisor."

    if medicine.get("dose_per_kg") is not None:
        amount = round(weight_kg * float(medicine["dose_per_kg"]))
        response = f"{amount} {medicine['unit']} {medicine['frequency']}"
    elif medicine.get("fixed_dose") is not None:
        response = f"{medicine['fixed_dose']} {medicine['unit']} {medicine['frequency']}"
    else:
        response = f"{medicine['frequency']}"

    if medicine.get("max_doses_per_day"):
        response += f" (max {medicine['max_doses_per_day']} doses/day)"
    if medicine.get("duration_days"):
        response += f" for {medicine['duration_days']} days"
    if medicine.get("notes"):
        response += f". Note: {medicine['notes']}"
    return response


def _lookup_referral_text(region_text: str) -> str:
    region_text = region_text.lower()
    facilities = REFERRAL_DATA.get("facilities", {})

    for province, cities in facilities.items():
        if province in region_text:
            first_city, first_facility = next(iter(cities.items()))
            return f"{province.title()}: {first_city.title()} - {first_facility}. Emergency: {REFERRAL_DATA.get('emergency', 'Ask local supervisor')}"
        for city, facility in cities.items():
            if city in region_text:
                return f"{city.title()}, {province.title()}: {facility}. Emergency: {REFERRAL_DATA.get('emergency', 'Ask local supervisor')}"

    return f"Nearest government health facility - ask local CHW supervisor. Emergency: {REFERRAL_DATA.get('emergency', 'Ask local supervisor')}"


def _extract_weight(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*kg", text.lower())
    return float(match.group(1)) if match else None


def _extract_drug(text: str) -> str | None:
    for name in DRUG_DATA.get("medicines", {}):
        if name in text.lower():
            return name
    return None


def _should_route_to_dosage(text: str) -> bool:
    text_lower = text.lower()
    return any(hint in text_lower for hint in DOSAGE_HINTS) and _extract_drug(text_lower) is not None


def _should_route_to_referral(text: str) -> bool:
    text_lower = text.lower()
    return any(hint in text_lower for hint in REFERRAL_HINTS)


def _build_direct_tool_reply(tool_name: str, tool_result: str | dict) -> str:
    if tool_name == "get_drug_dosage":
        return f"HOME CARE: {tool_result}"
    if tool_name == "lookup_referral":
        return f"REFER TO CLINIC: {tool_result}"
    if tool_name == "assess_triage" and isinstance(tool_result, dict):
        return f"{tool_result['level']}: {tool_result['message']}"
    return str(tool_result)


def execute_function(name: str, arguments: dict) -> str:
    """Gemma 4 ne jo function call kiya usse execute karo."""
    if name == "assess_triage":
        result = assess_severity(arguments.get("symptom_text", ""))
        return json.dumps(result, ensure_ascii=False)

    if name == "lookup_referral":
        region = arguments.get("region", "")
        return _lookup_referral_text(region)

    if name == "get_drug_dosage":
        drug = arguments.get("drug_name", "").lower().strip()
        weight = float(arguments.get("weight_kg", 10))
        return _format_drug_dose(drug, weight)

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

    direct_drug = _extract_drug(user_message)
    direct_weight = _extract_weight(user_message)

    if _should_route_to_dosage(user_message) and direct_drug and direct_weight:
        tool_used = "get_drug_dosage"
        tool_result = execute_function(tool_used, {"drug_name": direct_drug, "weight_kg": direct_weight})
        full_response = _build_direct_tool_reply(tool_used, tool_result)
    elif _should_route_to_referral(user_message):
        tool_used = "lookup_referral"
        tool_result = execute_function(tool_used, {"region": user_message})
        full_response = _build_direct_tool_reply(tool_used, tool_result)

    if full_response.strip():
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": tool_used,
            "tool_result": tool_result,
            "history": history,
        }

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
                    if fn_name == "assess_triage":
                        tool_payload = json.loads(tool_result)
                        tool_result = tool_payload

                    messages_with_tool = messages + [
                        {"role": "assistant", "content": "", "tool_calls": tool_calls},
                        {"role": "tool", "content": json.dumps(tool_result, ensure_ascii=False) if isinstance(tool_result, dict) else str(tool_result), "name": fn_name},
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
                    if not full_response.strip():
                        full_response = _build_direct_tool_reply(fn_name, tool_result)
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
