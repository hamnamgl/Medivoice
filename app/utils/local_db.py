import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "medivoice.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Database aur tables create karo"""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                language TEXT,
                symptoms TEXT,
                severity TEXT,
                action TEXT,
                tool_used TEXT,
                response TEXT,
                image_used INTEGER DEFAULT 0
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )
        conn.commit()


def log_visit(
    symptoms: str,
    severity: str,
    action: str,
    language: str = "unknown",
    tool_used: str = None,
    response: str = None,
    image_used: bool = False,
):
    """CHW visit locally log karo"""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO visits
            (timestamp, language, symptoms, severity, action, tool_used, response, image_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                language,
                symptoms,
                severity,
                action,
                tool_used,
                response,
                int(image_used),
            ),
        )
        conn.commit()


def get_recent_visits(limit: int = 10) -> list:
    """Recent visits return karo"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT timestamp, language, symptoms, severity, action
            FROM visits
            ORDER BY id DESC
            LIMIT ?
        """,
            (limit,),
        )
        cols = [description[0] for description in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_stats() -> dict:
    """Basic stats return karo"""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        emergency = conn.execute(
            "SELECT COUNT(*) FROM visits WHERE severity='EMERGENCY'"
        ).fetchone()[0]
        refer = conn.execute("SELECT COUNT(*) FROM visits WHERE severity='REFER'").fetchone()[0]
        return {
            "total_visits": total,
            "emergencies": emergency,
            "referrals": refer,
            "home_care": total - emergency - refer,
        }


def save_setting(key: str, value: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()


def get_setting(key: str, default: str = None) -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default


if __name__ == "__main__":
    init_db()
    log_visit(
        symptoms="Bachche ko 3 din se tez bukhar",
        severity="REFER",
        action="CLINIC REFER KAREIN",
        language="ur",
        tool_used="assess_triage",
        response="Clinic jana zaroori hai",
    )
    log_visit(
        symptoms="Mareez behosh ho gaya",
        severity="EMERGENCY",
        action="FORAN HOSPITAL",
        language="ur",
    )
    print("Stats:", get_stats())
    print("Recent:", get_recent_visits(5))
