from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import socket
import ssl
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from benchmark.evidence_tier import EvidenceTier, parse_evidence_tier
from foundation_core.normalization import canonical_url as _canonical_url

USER_AGENT = "HeroicAI-Benchmark/2026.09"
PRODUCT_HINTS = ("product", "itemprop=\"name\"", "productid", "sku", "add-to-cart", "price")
TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 2
REQUEST_TIMEOUT_SECONDS = 20.0
MAX_RESPONSE_BYTES = 2_000_000
MIN_CYCLE_INTERVAL_SECONDS = 5.0
EVIDENCE_TIER = parse_evidence_tier(EvidenceTier.LIVE_SOURCE_ACQUISITION.value)


class _ProductParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.jsonld_blocks: list[str] = []
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "script" and attr.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        if tag.lower() == "script" and self._in_jsonld:
            self._in_jsonld = False
            text = "".join(self._jsonld_parts).strip()
            if text:
                self.jsonld_blocks.append(text)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._in_jsonld:
            self._jsonld_parts.append(data)


@dataclass(frozen=True)
class Target:
    key: str
    url: str
    label: str = ""


@dataclass(frozen=True)
class Receipt:
    run_id: str
    shard: int
    shard_count: int
    key: str
    url: str
    status: str
    http_status: int
    elapsed_ms: int
    bytes_read: int
    pages_fetched: int
    title: str
    product_candidates: int
    jsonld_blocks: int
    diagnostics: tuple[str, ...]
    recorded_at: int


def canonical_url(value: str) -> str:
    """Compatibility wrapper preserving the benchmark's historical error text."""
    return _canonical_url(value, error_message=f"unsupported URL: {value!r}")


def target_key(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()


def load_targets(path: Path) -> list[Target]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("targets", raw.get("sites", raw)) if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError("benchmark corpus must contain a list")
    unique: dict[str, Target] = {}
    for item in rows:
        if isinstance(item, str):
            url, label = item, ""
        elif isinstance(item, dict):
            url = item.get("url") or item.get("site")
            label = str(item.get("name") or item.get("label") or "")
        else:
            continue
        if not isinstance(url, str):
            continue
        try:
            normalized = canonical_url(url)
        except ValueError:
            continue
        key = target_key(normalized)
        unique.setdefault(key, Target(key, normalized, label))
    if not unique:
        raise ValueError("no usable HTTP(S) targets found")
    return list(unique.values())


def shard_for(key: str, shards: int) -> int:
    if shards < 1:
        raise ValueError("shards must be positive")
    return int(key[:16], 16) % shards


def _classify(status: int, body: bytes, diagnostics: list[str]) -> tuple[str, int, str, int, int, int]:
    text = body.decode("utf-8", errors="ignore")
    parser = _ProductParser()
    try:
        parser.feed(text)
    except Exception as exc:
        diagnostics.append(f"parser:{type(exc).__name__}")
    product_candidates = sum(text.lower().count(h) for h in PRODUCT_HINTS)
    jsonld = len(parser.jsonld_blocks)
    title = " ".join(" ".join(parser.title_parts).split())[:300]
    if status in {401, 403}:
        result = "blocked"
    elif status == 429:
        result = "resource_limited"
    elif status >= 500:
        result = "error"
    elif 400 <= status < 500:
        result = "error"
    elif not text.strip():
        result = "empty"
    elif product_candidates or jsonld:
        result = "ok"
    else:
        result = "empty"
    return result, len(body), title, product_candidates, jsonld, 1


def _retry_after(headers: Message | None) -> float:
    if headers is None:
        return 0.0
    try:
        return min(max(float(headers.get("Retry-After", "0")), 0.0), 30.0)
    except (TypeError, ValueError):
        return 0.0


def fetch_target(target: Target, timeout: float = REQUEST_TIMEOUT_SECONDS) -> Receipt:
    started = time.perf_counter()
    diagnostics: list[str] = []
    last_status = 0
    last_body = b""
    final_error: str | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            request = Request(
                target.url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-IN,en;q=0.8",
                    "Connection": "close",
                },
            )
            with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
                last_status = int(getattr(response, "status", 200))
                last_body = response.read(MAX_RESPONSE_BYTES)
            if last_status in TRANSIENT_HTTP and attempt < MAX_ATTEMPTS:
                diagnostics.append(f"retry:http-{last_status}")
                time.sleep(0.25 * attempt)
                continue
            break
        except HTTPError as exc:
            last_status = int(exc.code)
            try:
                last_body = exc.read(MAX_RESPONSE_BYTES)
                if last_status in {429, 503} and attempt < MAX_ATTEMPTS:
                    retry_after = _retry_after(exc.headers)
                    diagnostics.append(f"retry:http-{last_status}")
                    time.sleep(retry_after or (0.5 * attempt))
                    continue
            finally:
                exc.close()
            break
        except (TimeoutError, socket.timeout):
            final_error = "timeout"
            diagnostics.append(f"attempt-{attempt}:timeout")
            if attempt < MAX_ATTEMPTS:
                time.sleep(0.25 * attempt)
                continue
        except (ssl.SSLError, ConnectionError, OSError) as exc:
            final_error = type(exc).__name__
            reason = str(exc.reason)[:160] if isinstance(exc, URLError) else str(exc)[:160]
            diagnostics.append(f"attempt-{attempt}:{final_error}:{reason}" if reason else f"attempt-{attempt}:{final_error}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(0.25 * attempt)
                continue
        except Exception as exc:
            final_error = type(exc).__name__
            diagnostics.append(f"attempt-{attempt}:{final_error}")
            break

    if last_status:
        result, size, title, candidates, jsonld, pages = _classify(last_status, last_body, diagnostics)
    else:
        result, size, title, candidates, jsonld, pages = (
            "resource_limited" if final_error == "timeout" else "error",
            len(last_body),
            "",
            0,
            0,
            0,
        )

    diagnostics.append(f"attempts-{attempt}")
    return Receipt(
        run_id="",
        shard=0,
        shard_count=1,
        key=target.key,
        url=target.url,
        status=result,
        http_status=last_status,
        elapsed_ms=int((time.perf_counter() - started) * 1000),
        bytes_read=size,
        pages_fetched=pages,
        title=title,
        product_candidates=candidates,
        jsonld_blocks=jsonld,
        diagnostics=tuple(diagnostics),
        recorded_at=int(time.time()),
    )


def _percentile(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * percentile)))
    return ordered[rank]




