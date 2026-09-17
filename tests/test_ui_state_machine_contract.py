from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_ui_contract_covers_required_lifecycle_states():
    text = (ROOT / "docs" / "UI_STATE_MACHINE_CONTRACT.md").read_text(encoding="utf-8")
    for state in ("NEW_CHAT", "SUBMITTING", "QUEUED", "RUNNING", "STREAMING", "COMPLETE", "PARTIAL", "BLOCKED", "REJECTED", "UNAVAILABLE", "UNKNOWN", "RECONNECTING", "RESUMED", "REPLAYED", "AUTH_EXPIRED"): assert state in text

def test_ui_contract_preserves_backend_authority_and_no_false_success():
    text = (ROOT / "docs" / "UI_STATE_MACHINE_CONTRACT.md").read_text(encoding="utf-8")
    assert "Missing fields are `UNKNOWN`, never success." in text
    assert "backend result states remain authoritative" in text
    assert "Provider names, policy internals, credentials and protected diagnostics are never UI state." in text

def test_research_requires_active_chat_and_replay_is_deterministic():
    text = (ROOT / "docs" / "UI_STATE_MACHINE_CONTRACT.md").read_text(encoding="utf-8")
    assert "Research requires an active chat before submission." in text
    assert "Replayed events must not manufacture a second completion." in text
