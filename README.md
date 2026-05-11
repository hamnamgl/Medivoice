# 🏥 MediVoice
### Offline AI Health Copilot for Frontline Community Health Workers

> **"When there's no doctor, no internet, and no time — Medi is there."**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Model: Gemma 4](https://img.shields.io/badge/Model-Gemma%204-orange.svg)](https://ollama.com/library/gemma3)
[![Offline First](https://img.shields.io/badge/Offline-First-green.svg)]()
[![PWA Ready](https://img.shields.io/badge/PWA-Android%20Ready-brightgreen.svg)]()
[![Ollama](https://img.shields.io/badge/Runs%20on-Ollama-purple.svg)](https://ollama.com)

---

## 🌍 The Problem

Over **1 billion people** rely on Community Health Workers (CHWs) — local frontline workers with minimal medical training, no reliable internet, and no clinical decision support. A CHW in rural Punjab, Lagos, or Nairobi must make triage decisions with nothing but instinct.

MediVoice changes that.

---

## 🤖 What is MediVoice?

MediVoice is an **offline-first AI clinical assistant** powered by **Gemma 4 running locally via Ollama**. It turns any laptop or Android phone into a smart medical copilot that:

- Guides CHWs through structured patient consultations
- Speaks and understands **22 languages**
- Works with **zero internet** — all AI runs on-device
- Analyzes wound/rash **photos** for visual triage
- Accepts **voice input** from workers who cannot type
- Gives a clear verdict: `HOME CARE`, `REFER TO CLINIC`, or `EMERGENCY`
- Logs every visit locally in SQLite — no cloud, no privacy risk

---

## ✨ Key Features

| Feature | Details |
|---|---|
| 🧠 Local LLM | Gemma 4 (gemma3:4b / gemma4:e4b) via Ollama — no API key, no internet |
| 🎤 Voice Input | Offline speech-to-text via OpenAI Whisper |
| 🗣️ Voice Output | Text-to-speech via edge-tts in 22 languages |
| 📷 Image Analysis | Wound/rash photo analysis via Gemma vision through Ollama |
| 🔧 Function Calling | Native tool use: triage assessment, referral lookup, drug dosage |
| 🌐 22 Languages | English, Urdu, Hindi, Hausa, Swahili, French, Bengali, Somali + more |
| 📱 PWA / Android | Installable Progressive Web App — works on cheap Android phones |
| 🗄️ Local Storage | SQLite visit logs — encrypted-ready, no cloud dependency |
| 🏥 Offline Datasets | Built-in protocols, referral directory, drug dosage database |

---

## 🏆 Hackathon Tracks Targeted

This project targets multiple Gemma 4 Good Hackathon prize tracks:

- **Main Track** — Real-world impact, offline-first, multimodal
- **Ollama Special Prize ($10K)** — Best project using Gemma 4 via Ollama locally
- **Health & Sciences Impact Track ($10K)** — Democratizing clinical decision support
- **Digital Equity & Inclusivity ($10K)** — 22 languages, voice-first, no literacy required

---

## 🏗️ Architecture
MediVoice
├── app/
│   ├── main.py                  # CLI consultation app (22 languages)
│   ├── core/
│   │   ├── gemma_engine.py      # Ollama LLM interface (Gemma 4)
│   │   ├── function_caller.py   # Native function calling: triage/referral/drugs
│   │   ├── triage_logic.py      # Rule-based severity classification
│   │   ├── voice_handler.py     # Whisper STT + edge-tts TTS
│   │   └── image_analyzer.py   # Gemma vision image analysis
│   ├── utils/
│   │   └── local_db.py          # SQLite visit logging
│   └── pwa/
│       ├── index.html           # Progressive Web App (Android-installable)
│       └── manifest.json        # PWA manifest
├── data/
│   ├── protocols/               # Offline clinical protocols
│   ├── referrals/               # Country referral directories
│   └── drugs/                   # Essential medicines dosage data
├── fine_tuning/                 # Unsloth fine-tuning scripts
├── tests/                       # Test suite
├── docs/                        # Technical documentation
└── deployment/                  # Docker + deployment configs


---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- Gemma model pulled

```bash
# 1. Pull Gemma 4 model
ollama pull gemma3:4b

# 2. Clone the repo
git clone https://github.com/hamnamgl/Medivoice.git
cd Medivoice

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run CLI app
python -m app.main
```

### Android / PWA Install
```bash
# Open in Chrome on Android
# Go to: file:///path/to/app/pwa/index.html
# OR serve locally:
cd app/pwa
python -m http.server 8080
# Then open http://localhost:8080 in Chrome
# Tap "Add to Home Screen" → installed like a native app
```

---

## 🔧 Why Ollama?

MediVoice uses **Ollama** to run Gemma 4 completely locally because:

- **Zero internet required** — critical for rural/remote deployment
- **Zero API cost** — sustainable for NGOs and health programs
- **Data privacy** — patient data never leaves the device
- **Works on consumer hardware** — gemma3:4b runs on 8GB RAM laptops
- **Easy model switching** — swap between gemma3:4b and gemma4:e4b with one line

```python
# From app/core/gemma_engine.py
for model in ["gemma3:4b", "gemma4:e4b"]:
    response = ollama.chat(model=model, messages=messages, ...)
```

---

## 🔧 Function Calling

MediVoice uses **Gemma 4's native function calling** via Ollama for structured clinical decisions:

```python
TOOLS = [
    assess_triage(symptom_text)     # → HOME CARE / REFER / EMERGENCY
    lookup_referral(region)         # → Nearest health facility
    get_drug_dosage(drug, weight_kg) # → Correct dosage for patient weight
]
```

The model decides which tool to call based on the conversation, executes it locally, then gives a grounded response — no hallucinated drug doses.

---

## 🌐 Supported Languages

English · Roman Urdu · اردو · हिंदी · Hausa · Swahili · Français · বাংলা · Tagalog · አማርኛ · پښتو · Soomaali · Português · Español · Indonesian · Yoruba · Igbo · Zulu · Tigrinya · Burmese · Khmer · Nepali

---

## 🧪 Testing

```bash
pytest tests/ -v
```

Covers: triage logic, local DB, language detection, image analyzer, Gemma engine, function caller, voice handler.

---

## 📊 Impact

- **Target users:** 1M+ CHWs across Sub-Saharan Africa, South Asia, Southeast Asia
- **Languages covered:** 22 — covering ~4.2 billion people
- **Connectivity required:** Zero
- **Cost to deploy:** $0 API cost — runs on donated/cheap hardware
- **Privacy:** 100% on-device — no patient data ever sent to cloud

---

## Demo Mode Vs True Offline

- **Demo mode:** If you use Kaggle + ngrok, the model runs on the Kaggle machine and the PWA talks to it through a public URL. This is great for demos, but your phone/browser still needs internet to reach that tunnel.
- **True offline mode:** Real offline use only happens when Ollama is running on the same laptop, Android device, or reachable local network machine. In that setup, no internet is needed after install and model download.

---

## Production-Grade Offline Roadmap

To make MediVoice properly production-grade for real field deployment, the architecture should move from a demo-friendly setup to a hardened offline stack:

### 1. Local Runtime on Target Device

- Run Ollama directly on the deployment laptop, mini PC, or Android-compatible edge device
- Preload the production model during setup so the user never has to download in the field
- Package FFmpeg, Whisper assets, and app dependencies with the installer

### 2. Local-Only Networking

- Default the PWA or local UI to `http://localhost:11434/api/chat` or a local LAN IP
- Use Kaggle + ngrok only for demo mode, never as the primary production path
- Add automatic local endpoint detection and a clear “demo mode / offline mode” indicator

### 3. Safer Clinical Tooling

- Expand structured function calling for triage, referrals, and dosing
- Validate tool arguments before execution
- Add explicit refusal / escalation rules for unsupported or ambiguous cases
- Add protocol-backed reasoning outputs for explainability and auditability

### 4. Stronger Data Layer

- Encrypt local SQLite records at rest
- Version offline protocol and referral datasets
- Add migration scripts for schema upgrades
- Add signed update bundles for trusted offline content refresh

### 5. Reliability and Recovery

- Add health checks for Ollama, audio devices, and model availability
- Cache model readiness state and fail gracefully if a model is missing
- Add structured logging for app, model, and tool failures
- Add restart-safe local queues for pending visit writes

### 6. Packaging and Device Management

- Create a one-click installer for Windows/Linux field laptops
- Build an Android-friendly wrapper or kiosk shell for the PWA
- Preconfigure language packs, voices, and local data during install
- Add a supervised update workflow for NGOs or district admins

### 7. Security and Governance

- Keep all patient data local by default
- Add role-based supervisor mode if case review is needed
- Store audit trails for triage decisions and tool outputs
- Provide a deployment checklist for device encryption, backups, and physical access control

### 8. Validation Before Field Rollout

- Run multilingual regression tests for core flows
- Evaluate tool-calling accuracy on protocol-aligned scenarios
- Benchmark latency on low-resource hardware
- Pilot with supervised health workers before broad deployment

In short: **Kaggle proves the demo, but production-grade offline MediVoice means local Ollama, preloaded models, encrypted local data, hardened tooling, and deployment packaging for field hardware.**

---

## 📁 Docs

- [Technical Write-up](docs/TECHNICAL_WRITEUP.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Impact Report](docs/IMPACT_REPORT.md)
- [Fine-tuning Guide](docs/FINE_TUNING_GUIDE.md)

---

## 👩‍💻 Built With

- [Gemma 4](https://ollama.com/library/gemma3) — Google DeepMind open model
- [Ollama](https://ollama.com) — Local LLM runtime
- [Whisper](https://github.com/openai/whisper) — Offline speech-to-text
- [edge-tts](https://github.com/rany2/edge-tts) — Multilingual text-to-speech
- [SQLite](https://sqlite.org) — Local visit logging
- PWA — Android-installable web interface

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE)

---

*Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) — Kaggle × Google DeepMind*
