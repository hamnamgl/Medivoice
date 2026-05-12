from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "scripts" / "data" / "global_sources_manifest.json"


def build_manifest() -> dict:
    return {
        "description": "Starter manifest for public data sources that MediVoice can normalize into offline bundles.",
        "sources": [
            {
                "name": "WHO Essential Medicines Lists",
                "type": "global_medicines",
                "url": "https://www.who.int/groups/expert-committee-on-selection-and-use-of-essential-medicines/essential-medicines-lists",
                "status": "planned",
            },
            {
                "name": "WHO IMCI guidance",
                "type": "global_protocols",
                "url": "https://apo.who.int/publications/i/item/9789241506823",
                "status": "planned",
            },
            {
                "name": "Kenya Master Health Facility Registry",
                "type": "country_referrals",
                "url": "https://kmhfr.health.go.ke/public/about",
                "status": "planned",
            },
            {
                "name": "Pakistan NHSRC downloads",
                "type": "country_protocols",
                "url": "https://nhsrc.gov.pk/download",
                "status": "planned",
            },
        ],
    }


def main() -> None:
    manifest = build_manifest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
