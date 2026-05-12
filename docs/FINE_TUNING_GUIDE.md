# Fine-Tuning Guide

## Purpose

This guide defines how MediVoice should approach future fine-tuning for CHW-specific workflows.

## Goals

Fine-tuning should improve:

- multilingual medical phrasing
- CHW-style follow-up questions
- same-language consistency
- safer verdict formatting
- domain vocabulary for target regions

## Recommended Dataset Categories

- curated CHW consultation dialogues
- protocol-grounded Q/A pairs
- local-language triage prompts
- image-triage examples with safe response formats

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

## Current Repo Status

The repo includes the structure for fine-tuning work, but this part is still a roadmap rather than a completed training pipeline.

## Future Additions

- repeatable dataset build scripts
- training config templates
- benchmark prompts
- base-vs-finetuned evaluation reports
