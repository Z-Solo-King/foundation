#!/usr/bin/env python3
"""Run the project-native AI-agent benchmark against approved Workers AI models.

Observation-only: responses are never printed or stored. Only bounded metadata,
latency/token counters, and response digests are retained.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from benchmark.ai_agent_benchmark_contract import validate_manifest, validate_observation_envelope

DEFAULT_MODELS = [
    "@cf/zai-org/glm-4.7-flash",
    "@cf/google/gemma-4-26b-a4b-it",
]
DEFAULT_ROLES = ["main", "explorer", "worker", "researcher", "advisor"]
ROLE_INSTRUCTIONS = {
    "main": "Act as the main orchestrator: define the smallest correct path, preserve canonical ownership, and state explicit acceptance boundaries.",
    "explorer": "Act as a read-only explorer: identify the canonical owner, relevant surfaces, risks, and the first missing evidence rung without claiming file access you were not given.",
    "worker": "Act as a scoped implementation worker: propose the smallest repository-addressable change, focused tests, and blocked runtime prerequisites; do not claim execution.",
    "researcher": "Act as a research/evidence specialist: separate source facts from hypotheses, preserve provenance, identify contradictions, and state what must be verified live.",
    "advisor": "Act as the adversarial advisor: challenge assumptions, look for security/provenance/authority violations, and state conditions required before completion.",
}
TOOL_POLICY_VERSION = "direct-provider-no-tools/v1"
PROMPT_CONTRACT_VERSION = "project-native-task-prompt/v1"
PROVIDER = "cloudflare_workers_ai"
MAX_TOKENS = 96
MAX_RETRIES = 3
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_matrix(path: Path) -> dict[str, Any]:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_manifest(matrix)
    if errors:
        raise SystemExit("invalid benchmark matrix: " + "; ".join(errors))
    return matrix


def build_prompt(task: dict[str, Any], role: str, repeat_index: int) -> str:
    return (
        "You are one controlled observation in the Heroic AI project-native benchmark. "
        f"Role: {role}. Role contract: {ROLE_INSTRUCTIONS[role]}\n\n"
        f"Task ID: {task['task_id']}\n"
        f"Lane: {task['lane']} ({task['lane_slug']})\n"
        f"Category: {task['category']}\n"
        f"Language lens: {task['language_lens']}\n"
        f"Project surface: {task['project_surface']}\n"
        f"Referenced paths: {task['paths']}\n"
        f"Acceptance target: {task['acceptance_target']}\n"
        f"Focus: {task['focus']}\n"
        f"Task instruction: {task['task_instruction']}\n"
        f"Repeat: {repeat_index}/3\n\n"
        "Constraints: no external tools, no repository writes, no hidden-chain-of-thought disclosure, "
        "and no claim that code, tests, deployments, providers, or runtime systems were accessed unless "
        "that fact is explicitly present above. Return a concise JSON object with keys "
        "decision_or_result, evidence_packet, remaining_rungs, and artifact_provenance."
    )


def extract_text(payload: dict[str, Any]) -> str:
    result = payload.get("result")
    if isinstance(result, dict):
        response = result.get("response")
        if isinstance(response, str):
            return response
        choices = result.get("choices")
    else:
        choices = None
    if choices is None:
        choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
            if isinstance(first.get("text"), str):
                return first["text"]
    return ""


def extract_usage(payload: dict[str, Any]) -> dict[str, int]:
    result = payload.get("result")
    candidates = [result.get("usage") if isinstance(result, dict) else None, payload.get("usage")]
    for usage in candidates:
        if isinstance(usage, dict):
            def pick(*names: str) -> int:
                for name in names:
                    value = usage.get(name)
                    if isinstance(value, int) and value >= 0:
                        return value
                return 0
            return {"input_tokens": pick("prompt_tokens", "input_tokens"),
                    "output_tokens": pick("completion_tokens", "output_tokens")}
    return {"input_tokens": 0, "output_tokens": 0}


def call_model(token: str, account_id: str, model: str, prompt: str, seed: int) -> dict[str, Any]:
    encoded_model = urllib.parse.quote(model, safe="@/")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{encoded_model}"
    body = {
        "messages": [
            {"role": "system", "content": "You are a benchmark subject. Follow the task contract exactly."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "seed": seed,
        "thinking": False,
        "store": False,
    }
    request_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "heroic-ai-agent-benchmark/1",
    }
    last_error = "unknown"
    for attempt in range(MAX_RETRIES + 1):
        started = time.perf_counter()
        started_at = now_iso()
        request = urllib.request.Request(url, data=request_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                response_bytes = response.read()
                status = int(response.status)
            payload = json.loads(response_bytes.decode("utf-8"))
            text = extract_text(payload)
            usage = extract_usage(payload)
            return {
                "http_status": status,
                "success": status == 200,
                "usable_text": bool(text.strip()),
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "response_sha256": sha256_bytes(text.encode("utf-8")),
                "output_chars": len(text),
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "started_at": started_at,
                "completed_at": now_iso(),
                "retry_count": attempt,
            }
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = ""
            last_error = f"http_{status}:{detail}"
            if status not in RETRYABLE_STATUS or attempt >= MAX_RETRIES:
                break
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if attempt >= MAX_RETRIES:
                break
        time.sleep(min(8.0, 2.0 ** attempt))
    timestamp = now_iso()
    return {
        "http_status": None,
        "success": False,
        "usable_text": False,
        "latency_ms": None,
        "response_sha256": "",
        "output_chars": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "started_at": timestamp,
        "completed_at": timestamp,
        "retry_count": MAX_RETRIES,
        "error_class": last_error.split(":", 1)[0],
    }


def build_observation(run_id: str, repo_sha: str, task: dict[str, Any], model: str, role: str,
                      repeat_index: int, seed: int, result: dict[str, Any], prompt: str) -> dict[str, Any]:
    envelope = {
        "schema": "heroic-ai-agent-benchmark-observation/v1",
        "run_id": run_id,
        "provider": PROVIDER,
        "model": model,
        "agent_role": role,
        "lane": task["lane"],
        "task_id": task["task_id"],
        "language_lens": task["language_lens"],
        "fixture_version": f"task-matrix-v1:{task['task_id']}",
        "repository_revision": repo_sha,
        "tool_policy_version": TOOL_POLICY_VERSION,
        "evidence_tier": task["evidence_tier_required"],
        "observation": {
            "run_id": run_id,
            "provider": PROVIDER,
            "model": model,
            "task_id": task["task_id"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "tool_calls": 0,
            "useful_tool_calls": 0,
            "successful_actions": 1 if result["success"] and result["usable_text"] else 0,
            "http_status": result["http_status"],
            "usable_text": result["usable_text"],
            "latency_ms": result["latency_ms"],
            "output_chars": result["output_chars"],
            "response_sha256": result["response_sha256"],
            "retry_count": result["retry_count"],
            "repeat_index": repeat_index,
            "seed": seed,
            "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
            "execution_mode": "direct_provider_model_generation",
            "semantic_grading_applied": False,
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
        },
    }
    envelope["artifact_digest"] = canonical_digest(envelope)
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=Path("benchmark/ai_agent_task_matrix_v1.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "local"))
    parser.add_argument("--repo-sha", default=os.environ.get("GITHUB_SHA", "unknown"))
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--roles", default=",".join(DEFAULT_ROLES))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-workers", type=int, default=6)
    args = parser.parse_args()

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not token or not account_id:
        raise SystemExit("missing CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID")
    if args.repeats != 3:
        raise SystemExit("benchmark contract requires exactly 3 repeats")

    matrix = load_matrix(args.matrix)
    models = [x.strip() for x in args.models.split(",") if x.strip()]
    roles = [x.strip() for x in args.roles.split(",") if x.strip()]
    unknown_roles = [role for role in roles if role not in DEFAULT_ROLES]
    if unknown_roles:
        raise SystemExit("unknown roles: " + ",".join(unknown_roles))
    if not models:
        raise SystemExit("at least one model is required")

    tasks = sorted(matrix["tasks"], key=lambda item: item["task_id"])
    jobs = []
    for task in tasks:
        for role in roles:
            for model in models:
                for repeat_index in range(1, args.repeats + 1):
                    seed_material = f"{task['task_id']}|{role}|{model}|{repeat_index}".encode("utf-8")
                    seed = int(hashlib.sha256(seed_material).hexdigest()[:8], 16)
                    prompt = build_prompt(task, role, repeat_index)
                    jobs.append((len(jobs), task, role, model, repeat_index, seed, prompt))

    expected = len(tasks) * len(roles) * len(models) * args.repeats
    if expected != 720:
        raise SystemExit(f"benchmark contract expects 720 observations, got {expected}")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    observations_path = out_dir / "observations.jsonl"
    results: list[dict[str, Any] | None] = [None] * expected

    def run_one(item: tuple[int, dict[str, Any], str, str, int, int, str]) -> tuple[int, dict[str, Any]]:
        index, task, role, model, repeat_index, seed, prompt = item
        return index, build_observation(
            args.run_id, args.repo_sha, task, model, role, repeat_index, seed,
            call_model(token, account_id, model, prompt, seed), prompt,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(run_one, item) for item in jobs]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            index, envelope = future.result()
            errors = validate_observation_envelope(envelope)
            if errors:
                raise SystemExit(f"invalid observation envelope at index {index}: {'; '.join(errors)}")
            results[index] = envelope
            if completed % 24 == 0 or completed == expected:
                print(f"benchmark progress: {completed}/{expected}")

    rows = [row for row in results if row is not None]
    with observations_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    successes = sum(
        1 for row in rows
        if row["observation"]["http_status"] == 200 and row["observation"]["usable_text"] is True
    )
    summary = {
        "schema": "live-ai-agent-benchmark/v1",
        "run_id": args.run_id,
        "repository_revision": args.repo_sha,
        "matrix_sha256": sha256_bytes(args.matrix.read_bytes()),
        "models": models,
        "agent_roles": roles,
        "task_count": len(tasks),
        "lane_count": len(matrix["lanes"]),
        "repeats": args.repeats,
        "expected_observations": expected,
        "successful_observations": successes,
        "failed_observations": expected - successes,
        "evidence_class": "live provider integration/model-generation",
        "execution_mode": "direct_provider_model_generation",
        "semantic_grading_applied": False,
        "retained_per_run_observations": True,
        "runtime_certification": False,
        "limitations": [
            "Raw model text is not stored; each response is represented by a SHA-256 digest.",
            "No semantic correctness grader is applied in this run.",
            "Benchmark results do not change repository or production authority.",
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run_manifest.json").write_text(json.dumps({
        "schema": "live-ai-agent-benchmark-manifest/v1",
        "run_id": args.run_id,
        "repository_revision": args.repo_sha,
        "matrix_sha256": summary["matrix_sha256"],
        "task_count": len(tasks),
        "lane_count": len(matrix["lanes"]),
        "models": models,
        "agent_roles": roles,
        "repeats": args.repeats,
        "expected_observations": expected,
        "observation_schema": "heroic-ai-agent-benchmark-observation/v1",
        "tool_policy_version": TOOL_POLICY_VERSION,
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "evidence_class": "live provider integration/model-generation",
        "runtime_certification": False,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if successes == expected else 2


if __name__ == "__main__":
    raise SystemExit(main())