def classify_target_health(
    observations: int,
    failures: int,
    status_counts: dict[str, int],
    http_status_counts: dict[str, int],
) -> tuple[str, str]:
    if observations <= 0:
        return "unknown", "collect_more_observations"
    failure_rate = failures / observations
    blocked = int(status_counts.get("blocked", 0))
    limited = int(status_counts.get("resource_limited", 0))
    errors = int(status_counts.get("error", 0))
    if blocked / observations >= 0.95:
        return "blocked", "quarantine_until_manual_recheck"
    if limited / observations >= 0.95:
        return "rate_limited", "exponential_backoff_and_quarantine"
    if errors / observations >= 0.95 and not http_status_counts:
        return "transport_error", "investigate_dns_tls_or_network_path"
    if failure_rate == 0:
        return "healthy", "retain_normal_sampling"
    if failure_rate >= 0.5:
        return "degraded", "retain_for_targeted_recheck"
    return "intermittent", "retain_with_failure_aware_retry"

def _target_entry() -> dict[str, object]:
    return {
        "url": "",
        "observations": 0,
        "failures": 0,
        "status_counts": Counter(),
        "http_status_counts": Counter(),
        "diagnostics": Counter(),
        "elapsed_ms": [],
        "product_candidates": 0,
        "jsonld_blocks": 0,
    }


