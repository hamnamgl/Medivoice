from __future__ import annotations

import json
import re
from pathlib import Path

import ollama

from app.core.triage_logic import assess_severity

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CUSTOM_DIR = DATA_DIR / "custom"
REFERRAL_DIR = DATA_DIR / "referrals"
DRUGS_FILE = DATA_DIR / "drugs" / "essential_medicines.json"
CUSTOM_REFERRALS_FILE = CUSTOM_DIR / "referrals.json"
CUSTOM_DRUGS_FILE = CUSTOM_DIR / "drugs.json"

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


def _merge_facility_maps(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for region, cities in overlay.items():
        existing = dict(merged.get(region, {}))
        if isinstance(cities, dict):
            existing.update(cities)
        merged[region] = existing
    return merged


def _normalize_country_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _merge_country_pack(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    merged["country"] = overlay.get("country", base.get("country", "Custom"))
    merged["status"] = overlay.get("status", base.get("status", "custom"))
    merged["emergency"] = overlay.get("emergency", base.get("emergency", "Ask local supervisor"))
    merged["facilities"] = _merge_facility_maps(base.get("facilities", {}), overlay.get("facilities", {}))
    for key, value in overlay.items():
        if key not in {"country", "status", "emergency", "facilities"}:
            merged[key] = value
    return merged


def _load_base_referral_packs() -> dict:
    packs = {}
    for path in sorted(REFERRAL_DIR.glob("*.json")):
        pack = _load_json(path)
        if not pack:
            continue
        country = pack.get("country", path.stem)
        packs[_normalize_country_key(country)] = pack
    return packs


def _load_referral_data() -> dict:
    packs = _load_base_referral_packs()
    custom = _load_json(CUSTOM_REFERRALS_FILE)
    if not custom:
        return {"countries": packs}

    custom_country = custom.get("country", "Custom")
    custom_key = _normalize_country_key(custom_country)
    base_pack = packs.get(custom_key, {"country": custom_country, "facilities": {}})
    packs[custom_key] = _merge_country_pack(base_pack, custom)
    return {"countries": packs}


def _load_drug_data() -> dict:
    base = _load_json(DRUGS_FILE)
    custom = _load_json(CUSTOM_DRUGS_FILE)
    if not custom:
        return base

    merged = dict(base)
    merged["version"] = custom.get("version", base.get("version", "custom"))
    merged["source"] = custom.get("source", base.get("source", "Custom organization data"))
    medicines = dict(base.get("medicines", {}))
    medicines.update(custom.get("medicines", {}))
    merged["medicines"] = medicines
    return merged


REFERRAL_DATA = _load_referral_data()
DRUG_DATA = _load_drug_data()

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
REFERRAL_HINTS = [
    "hospital", "clinic", "referral", "nearest", "kahan", "where", "facility",
    "punjab", "sindh", "kpk", "balochistan", "rawalpindi", "lahore", "karachi", "peshawar", "quetta",
    "kenya", "nairobi", "embakasi", "starehe",
    "nigeria", "lagos", "abuja", "kano",
]
HAUSA_HINTS = ["yaro", "zazzabi", "majiyyaci", "suma", "jini", "numfashi"]
ROMAN_URDU_HINTS = ["bach", "mareez", "bukhar", "behosh", "foran", "dast", "ulti", "khansi", "saans"]


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
    countries = REFERRAL_DATA.get("countries", {})

    for country_key, pack in countries.items():
        country_name = pack.get("country", country_key.title())
        facilities = pack.get("facilities", {})
        emergency = pack.get("emergency", "Ask local supervisor")

        if country_name.lower() in region_text:
            for region, cities in facilities.items():
                if isinstance(cities, dict) and cities:
                    first_city, first_facility = next(iter(cities.items()))
                    return f"{country_name}: {first_city.title()}, {region.title()} - {first_facility}. Emergency: {emergency}"

        for region, cities in facilities.items():
            if region in region_text and isinstance(cities, dict) and cities:
                first_city, first_facility = next(iter(cities.items()))
                return f"{country_name}: {first_city.title()}, {region.title()} - {first_facility}. Emergency: {emergency}"
            if not isinstance(cities, dict):
                continue
            for city, facility in cities.items():
                if city in region_text:
                    return f"{country_name}: {city.title()}, {region.title()} - {facility}. Emergency: {emergency}"

    fallback_country = countries.get("pakistan") or next(iter(countries.values()), {})
    fallback_emergency = fallback_country.get("emergency", "Ask local CHW supervisor")
    return f"Nearest government health facility - ask local CHW supervisor. Emergency: {fallback_emergency}"


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


def _build_explainability(tool_name: str | None, tool_result: str | dict, user_message: str) -> dict | None:
    if tool_name == "get_drug_dosage":
        drug = _extract_drug(user_message or "")
        medicine = DRUG_DATA.get("medicines", {}).get(drug or "", {})
        return {
            "type": "drug_reference",
            "source": DRUG_DATA.get("source"),
            "source_url": DRUG_DATA.get("source_url"),
            "matched_item": drug,
            "notes": medicine.get("notes"),
        }
    if tool_name == "lookup_referral":
        return {
            "type": "referral_lookup",
            "source": "local_referral_pack",
            "matched_query": user_message,
        }
    if tool_name == "assess_triage" and isinstance(tool_result, dict):
        return {
            "type": "triage_rule",
            "matched_rules": tool_result.get("matched_rules", []),
            "rule_source": tool_result.get("rule_source"),
        }
    return None


def _detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text):
        return "ur"
    text_lower = text.lower()
    if any(hint in text_lower for hint in HAUSA_HINTS):
        return "ha"
    if any(hint in text_lower for hint in ROMAN_URDU_HINTS):
        return "ur-roman"
    return "en"


def _has_duration(text: str) -> bool:
    text_lower = text.lower()
    return bool(
        re.search(r"\b\d+\s*(day|days|week|weeks|din|hafta|haftay)\b", text_lower)
        or "since" in text_lower
        or "se " in text_lower
    )


def _choose_symptom_question(text: str, lang: str) -> str:
    text_lower = text.lower()
    if "pregnan" in text_lower or "hamal" in text_lower:
        prompts = {
            "en": "Is there bleeding, severe headache, or swelling?",
            "ur-roman": "Kya bleeding, shadeed sar dard, ya soojan hai?",
            "ha": "Akwai zubar jini, ciwon kai mai tsanani, ko kumburi?",
        }
    elif any(word in text_lower for word in ["dast", "diarr", "loose stool", "stool"]):
        prompts = {
            "en": "Is the patient drinking fluids and is there blood in the stool?",
            "ur-roman": "Kya mareez pani pee raha hai aur kya dast mein khoon hai?",
            "ha": "Majiyyacin na shan ruwa, kuma akwai jini a bayan gida?",
        }
    elif any(word in text_lower for word in ["saans", "breath", "cough", "khansi", "numfashi"]):
        prompts = {
            "en": "Is there fast breathing, chest pain, or chest indrawing?",
            "ur-roman": "Kya saans tez hai, seenay mein dard hai, ya seena dhans raha hai?",
            "ha": "Numfashi yana sauri, akwai ciwon kirji, ko kirji na nutsewa?",
        }
    else:
        prompts = {
            "en": "Is there fever, vomiting, diarrhea, or is the patient not eating?",
            "ur-roman": "Kya bukhar, ulti, dast, ya na khane ki shikayat hai?",
            "ha": "Akwai zazzabi, amai, gudawa, ko mara lafiyan baya cin abinci?",
        }
    return prompts.get(lang, prompts["en"])


def _danger_sign_question(lang: str) -> str:
    prompts = {
        "en": "Is the patient unconscious, not breathing well, bleeding heavily, or unable to drink?",
        "ur-roman": "Kya mareez behosh hai, saans mein mushkil hai, zyada khoon beh raha hai, ya pani nahi pee raha?",
        "ha": "Majiyyacin a sume yake, numfashi na wahala, jini na fita sosai, ko ba zai iya sha ba?",
    }
    return prompts.get(lang, prompts["en"])


def _duration_question(lang: str) -> str:
    prompts = {
        "en": "How long has this been happening?",
        "ur-roman": "Yeh masla kitne arsay se hai?",
        "ha": "Tun yaushe wannan yake faruwa?",
    }
    return prompts.get(lang, prompts["en"])


def _acknowledge(lang: str) -> str:
    prompts = {
        "en": "I am sorry the patient is unwell.",
        "ur-roman": "Mujhe afsos hai ke mareez theek mehsoos nahi kar raha.",
        "ha": "Yi hakuri, majiyyacin baya jin dadi.",
    }
    return prompts.get(lang, prompts["en"])


def _verdict_from_severity(result: dict, lang: str) -> str:
    if lang == "ur-roman":
        mapped = {
            "EMERGENCY": f"EMERGENCY: {result['message']}",
            "REFER": f"REFER TO CLINIC: {result['message']}",
            "HOME CARE": f"HOME CARE: {result['message']}",
        }
        return mapped[result["level"]]
    if lang == "ha":
        mapped = {
            "EMERGENCY": "EMERGENCY: Wannan alamar hadari ce. A kai asibiti nan da nan.",
            "REFER": "REFER TO CLINIC: A kai majiyyacin asibiti ko cibiya a yau.",
            "HOME CARE": "HOME CARE: A kula a gida, amma a kai asibiti idan ya kara tsananta.",
        }
        return mapped[result["level"]]
    mapped = {
        "EMERGENCY": "EMERGENCY: This is dangerous and needs immediate hospital care.",
        "REFER": "REFER TO CLINIC: This case should be reviewed at a clinic today.",
        "HOME CARE": "HOME CARE: Home care is reasonable for now, but seek help if symptoms worsen.",
    }
    return mapped[result["level"]]


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
    language = _detect_language(user_message)

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
        explanation = _build_explainability(tool_used, tool_result, user_message)
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": tool_used,
            "tool_result": tool_result,
            "explanation": explanation,
            "history": history,
        }

    all_user_text = " ".join(item["content"] for item in history if item["role"] == "user")
    user_turns = sum(1 for item in history if item["role"] == "user")
    severity_now = assess_severity(all_user_text)

    if severity_now["level"] == "EMERGENCY":
        full_response = _verdict_from_severity(severity_now, language)
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": "assess_triage",
            "tool_result": severity_now,
            "explanation": _build_explainability("assess_triage", severity_now, all_user_text),
            "history": history,
        }

    if user_turns == 1:
        if not _has_duration(user_message):
            full_response = f"{_acknowledge(language)} {_duration_question(language)}"
        else:
            full_response = f"{_acknowledge(language)} {_choose_symptom_question(all_user_text, language)}"
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": None,
            "tool_result": None,
            "explanation": None,
            "history": history,
        }

    if user_turns == 2:
        full_response = _choose_symptom_question(all_user_text, language)
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": None,
            "tool_result": None,
            "explanation": None,
            "history": history,
        }

    if user_turns == 3:
        full_response = _danger_sign_question(language)
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": None,
            "tool_result": None,
            "explanation": None,
            "history": history,
        }

    if user_turns >= 4:
        full_response = _verdict_from_severity(severity_now, language)
        history.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "tool_used": "assess_triage",
            "tool_result": severity_now,
            "explanation": _build_explainability("assess_triage", severity_now, all_user_text),
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
        "explanation": _build_explainability(tool_used, tool_result, all_user_text),
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
