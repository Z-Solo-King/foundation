from pathlib import Path

from backend.worker_auth import bearer_token


def test_bearer_token_scheme_is_case_insensitive_and_stripped():
    class Request:
        headers = {"Authorization": "  bearer  secret  "}
    assert bearer_token(Request()) == "secret"


def test_bearer_token_rejects_wrong_or_missing_scheme():
    class A:
        headers = {"Authorization": "Token secret"}
    class B:
        headers = {}
    class C:
        headers = {"Authorization": "Bearer"}
    assert bearer_token(A()) is None
    assert bearer_token(B()) is None
    assert bearer_token(C()) is None


def test_json_object_does_not_swallow_unexpected_runtime_error():
    import asyncio
    from backend.worker_auth import json_object

    class Request:
        headers = {"Content-Type": "application/json"}
        async def arrayBuffer(self):
            raise RuntimeError("unexpected parser/runtime fault")

    with __import__("pytest").raises(RuntimeError, match="unexpected parser/runtime fault"):
        asyncio.run(json_object(Request()))


def test_auth_model_documents_single_operator_scope():
    text = (Path(__file__).resolve().parents[1] / "docs" / "PUBLIC_API_AUTH_MODEL.md").read_text(encoding="utf-8")
    assert "one operator credential" in text
    assert "not a user-account" in text
    assert "identity." in text
