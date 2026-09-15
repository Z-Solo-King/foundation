"""Target normalization and shard selection for the public benchmark."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from foundation_core.normalization import canonical_url as _canonical_url

@dataclass(frozen=True)
class Target:
    key: str
    url: str
    label: str = ""

def canonical_url(value: str) -> str:
    return _canonical_url(value, error_message=f"unsupported URL: {value!r}")

def target_key(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()

def load_targets(path: Path) -> list[Target]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("targets", raw.get("sites", raw)) if isinstance(raw, dict) else raw
    if not isinstance(rows, list): raise ValueError("benchmark corpus must contain a list")
    unique: dict[str, Target] = {}
    for item in rows:
        if isinstance(item, str): url, label = item, ""
        elif isinstance(item, dict): url, label = item.get("url") or item.get("site"), str(item.get("name") or item.get("label") or "")
        else: continue
        if not isinstance(url, str): continue
        try: normalized = canonical_url(url)
        except ValueError: continue
        unique.setdefault(target_key(normalized), Target(target_key(normalized), normalized, label))
    if not unique: raise ValueError("no usable HTTP(S) targets found")
    return list(unique.values())

def shard_for(key: str, shards: int) -> int:
    if shards < 1: raise ValueError("shards must be positive")
    return int(key[:16], 16) % shards
