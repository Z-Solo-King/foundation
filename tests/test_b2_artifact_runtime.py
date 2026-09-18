from __future__ import annotations

import asyncio

from backend.persistence.artifacts import B2ArtifactStore


class _Response:
    status = 200

    async def bytes(self):
        return b"artifact-body"

    async def text(self):
        return ""

def test_b2_get_uses_python_workers_bytes_response_method(monkeypatch):
    store = B2ArtifactStore(
        bucket="SoloKing",
        endpoint="https://s3.eu-central-003.backblazeb2.com",
        key_id="key-id",
        application_key="application-key",
    )

    async def fake_request(method, key, body=b"", content_type=None):
        assert method == "GET"
        assert key == "diagnostics/test"
        return _Response()

    monkeypatch.setattr(store, "_request", fake_request)
    value = asyncio.run(store.get("diagnostics/test"))
    assert value == b"artifact-body"
