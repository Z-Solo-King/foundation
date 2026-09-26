#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"schemas/registry.json"

def load_registry():
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema_version")!="family-schema-registry/v1": raise ValueError("invalid registry version")
    return data

def main():
    data=load_registry()
    failures=[]
    for item in data["schemas"]:
        path=ROOT/item["path"]
        if not path.exists(): failures.append(f"missing:{item['path']}"); continue
        schema=json.loads(path.read_text(encoding="utf-8"))
        if schema.get("$schema")!="https://json-schema.org/draft/2020-12/schema": failures.append(f"draft:{item['path']}")
        if schema.get("additionalProperties") is not False: failures.append(f"additionalProperties:{item['path']}")
        if item["version"] not in schema.get("$id",""): failures.append(f"id-version:{item['path']}")
    if failures:
        print("\n".join(failures)); return 1
    print(f"schema registry PASS: {len(data['schemas'])} schemas")
    return 0
if __name__=="__main__": raise SystemExit(main())
