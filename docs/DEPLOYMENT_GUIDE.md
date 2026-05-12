# Deployment Guide

Use this guide for laptop, Raspberry Pi, Docker, and future Android packaging instructions.

## Deployment Modes

MediVoice supports two different deployment patterns:

- **Demo mode**: Kaggle + ngrok + PWA, useful for hackathon judging and quick public demos
- **True offline mode**: Ollama runs locally on the deployment device or on the same local network

For real field use, always prefer true offline mode.

## Data Architecture

MediVoice uses a two-layer offline data model:

1. **Core bundled data**
   - built-in triage rules
   - built-in medicine dosing data
   - bundled referral starter packs

2. **Organization custom overlays**
   - local hospital lists
   - district or NGO supervisor numbers
   - approved local formulary overrides

Editable local overlay files live in:

- `data/custom/referrals.json`
- `data/custom/drugs.json`

Reference and provenance notes live in:

- `data/SOURCES.md`
- `data/custom/README.md`

## Recommended Field Workflow

### 1. Keep core medical defaults bundled

Do not ask frontline CHWs to manually edit core clinical rules or dosing logic.

### 2. Let supervisors or organizations add local operational data

Use `data/custom/referrals.json` for:

- district hospitals
- clinic phone numbers
- ambulance numbers
- supervisor contact details

Use `data/custom/drugs.json` for:

- approved local formulary additions
- organization-reviewed dosing overrides

### 3. Package the app with local data preloaded

Before deployment:

- preload the Ollama model
- include the built-in data bundle
- add the organization custom pack
- test referral and dosage lookups offline

## Example Custom Referral Overlay

```json
{
  "country": "Example NGO Pack",
  "emergency": "1122 | Supervisor: 0300-1234567",
  "facilities": {
    "punjab": {
      "gujranwala": "DHQ Hospital Gujranwala - 055-9200123"
    }
  }
}
```

## Example Custom Drug Overlay

```json
{
  "version": "org-pack-v1",
  "source": "Approved NGO pediatric formulary 2026",
  "medicines": {
    "paracetamol": {
      "dose_per_kg": 15,
      "unit": "mg",
      "frequency": "every 6 hours",
      "max_doses_per_day": 4
    }
  }
}
```
