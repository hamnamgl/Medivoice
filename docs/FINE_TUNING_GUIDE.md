# Fine-Tuning Guide

## Purpose

This guide describes the current MediVoice fine-tuning scaffold for CHW-style adaptation.

## What Is Now Implemented

The repo now includes:

- `fine_tuning/prepare_dataset.py`
  - builds a supervised JSONL dataset from protocol files, demo consultations, and drug reference examples
- `fine_tuning/train_unsloth.py`
  - creates a concrete Unsloth training plan JSON from `training_config.yaml`
- `fine_tuning/evaluate_model.py`
  - evaluates dataset coverage, language spread, and strict verdict formatting
- `fine_tuning/configs/training_config.yaml`
  - stores the current LoRA-oriented training configuration

## Workflow

1. Prepare the dataset

```bash
python fine_tuning/prepare_dataset.py
```

2. Build the training plan

```bash
python fine_tuning/train_unsloth.py
```

3. Evaluate the prepared dataset

```bash
python fine_tuning/evaluate_model.py
```

## Current Dataset Contents

The generated supervised dataset combines:

- protocol follow-up examples from `data/protocols/*.json`
- demo consultation samples from `demo/sample_consultations/`
- dosage-reference examples from `data/drugs/essential_medicines.json`
- synthetic CHW-style dialogues for Roman Urdu, Hausa, and Swahili

## Goals

Fine-tuning should improve:

- multilingual medical phrasing
- CHW-style one-question-at-a-time guidance
- same-language consistency
- safer verdict formatting
- local clinical vocabulary

## Data Preparation Rules

- remove personally identifiable information
- keep source attribution in `data/SOURCES.md` or dataset docs
- preserve language labels
- separate `home care`, `refer`, and `emergency` examples clearly

## Evaluation Priorities

- same-language response fidelity
- verdict correctness
- tool-routing recall for referral and dosage requests
- low-resource symptom handling

## What Is Still Missing

- actual Unsloth training execution logs
- checkpoint artifacts
- base-vs-finetuned benchmark comparison
- larger public dataset ingestion from Hugging Face medical corpora
