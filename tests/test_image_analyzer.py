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
        assert "Yeh wound kaisa lag raha hai?" in result
    finally:
        import os

        if os.path.exists(image_file):
            os.remove(image_file)
