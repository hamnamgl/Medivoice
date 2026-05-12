import pytest
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
