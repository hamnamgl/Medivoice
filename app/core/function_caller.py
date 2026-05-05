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

SYSTEM_PROMPT = """You are MediVoice, an AI clinical decision support assistant 
for community health workers in low-resource settings.

RULES:
1. Always respond in the SAME language the user speaks
2. Use simple non-technical words
3. Ask ONE question at a time
4. Use your tools to assess triage, lookup referrals, and get drug dosages
5. Always end with: HOME CARE / REFER TO CLINIC / EMERGENCY
6. Be brief - user may be semi-literate"""


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


def run_agent(user_message: str, history: list | None = None) -> dict:
    """
    Full agent loop with function calling.
    Returns: {response, tool_used, tool_result, history}
    """
    if history is None:
        history = []

    history.append({"role": "user", "content": user_message})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    response = ollama.chat(model="gemma4:e4b", messages=messages, tools=TOOLS)
    msg = response["message"]
    tool_used = None
    tool_result = None

    if msg.get("tool_calls"):
        for tool_call in msg["tool_calls"]:
            fn_name = tool_call["function"]["name"]
            fn_args = tool_call["function"]["arguments"]
            tool_result = execute_function(fn_name, fn_args)
            tool_used = fn_name

            history.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
            history.append({"role": "tool", "content": tool_result, "name": fn_name})

        final_response = ollama.chat(
            model="gemma4:e4b",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        )
        final_text = final_response["message"]["content"]
    else:
        final_text = msg.get("content", "")

    history.append({"role": "assistant", "content": final_text})

    return {
        "response": final_text,
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
        print(f"MediVoice: {result['response']}")
        print("-" * 40)
