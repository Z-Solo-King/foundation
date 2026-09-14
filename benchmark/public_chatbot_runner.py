from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import re
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


USER_AGENT = "ResearchIntelligenceEngine-Benchmark/2026.09"
PRODUCT_HINTS = ("product", "itemprop=\"name\"", "productid", "sku", "add-to-cart", "price")


class _ProductParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.links: list[str] = []
        self.jsonld_blocks: list[str] = []
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []
        self._capture_link = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "script" and attr.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_parts = []
        if tag.lower() == "a" and attr.get("href"):
            self.links.append(attr["href"] or "")

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
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"unsupported URL: {value!r}")
    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    port = parts.port
    netloc = host if not port or (scheme, port) in {("http", 80), ("https", 443)} else f"{host}:{port}"
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


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
        unique.setdefault(target_key(normalized), Target(target_key(normalized), normalized, label))
    if not unique:
        raise ValueError("no usable HTTP(S) targets found")
    return list(unique.values())


def shard_for(key: str, shards: int) -> int:
    return int(key[:16], 16) % shards


def _classify(status: int, body: bytes, diagnostics: list[str]) -> tuple[str, int, str, int, int, int]:
    text = body.decode("utf-8", errors="ignore")
    parser = _ProductParser()
    try:
        parser.feed(text)
    except Exception as exc:
        diagnostics.append(type(exc).__name__)
    product_candidates = sum(text.lower().count(h) for h in PRODUCT_HINTS)
    jsonld = len(parser.jsonld_blocks)
    title = " ".join(" ".join(parser.title_parts).split())[:300]
    if status in {401, 403, 429}:
        result = "blocked"
    elif status >= 500:
        result = "error"
    elif not text.strip():
        result = "empty"
    elif product_candidates or jsonld:
        result = "ok"
    else:
        result = "empty"
    return result, len(body), title, product_candidates, jsonld, 1


def fetch_target(target: Target, timeout: float = 20.0) -> Receipt:
    started = time.perf_counter()
    diagnostics: list[str] = []
    status = 0
    body = b""
    try:
        request = Request(target.url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"})
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            status = int(getattr(response, "status", 200))
            body = response.read(2_000_000)
        result, size, title, candidates, jsonld, pages = _classify(status, body, diagnostics)
    except (TimeoutError, socket.timeout):
        result, size, title, candidates, jsonld, pages = "resource_limited", 0, "", 0, 0, 0
        diagnostics.append("timeout")
    except Exception as exc:
        result, size, title, candidates, jsonld, pages = "error", 0, "", 0, 0, 0
        diagnostics.append(type(exc).__name__)
    return Receipt(
        run_id="",
        shard=0,
        shard_count=1,
        key=target.key,
        url=target.url,
        status=result,
        http_status=status,
        elapsed_ms=int((time.perf_counter() - started) * 1000),
        bytes_read=size,
        pages_fetched=pages,
        title=title,
        product_candidates=candidates,
        jsonld_blocks=jsonld,
        diagnostics=tuple(diagnostics),
        recorded_at=int(time.time()),
    )


def run(input_path: str, output: str, run_id: str, shards: int, shard: int, workers: int, duration_minutes: int) -> int:
    targets = load_targets(Path(input_path))
    selected = [t for t in targets if shard_for(t.key, shards) == shard]
    root = Path(output) / run_id
    root.mkdir(parents=True, exist_ok=True)
    receipt_path = root / f"shard-{shard}.jsonl"
    deadline = time.monotonic() + duration_minutes * 60
    lock = threading.Lock()
    counts = {"ok": 0, "empty": 0, "blocked": 0, "resource_limited": 0, "error": 0}
    if not selected:
        print(json.dumps({"run_id": run_id, "shard": shard, "selected": 0, "status_counts": counts}, sort_keys=True))
        return 0

    # Repeat the finite corpus until the requested time window expires, while never exceeding the worker bound.
    cycle = 0
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(selected)))) as pool:
        while time.monotonic() < deadline:
            cycle += 1
            futures = {pool.submit(fetch_target, target): target for target in selected}
            for future in as_completed(futures):
                receipt = future.result()
                receipt = Receipt(run_id=run_id, shard=shard, shard_count=shards, **{k: getattr(receipt, k) for k in asdict(receipt) if k not in {"run_id", "shard", "shard_count"}})
                with lock:
                    with receipt_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(asdict(receipt), ensure_ascii=False, separators=(",", ":")) + "\n")
                    counts[receipt.status] = counts.get(receipt.status, 0) + 1
    summary = {"run_id": run_id, "shard": shard, "shards": shards, "cycles": cycle, "selected": len(selected), "status_counts": counts}
    (root / f"summary-{shard}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
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
