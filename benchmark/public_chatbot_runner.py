"""Compatibility entrypoint for the public benchmark runner.

Target handling, HTTP fetch/classification and execution cycles are grouped in focused
modules; existing imports and CLI behavior remain available here.
"""
from __future__ import annotations

import argparse
import json

from benchmark.public_chatbot_targets import Target, canonical_url, load_targets, shard_for, target_key
from benchmark.public_chatbot_fetch import Receipt, fetch_target
from benchmark.public_chatbot_execution import chatbot_enqueue_smoke, run

MAX_ATTEMPTS = 2
REQUEST_TIMEOUT_SECONDS = 20.0
MAX_RESPONSE_BYTES = 2_000_000
MIN_CYCLE_INTERVAL_SECONDS = 5.0
TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}
USER_AGENT = "ResearchIntelligenceEngine-Benchmark/2026.09"
PRODUCT_HINTS = ("product", "itemprop=\"name\"", "productid", "sku", "add-to-cart", "price")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["run", "chatbot-smoke"]); parser.add_argument("--input"); parser.add_argument("--output", default=".runtime/benchmarks"); parser.add_argument("--run-id", default="public-benchmark"); parser.add_argument("--shards", type=int, default=4); parser.add_argument("--shard", type=int, default=0); parser.add_argument("--workers", type=int, default=6); parser.add_argument("--duration-minutes", type=int, default=18)
    args = parser.parse_args()
    if args.command == "chatbot-smoke": print(json.dumps(chatbot_enqueue_smoke(), sort_keys=True)); return 0
    if not args.input: parser.error("--input is required for run")
    return run(args.input,args.output,args.run_id,args.shards,args.shard,args.workers,args.duration_minutes)

if __name__ == "__main__": raise SystemExit(main())
