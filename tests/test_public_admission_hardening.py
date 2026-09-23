import asyncio

import pytest

from backend.api.models import (
    MAX_HISTORY_TOTAL_TEXT_LENGTH,
    MAX_HISTORY_TEXT_LENGTH,
    MAX_METADATA_KEY_LENGTH,
    MAX_METADATA_VALUE_LENGTH,
    MAX_RESEARCH_EVIDENCE_ITEMS,
    MAX_RESEARCH_SOURCES,
    MAX_SOURCE_URL_LENGTH,
    ChatRequest,
    ResearchRequest,
)
from backend.worker_auth import MAX_PUBLIC_JSON_BODY_BYTES, authorized, json_object


class Request:
    def __init__(self, payload, headers=None, error=None):
        self.payload = payload
        self.headers = headers or {}
        self.error = error

    async def json(self):
        if self.error:
            raise self.error
        return self.payload


def test_research_admission_rejects_non_integer_and_bool_limits():
    with pytest.raises(ValueError, match="max_sources must be an integer"):
        ResearchRequest("q", max_sources=True).validate()
    with pytest.raises(ValueError, match="max_evidence_items must be an integer"):
        ResearchRequest("q", max_evidence_items=False).validate()


def test_research_admission_rejects_finite_ceiling_and_bad_urls():
    with pytest.raises(ValueError, match="max_sources exceeds"):
        ResearchRequest("q", max_sources=MAX_RESEARCH_SOURCES + 1).validate()
    with pytest.raises(ValueError, match="max_evidence_items exceeds"):
        ResearchRequest("q", max_evidence_items=MAX_RESEARCH_EVIDENCE_ITEMS + 1).validate()
    with pytest.raises(ValueError, match="non-empty strings"):
        ResearchRequest("q", source_urls=("",)).validate()
    with pytest.raises(ValueError, match="non-empty strings"):
        ResearchRequest("q", source_urls=(123,)).validate()
    with pytest.raises(ValueError, match="source URL exceeds"):
        ResearchRequest("q", source_urls=("x" * (MAX_SOURCE_URL_LENGTH + 1),)).validate()

    ResearchRequest("q", source_urls=("https://example.com/a", "https://example.org/b")).validate()
    with pytest.raises(ValueError, match="question exceeds"):
        ResearchRequest("x" * (16_384 + 1)).validate()


def test_chat_admission_rejects_metadata_and_history_amplification():
    with pytest.raises(ValueError, match="metadata key"):
        ChatRequest("c", "r", "m", metadata={"x" * (MAX_METADATA_KEY_LENGTH + 1): "v"}).validate()
    with pytest.raises(ValueError, match="metadata key"):
        ChatRequest("c", "r", "m", metadata={1: "v"}).validate()
    with pytest.raises(ValueError, match="metadata value"):
        ChatRequest("c", "r", "m", metadata={"k": "x" * (MAX_METADATA_VALUE_LENGTH + 1)}).validate()
    with pytest.raises(ValueError, match="metadata value"):
        ChatRequest("c", "r", "m", metadata={"k": 1}).validate()

    ChatRequest("c", "r", "m", metadata={"first": "value", "second": "value"}).validate()

    with pytest.raises(ValueError, match="history role"):
        ChatRequest("c", "r", "m", history=({"role": "system", "text": "x"},)).validate()
    with pytest.raises(ValueError, match="history text exceeds"):
        ChatRequest("c", "r", "m", history=({"role": "user", "text": "x" * (MAX_HISTORY_TEXT_LENGTH + 1)},)).validate()

    valid_history = (
        {"role": "user", "text": "first"},
        {"role": "assistant", "text": "second"},
    )
    ChatRequest("c", "r", "m", history=valid_history).validate()

    history = tuple(
        {"role": "user" if index % 2 == 0 else "assistant", "text": "x" * 12_000}
        for index in range(9)
    )
    assert sum(len(turn["text"]) for turn in history) > MAX_HISTORY_TOTAL_TEXT_LENGTH
    with pytest.raises(ValueError, match="aggregate text"):
        ChatRequest("c", "r", "m", history=history).validate()


def test_chat_admission_accepts_governed_operation_fields():
    request = ChatRequest(
        "c",
        "r",
        "https://example.com/",
        operation="map",
        input_records=({"id": "policy-probe"},),
    )
    request.validate()

    with pytest.raises(ValueError, match="unsupported chat operation"):
        ChatRequest("c", "r", "m", operation="unsupported").validate()

    with pytest.raises(ValueError, match="input_records must be a list or tuple"):
        ChatRequest("c", "r", "m", operation="map", input_records="bad").validate()


def test_auth_requires_explicit_development_bypass():
    request = Request({}, {})
    assert authorized(request, type("Env", (), {"ENVIRONMENT": "development", "AUTH_TOKEN": None, "LOCAL_DEVELOPMENT_AUTH_BYPASS": "true"})()) is True
    assert authorized(request, type("Env", (), {"ENVIRONMENT": "development", "AUTH_TOKEN": None, "LOCAL_DEVELOPMENT_AUTH_BYPASS": "false"})()) is False
    assert authorized(request, type("Env", (), {"ENVIRONMENT": "production", "AUTH_TOKEN": None, "LOCAL_DEVELOPMENT_AUTH_BYPASS": "true"})()) is False


def test_json_admission_rejects_missing_wrong_and_oversized_content_type():
    assert asyncio.run(json_object(Request({"ok": True}, {}))) is None
    assert asyncio.run(json_object(Request({"ok": True}, {"Content-Type": "text/plain"}))) is None
    assert asyncio.run(json_object(Request({"ok": True}, {"Content-Type": "application/json", "Content-Length": str(MAX_PUBLIC_JSON_BODY_BYTES + 1)}))) is None
    assert asyncio.run(json_object(Request({"ok": True}, {"Content-Type": "application/json", "Content-Length": "bad"}))) is None
    assert asyncio.run(json_object(Request({"ok": True}, {"Content-Type": "application/json", "Content-Length": "-1"}))) is None


def test_json_admission_accepts_json_charset_and_handles_shapes_and_parse_errors():
    headers = {"Content-Type": "application/json; charset=utf-8", "Content-Length": "10"}
    assert asyncio.run(json_object(Request({"ok": True}, headers))) == {"ok": True}
    assert asyncio.run(json_object(Request([1], headers))) is None
    assert asyncio.run(json_object(Request(None, headers, error=RuntimeError("bad json")))) is None


def test_authenticated_response_size_guard_constant_is_explicit():
    from backend.worker_auth import MAX_PUBLIC_JSON_BODY_BYTES
    assert MAX_PUBLIC_JSON_BODY_BYTES == 1_048_576


def test_authenticated_response_rejects_oversized_payload():
    from worker import _authenticated_json
    from backend.worker_auth import MAX_PUBLIC_JSON_BODY_BYTES
    response = _authenticated_json({"payload": "x" * MAX_PUBLIC_JSON_BODY_BYTES}, status=200)
    assert response.status == 500


def test_public_json_object_rejects_duplicate_fields_from_actual_body():
    raw = b'{"message":"first","message":"second"}'
    request = type("Request", (), {
        "headers": {"Content-Type": "application/json"},
        "arrayBuffer": lambda self: __import__("asyncio").sleep(0, result=raw),
    })()
    assert asyncio.run(json_object(request)) is None
