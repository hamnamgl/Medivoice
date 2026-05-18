# Architecture

## System Layers

MediVoice is organized into four major layers:

### 1. Interface Layer

- CLI flow in `app/main.py`
- PWA interface in `app/pwa/` and `docs/`
- optional Streamlit companion UI in `app/streamlit_app.py` and `app/ui/`

### 2. Core Decision Layer

- `gemma_engine.py`: local LLM interaction
- `function_caller.py`: deterministic routing plus tool-calling support
- `triage_logic.py`: protocol-backed severity logic
- `language_detector.py`: lightweight language hints
- `image_analyzer.py`: image prompt construction and model fallback

### 3. Local Data Layer

- `data/protocols/`: bundled clinical starter packs
- `data/drugs/`: offline dosage references
- `data/referrals/`: bundled referral packs
- `data/source_snapshots/`: official-source provenance snapshots
- `data/custom/`: organization-specific overlays
- `data/medivoice.db`: visit and settings storage

### 4. Demo and Reproducibility Layer

- `notebooks/04_demo_consultation.ipynb`: Kaggle demo entrypoint
- proxy + ngrok path for remote browser access

## Offline Design Principle

At runtime, the app should rely on:

- local model execution
- local bundled data
- optional local custom overlays
- local storage only

This keeps the deployment aligned with the offline-first requirement.

## Data Flow

1. User provides text, voice, or image input
2. Language and symptom cues are inspected
3. Deterministic routing handles clear referral/dosage cases
4. Guided triage flow continues for general clinical chat
5. Verdict or action is returned
6. Visit is stored locally in SQLite

## Custom Data Flow

The organization overlay pattern is:

1. core bundled data loads first
2. official-source snapshots remain separate for provenance
3. `data/custom/*.json` is loaded second for runtime overrides
4. local overlay values are merged on top

This lets local health programs adapt operational details without changing the whole application.
