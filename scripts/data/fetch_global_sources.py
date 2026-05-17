from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SNAPSHOT_DIR = DATA_DIR / "source_snapshots"
MANIFEST_PATH = ROOT / "scripts" / "data" / "global_sources_manifest.json"


SOURCE_DEFINITIONS = [
    {
        "id": "who_eml_2025",
        "output": SNAPSHOT_DIR / "who_essential_medicines_2025.json",
        "payload": {
            "source_id": "who_eml_2025",
            "title": "The selection and use of essential medicines, 2025: WHO Model List of Essential Medicines, 24th list",
            "publisher": "World Health Organization",
            "publication_date": "2025-09-05",
            "document_type": "Technical document",
            "reference_number": "B09474",
            "source_url": "https://www.who.int/publications/i/item/B09474",
            "index_url": "https://www.who.int/groups/expert-committee-on-selection-and-use-of-essential-medicines/essential-medicines-lists",
            "license": "WHO site lists Creative Commons licensing on publication page",
            "snapshot_kind": "metadata_only",
            "notes": [
                "Current WHO EML page says the 24th EML and 10th EMLc were updated in September 2025.",
                "MediVoice currently uses a curated offline subset of medicine dosing rather than the full WHO list.",
                "This snapshot records the official source for provenance and future normalization work.",
            ],
            "current_list_facts": {
                "eml_revision": "24th list",
                "emlc_revision": "10th list",
                "updated_month": "2025-09",
            },
            "medivoice_subset_candidates": [
                "paracetamol",
                "amoxicillin",
                "oral rehydration salts",
                "zinc",
                "ibuprofen",
                "cotrimoxazole",
            ],
        },
    },
    {
        "id": "who_imci_2014",
        "output": SNAPSHOT_DIR / "who_imci_2014.json",
        "payload": {
            "source_id": "who_imci_2014",
            "title": "IMCI chart booklet",
            "publisher": "World Health Organization",
            "publication_date": "2014-06-15",
            "document_type": "Publication",
            "isbn": "978 92 4 150682 3",
            "source_url": "https://apo.who.int/publications/i/item/9789241506823",
            "download_url": "https://iris.who.int/",
            "snapshot_kind": "metadata_only",
            "scope": {
                "audience": "Doctors, nurses and health professionals caring for sick children under five",
                "sections": [
                    "Sick child aged 2 months to 5 years",
                    "Sick young infant aged up to 2 months",
                ],
            },
            "notes": [
                "The publication page says the booklet reflects technical updates published in 2012.",
                "MediVoice currently uses a starter JSON protocol derived from IMCI concepts, not a full chart-by-chart conversion.",
                "This snapshot anchors the current WHO source for future structured extraction work.",
            ],
        },
    },
    {
        "id": "official_referral_registries",
        "output": SNAPSHOT_DIR / "official_referral_registries.json",
        "payload": {
            "source_id": "official_referral_registries",
            "snapshot_kind": "catalog",
            "entries": [
                {
                    "country": "Kenya",
                    "registry_name": "Kenya Master Health Facility Registry",
                    "status": "official_registry_catalogued",
                    "source_url": "https://kmhfr.health.go.ke/public/about",
                    "api_docs_url": "https://mfl-api-docs.readthedocs.io/en/latest",
                    "owner": "Republic of Kenya, Ministry of Health",
                    "notes": [
                        "The official about page says KMHFR contains all health facilities and community units in Kenya.",
                        "The page also says KMHFR provides a RESTful API for developers.",
                        "MediVoice does not yet bundle a full Kenya facility extract.",
                    ],
                },
                {
                    "country": "Nigeria",
                    "registry_name": "Nigeria Health Facility Registry",
                    "status": "official_registry_catalogued",
                    "source_url": "https://hfr.health.gov.ng/about-us",
                    "owner": "Federal Ministry of Health and Social Welfare, Nigeria",
                    "notes": [
                        "The about page says the HFR was developed in 2017 to dynamically manage the Master Health Facility List.",
                        "The public site exposes Facilities List and Data Downloads sections.",
                        "MediVoice does not yet bundle a full Nigeria facility extract.",
                    ],
                },
                {
                    "country": "Pakistan",
                    "registry_name": "NHSRC downloads and health facility policy documents",
                    "status": "official_document_catalogued",
                    "source_url": "https://www.nhsrc.gov.pk/download",
                    "owner": "Ministry of National Health Services, Regulations and Coordination",
                    "notes": [
                        "The downloads page contains official advisories, policies, and health-facility related publications.",
                        "MediVoice currently uses a curated Pakistan referral starter pack, not a ministry export.",
                        "This source is catalogued for future normalization of official Pakistan reference material.",
                    ],
                },
            ],
        },
    },
]


def build_manifest() -> dict:
    return {
        "description": (
            "Source manifest for official public references that MediVoice tracks and "
            "converts into offline-friendly snapshots."
        ),
        "generated_files": [str(item["output"].relative_to(ROOT)).replace("\\", "/") for item in SOURCE_DEFINITIONS],
        "sources": [
            {
                "id": item["id"],
                "output": str(item["output"].relative_to(ROOT)).replace("\\", "/"),
                "status": "imported_snapshot",
                "source_url": item["payload"].get("source_url"),
                "snapshot_kind": item["payload"]["snapshot_kind"],
            }
            for item in SOURCE_DEFINITIONS
        ],
    }


def write_snapshot_files() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for item in SOURCE_DEFINITIONS:
        item["output"].write_text(json.dumps(item["payload"], indent=2), encoding="utf-8")


def main() -> None:
    write_snapshot_files()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(build_manifest(), indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH}")
    for item in SOURCE_DEFINITIONS:
        print(f"Wrote {item['output']}")


if __name__ == "__main__":
    main()
