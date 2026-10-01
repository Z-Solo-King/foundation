# LIVE BENCHMARK TRIGGER: 2026-10-01 parallel provider run
#!/usr/bin/env python3
"""Concurrent live zero-cost provider benchmark with deterministic quality checks."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


ALLOWED = {
    "openrouter_free",
    "groq",
    "gemini",
    "nvidia_nim",
    "cohere_free",
    "huggingface_free",
    "siliconflow",
}

TASKS = [
    {"id": "json_extract", "prompt": "Return JSON only with keys brand, price_inr, stock. Input: brand=Nova; price=59999; availability=in stock."},
    {"id": "arithmetic", "prompt": "Return only the integer result of 3847*29."},
    {"id": "instruction", "prompt": 'Return exactly JSON: {"answer":"PASS"} and nothing else.'},
]


def load_config() -> dict[str, dict[str, str]]:
    file_path = os.environ.get("PROVIDER_KEYS_JSON_FILE", "").strip()
    raw = ""
    if file_path:
        with open(file_path, encoding="utf-8") as handle:
            raw = handle.read().strip()
    if not raw:
        raw = os.environ.get("PROVIDER_KEYS_JSON", "").strip()
    config: dict[str, dict[str, str]] = {}
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            for name, value in payload.items():
                if name in ALLOWED and isinstance(value, dict):
                    endpoint, api_key, model = value.get("endpoint"), value.get("api_key"), value.get("model")
                    if all(isinstance(x, str) and x.strip() for x in (endpoint, api_key, model)):
                        config[name] = {"endpoint": endpoint, "api_key": api_key, "model": model}
    return config


def quality_pass(task_id: str, body: str) -> bool:
    text = body.strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = None
    if task_id == "json_extract":
        if not isinstance(value, dict) or set(value) != {"brand", "price_inr", "stock"}:
            return False
        try:
            return value["brand"] == "Nova" and int(value["price_inr"]) == 59999 and bool(value["stock"]) is True
        except (TypeError, ValueError):
            return False
    if task_id == "arithmetic":
        return text == "111563" or (isinstance(value, (int, float)) and int(value) == 111563)
    if task_id == "instruction":
        return value == {"answer": "PASS"}
    return False


def call(provider: str, cfg: dict[str, str], task: dict[str, str], repeat: int) -> dict[str, Any]:
    request = json.dumps({
        "model": cfg["model"],
        "messages": [{"role": "user", "content": task["prompt"]}],
        "temperature": 0,
        "max_tokens": 64,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        cfg["endpoint"], data=request, method="POST",
        headers={
            "Authorization": "Bearer " + cfg["api_key"],
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "heroic-ai-provider-crossfire/1",
        },
    )
    started = time.perf_counter()
    row: dict[str, Any] = {
        "provider": provider,
        "task": task["id"],
        "repeat": repeat,
        "latency_ms": None,
        "ok": False,
        "quality_pass": False,
        "http_status": None,
        "error_type": None,
        "response_preview": None,
    }
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            row["http_status"] = int(response.status)
            raw = response.read(64 * 1024)
            data = json.loads(raw.decode("utf-8", "replace"))
        choices = data.get("choices") if isinstance(data, dict) else None
        body = ""
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                body = str(message.get("content") or "")
        row["ok"] = bool(body.strip())
        row["quality_pass"] = quality_pass(task["id"], body) if row["ok"] else False
        row["response_preview"] = body[:600]
    except urllib.error.HTTPError as exc:
        row["http_status"] = int(exc.code)
        row["error_type"] = "HTTPError"
    except Exception as exc:
        row["error_type"] = type(exc).__name__
    row["latency_ms"] = max(0, int((time.perf_counter() - started) * 1000))
    return row


def percentile(values: list[int], q: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * q))))
    return ordered[rank]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers-max", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    config = load_config()
    names = sorted(config)[: max(0, args.providers_max)]
    if len(names) < 3:
        raise SystemExit(f"need at least 3 configured external providers for cross-fire; found {len(names)}")

    jobs = [(name, config[name], task, repeat) for name in names for task in TASKS for repeat in range(1, args.repeats + 1)]
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda job: call(*job), jobs))
    batch_wall_ms = max(0, int((time.perf_counter() - started) * 1000))

    providers = []
    for name in names:
        own = [row for row in rows if row["provider"] == name]
        lat = [int(row["latency_ms"]) for row in own if row["latency_ms"] is not None]
        successes = sum(bool(row["ok"]) for row in own)
        quality = sum(bool(row["quality_pass"]) for row in own)
        providers.append({
            "provider": name,
            "model": config[name]["model"],
            "calls": len(own),
            "successes": successes,
            "failures": len(own) - successes,
            "quality_passes": quality,
            "quality_total": len(own),
            "quality_score": round(quality / len(own), 4) if own else 0,
            "latency_ms": {
                "p50": percentile(lat, 0.50),
                "p95": percentile(lat, 0.95),
                "p99": percentile(lat, 0.99),
                "min": min(lat) if lat else None,
                "max": max(lat) if lat else None,
                "mean": round(statistics.mean(lat), 1) if lat else None,
            },
            "provider_batch_ms": max(lat) if lat else None,
            "errors": sorted({str(row["error_type"]) for row in own if row["error_type"]}),
            "samples": [
                {
                    "task": row["task"],
                    "repeat": row["repeat"],
                    "ok": row["ok"],
                    "quality_pass": row["quality_pass"],
                    "latency_ms": row["latency_ms"],
                    "http_status": row["http_status"],
                    "response_preview": row["response_preview"],
                }
                for row in own
            ],
        })

    output = {
        "schema": "live-ai-provider-crossfire/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "concurrency_workers": args.workers,
        "providers_tested": names,
        "task_count": len(TASKS),
        "repeats": args.repeats,
        "call_count": len(rows),
        "batch_wall_ms": batch_wall_ms,
        "providers": providers,
        "quality_note": "Quality score is deterministic contract/compliance correctness on the fixed benchmark prompts; it is not a general intelligence or human-preference ranking.",
    }
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())