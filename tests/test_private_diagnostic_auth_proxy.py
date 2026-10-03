from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_private_diagnostic_runtime_is_not_public_source_owned() -> None:
    assert not (ROOT / "worker.py").exists()
    assert not (ROOT / "backend").exists()
    assert not (ROOT / "operations").exists()


def test_public_edge_uses_only_the_public_core_service_binding() -> None:
    edge = (ROOT / "edge.ts").read_text(encoding="utf-8")
    wrangler = (ROOT / "wrangler.toml").read_text(encoding="utf-8")
    assert "env.CORE.fetch(forwardRequest(request))" in edge
    assert 'binding = "CORE"' in wrangler
    assert 'service = "heroic-core"' in wrangler
    assert "private.chatbot" not in edge
    assert "operations-edge" not in edge
