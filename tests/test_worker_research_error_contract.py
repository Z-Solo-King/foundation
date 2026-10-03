from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROXY = ROOT / "scripts" / "research_worker_proxy.mjs"


def test_research_proxy_initializes_request_identity_before_upstream_call() -> None:
    source = PROXY.read_text(encoding="utf-8")
    assert 'const requestId = "research-proxy-" + randomUUID()' in source
    assert '"Idempotency-Key: " + requestId' in source
    assert source.index("const requestId =") < source.index("const upstreamPayload =")


def test_research_proxy_rejects_unproven_model_execution() -> None:
    source = PROXY.read_text(encoding="utf-8")
    assert 'response.generation_status !== "model_generated"' in source
    assert 'type: "provider_execution_not_proven"' in source
