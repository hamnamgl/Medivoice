from uuid import uuid4

import app.utils.local_db as db_module


def test_local_db_visit_logging_and_stats(monkeypatch, tmp_path):
    temp_db = tmp_path / f"test_medivoice_{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DB_PATH", temp_db)

    db_module.init_db()
    db_module.log_visit(
        symptoms="Bachche ko 3 din se tez bukhar",
        severity="REFER",
        action="CLINIC REFER KAREIN",
        language="ur",
    )
    db_module.log_visit(
        symptoms="Mareez behosh ho gaya",
        severity="EMERGENCY",
        action="FORAN HOSPITAL",
        language="ur",
    )

    recent = db_module.get_recent_visits(5)
    stats = db_module.get_stats()

    assert len(recent) == 2
    assert stats["total_visits"] == 2
    assert stats["emergencies"] == 1
    assert stats["referrals"] == 1


def test_local_db_settings_roundtrip(monkeypatch, tmp_path):
    temp_db = tmp_path / f"test_settings_{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DB_PATH", temp_db)

    db_module.init_db()
    db_module.save_setting("language", "ur")

    assert db_module.get_setting("language") == "ur"
    assert db_module.get_setting("missing", "default") == "default"
