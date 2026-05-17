# MediVoice
### Offline AI Health Copilot for Frontline Community Health Workers

> When there is no doctor, no internet, and no time, MediVoice helps the frontline worker make a safer next-step decision.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Model: Gemma%204](https://img.shields.io/badge/Model-Gemma%204-orange.svg)](https://ollama.com/library/gemma3)
[![Offline First](https://img.shields.io/badge/Offline-First-green.svg)]()
[![PWA Ready](https://img.shields.io/badge/PWA-Android%20Ready-brightgreen.svg)]()
[![Runs on Ollama](https://img.shields.io/badge/Runs%20on-Ollama-purple.svg)](https://ollama.com)

## What It Is

MediVoice is an offline-first AI assistant for community health workers. It runs locally through Ollama, supports multilingual consultation flows, gives structured triage guidance, and keeps patient data on-device.

Current project goals:

- guided consultation in low-resource settings
- voice-first and mobile-friendly interaction
- offline triage, referral, and dosage support
- local-only storage and data overlays for NGOs or district programs

## Current Capabilities

| Feature | Status |
|---|---|
| Local LLM via Ollama | Working |
| PWA / GitHub Pages demo | Working |
| Kaggle + ngrok demo path | Working |
| Offline dosage lookup | Working |
| Offline referral lookup | Working |
| SQLite visit logging | Working |
| Image triage prompt + fallback | Working |
| Custom local organization data pack | Working |
| Official source snapshots in repo | Working |
| Fully verified worldwide medical dataset | Not yet complete |

## Data Model

MediVoice uses a two-layer offline data model:

1. Core bundled data
   - built-in triage starter packs
   - built-in essential medicine dosing
   - built-in referral starter packs

2. Organization custom overlays
   - local district hospitals
   - ambulance numbers
   - supervisor contacts
   - approved local formulary overrides

Editable overlay files:

- `data/custom/referrals.json`
- `data/custom/drugs.json`
- `data/custom/README.md`

Data provenance notes:

- `data/SOURCES.md`

This design keeps core defaults bundled with the app while letting NGOs, ministries, or clinic networks add local operational data safely.

## Architecture

```text
medivoice/
|-- app/
|   |-- main.py
|   |-- core/
|   |   |-- gemma_engine.py
|   |   |-- function_caller.py
|   |   |-- triage_logic.py
|   |   |-- voice_handler.py
|   |   |-- image_analyzer.py
|   |   `-- language_detector.py
|   |-- pwa/
|   `-- utils/
|-- data/
|   |-- protocols/
|   |-- referrals/
|   |-- drugs/
|   |-- source_snapshots/
|   |-- custom/
|   `-- SOURCES.md
|-- docs/
|-- notebooks/
|-- scripts/
|   `-- data/
`-- tests/
```

## Quick Start

### Prerequisites

- Python 3.10+
- Ollama installed
- at least one local Gemma model available

### Local CLI

```bash
git clone https://github.com/hamnamgl/Medivoice.git
cd Medivoice
pip install -r requirements.txt
ollama pull gemma3:4b
python -m app.main
```

### PWA Demo

```bash
cd docs
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Demo Mode vs True Offline Mode

- Demo mode:
  - Kaggle + ngrok + GitHub Pages PWA
  - useful for judges and quick remote demos
  - phone/browser still needs internet to reach the tunnel

- True offline mode:
  - Ollama runs on the same machine or same local network
  - no internet needed after setup and model download

## Worldwide Data Strategy

MediVoice should not depend on live websites at runtime. For worldwide scale, the recommended pattern is:

1. fetch data from public or official sources
2. clean and normalize it into app-friendly JSON
3. store offline snapshots in the repo or deployment bundle
4. let organizations apply local overlays through `data/custom/`

Planned source-driven workflow:

- global protocol layer: WHO IMCI and generic triage
- global medicines layer: WHO essential medicines
- country referral packs: official registries where available
- local organization overlays: district or NGO-specific updates

Supporting scripts and notes:

- `scripts/data/README.md`
- `scripts/data/fetch_global_sources.py`
- `scripts/data/global_sources_manifest.json`
- `data/source_snapshots/`
- `data/SOURCES.md`

## Testing

```bash
python -m pytest tests -q
```

Focused tests already cover:

- function caller routing
- image analyzer fallback
- local DB behavior
- language detection

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Technical Write-Up](docs/TECHNICAL_WRITEUP.md)
- [Impact Report](docs/IMPACT_REPORT.md)
- [Fine-Tuning Guide](docs/FINE_TUNING_GUIDE.md)
- [Data Sources](data/SOURCES.md)

## License

Apache 2.0. See [LICENSE](LICENSE).
