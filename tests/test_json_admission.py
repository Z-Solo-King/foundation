import pytest

from backend.json_admission import MAX_JSON_COLLECTION_ITEMS, MAX_JSON_DEPTH, validate_json_shape


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


class Request:
    def __init__(self, payload):
        self.headers = {"Content-Type": "application/json"}
        self.payload = payload
        self.json_called = False

    async def json(self):
        self.json_called = True
        return self.payload


@pytest.mark.asyncio
async def test_public_json_object_rejects_deep_payload():
    value = {}
    current = value
    for _ in range(MAX_JSON_DEPTH + 1):
        current["nested"] = {}
        current = current["nested"]
    request = Request(value)
    from backend.worker_auth import json_object
    assert await json_object(request) is None
    assert request.json_called is True


@pytest.mark.asyncio
async def test_public_json_object_rejects_large_array():
    request = Request({"items": list(range(MAX_JSON_COLLECTION_ITEMS + 1))})
    from backend.worker_auth import json_object
    assert await json_object(request) is None
