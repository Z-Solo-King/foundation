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


def _request(url: str, *, token: str | None = None, body: dict[str, Any] | None = None) -> tuple[int, bytes]:
    data = json.dumps(body, separators=(",", ":")).encode("utf-8") if body is not None else None
    headers = {
        "Accept": "application/json",
        "User-Agent": "HeroicNightlyResearchContract/2026.09",
        "Connection": "close",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return int(response.status), response.read(2_000_001)
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(2_000_001)
    except (urllib.error.URLError, TimeoutError):
        return 0, b""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--expected-foundation-sha", default="")
    parser.add_argument("--expected-operations-ref", default="")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    readiness_status, readiness_raw = _request(base + "/readiness")
    readiness: dict[str, Any] = {}
    try:
        parsed = json.loads(readiness_raw.decode("utf-8"))
        if isinstance(parsed, dict):
            readiness = parsed
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass

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
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + args.token,
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
            "X-Heroic-Research-Proof": "1",
            "User-Agent": "HeroicNightlyResearchContract/2026.09",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        request = urllib.request.Request(
            base + "/api/v1/chat",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                chat_status = int(response.status)
                raw = response.read(2_000_001)
        except urllib.error.HTTPError as exc:
            chat_status = int(exc.code)
            raw = exc.read(2_000_001)
        except (urllib.error.URLError, TimeoutError):
            raw = b""
        try:
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict):
                payload = parsed
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

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
        if not readiness_ok
        and readiness_status == 200
        and release
        else "research_contract_rejected"
    )

    result = {
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
        "model": payload.get("model") if isinstance(payload, dict) else None,
        "provider_present": isinstance(payload.get("provider"), str) if isinstance(payload, dict) else False,
        "execution_id_present": isinstance(payload.get("execution_id"), str) if isinstance(payload, dict) else False,
        "structured_output": isinstance(structured, dict),
        "request_contract": {
            "operation": "knowledge",
            "proof_header": True,
            "require_model_generation": True,
        },
        "probe_timestamp_unix": int(time.time()),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
