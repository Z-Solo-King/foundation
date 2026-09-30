#!/usr/bin/env python3
"""Probe the exact deployed public Worker contract used by nightly CrossFire."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from typing import Any


def _get_json(url: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "HeroicNightlyResearchContract/2026.09",
            "Connection": "close",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(500_001)
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code), {}
    except (urllib.error.URLError, TimeoutError):
        return 0, {}
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, {}
    return status, value if isinstance(value, dict) else {}


def _post_json(url: str, token: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Idempotency-Key": str(body["request_id"]),
            "X-Heroic-Research-Proof": "1",
            "User-Agent": "HeroicNightlyResearchContract/2026.09",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read(2_000_001)
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        raw = exc.read(2_000_001)
        status = int(exc.code)
    except (urllib.error.URLError, TimeoutError):
        return 0, {}
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, {}
    return status, value if isinstance(value, dict) else {}


def _validate_chat_response(payload: dict[str, Any], expected_model: str = "") -> tuple[bool, dict[str, Any]]:
    """Validate the authenticated Foundation research response contract.

    The public edge returns provider provenance inside response and intentionally
    does not expose an OpenAI-compatible choices envelope. Model identity is
    separately proven by the runtime/provider preflight; when a model field is
    present here it must match the expected value.
    """
    response = payload.get("response")
    if not isinstance(response, dict):
        return False, {
            "response_id_present": False,
            "provider_present": False,
            "generation_status": None,
            "structured_output": False,
        }
    provider = response.get("provider")
    response_id = response.get("response_id")
    generation_status = response.get("generation_status")
    text = response.get("text")
    model = response.get("model")
    structured = None
    if isinstance(text, str) and text.strip():
        try:
            structured = json.loads(text)
        except json.JSONDecodeError:
            structured = None
    model_ok = model is None or not expected_model or model == expected_model
    details = {
        "response_id_present": isinstance(response_id, str) and bool(response_id.strip()),
        "provider_present": isinstance(provider, str) and bool(provider.strip()),
        "provider": provider if isinstance(provider, str) else None,
        "generation_status": generation_status if isinstance(generation_status, str) else None,
        "model_present": isinstance(model, str) and bool(model.strip()),
        "model_match": model_ok,
        "structured_output": isinstance(structured, dict),
    }
    ok = (
        payload.get("ok") is True
        and details["response_id_present"]
        and details["provider_present"]
        and generation_status == "model_generated"
        and isinstance(text, str)
        and bool(text.strip())
        and isinstance(structured, dict)
        and isinstance(structured.get("findings"), list)
        and isinstance(structured.get("follow_up_questions"), list)
        and isinstance(structured.get("note"), str)
        and model_ok
    )
    return ok, details


def main() -> int:    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--expected-foundation-sha", default="")
    parser.add_argument("--expected-operations-ref", default="")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    readiness_status, readiness = _get_json(base + "/readiness")
    release = readiness.get("release") if isinstance(readiness.get("release"), dict) else {}

    readiness_ok = (
        readiness_status == 200
        and readiness.get("ready") is True
        and readiness.get("database") is True
        and (
            not args.expected_foundation_sha
            or release.get("foundation_sha") == args.expected_foundation_sha
        )
        and (
            not args.expected_operations_ref
            or release.get("operations_ref") == args.expected_operations_ref
        )
    )

    request_id = "nightly-contract-probe-" + uuid.uuid4().hex
    body = {
        "chat_id": request_id,
        "request_id": request_id,
        "message": (
            "Return the smallest valid research object with findings as an empty "
            "array, follow_up_questions as an empty array, and note as probe."
        ),
        "mode": "chat",
        "operation": "knowledge",
        "strict_zero_cost_only": True,
        "require_model_generation": True,
    }

    chat_status = 0
    payload: dict[str, Any] = {}
    if readiness_ok:
        chat_status, payload = _post_json(base + "/api/v1/chat", args.token, body)

    chat_ok, chat_details = _validate_chat_response(payload, expected_model=args.model)
    chat_ok = chat_status == 200 and chat_ok

    ok = readiness_ok and chat_ok
    if ok:
        classification = "accepted_exact_research_contract"
    elif not readiness_ok:
        classification = (
            "runtime_revision_mismatch"
            if readiness_status == 200 and bool(release)
            else "readiness_failure"
        )
    elif chat_status == 0:
        classification = "probe_transport_error"
    elif not payload:
        classification = "invalid_json_response"
    else:
        classification = "research_contract_rejected"

    print(json.dumps({
        "schema": "nightly-runtime-contract-probe/v2",
        "ok": ok,
        "classification": classification,
        "readiness_http_status": readiness_status,
        "readiness_ready": readiness.get("ready") is True,
        "readiness_database": readiness.get("database") is True,
        "deployed_foundation_sha": release.get("foundation_sha"),
        "deployed_operations_ref": release.get("operations_ref"),
        "expected_foundation_sha": args.expected_foundation_sha,
        "expected_operations_ref": args.expected_operations_ref,
        "chat_http_status": chat_status,
        "expected_model": args.model,
        **chat_details,
        "request_contract": {
            "operation": "knowledge",
            "proof_header": True,
            "require_model_generation": True,
        },
        "probe_timestamp_unix": int(time.time()),
    }, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
