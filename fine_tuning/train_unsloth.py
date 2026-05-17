from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "fine_tuning" / "configs" / "training_config.yaml"
OUTPUT_DIR = ROOT / "fine_tuning" / "checkpoints"


def _parse_simple_yaml(path: Path) -> dict:
    values: dict[str, object] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.isdigit():
            values[key] = int(value)
        else:
            try:
                values[key] = float(value)
            except ValueError:
                values[key] = value.strip('"').strip("'")
    return values


def build_training_plan(config: dict) -> dict:
    dataset_path = Path(str(config["dataset_path"]))
    checkpoint_dir = OUTPUT_DIR / str(config.get("run_name", "medivoice_unsloth"))
    return {
        "model_name": config.get("model_name", "unsloth/gemma-3-4b-it"),
        "dataset_path": str(dataset_path).replace("\\", "/"),
        "output_dir": str(checkpoint_dir).replace("\\", "/"),
        "max_seq_length": config.get("max_seq_length", 2048),
        "per_device_train_batch_size": config.get("per_device_train_batch_size", 2),
        "gradient_accumulation_steps": config.get("gradient_accumulation_steps", 4),
        "learning_rate": config.get("learning_rate", 0.0002),
        "epochs": config.get("epochs", 3),
        "lora_r": config.get("lora_r", 16),
        "lora_alpha": config.get("lora_alpha", 16),
        "target_modules": str(config.get("target_modules", "q_proj,k_proj,v_proj,o_proj")).split(","),
        "notes": [
            "This repo ships a training plan scaffold so teams can run Unsloth fine-tuning outside the core app.",
            "Actual GPU training is expected on Kaggle, Colab, or another compatible environment.",
        ],
    }


def main() -> None:
    config = _parse_simple_yaml(CONFIG_PATH)
    plan = build_training_plan(config)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "training_plan.json"
    output_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
