# Custom Data Pack

This folder is for organization-specific local data that can safely override the built-in offline bundle.

Use this folder for:

- district or NGO referral facilities
- local emergency phone numbers
- approved local formulary overrides

Do not use this folder for:

- changing core triage danger signs without clinical review
- editing weight-based dosing without an approved supervisor or medical source

Files:

- `referrals.json`: optional overlay for facility and emergency contact data
- `drugs.json`: optional overlay for local medicines or approved dosing adjustments

Example `referrals.json` shape:

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

Example `drugs.json` shape:

```json
{
  "version": "org-pack-v1",
  "source": "Approved NGO pediatric formulary 2026",
  "medicines": {
    "paracetamol": {
      "dose_per_kg": 15,
      "unit": "mg",
      "frequency": "every 6 hours",
      "max_doses_per_day": 4,
      "notes": "Use only supervisor-approved local guidance"
    }
  }
}
```

At runtime, MediVoice loads built-in data first and then applies these custom overlays on top.