def run(input_path: str, output: str, run_id: str, shards: int, shard: int, workers: int, duration_minutes: int) -> int:
    targets = load_targets(Path(input_path))
    if not 0 <= shard < shards:
        raise ValueError(f"shard must be within [0, {shards})")
    selected = [t for t in targets if shard_for(t.key, shards) == shard]
    root = Path(output) / run_id
    root.mkdir(parents=True, exist_ok=True)
    receipt_path = root / f"shard-{shard}.jsonl"
    summary_path = root / f"summary-{shard}.json"
    deadline = time.monotonic() + duration_minutes * 60
    counts = {"ok": 0, "empty": 0, "blocked": 0, "resource_limited": 0, "error": 0}
    http_counts: Counter[str] = Counter()
    diagnostic_counts: Counter[str] = Counter()
    target_stats: dict[str, dict[str, object]] = {}
    elapsed_values: list[int] = []
    total_bytes = 0
    total_product_candidates = 0
    total_jsonld_blocks = 0
    observations = 0
    cycle = 0

    if not selected:
        summary = {
            "schema": "autonomous-public-benchmark-summary/v10",
            "run_id": run_id,
            "shard": shard,
            "shards": shards,
            "cycles": 0,
            "selected": 0,
            "selected_targets": 0,
            "observations": 0,
            "evidence": EVIDENCE_TIER.to_dict(),
            "evidence_rule": "Live HTTP acquisition measures transport and structural page signals only; it does not certify provider behavior, field-level correctness or production capability.",
            "status_counts": counts,
            "http_status_counts": {},
            "diagnostic_counts": {},
            "measurement": {
                "elapsed_ms": {"min": None, "median": None, "p95": None, "max": None},
                "bytes_read_total": 0,
                "product_candidates_total": 0,
                "jsonld_blocks_total": 0,
                "observations_with_product_candidates": 0,
                "observations_with_jsonld": 0,
                "field_level_correctness_oracle": False,
                "evidence_scope": "transport_and_structural_signals_only",
            },
            "targets_with_failures": [],
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, sort_keys=True))
        return 0

    pool = ThreadPoolExecutor(max_workers=max(1, min(workers, len(selected))))
    try:
        while time.monotonic() < deadline:
            cycle += 1
            cycle_started = time.monotonic()
            futures = {pool.submit(fetch_target, target): target for target in selected}
            for future in as_completed(futures):
                receipt = future.result()
                receipt = Receipt(
                    run_id=run_id,
                    shard=shard,
                    shard_count=shards,
                    **{k: getattr(receipt, k) for k in asdict(receipt) if k not in {"run_id", "shard", "shard_count"}},
                )
                with receipt_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(asdict(receipt), ensure_ascii=False, separators=(",", ":")) + "\n")
                observations += 1
                counts[receipt.status] = counts.get(receipt.status, 0) + 1
                elapsed_values.append(receipt.elapsed_ms)
                total_bytes += receipt.bytes_read
                total_product_candidates += receipt.product_candidates
                total_jsonld_blocks += receipt.jsonld_blocks
                if receipt.http_status:
                    http_counts[str(receipt.http_status)] += 1
                for diagnostic in receipt.diagnostics:
                    diagnostic_counts[diagnostic] += 1

                entry = target_stats.setdefault(receipt.url, _target_entry())
                entry["url"] = receipt.url
                entry["observations"] = int(entry["observations"]) + 1
                entry["failures"] = int(entry["failures"]) + int(receipt.status != "ok")
                entry["status_counts"].update({receipt.status: 1})
                if receipt.http_status:
                    entry["http_status_counts"].update({str(receipt.http_status): 1})
                entry["diagnostics"].update(receipt.diagnostics)
                entry["elapsed_ms"].append(receipt.elapsed_ms)
                entry["product_candidates"] = int(entry["product_candidates"]) + receipt.product_candidates
                entry["jsonld_blocks"] = int(entry["jsonld_blocks"]) + receipt.jsonld_blocks
            remaining = MIN_CYCLE_INTERVAL_SECONDS - (time.monotonic() - cycle_started)
            if remaining > 0 and time.monotonic() < deadline:
                time.sleep(min(remaining, max(0.0, deadline - time.monotonic())))
    finally:
        pool.shutdown(wait=True, cancel_futures=True)

    targets_with_failures = []
    for entry in target_stats.values():
        target_rows = {
            "url": entry["url"],
            "observations": int(entry["observations"]),
            "failures": int(entry["failures"]),
            "failure_rate": round(int(entry["failures"]) / int(entry["observations"]), 6) if entry["observations"] else None,
            "status_counts": dict(sorted(entry["status_counts"].items())),
            "http_status_counts": dict(sorted(entry["http_status_counts"].items())),
            "diagnostics": dict(sorted(entry["diagnostics"].items())),
            "health_class": classify_target_health(int(entry["observations"]), int(entry["failures"]), dict(entry["status_counts"]), dict(entry["http_status_counts"]))[0],
            "recommended_action": classify_target_health(int(entry["observations"]), int(entry["failures"]), dict(entry["status_counts"]), dict(entry["http_status_counts"]))[1],
            "measurement": {
                "elapsed_ms": {
                    "min": _percentile(entry["elapsed_ms"], 0.0),
                    "median": _percentile(entry["elapsed_ms"], 0.5),
                    "p95": _percentile(entry["elapsed_ms"], 0.95),
                    "max": _percentile(entry["elapsed_ms"], 1.0),
                },
                "product_candidates_total": int(entry["product_candidates"]),
                "jsonld_blocks_total": int(entry["jsonld_blocks"]),
            },
        }
        if int(entry["failures"]) > 0:
            targets_with_failures.append(target_rows)

    summary = {
        "schema": "autonomous-public-benchmark-summary/v10",
        "run_id": run_id,
        "shard": shard,
        "shards": shards,
        "cycles": cycle,
        "selected": len(selected),
        "selected_targets": len(selected),
        "observations": observations,
        "evidence": EVIDENCE_TIER.to_dict(),
        "evidence_rule": "Live HTTP acquisition measures transport and structural page signals only; it does not certify provider behavior, field-level correctness or production capability.",
        "status_counts": counts,
        "http_status_counts": dict(sorted(http_counts.items())),
        "diagnostic_counts": dict(sorted(diagnostic_counts.items())),
        "min_cycle_interval_seconds": MIN_CYCLE_INTERVAL_SECONDS,
        "max_attempts": MAX_ATTEMPTS,
        "measurement": {
            "elapsed_ms": {
                "min": _percentile(elapsed_values, 0.0),
                "median": _percentile(elapsed_values, 0.5),
                "p95": _percentile(elapsed_values, 0.95),
                "max": _percentile(elapsed_values, 1.0),
            },
            "bytes_read_total": total_bytes,
            "product_candidates_total": total_product_candidates,
            "jsonld_blocks_total": total_jsonld_blocks,
            "observations_with_product_candidates": sum(1 for value in target_stats.values() if int(value["product_candidates"]) > 0),
            "observations_with_jsonld": sum(1 for value in target_stats.values() if int(value["jsonld_blocks"]) > 0),
            "field_level_correctness_oracle": False,
            "evidence_scope": "transport_and_structural_signals_only",
        },
        "targets_with_failures": sorted(targets_with_failures, key=lambda item: (-float(item["failure_rate"] or 0), str(item["url"]))),
        "measurement_gaps": [
            "no oracle-backed product-field precision/recall",
            "product_candidates and JSON-LD counts are structural hints, not correctness judgments",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


def chatbot_enqueue_smoke() -> dict[str, object]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        corpus = root / "corpus"
        inbox = root / "inbox"
        corpus.mkdir()
        inbox.mkdir()
        target = corpus / "sites.json"
        target.write_text(json.dumps(["https://example.com/"]), encoding="utf-8")
        relative = Path("sites.json")
        resolved = (corpus / relative).resolve()
        if corpus.resolve() not in resolved.parents:
            raise AssertionError("corpus root escape")
        job = inbox / f"run-{os.getpid()}.json"
        job.write_text(json.dumps({"input": str(resolved), "run_id": "chatbot-smoke"}), encoding="utf-8")
        payload = json.loads(job.read_text(encoding="utf-8"))
        return {"passed": payload["run_id"] == "chatbot-smoke", "job": job.name}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run", "chatbot-smoke"])
    parser.add_argument("--input")
    parser.add_argument("--output", default=".runtime/benchmarks")
    parser.add_argument("--run-id", default="public-benchmark")
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--duration-minutes", type=int, default=18)
    args = parser.parse_args()
    if args.command == "chatbot-smoke":
        print(json.dumps(chatbot_enqueue_smoke(), sort_keys=True))
        return 0
    if not args.input:
        parser.error("--input is required for run")
    return run(args.input, args.output, args.run_id, args.shards, args.shard, args.workers, args.duration_minutes)


if __name__ == "__main__":
    raise SystemExit(main())
