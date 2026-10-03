import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_ux_layers_are_wired_in_safe_order():
    index = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert index.index("markdown_renderer.js") < index.index("chat_view.js")
    assert index.index("ux_enhancements.js") > index.index("feedback_bridge.js")
    assert 'maxlength="12000"' in index


def test_markdown_renderer_is_dependency_free_and_safe():
    text = (ROOT / "frontend/markdown_renderer.js").read_text(encoding="utf-8")
    assert "api.escapeHtml" in text
    assert "https?:\\/\\/" in text
    assert "<strong>" in text and "<em>" in text
    assert "code-block" in text
    assert "highlightCode" in text
    assert "code-keyword" in text
    assert "api.renderMarkdown" in text


def test_ux_layer_covers_copy_retry_stop_counter_and_guided_auth():
    text = (ROOT / "frontend/ux_enhancements.js").read_text(encoding="utf-8")
    for marker in (
        "navigator.clipboard",
        "ux-retry",
        "api.cancelActiveChat?.()",
        "Response stopped by you",
        "12_000",
        "unauthorized",
        "Guest test mode",
        "Open Settings",
        "ux-icon",
        "renderMarkdownMessages",
    ):
        assert marker in text


def test_frontend_error_feedback_boundary_remains_enforced():
    text = (ROOT / "frontend/feedback_bridge.js").read_text(encoding="utf-8")
    assert "message-error" in text


def test_research_first_use_fallback_remains_present():
    text = (ROOT / "frontend/lifecycle_controller.js").read_text(encoding="utf-8")
    assert "currentChatId() || api.ensureChat().id" in text


def test_ux_bootstrap_is_parse_safe_and_event_driven():
    text = (ROOT / "frontend/ux_enhancements.js").read_text(encoding="utf-8")
    assert "document.readyState === 'loading'" in text
    assert (
        "document.addEventListener('DOMContentLoaded', start, { once: true })" in text
    )
    assert "rie:chat-updated" in text
    assert "new MutationObserver" not in text
    assert "window.setInterval(observe, 250)" not in text


def test_chat_submit_creates_first_chat_when_none_is_active():
    text = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
    assert re.search(r"const activeChatId = chatId \\|\\| api\\.ensureChat\\(\\)\\.id;", text)
    assert text.count("chat_id: activeChatId") >= 2
    assert text.count("detail: { chatId: activeChatId, requestId, body }") == 1
    assert text.count("detail: { chatId, requestId, body }") == 1
    assert (
        "detail: { chatId: activeChatId, requestId, responseId, partial: Boolean(answer) }"
        in text
    )
