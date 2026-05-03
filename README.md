# Medivoice

Medivoice is an offline-first community health worker assistant designed for low-connectivity settings. It combines multilingual voice intake, protocol-guided triage, simple image assessment, and local record-keeping in a lightweight Streamlit app.

## Project Goals

- Support frontline health workers with guided consultations.
- Work offline on laptops or edge devices with local data storage.
- Provide safe, explainable triage aligned with public-health protocols.
- Prepare a clean base for demos, hackathons, and future deployment work.

## Repository Layout

The repository is organized into:

- `app/` for the Streamlit experience and application logic
- `data/` for protocols, referrals, and medicine reference data
- `docs/` for architecture, deployment, and impact documentation
- `fine_tuning/` for dataset preparation and Unsloth training workflows
- `tests/` for basic regression coverage
- `demo/` and `assets/` for presentation material

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/main.py
```

## Current Status

This scaffold includes a working starter app, placeholder protocol data, documentation shells, and test stubs so the project can be extended cleanly.
