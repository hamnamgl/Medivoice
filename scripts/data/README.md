# Data Import Workflow

This folder is for source-driven data ingestion and normalization.

## What exists now

`fetch_global_sources.py` writes official-source snapshot metadata into:

- `data/source_snapshots/who_essential_medicines_2025.json`
- `data/source_snapshots/who_imci_2014.json`
- `data/source_snapshots/official_referral_registries.json`
- `scripts/data/global_sources_manifest.json`

These are provenance snapshots, not final runtime datasets.

## Goal

- track public or official sources
- keep provenance outside runtime logic
- normalize selected content into `data/` JSON files used by the app

## Recommended workflow

1. fetch or catalogue an official source
2. save a reproducible local snapshot or metadata record
3. clean and normalize only the fields MediVoice needs
4. write app-friendly JSON into `data/`
5. update `data/SOURCES.md`
6. mark output as `placeholder`, `curated`, `starter`, or `verified`

## Important

- the app should not depend on live URLs at runtime
- runtime should use local offline snapshots only
- full source exports and runtime subsets should stay clearly separated
