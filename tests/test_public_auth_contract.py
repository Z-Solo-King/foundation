import asyncio

import pytest

from backend.worker_auth import authenticated_subject_fingerprint, bearer_token, json_object


class Request:
    def __init__(self, headers, body):
        self.headers = headers
        self.body = body

    async def arrayBuffer(self):
        return self.body


def test_bearer_scheme_is_case_insensitive_and_trimmed():
    assert bearer_token(Request({"Authorization": "bearer secret "}, b"")) == "secret"
    assert bearer_token(Request({"Authorization": "BEARER secret"}, b"")) == "secret"


def test_single_operator_fingerprint_is_deterministic_and_secret_free():
    first = authenticated_subject_fingerprint(Request({"Authorization": "Bearer secret"}, b""))
    second = authenticated_subject_fingerprint(Request({"Authorization": "bearer secret"}, b""))
    assert first == second
    assert "secret" not in first


def test_json_object_rejects_only_input_errors():
    request = Request({"Content-Type": "application/json"}, b"{bad")
    assert asyncio.run(json_object(request)) is None


def test_json_object_does_not_swallow_unexpected_runtime_errors():
    class Broken(Request):
        async def arrayBuffer(self):
            raise RuntimeError("runtime transport failure")

    with pytest.raises(RuntimeError, match="runtime transport failure"):
        asyncio.run(json_object(Broken({"Content-Type": "application/json"}, b"{}")))


def test_public_auth_contract_is_explicit():
    text = open("docs/PUBLIC_API_AUTH_CONTRACT.md", encoding="utf-8").read()
    assert "one operator credential" in text
    assert "not a user-account identity" in text
    assert "single-operator" in text
