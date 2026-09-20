from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_frontend_chat_stream_has_explicit_cancellation_contract():
    text = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    assert "new AbortController()" in text
    assert "signal: abortController.signal" in text
    assert "reader.cancel()" in text
    assert "chat-stream-cancelled" in text
    assert "backend_state: 'UNKNOWN'" in text
    assert "client_cancelled: true" in text
    assert "cancelButton.hidden = false" in text
    assert "cancelButton.hidden = true" in text
