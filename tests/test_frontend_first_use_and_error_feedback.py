from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_research_first_submission_creates_missing_chat():
    text = (ROOT / "frontend/lifecycle_controller.js").read_text(encoding="utf-8")
    assert "item.chat_id || currentChatId() || api.ensureChat().id" in text
    assert "No active chat is available for this research run" not in text


def test_error_messages_do_not_get_answer_quality_feedback():
    text = (ROOT / "frontend/feedback_bridge.js").read_text(encoding="utf-8")
    assert "message.classList.contains('message-error')" in text
    assert text.index("message-error") < text.index("const actions")
