from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "fine_tuning" / "datasets" / "processed"
REPORTS_DIR = ROOT / "fine_tuning" / "reports"


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def evaluate_examples(records: list[dict]) -> dict:
    task_counts: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    verdict_coverage = 0

    for record in records:
        task = record.get("task_type", "unknown")
        language = record.get("language", "unknown")
        task_counts[task] = task_counts.get(task, 0) + 1
        language_counts[language] = language_counts.get(language, 0) + 1

        assistant = next((item["content"] for item in record.get("messages", []) if item["role"] == "assistant"), "")
        if assistant.startswith(("HOME CARE:", "REFER TO CLINIC:", "EMERGENCY:")):
            verdict_coverage += 1

    total = len(records)
    return {
        "total_examples": total,
        "task_counts": task_counts,
        "language_counts": language_counts,
        "strict_verdict_coverage": round(verdict_coverage / total, 3) if total else 0.0,
        "notes": [
            "This evaluation checks dataset shape and verdict formatting coverage.",
            "Model-vs-model benchmarking should be added after an actual Unsloth fine-tuned checkpoint is produced.",
        ],
    }


def main() -> None:
    input_path = PROCESSED_DIR / "supervised_training.jsonl"
    records = _load_jsonl(input_path)
    report = evaluate_examples(records)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "dataset_eval_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
