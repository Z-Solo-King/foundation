import array
from datetime import datetime, timezone

import pytest

from backend.persistence.artifacts import (
    ArtifactStore,
    B2ArtifactStore,
    _response_bytes,
    artifact_store_from_env,
)


class FakeResponse:
    def __init__(self, status=200, body=b"", text_body=""):
        self.status = status
        self.body = body
        self.text_body = text_body

    async def text(self):
        return self.text_body

    async def bytes(self):
        return self.body


class FakeFetcher:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def __call__(self, url, options):
        self.calls.append((url, options))
        return self.response


class ToPyBytes:
    def to_py(self):
        return b"bytes"


class ToPyBytearray:
    def to_py(self):
        return bytearray(b"bytearray")


class ToPyMemoryview:
    def to_py(self):
        return memoryview(b"memoryview")


class ToPyToBytes:
    def to_py(self):
        return self

    def to_bytes(self):
        return b"nested"


class DirectToBytes:
    def to_bytes(self):
        return b"direct"


class NestedToPy:
    def to_bytes(self):
        return ToPyMemoryview()


def test_artifact_store_base_methods_are_abstract_by_behavior():
    store = ArtifactStore()
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.run(store.put("x", b"y"))
    with pytest.raises(NotImplementedError):
        import asyncio
        assert asyncio.run(store.get("x")) is None
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.run(store.delete("x"))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (b"native", b"native"),
        (bytearray(b"array"), b"array"),
        (memoryview(b"view"), b"view"),
        (ToPyBytes(), b"bytes"),
        (ToPyBytearray(), b"bytearray"),
        (ToPyMemoryview(), b"memoryview"),
        (ToPyToBytes(), b"nested"),
        (DirectToBytes(), b"direct"),
        (NestedToPy(), b"memoryview"),
        (array.array("B", [1, 2, 3]), b"\x01\x02\x03"),
    ],
)
def test_response_bytes_accepts_workers_and_pyodide_shapes(value, expected):
    assert _response_bytes(value) == expected


@pytest.mark.parametrize(
    ("bucket", "endpoint", "key_id", "app_key"),
    [
        ("", "https://s3.eu-central-003.backblazeb2.com", "id", "secret"),
        ("bucket", "", "id", "secret"),
        ("bucket", "http://s3.eu-central-003.backblazeb2.com", "id", "secret"),
        ("bucket", "https://example.com", "id", "secret"),
        ("bucket", "https://s3.eu-central-003.backblazeb2.com", "", "secret"),
        ("bucket", "https://s3.eu-central-003.backblazeb2.com", "id", ""),
    ],
)
def test_b2_rejects_invalid_configuration(bucket, endpoint, key_id, app_key):
    with pytest.raises(ValueError):
        B2ArtifactStore(bucket, endpoint, key_id, app_key)


def test_b2_valid_configuration_url_and_key_validation():
    store = B2ArtifactStore(
        "SoloKing",
        "https://s3.eu-central-003.backblazeb2.com/",
        "id",
        "secret",
    )
    assert store.host == "s3.eu-central-003.backblazeb2.com"
    assert store.region == "eu-central-003"
    assert store._url("reports/run.json").endswith("/SoloKing/reports/run.json")

    for key in ("", "/absolute", "a\\b", "a//b", "./a", "a/../b", "a/./b"):
        with pytest.raises(ValueError):
            store._url(key)


def test_b2_authorization_is_deterministic_and_content_type_sensitive():
    store = B2ArtifactStore(
        "SoloKing",
        "https://s3.eu-central-003.backblazeb2.com",
        "id",
        "secret",
    )
    now = datetime(2026, 9, 21, tzinfo=timezone.utc)
    h1, auth1 = store._authorization(
        "GET",
        store._url("a.txt"),
        b"",
        now,
        None,
    )
    h2, auth2 = store._authorization(
        "PUT",
        store._url("a.txt"),
        b"body",
        now,
        "text/plain",
    )
    assert h1["host"] == store.host
    assert "content-type" not in h1
    assert h2["content-type"] == "text/plain"
    assert auth1.startswith("AWS4-HMAC-SHA256 ")
    assert auth2.startswith("AWS4-HMAC-SHA256 ")


@pytest.mark.asyncio
async def test_b2_request_put_get_delete_and_error_paths():
    store = B2ArtifactStore(
        "SoloKing",
        "https://s3.eu-central-003.backblazeb2.com",
        "id",
        "secret",
    )
    fetcher = FakeFetcher(FakeResponse(200, b"payload", "ok"))
    store._workers_fetch = lambda: fetcher

    await store.put("run/a.json", b"payload", content_type="application/json")
    body = await store.get("run/a.json")
    await store.delete("run/a.json")
    assert body == b"payload"
    assert len(fetcher.calls) == 3
    assert fetcher.calls[0][1]["method"] == "PUT"
    assert fetcher.calls[0][1]["body"] == b"payload"
    assert fetcher.calls[1][1]["method"] == "GET"
    assert fetcher.calls[1][1]["body"] is None
    assert fetcher.calls[2][1]["method"] == "DELETE"
    assert fetcher.calls[2][1]["body"] is None

    not_found = FakeFetcher(FakeResponse(404))
    store._workers_fetch = lambda: not_found
    assert await store.get("missing.json") is None

    failed = FakeFetcher(FakeResponse(500, text_body="failure"))
    store._workers_fetch = lambda: failed
    with pytest.raises(RuntimeError, match="B2 PUT failed"):
        await store.put("bad.json", b"x")
    with pytest.raises(RuntimeError, match="B2 GET failed"):
        await store.get("bad.json")
    with pytest.raises(RuntimeError, match="B2 DELETE failed"):
        await store.delete("bad.json")


def test_artifact_store_from_env():
    class Env:
        B2_BUCKET = "SoloKing"
        B2_ENDPOINT = "https://s3.eu-central-003.backblazeb2.com"
        B2_KEY_ID = "id"
        B2_APPLICATION_KEY = "secret"

    store = artifact_store_from_env(Env())
    assert isinstance(store, B2ArtifactStore)
    assert store.bucket == "SoloKing"
