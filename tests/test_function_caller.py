import pytest
from pathlib import Path
import app.core.function_caller as function_module
from app.core.function_caller import execute_function, run_agent


class DummyMessage:
    def __init__(self, content="Test response"):
        self.content = content

    def get(self, key, default=None):
        if key == "content":
            return self.content
        if key == "tool_calls":
            return None
        return default


class DummyChunk:
    def __init__(self, content="Test response"):
        self.message = DummyMessage(content)

    def get(self, key, default=None):
        if key == "message":
            return self.message
        return default


class DummyOllama:
    def chat(self, **kwargs):
        if kwargs.get("stream"):
            return [DummyChunk("Test response")]
        return DummyChunk("Test response")


def test_execute_function_runs_triage():
    result = execute_function("assess_triage", {"symptom_text": "tez bukhar 3 din se"})
    assert "level" in result or "REFER" in result or "HOME" in result


def test_execute_function_handles_unknown_name():
    result = execute_function("unknown_function", {})
    assert "Unknown" in result or "unknown" in result.lower()


def test_run_agent_uses_tool_and_returns_final_response(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    result = run_agent("Bachche ko 3 din se tez bukhar hai")
    assert "response" in result
    assert isinstance(result["response"], str)
    assert "history" in result


def test_run_agent_routes_drug_queries_without_model(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    result = run_agent("15kg child - paracetamol dosage?")
    assert result["tool_used"] == "get_drug_dosage"
    assert "225 mg" in result["response"]


def test_run_agent_routes_referral_queries_without_model(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    result = run_agent("Nearest hospital in Punjab?")
    assert result["tool_used"] == "lookup_referral"
    assert "Punjab" in result["response"] or "Rawalpindi" in result["response"]


def test_run_agent_first_turn_asks_duration(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    result = run_agent("I am feeling sick", [])
    assert result["tool_used"] is None
    assert "how long" in result["response"].lower()


def test_run_agent_third_turn_asks_danger_sign(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    history = []
    result = run_agent("I am sick", history)
    history = result["history"]
    result = run_agent("for 1 week", history)
    history = result["history"]
    result = run_agent("fever", history)
    assert "unconscious" in result["response"].lower() or "bleeding" in result["response"].lower()


def test_run_agent_fourth_turn_returns_verdict(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    history = []
    for text in ["I am sick", "for 1 week", "fever", "no bleeding"]:
        result = run_agent(text, history)
        history = result["history"]
    assert result["tool_used"] == "assess_triage"
    assert result["response"].startswith(("HOME CARE:", "REFER TO CLINIC:", "EMERGENCY:"))


def test_custom_referral_overlay_merges_regions(monkeypatch, tmp_path):
    custom_referrals = tmp_path / "referrals.json"
    custom_referrals.write_text(
        '{"country":"Custom","emergency":"999","facilities":{"punjab":{"gujranwala":"DHQ Gujranwala - 055"}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(function_module, "CUSTOM_REFERRALS_FILE", custom_referrals)
    merged = function_module._load_referral_data()
    assert merged["facilities"]["punjab"]["gujranwala"] == "DHQ Gujranwala - 055"
    assert "rawalpindi" in merged["facilities"]["punjab"]


def test_custom_drug_overlay_adds_medicine(monkeypatch, tmp_path):
    custom_drugs = tmp_path / "drugs.json"
    custom_drugs.write_text(
        '{"version":"custom","source":"test","medicines":{"testmed":{"fixed_dose":5,"unit":"mg","frequency":"once daily"}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(function_module, "CUSTOM_DRUGS_FILE", custom_drugs)
    merged = function_module._load_drug_data()
    assert merged["medicines"]["testmed"]["fixed_dose"] == 5
    assert "paracetamol" in merged["medicines"]
