from pathlib import Path


def test_frontend_uses_same_origin_api_by_default():
    source = Path("frontend/frontend_state.js").read_text(encoding="utf-8")
    assert "window.location.origin" in source
    assert "data-api-base" in source


def test_chat_ui_calls_canonical_chat_route_and_clears_pending_state():
    app = Path("frontend/app.js").read_text(encoding="utf-8")
    view = Path("frontend/chat_view.js").read_text(encoding="utf-8")
    assert "/api/v1/chat" in app
    assert "Idempotency-Key" in app
    assert "pending: false" in app
    assert "Request failed" in view
    assert "Heroic AI" in view


def test_guest_test_mode_is_explicit_and_network_free():
    state = Path("frontend/frontend_state.js").read_text(encoding="utf-8")
    app = Path("frontend/app.js").read_text(encoding="utf-8")
    contract = Path("frontend/guest_test_mode_contract_test.mjs").read_text(encoding="utf-8")
    product = Path("docs/HEROIC_AI_PRODUCT.md").read_text(encoding="utf-8")
    assert "guestTestMode" in state
    assert "enableGuestTestMode" in state
    assert "disableGuestTestMode" in state
    assert "submitGuestTestChat" in app
    assert "guest_test: true" in app
    assert "deterministic simulation" in app
    assert "Message is required" in app
    assert "12000 character limit" in app
    assert "guest_test_mode_contract_test: PASS" in contract
    assert "Guest Test mode" in product
    assert "TEST_ONLY" in app
    assert "deterministic_test" in app
    guest_start = app.index("async function submitGuestTestChat")
    guest_end = app.index("async function consumeChatStream")
    guest_block = app[guest_start:guest_end]
    assert "fetch(" not in guest_block
    assert "Authorization" not in guest_block


def test_session_settings_are_functional():
    view = Path("frontend/chat_view.js").read_text(encoding="utf-8")
    assert 'data-action="save-session-token"' in view
    assert 'data-action="clear-session-token"' in view
    assert "sessionStorage.setItem" in view


def test_chat_render_updates_changed_messages_without_rebuilding_every_message():
    view = Path("frontend/chat_view.js").read_text(encoding="utf-8")
    assert "messageRenderSignature" in view
    assert "data-render-signature" in view
    assert "node.outerHTML = messageHtml(message)" in view
    assert "chat.messages.map(messageHtml).join('')" in view


def test_dashboard_exposes_truthful_provider_telemetry():
    js = Path("frontend/dashboard.js").read_text(encoding="utf-8")
    assert "recent_failures" in js
    assert "metricReason" in js
    assert "Unavailable" in js
    assert "dashboard_auth_required" in js


def test_dashboard_styles_cover_provenance_and_errors():
    css = Path("frontend/dashboard.css").read_text(encoding="utf-8")
    assert ".dashboard-provenance" in css
    assert ".dashboard-provider-resource" in css
    assert ".dashboard-error" in css
