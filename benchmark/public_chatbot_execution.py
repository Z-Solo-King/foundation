"""Repeated-cycle benchmark execution and receipt persistence."""
from __future__ import annotations

import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from .public_chatbot_fetch import fetch_target, Receipt
from .public_chatbot_targets import load_targets, shard_for

MIN_CYCLE_INTERVAL_SECONDS=5.0

def run(input_path: str, output: str, run_id: str, shards: int, shard: int, workers: int, duration_minutes: int) -> int:
    targets=load_targets(Path(input_path))
    if not 0<=shard<shards: raise ValueError(f"shard must be within [0, {shards})")
    selected=[t for t in targets if shard_for(t.key,shards)==shard]
    root=Path(output)/run_id; root.mkdir(parents=True,exist_ok=True)
    receipt_path=root/f"shard-{shard}.jsonl"; summary_path=root/f"summary-{shard}.json"
    deadline=time.monotonic()+duration_minutes*60
    counts={"ok":0,"empty":0,"blocked":0,"resource_limited":0,"error":0}; http_counts=Counter(); diagnostic_counts=Counter(); cycle=0
    if not selected:
        summary={"run_id":run_id,"shard":shard,"shards":shards,"cycles":0,"selected":0,"status_counts":counts,"http_status_counts":{},"diagnostic_counts":{}}
        summary_path.write_text(json.dumps(summary,indent=2),encoding="utf-8"); print(json.dumps(summary,sort_keys=True)); return 0
    pool=ThreadPoolExecutor(max_workers=max(1,min(workers,len(selected))))
    try:
        while time.monotonic()<deadline:
            cycle+=1; cycle_started=time.monotonic(); futures={pool.submit(fetch_target,t):t for t in selected}
            for future in as_completed(futures):
                receipt=future.result(); receipt=Receipt(run_id,shard,shards,receipt.key,receipt.url,receipt.status,receipt.http_status,receipt.elapsed_ms,receipt.bytes_read,receipt.pages_fetched,receipt.title,receipt.product_candidates,receipt.jsonld_blocks,receipt.diagnostics,receipt.recorded_at)
                with receipt_path.open("a",encoding="utf-8") as handle: handle.write(json.dumps(asdict(receipt),ensure_ascii=False,separators=(",",":"))+"\n")
                counts[receipt.status]=counts.get(receipt.status,0)+1
                if receipt.http_status: http_counts[str(receipt.http_status)]+=1
                for diagnostic in receipt.diagnostics: diagnostic_counts[diagnostic]+=1
            remaining=MIN_CYCLE_INTERVAL_SECONDS-(time.monotonic()-cycle_started)
            if remaining>0 and time.monotonic()<deadline: time.sleep(min(remaining,max(0.0,deadline-time.monotonic())))
    finally: pool.shutdown(wait=True,cancel_futures=True)
    summary={"run_id":run_id,"shard":shard,"shards":shards,"cycles":cycle,"selected":len(selected),"status_counts":counts,"http_status_counts":dict(sorted(http_counts.items())),"diagnostic_counts":dict(sorted(diagnostic_counts.items())),"min_cycle_interval_seconds":MIN_CYCLE_INTERVAL_SECONDS,"max_attempts":2}
    summary_path.write_text(json.dumps(summary,indent=2),encoding="utf-8"); print(json.dumps(summary,sort_keys=True)); return 0

def chatbot_enqueue_smoke() -> dict[str,object]:
    import os,tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); corpus=root/"corpus"; inbox=root/"inbox"; corpus.mkdir(); inbox.mkdir(); target=corpus/"sites.json"; target.write_text(json.dumps(["https://example.com/"]),encoding="utf-8"); job=inbox/f"run-{os.getpid()}.json"; job.write_text(json.dumps({"input":str((corpus/"sites.json").resolve()),"run_id":"chatbot-smoke"}),encoding="utf-8"); payload=json.loads(job.read_text(encoding="utf-8")); return {"passed":payload["run_id"]=="chatbot-smoke","job":job.name}
