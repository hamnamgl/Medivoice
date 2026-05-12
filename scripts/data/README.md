# Data Import Workflow

This folder is for source-driven data ingestion and normalization.

Goal:

- fetch public or official data
- store raw snapshots outside runtime logic
- normalize into `data/` JSON files used by the app

Recommended workflow:

1. fetch source data
2. save or inspect raw export
3. clean and normalize
4. write app-friendly JSON into `data/`
5. update `data/SOURCES.md`

Important:

- the app should not depend on live URLs at runtime
- runtime should use local offline snapshots only
- country packs should be clearly marked as `placeholder`, `curated`, or `verified`
