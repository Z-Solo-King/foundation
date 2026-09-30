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


def main() -> int:
    parser = argparse.ArgumentParser()
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

    content = (
        payload.get("choices", [{}])[0].get("message", {}).get("content")
        if isinstance(payload, dict)
        else None
    )
    structured = None
    if isinstance(content, str) and content.strip():
        try:
            structured = json.loads(content)
        except json.JSONDecodeError:
            pass

    chat_ok = (
        chat_status == 200
        and isinstance(payload.get("provider"), str)
        and bool(payload["provider"].strip())
        and payload.get("model") == args.model
        and isinstance(payload.get("execution_id"), str)
        and bool(payload["execution_id"].strip())
        and isinstance(content, str)
        and bool(content.strip())
        and isinstance(structured, dict)
        and isinstance(structured.get("findings"), list)
        and isinstance(structured.get("follow_up_questions"), list)
        and isinstance(structured.get("note"), str)
    )

    ok = readiness_ok and chat_ok
    classification = (
        "accepted_exact_research_contract"
        if ok
        else "runtime_revision_mismatch"
        if not readiness_ok and readiness_status == 200 and bool(release)
        else "research_contract_rejected"
    )

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
        "model": payload.get("model"),
        "provider_present": isinstance(payload.get("provider"), str),
        "execution_id_present": isinstance(payload.get("execution_id"), str),
        "structured_output": isinstance(structured, dict),
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
