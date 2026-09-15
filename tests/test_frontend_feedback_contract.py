from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_feedback_contract_is_typed_and_candidate_only():
    text = (ROOT / "frontend/feedback_contract.js").read_text(encoding="utf-8")
    assert "chat-feedback/v1" in text
    assert "authority: 'candidate'" in text
    assert "evidence_overwrite_allowed: false" in text
    assert "localStorage" not in text


def test_feedback_bridge_never_sends_raw_chat_content():
    text = (ROOT / "frontend/feedback_bridge.js").read_text(encoding="utf-8")
    assert "user_text" not in text
    assert "assistant_text" not in text
    assert "localStorage" in text
    assert "task_success" in text
    assert "task_failure" in text


def test_index_wires_feedback_layers_before_bridge():
    text = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert text.index("feedback_contract.js") < text.index("app.js")
    assert text.index("feedback_bridge.js") > text.index("app.js")
