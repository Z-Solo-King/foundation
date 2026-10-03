"""Protected six-model Workers AI cross-fire endpoint for nightly benchmark advisories."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Mapping

from workers import Response

CROSSFIRE_MODELS: tuple[str, ...] = (
    "@cf/meta/llama-4-scout-17b-16e-instruct",
    "@cf/mistralai/mistral-small-3.1-24b-instruct",
    "@cf/ibm-granite/granite-4.0-h-micro",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/meta/llama-3.2-3b-instruct",
    "@cf/mistral/mistral-7b-instruct-v0.2-lora",
)
MAX_EVIDENCE_BYTES = 12_000
MODEL_OUTPUT_TOKENS = 128
MODEL_RETRY_OUTPUT_TOKENS = 128
REQUEST_SCHEMA = "nightly-benchmark-ai-crossfire-request/v2"
RECEIPT_SCHEMA = "nightly-benchmark-ai-crossfire-result/v2"


def _text_from_result(result: Any) -> str:
    if hasattr(result, "to_py") and callable(result.to_py):
        result = result.to_py()
    if not isinstance(result, Mapping):
        return ""
    value = result.get("response")
    if isinstance(value, str):
        return value
    choices = result.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], Mapping):
        first = choices[0]
        message = first.get("message")
        if isinstance(message, Mapping) and isinstance(message.get("content"), str):
            return str(message["content"])
        if isinstance(first.get("text"), str):
            return str(first["text"])
    return ""


def _normalize_json_text(value: str) -> str:
    normalized = value.strip()
    if normalized.startswith("```") and normalized.endswith("```"):
        lines = normalized.splitlines()
        if len(lines) >= 3 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
            normalized = "\n".join(lines[1:-1]).strip()
    return normalized


def _valid_advisory(value: str) -> tuple[bool, dict[str, Any] | None]:
    try:
        parsed = json.loads(_normalize_json_text(value))
    except (TypeError, ValueError):
        return False, None
    if not isinstance(parsed, dict):
        return False, None
    if set(parsed) != {"advisory_assessment", "reason", "flags"}:
        return False, None
    if parsed.get("advisory_assessment") not in {"pass", "attention", "blocked"}:
        return False, None
    if not isinstance(parsed.get("reason"), str):
        return False, None
    if not isinstance(parsed.get("flags"), list) or not all(isinstance(flag, str) for flag in parsed["flags"]):
        return False, None
    return True, {
        "advisory_assessment": parsed["advisory_assessment"],
        "reason": parsed["reason"][:500],
        "flags": [flag[:160] for flag in parsed["flags"][:8]],
    }


def _model_input(prompt: str, max_tokens: int) -> dict[str, Any]:
    return {
        "messages": [
            {
                "role": "system",
                "content": "Return only one JSON object. No Markdown, no analysis, no extra keys.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 17,
        "response_format": {"type": "json_object"},
    }

async def _run_model(env: Any, model: str, prompt: str, run_id: str) -> dict[str, Any]:
    started = time.time()
    receipt: dict[str, Any] = {
        "model": model,
        "transport_ok": False,
        "advisory_schema_compliant": False,
        "advisory_assessment": None,
        "reason": "",
        "flags": [],
        "neurons": 0,
        "elapsed_ms": None,
        "attempts": 0,
        "recovery_used": False,
    }
    binding = getattr(env, "AI", None)
    try:
        if binding is None:
            raise RuntimeError("workers_ai_binding_missing")
        recovery_prompt = (
            "Return exactly one compact JSON object with only these keys: "
            "advisory_assessment, reason, flags. "
            "advisory_assessment must be pass, attention, or blocked. "
            "reason must be a short string and flags must be an array of strings. "
            "Do not include Markdown or analysis. Evidence: " + prompt.rsplit("\n", 1)[-1]
        )
        last_error: str | None = None
        for attempt, request_prompt in enumerate((prompt, recovery_prompt), start=1):
            receipt["attempts"] = attempt
            try:
                result = await binding.run(
                    model,
                    _model_input(request_prompt, MODEL_OUTPUT_TOKENS if attempt == 1 else MODEL_RETRY_OUTPUT_TOKENS),
                    {"rejectIfBusy": False},
                )
                if hasattr(result, "to_py") and callable(result.to_py):
                    result = result.to_py()
                receipt["transport_ok"] = bool(
                    isinstance(result, Mapping)
                    and result.get("success", True) is not False
                    and not result.get("errors")
                )
                if isinstance(result, Mapping):
                    usage = result.get("usage")
                    if isinstance(usage, Mapping):
                        receipt["neurons"] = float(usage.get("neurons") or receipt["neurons"] or 0)
                    choices = result.get("choices")
                    receipt["finish_reason"] = (
                        choices[0].get("finish_reason")
                        if isinstance(choices, list) and choices and isinstance(choices[0], Mapping)
                        else None
                    )
                value = _text_from_result(result)
                valid, parsed = _valid_advisory(value)
                if valid and parsed is not None:
                    receipt["advisory_schema_compliant"] = True
                    receipt.update(parsed)
                    if attempt > 1:
                        receipt["recovery_used"] = True
                    last_error = None
                    break
                last_error = "advisory_schema_invalid"
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {str(exc)[:300]}"
                receipt["transport_ok"] = False
            if attempt == 1:
                receipt["recovery_used"] = True
        if last_error and not receipt["advisory_schema_compliant"]:
            receipt["error"] = last_error
    except Exception as exc:
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)[:500]
    receipt["elapsed_ms"] = int((time.time() - started) * 1000)
    receipt["run_id"] = run_id
    return receipt


async def handle_ai_crossfire(runtime: Any, request: Any) -> Response:
    if request.method != "POST":
        return Response.json({"ok": False, "error": "method_not_allowed"}, status=405)

    try:
        payload = json.loads(await request.text())
    except Exception:
        return Response.json({"ok": False, "error": "invalid_json"}, status=400)

    if not isinstance(payload, dict):
        return Response.json({"ok": False, "error": "invalid_json_object"}, status=400)
    if payload.get("schema") != REQUEST_SCHEMA:
        return Response.json({"ok": False, "error": "unexpected_schema"}, status=400)

    run_id = str(payload.get("run_id", "")).strip()
    if not run_id or len(run_id) > 120:
        return Response.json({"ok": False, "error": "invalid_run_id"}, status=400)

    expected_operations_ref = str(payload.get("expected_operations_ref", "")).strip()
    live_operations_ref = str(getattr(runtime.env, "RELEASE_OPERATIONS_REF", "") or "").strip()
    if expected_operations_ref and live_operations_ref != expected_operations_ref:
        return Response.json(
            {
                "ok": False,
                "error": "operations_runtime_pin_mismatch",
                "expected_operations_ref": expected_operations_ref,
                "live_operations_ref": live_operations_ref or None,
            },
            status=409,
        )

    evidence = payload.get("evidence")
    if not isinstance(evidence, Mapping):
        return Response.json({"ok": False, "error": "evidence_object_required"}, status=400)

    evidence_json = json.dumps(evidence, separators=(",", ":"), ensure_ascii=False)
    if len(evidence_json.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        return Response.json({"ok": False, "error": "evidence_too_large"}, status=413)

    evidence_sha256 = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()
    prompt = (
        "NIGHTLY_BENCHMARK_AI_CROSSFIRE_V2\n"
        "Return exactly one JSON object with only these keys: advisory_assessment, reason, flags.\n"
        "advisory_assessment must be exactly pass, attention, or blocked.\n"
        "reason must be a short string. flags must be an array of strings.\n"
        "Do not use Markdown or code fences.\n"
        "This is advisory-only analysis. Never certify correctness, production health, or research completion.\n"
        "Do not propose credential, policy, deployment, Cloudflare mutation, or workflow-dispatch actions.\n"
        "Evaluate only the evidence below.\n"
        + evidence_json
    )

    started = time.time()
    lanes = await asyncio.gather(*(_run_model(runtime.env, model, prompt, run_id) for model in CROSSFIRE_MODELS))
    successful = [lane for lane in lanes if lane["transport_ok"]]
    compliant = [lane for lane in lanes if lane["advisory_schema_compliant"]]
    counts: dict[str, int] = {}
    for lane in compliant:
        assessment = str(lane["advisory_assessment"])
        counts[assessment] = counts.get(assessment, 0) + 1
    consensus = max(counts, key=counts.get) if counts else None

    report = {
        "schema": RECEIPT_SCHEMA,
        "run_id": run_id,
        "foundation_sha": str(getattr(runtime.env, "RELEASE_FOUNDATION_SHA", "") or "").strip() or None,
        "operations_ref": str(getattr(runtime.env, "RELEASE_OPERATIONS_REF", "") or "").strip() or None,
        "model_count_expected": len(CROSSFIRE_MODELS),
        "model_count_observed": len(lanes),
        "transport_ok_count": len(successful),
        "schema_compliant_count": len(compliant),
        "coverage_complete": len(lanes) == len(CROSSFIRE_MODELS)
        and {lane["model"] for lane in lanes} == set(CROSSFIRE_MODELS),
        "quality_complete": len(compliant) == len(CROSSFIRE_MODELS) and len(successful) == len(CROSSFIRE_MODELS),
        "evidence_sha256": evidence_sha256,
        "batch_elapsed_ms": int((time.time() - started) * 1000),
        "total_neurons": sum(float(lane["neurons"] or 0) for lane in lanes),
        "consensus": consensus,
        "agreement": (counts.get(consensus, 0) / len(compliant)) if consensus and compliant else 0,
        "models": lanes,
        "authority": "advisory_only_no_acceptance_or_mutation_authority",
    }
    return Response.json(report, status=200)