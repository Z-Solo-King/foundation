#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT.parent / "operations"
CORPUS = OPERATIONS / "benchmark/polyglot/rust_url_identity/corpus.jsonl"
RUST_MANIFEST = OPERATIONS / "benchmark/polyglot/rust_url_identity/Cargo.toml"

# backend.sources.http depends on Cloudflare's runtime-only workers_fetch module.
# Stub that runtime boundary so the pure canonicalization helper can be tested
# under normal CPython without executing network code.
runtime_mod = types.ModuleType("backend.core.workers_runtime")
runtime_mod.workers_fetch = lambda _reason: None
sys.modules["backend.core.workers_runtime"] = runtime_mod

from backend.sources.http import canonicalize_url  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not CORPUS.is_file() or not RUST_MANIFEST.is_file():
        raise SystemExit("Operations Rust URL identity corpus/manifest missing")

    with tempfile.TemporaryDirectory(prefix="url-parity-") as tmp:
        rust_output = Path(tmp) / "rust-output.jsonl"
        subprocess.run(
            [
                "cargo",
                "run",
                "--quiet",
                "--manifest-path",
                str(RUST_MANIFEST),
                "--",
                str(CORPUS),
                str(rust_output),
            ],
            check=True,
        )

        rust_rows = {}
        for line in rust_output.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                rust_rows[str(row["id"])] = row

        python_rows = {}
        for line in CORPUS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                output = canonicalize_url(row["input"])
                python_rows[str(row["id"])] = {"ok": True, "output": output}
            except Exception as exc:
                python_rows[str(row["id"])] = {"ok": False, "error": type(exc).__name__}

        if set(rust_rows) != set(python_rows):
            missing_rust = sorted(set(python_rows) - set(rust_rows))
            missing_python = sorted(set(rust_rows) - set(python_rows))
            raise SystemExit(
                f"corpus identity mismatch: missing_rust={missing_rust}, missing_python={missing_python}"
            )

        mismatches = []
        rejected = 0
        for case_id in sorted(python_rows):
            py = python_rows[case_id]
            rs = rust_rows[case_id]
            if not py["ok"]:
                rejected += 1
            if bool(py["ok"]) != bool(rs.get("ok")):
                mismatches.append((case_id, py, rs))
                continue
            if py["ok"] and py["output"] != rs.get("output"):
                mismatches.append((case_id, py, rs))

        if rejected < 20:
            raise SystemExit(f"negative corpus requirement failed: {rejected} rejected cases")
        if mismatches:
            raise SystemExit(f"Rust/Python URL parity mismatch: {json.dumps(mismatches[:10], sort_keys=True)}")

        receipt = {
            "schema": "rust-python-url-parity/v1",
            "status": "PASS",
            "case_count": len(python_rows),
            "rejected_case_count": rejected,
            "accepted_case_count": len(python_rows) - rejected,
            "foundation_http_sha256": sha256(ROOT / "backend/sources/http.py"),
            "operations_lib_sha256": sha256(OPERATIONS / "benchmark/polyglot/rust_url_identity/src/lib.rs"),
            "operations_main_sha256": sha256(OPERATIONS / "benchmark/polyglot/rust_url_identity/src/main.rs"),
            "corpus_sha256": sha256(CORPUS),
            "comparison": "acceptance parity plus canonical output equality for accepted cases",
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))

if __name__ == "__main__":
    raise SystemExit(main())
