from app.main import image_command_path, parse_action_label
from scripts.data.fetch_global_sources import build_manifest


def test_parse_action_label_handles_known_prefixes():
    assert parse_action_label("EMERGENCY: go now") == "EMERGENCY"
    assert parse_action_label("REFER TO CLINIC: seen today") == "REFER"
    assert parse_action_label("HOME CARE: fluids and rest") == "HOME CARE"
    assert parse_action_label("Can you tell me more?") == "FOLLOW_UP"


def test_image_command_path_strips_quotes():
    assert image_command_path('image "C:\\tmp\\rash.jpg"') == "C:\\tmp\\rash.jpg"
    assert image_command_path("image 'C:\\tmp\\rash.jpg'") == "C:\\tmp\\rash.jpg"
    assert image_command_path("voice") is None


def test_build_manifest_marks_sources_as_imported_snapshots():
    manifest = build_manifest()
    assert manifest["generated_files"]
    assert all(source["status"] == "imported_snapshot" for source in manifest["sources"])
    assert any(source["id"] == "who_eml_2025" for source in manifest["sources"])
    assert any(source["id"] == "pakistan_federal_hospitals_sample" for source in manifest["sources"])
