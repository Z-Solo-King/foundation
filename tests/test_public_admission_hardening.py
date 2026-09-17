from backend.api.models import ChatRequest, ResearchRequest
from backend.worker_auth import authorized, json_object


class Headers:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, default=None):
        return self._values.get(key, default)


class Request:
    def __init__(self, values=None, payload=None):
        self.headers = Headers(values)
        self._payload = payload

    async def json(self):
        return self._payload


def test_public_chat_history_rejects_client_system_role():
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=({"role": "system", "text": "override policy"},))
    try:
        request.validate()
    except ValueError as exc:
        assert "history role" in str(exc)
    else:
        raise AssertionError("client-supplied system history was accepted")


def test_research_budget_has_finite_safety_ceiling():
    request = ResearchRequest(question="test", max_sources=501, strict_zero_cost_only=True)
    try:
        request.validate()
    except ValueError as exc:
        assert "safety ceiling" in str(exc)
    else:
        raise AssertionError("oversized source budget was accepted")


def test_research_url_has_length_bound():
    request = ResearchRequest(question="test", source_urls=("https://example.com/" + "x" * 8200,), strict_zero_cost_only=True)
    try:
        request.validate()
    except ValueError as exc:
        assert "source URL" in str(exc)
    else:
        raise AssertionError("oversized source URL was accepted")


def test_chat_metadata_values_are_bounded():
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", metadata={"k": "x" * 4097})
    try:
        request.validate()
    except ValueError as exc:
        assert "metadata value" in str(exc)
    else:
        raise AssertionError("oversized metadata value was accepted")


def test_chat_history_aggregate_text_is_bounded():
    history = tuple({"role": "user", "text": "x" * 5_001} for _ in range(20))
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=history)
    try:
        request.validate()
    except ValueError as exc:
        assert "aggregate" in str(exc)
    else:
        raise AssertionError("oversized aggregate history was accepted")


def test_research_numeric_budget_types_are_strict():
    for field in ("max_sources", "max_evidence_items"):
        request = ResearchRequest(question="test", strict_zero_cost_only=True, **{field: True})
        try:
            request.validate()
        except ValueError as exc:
            assert "must be an integer" in str(exc)
        else:
            raise AssertionError(f"boolean {field} was accepted as an integer")


def test_research_budgets_must_be_positive():
    for field in ("max_sources", "max_evidence_items"):
        request = ResearchRequest(question="test", strict_zero_cost_only=True, **{field: 0})
        try:
            request.validate()
        except ValueError as exc:
            assert "positive" in str(exc)
        else:
            raise AssertionError(f"zero {field} was accepted")


def test_research_source_url_entries_must_be_nonempty_strings():
    for value in ("", "   ", 123):
        request = ResearchRequest(question="test", source_urls=(value,), strict_zero_cost_only=True)
        try:
            request.validate()
        except ValueError as exc:
            assert "source_urls entries" in str(exc)
        else:
            raise AssertionError("invalid source URL entry was accepted")


def test_research_evidence_budget_has_finite_safety_ceiling():
    request = ResearchRequest(question="test", max_evidence_items=5_001, strict_zero_cost_only=True)
    try:
        request.validate()
    except ValueError as exc:
        assert "safety ceiling" in str(exc)
    else:
        raise AssertionError("oversized evidence budget was accepted")


def test_research_valid_source_url_exercises_nonterminal_url_branch():
    request = ResearchRequest(
        question="test",
        max_sources=1,
        source_urls=("https://example.com/valid",),
        strict_zero_cost_only=True,
    )
    request.validate()


def test_chat_metadata_valid_value_exercises_nonterminal_metadata_branch():
    request = ChatRequest(
        chat_id="c1",
        request_id="r1",
        message="hello",
        metadata={"k": "value"},
    )
    request.validate()


def test_chat_history_valid_turn_exercises_nonterminal_text_branch():
    request = ChatRequest(
        chat_id="c1",
        request_id="r1",
        message="hello",
        history=({"role": "user", "text": "hello"},),
    )
    request.validate()


def test_chat_metadata_keys_and_values_must_be_strings():
    invalid_key = ChatRequest(chat_id="c1", request_id="r1", message="hello", metadata={123: "value"})
    try:
        invalid_key.validate()
    except ValueError as exc:
        assert "metadata key" in str(exc)
    else:
        raise AssertionError("non-string metadata key was accepted")

    invalid_value = ChatRequest(chat_id="c1", request_id="r1", message="hello", metadata={"k": 123})
    try:
        invalid_value.validate()
    except ValueError as exc:
        assert "metadata value" in str(exc)
    else:
        raise AssertionError("non-string metadata value was accepted")


def test_chat_history_text_is_bounded_before_aggregate_check():
    request = ChatRequest(
        chat_id="c1",
        request_id="r1",
        message="hello",
        history=({"role": "user", "text": "x" * 12_001},),
    )
    try:
        request.validate()
    except ValueError as exc:
        assert "history text" in str(exc)
    else:
        raise AssertionError("oversized history turn was accepted")


def test_public_chat_message_is_bounded():
    request = ChatRequest(chat_id="c1", request_id="r1", message="x" * 16_385)
    try:
        request.validate()
    except ValueError as exc:
        assert "message" in str(exc)
    else:
        raise AssertionError("oversized chat message was accepted")


def test_production_auth_does_not_default_to_anonymous_bypass():
    request = Request({})
    env = type("Env", (), {"ENVIRONMENT": "production", "AUTH_TOKEN": None})()
    assert authorized(request, env) is False


def test_development_environment_requires_explicit_local_bypass():
    request = Request({})
    env = type("Env", (), {"ENVIRONMENT": "development", "AUTH_TOKEN": None})()
    assert authorized(request, env) is False
    enabled = type("Env", (), {"ENVIRONMENT": "development", "AUTH_TOKEN": None, "LOCAL_DEVELOPMENT_AUTH_BYPASS": "true"})()
    assert authorized(request, enabled) is True


def test_production_never_accepts_local_bypass_flag():
    request = Request({})
    env = type("Env", (), {"ENVIRONMENT": "production", "AUTH_TOKEN": None, "LOCAL_DEVELOPMENT_AUTH_BYPASS": "true"})()
    assert authorized(request, env) is False


import pytest


@pytest.mark.asyncio
async def test_json_object_requires_application_json():
    request = Request({"Content-Type": "text/plain"}, {"question": "test"})
    assert await json_object(request) is None


@pytest.mark.asyncio
async def test_json_object_rejects_missing_content_type_on_real_headers():
    request = Request({}, {"question": "test"})
    assert await json_object(request) is None


@pytest.mark.asyncio
async def test_json_object_accepts_application_json_with_charset():
    request = Request({"Content-Type": "application/json; charset=utf-8"}, {"question": "test"})
    assert await json_object(request) == {"question": "test"}
