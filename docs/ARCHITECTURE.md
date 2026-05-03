# Architecture

Medivoice follows a lightweight layered structure:

- `ui/` handles Streamlit presentation and input flows.
- `core/` contains model interfaces, triage rules, and multimodal helpers.
- `utils/` stores configuration, logging, and local persistence helpers.
- `data/` ships local protocol and referral content for offline usage.
