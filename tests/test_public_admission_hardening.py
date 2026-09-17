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
    with pytest.raises(ValueError, match="source URL exceeds"):
        ResearchRequest("q", source_urls=("x" * (MAX_SOURCE_URL_LENGTH + 1),)).validate()


def test_chat_admission_rejects_metadata_and_history_amplification():
    with pytest.raises(ValueError, match="metadata key"):
        ChatRequest("c", "r", "m", metadata={"x" * (MAX_METADATA_KEY_LENGTH + 1): "v"}).validate()
    with pytest.raises(ValueError, match="metadata value"):
        ChatRequest("c", "r", "m", metadata={"k": "x" * (MAX_METADATA_VALUE_LENGTH + 1)}).validate()
    with pytest.raises(ValueError, match="history role"):
        ChatRequest("c", "r", "m", history=({"role": "system", "text": "x"},)).validate()
    with pytest.raises(ValueError, match="history text exceeds"):
        ChatRequest("c", "r", "m", history=({"role": "user", "text": "x" * (MAX_HISTORY_TEXT_LENGTH + 1)},)).validate()
    history = tuple(
        {"role": "user" if index % 2 == 0 else "assistant", "text": "x" * 12_000}
        for index in range(9)
    )
    assert sum(len(turn["text"]) for turn in history) > MAX_HISTORY_TOTAL_TEXT_LENGTH
    with pytest.raises(ValueError, match="aggregate text"):
        ChatRequest("c", "r", "m", history=history).validate()


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
