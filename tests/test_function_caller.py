import app.core.function_caller as function_module
from app.core.function_caller import execute_function, run_agent


class DummyOllama:
    def __init__(self):
        self.calls = 0

    def chat(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "assess_triage",
                                "arguments": {"symptom_text": "high fever for 3 days"},
                            }
                        }
                    ]
                }
            }
        return {"message": {"content": "Clinic le jayen. REFER TO CLINIC"}}


def test_execute_function_runs_triage():
    result = execute_function("assess_triage", {"symptom_text": "high fever for 3 days"})
    assert '"level": "REFER"' in result


def test_execute_function_handles_unknown_name():
    result = execute_function("missing_function", {})
    assert result == "Unknown function: missing_function"


def test_run_agent_uses_tool_and_returns_final_response(monkeypatch):
    monkeypatch.setattr(function_module, "ollama", DummyOllama())
    result = run_agent("Bachche ko 3 din se tez bukhar hai")
    assert result["tool_used"] == "assess_triage"
    assert "REFER TO CLINIC" in result["response"]
