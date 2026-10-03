from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROXY = ROOT / "scripts" / "research_worker_proxy.mjs"


def test_research_proxy_is_current_javascript_boundary() -> None:
    assert PROXY.is_file()
    result = subprocess.run(
        ["node", "--check", str(PROXY)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_research_proxy_uses_bounded_retry_and_explicit_proof_headers() -> None:
    text = PROXY.read_text(encoding="utf-8")
    assert "MAX_UPSTREAM_ATTEMPTS = 3" in text
    assert "Idempotency-Key" in text
    assert "X-Heroic-Research-Proof" in text
    assert "UPSTREAM_USER_AGENT" in text


def test_research_proxy_requires_model_generated_provider_proof() -> None:
    text = PROXY.read_text(encoding="utf-8")
    assert 'response.generation_status !== "model_generated"' in text
    assert "upstream_worker_rejected" in text
