from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEMO_DIR = ROOT / "demo" / "sample_consultations"
RAW_DIR = ROOT / "fine_tuning" / "datasets" / "raw"
PROCESSED_DIR = ROOT / "fine_tuning" / "datasets" / "processed"
SYNTHETIC_DIR = ROOT / "fine_tuning" / "datasets" / "synthetic"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _build_protocol_examples() -> list[dict]:
    examples: list[dict] = []
    protocol_dir = DATA_DIR / "protocols"
    for path in sorted(protocol_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for condition, details in payload.get("conditions", {}).items():
            prompt = f"Patient concern: {condition.replace('_', ' ')}"
            reply = " ".join(details.get("ask", [])[:2]).strip()
            examples.append(
                {
                    "source": path.name,
                    "language": "English",
                    "task_type": "protocol_followup",
                    "messages": [
                        {"role": "system", "content": "Ask one safe CHW follow-up question at a time."},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": reply or "Ask one symptom question."},
                    ],
                }
            )
    return examples


def _build_demo_examples() -> list[dict]:
    mapping = {
        "urdu_fever_child.txt": ("Roman Urdu", "triage_dialogue"),
        "hausa_maternal_danger.txt": ("Hausa", "triage_dialogue"),
        "swahili_wound_photo.txt": ("Swahili", "image_triage"),
    }
    examples: list[dict] = []
    for filename, (language, task_type) in mapping.items():
        path = DEMO_DIR / filename
        content = _read_text(path)
        examples.append(
            {
                "source": filename,
                "language": language,
                "task_type": task_type,
                "messages": [
                    {"role": "system", "content": "Respond in the same language and give a safe next step."},
                    {"role": "user", "content": content},
                    {"role": "assistant", "content": "REFER TO CLINIC: Assess danger signs and guide the worker to the safest next step."},
                ],
            }
        )
    return examples


def _build_drug_examples() -> list[dict]:
    payload = json.loads((DATA_DIR / "drugs" / "essential_medicines.json").read_text(encoding="utf-8"))
    examples: list[dict] = []
    for medicine_name, details in payload.get("medicines", {}).items():
        weight = 15
        prompt = f"{weight}kg child - {medicine_name} dosage?"
        if details.get("dose_per_kg") is not None:
            amount = round(weight * float(details["dose_per_kg"]))
            answer = f"HOME CARE: {amount} {details['unit']} {details['frequency']}"
        elif details.get("fixed_dose") is not None:
            answer = f"HOME CARE: {details['fixed_dose']} {details['unit']} {details['frequency']}"
        else:
            answer = f"HOME CARE: {details['frequency']}"
        examples.append(
            {
                "source": "essential_medicines.json",
                "language": "English",
                "task_type": "drug_dosage",
                "messages": [
                    {"role": "system", "content": "Use drug reference data and answer in a short safe format."},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ],
            }
        )
    return examples


def _build_synthetic_examples() -> list[dict]:
    examples = [
        {
            "source": "synthetic_roman_urdu",
            "language": "Roman Urdu",
            "task_type": "triage_dialogue",
            "messages": [
                {"role": "system", "content": "Ask one question at a time and end with HOME CARE, REFER TO CLINIC, or EMERGENCY."},
                {"role": "user", "content": "Bachay ko 4 din se bukhar hai aur pani kam pee raha hai."},
                {"role": "assistant", "content": "REFER TO CLINIC: Bukhar 4 din se hai aur pani kam peena dehydration ka risk dikhata hai."},
            ],
        },
        {
            "source": "synthetic_hausa",
            "language": "Hausa",
            "task_type": "triage_dialogue",
            "messages": [
                {"role": "system", "content": "Respond in Hausa and keep the verdict format strict."},
                {"role": "user", "content": "Jariri yana amai kuma baya shan ruwa."},
                {"role": "assistant", "content": "EMERGENCY: Jaririn baya shan ruwa kuma yana amai, a kai asibiti nan da nan."},
            ],
        },
        {
            "source": "synthetic_swahili",
            "language": "Swahili",
            "task_type": "image_triage",
            "messages": [
                {"role": "system", "content": "Describe visible signs and give one action."},
                {"role": "user", "content": "Kidonda kinaonekana kuvimba na kutoa usaha."},
                {"role": "assistant", "content": "REFER TO CLINIC: Kuna dalili za maambukizi zinazoonekana, mgonjwa apelekwe kliniki leo."},
            ],
        },
    ]
    return examples


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    protocol_examples = _build_protocol_examples()
    demo_examples = _build_demo_examples()
    drug_examples = _build_drug_examples()
    synthetic_examples = _build_synthetic_examples()

    combined = protocol_examples + demo_examples + drug_examples + synthetic_examples

    _write_jsonl(PROCESSED_DIR / "supervised_training.jsonl", combined)
    _write_jsonl(SYNTHETIC_DIR / "synthetic_dialogues.jsonl", synthetic_examples)
    (RAW_DIR / "README.txt").write_text(
        "Place downloaded public datasets here before custom normalization.\n",
        encoding="utf-8",
    )

    summary = {
        "total_examples": len(combined),
        "protocol_examples": len(protocol_examples),
        "demo_examples": len(demo_examples),
        "drug_examples": len(drug_examples),
        "synthetic_examples": len(synthetic_examples),
    }
    (PROCESSED_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
