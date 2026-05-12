import app.core.image_analyzer as image_module


class DummyOllama:
    def chat(self, *, model, messages):
        return {"message": {"content": f"{model}: {messages[0]['content']}"}}


def test_analyze_image_returns_missing_file_message():
    result = image_module.analyze_image("tests/does-not-exist.jpg")
    assert result == "Image file nahi mili"


def test_analyze_image_calls_ollama(monkeypatch):
    image_file = "tests/mock_wound.jpg"
    with open(image_file, "wb") as file_handle:
        file_handle.write(b"fake-image-data")
    monkeypatch.setattr(image_module, "ollama", DummyOllama())
    try:
        result = image_module.analyze_image(image_file, "Yeh wound kaisa lag raha hai?")
        assert "gemma4:e4b" in result
        assert "Roman Urdu" not in result
        assert "Yeh wound kaisa lag raha hai?" in result
    finally:
        import os

        if os.path.exists(image_file):
            os.remove(image_file)


def test_analyze_image_falls_back_when_first_model_fails(monkeypatch):
    image_file = "tests/mock_wound.jpg"
    with open(image_file, "wb") as file_handle:
        file_handle.write(b"fake-image-data")

    class FallbackOllama:
        def __init__(self):
            self.calls = 0

        def chat(self, *, model, messages):
            self.calls += 1
            if model == "gemma4:e4b":
                raise RuntimeError("primary failed")
            return {"message": {"content": f"{model}: ok"}}

    monkeypatch.setattr(image_module, "ollama", FallbackOllama())
    try:
        result = image_module.analyze_image(image_file, "What does this rash look like?")
        assert "gemma3:4b" in result
    finally:
        import os

        if os.path.exists(image_file):
            os.remove(image_file)
