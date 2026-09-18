import json

import pytest

from backend.json_admission import MAX_JSON_COLLECTION_ITEMS, MAX_JSON_DEPTH, validate_json_shape
from backend.worker_auth import MAX_PUBLIC_JSON_BODY_BYTES, json_object


def test_json_shape_accepts_bounded_payload():
    validate_json_shape({"items": [1, {"ok": True}]})


def test_json_shape_rejects_excessive_depth():
    value = {}
    current = value
    for _ in range(MAX_JSON_DEPTH + 1):
        current["nested"] = {}
        current = current["nested"]
    with pytest.raises(ValueError, match="nesting"):
        validate_json_shape(value)


def test_json_shape_rejects_oversized_object():
    with pytest.raises(ValueError, match="field count"):
        validate_json_shape({str(i): i for i in range(MAX_JSON_COLLECTION_ITEMS + 1)})


def test_json_shape_rejects_oversized_array():
    with pytest.raises(ValueError, match="item count"):
        validate_json_shape(list(range(MAX_JSON_COLLECTION_ITEMS + 1)))


def test_json_shape_rejects_invalid_limits():
    with pytest.raises(ValueError, match="max_depth"):
        validate_json_shape({}, max_depth=0)
    with pytest.raises(ValueError, match="max_collection_items"):
        validate_json_shape({}, max_collection_items=0)
    with pytest.raises(ValueError, match="max_string_chars"):
        validate_json_shape({}, max_string_chars=0)


class Request:
    def __init__(self, payload, *, raw=None):
        self.headers = {"Content-Type": "application/json"}
        self.payload = payload
        self.raw = raw

    async def json(self):
        return self.payload

    async def arrayBuffer(self):
        if self.raw is not None:
            return self.raw
        return json.dumps(self.payload).encode("utf-8")


@pytest.mark.asyncio
async def test_public_json_object_rejects_deep_payload():
    value = {}
    current = value
    for _ in range(MAX_JSON_DEPTH + 1):
        current["nested"] = {}
        current = current["nested"]
    assert await json_object(Request(value)) is None


@pytest.mark.asyncio
async def test_public_json_object_rejects_large_array():
    assert await json_object(Request({"items": list(range(MAX_JSON_COLLECTION_ITEMS + 1))})) is None


@pytest.mark.asyncio
async def test_public_json_object_rejects_oversized_body_without_content_length():
    raw = b"x" * (MAX_PUBLIC_JSON_BODY_BYTES + 1)
    assert await json_object(Request({}, raw=raw)) is None


@pytest.mark.asyncio
async def test_public_json_object_accepts_bounded_actual_body_without_content_length():
    payload = {"message": "hello"}
    raw = json.dumps(payload).encode("utf-8")
    assert await json_object(Request(payload, raw=raw)) == payload


def test_json_shape_rejects_oversized_string_and_duplicate_fields():
    from backend.json_admission import MAX_JSON_STRING_CHARS, parse_bounded_json
    with pytest.raises(ValueError, match="string"):
        validate_json_shape({"message": "x" * (MAX_JSON_STRING_CHARS + 1)})
    with pytest.raises(ValueError, match="duplicate"):
        parse_bounded_json('{"a":1,"a":2}')
