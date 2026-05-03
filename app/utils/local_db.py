from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(db_path: str = "medivoice.db") -> sqlite3.Connection:
    path = Path(db_path)
    return sqlite3.connect(path)
