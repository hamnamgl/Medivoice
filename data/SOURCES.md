# Data Sources

This file tracks where MediVoice data comes from and whether it is fully verified, curated, or still placeholder content.

## Current Status

### Built-in drugs

- File: `data/drugs/essential_medicines.json`
- Status: `curated`
- Basis: WHO Essential Medicines list structure, manually converted into app-friendly JSON
- Notes: Good for demo and offline routing, but should still be clinically reviewed before field deployment

### Built-in Pakistan referrals

- File: `data/referrals/pk_facilities.json`
- Status: `curated`
- Basis: manually assembled referral entries for demo use
- Notes: useful for demonstration, but should be replaced with a larger verified registry before real deployment

### Built-in Kenya referrals

- File: `data/referrals/ke_facilities.json`
- Status: `placeholder`
- Notes: currently only starter content and not suitable as a nationwide facility registry

### Built-in Nigeria referrals

- File: `data/referrals/ng_facilities.json`
- Status: `placeholder`
- Notes: currently only starter content and not suitable as a nationwide facility registry

### Built-in protocols

- Files: `data/protocols/*.json`
- Status:
  - `generic_triage.json`: `curated`
  - `who_imci.json`: `placeholder/starter`
  - `pakistan_lhw.json`: `starter`
  - `nigeria_chew.json`: `starter`
  - `ethiopia_hew.json`: `starter`
- Notes: these are not yet full official protocol conversions

## Recommended Source Strategy

For production-grade deployment, replace or expand current files using:

- WHO IMCI official guidance for child triage
- WHO Essential Medicines list for baseline dosing structure
- ministry or registry facility exports for each supported country
- organization-specific overlays in `data/custom/`

## Overlay Model

MediVoice is designed to use:

1. built-in offline core data
2. optional organization-specific overlays in `data/custom/`

This allows an NGO, district program, or clinic network to add local facilities and approved medicine variations without modifying the core bundled files directly.
