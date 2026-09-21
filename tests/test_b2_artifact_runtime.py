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



def test_b2_get_converts_pyodide_jsproxy_response_bytes(monkeypatch):
    store = B2ArtifactStore(
        bucket="SoloKing",
        endpoint="https://s3.eu-central-003.backblazeb2.com",
        key_id="key-id",
        application_key="application-key",
    )

    class JsProxyBytes:
        def to_py(self):
            return memoryview(b"proxy-artifact-body")

    class Response:
        status = 200

        async def bytes(self):
            return JsProxyBytes()

        async def text(self):
            return ""

    async def fake_request(method, key, body=b"", content_type=None):
        return Response()

    monkeypatch.setattr(store, "_request", fake_request)
    value = asyncio.run(store.get("diagnostics/proxy"))
    assert value == b"proxy-artifact-body"


def test_response_bytes_covers_worker_and_pyodide_binary_shapes():
    from backend.persistence.artifacts import _response_bytes

    class ToPyBytearray:
        def to_py(self):
            return bytearray(b"bytearray")

    class ToPyTobytes:
        class Converted:
            def tobytes(self):
                return b"tobytes"
        def to_py(self):
            return self.Converted()

    class ToBytesBytearray:
        def to_bytes(self):
            return bytearray(b"to-bytes")

    class ToBytesNested:
        class Converted:
            def to_py(self):
                return memoryview(b"nested")
        def to_bytes(self):
            return self.Converted()

    assert _response_bytes(b"bytes") == b"bytes"
    assert _response_bytes(bytearray(b"array")) == b"array"
    assert _response_bytes(memoryview(b"memory")) == b"memory"
    assert _response_bytes(ToPyBytearray()) == b"bytearray"
    assert _response_bytes(ToPyTobytes()) == b"tobytes"
    assert _response_bytes(ToBytesBytearray()) == b"to-bytes"
    assert _response_bytes(ToBytesNested()) == b"nested"
    assert _response_bytes(bytearray(b"fallback")) == b"fallback"


def test_artifact_store_from_env_materializes_b2_configuration():
    from types import SimpleNamespace
    from backend.persistence.artifacts import artifact_store_from_env

    store = artifact_store_from_env(
        SimpleNamespace(
            B2_BUCKET="SoloKing",
            B2_ENDPOINT="https://s3.eu-central-003.backblazeb2.com",
            B2_KEY_ID="key-id",
            B2_APPLICATION_KEY="application-key",
        )
    )
    assert store.bucket == "SoloKing"
    assert store.region == "eu-central-003"
    assert store.key_id == "key-id"
