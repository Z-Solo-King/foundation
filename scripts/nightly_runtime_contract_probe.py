#!/usr/bin/env python3
"""Exact production-path nightly research contract probe.

This probes the same public Worker /api/v1/chat boundary used by the nightly
research proxy. It intentionally does not call the separate infrastructure
diagnostic endpoint, because that endpoint is not sufficient to prove that
CrossFire's research request is accepted.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--expected-foundation-sha", default="")
    parser.add_argument("--expected-operations-ref", default="")
    args = parser.parse_args()

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
    data = json.dumps(body, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        args.url.rstrip("/") + "/api/v1/chat",
        data=data,
        headers={
            "Authorization": "Bearer " + args.token,
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
            "X-Heroic-Research-Proof": "1",
            "User-Agent": "HeroicNightlyResearchContract/2026.09",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            status = int(response.status)
            raw = response.read(2_000_001)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(2_000_001)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({
            "schema": "nightly-runtime-contract-probe/v1",
            "ok": False,
            "classification": "transport_failure",
            "http_status": 0,
            "error_type": type(exc).__name__,
        }, sort_keys=True))
        return 1

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print(json.dumps({
            "schema": "nightly-runtime-contract-probe/v1",
            "ok": False,
            "classification": "invalid_json_response",
            "http_status": status,
        }, sort_keys=True))
        return 1

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
            structured = None

    ok = (
        status == 200
        and isinstance(payload, dict)
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

    result = {
        "schema": "nightly-runtime-contract-probe/v1",
        "ok": ok,
        "classification": "accepted_exact_research_contract" if ok else "research_contract_rejected",
        "http_status": status,
        "model": payload.get("model") if isinstance(payload, dict) else None,
        "provider_present": isinstance(payload.get("provider"), str) if isinstance(payload, dict) else False,
        "execution_id_present": isinstance(payload.get("execution_id"), str) if isinstance(payload, dict) else False,
        "structured_output": isinstance(structured, dict),
        "expected_foundation_sha": args.expected_foundation_sha,
        "expected_operations_ref": args.expected_operations_ref,
        "request_id_prefix": request_id[:28],
        "probe_timestamp_unix": int(time.time()),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
