from fine_tuning.evaluate_model import evaluate_examples
from fine_tuning.prepare_dataset import _build_synthetic_examples
from fine_tuning.train_unsloth import build_training_plan


def test_build_synthetic_examples_returns_multilingual_records():
    records = _build_synthetic_examples()
    assert len(records) >= 3
    assert any(record["language"] == "Roman Urdu" for record in records)
    assert any(record["language"] == "Hausa" for record in records)


def test_build_training_plan_uses_config_values():
    plan = build_training_plan(
        {
            "model_name": "unsloth/gemma-3-4b-it",
            "dataset_path": "fine_tuning/datasets/processed/supervised_training.jsonl",
            "run_name": "demo_run",
            "epochs": 2,
            "learning_rate": 0.0001,
        }
    )
    assert plan["model_name"] == "unsloth/gemma-3-4b-it"
    assert plan["epochs"] == 2
    assert "demo_run" in plan["output_dir"]


def test_evaluate_examples_reports_verdict_coverage():
    records = [
        {
            "task_type": "triage_dialogue",
            "language": "English",
            "messages": [
                {"role": "assistant", "content": "HOME CARE: Fluids and rest."}
            ],
        },
        {
            "task_type": "drug_dosage",
            "language": "Roman Urdu",
            "messages": [
                {"role": "assistant", "content": "REFER TO CLINIC: Bring the child today."}
            ],
        },
    ]
    report = evaluate_examples(records)
    assert report["total_examples"] == 2
    assert report["strict_verdict_coverage"] == 1.0
