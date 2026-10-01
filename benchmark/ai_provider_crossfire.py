#!/usr/bin/env python3
"""Public bridge for the private provider CrossFire implementation.

The executable benchmark, provider inventory, prompts and selection logic live in
private Operations. This file exposes only the stable public invocation path.
"""
from __future__ import annotations

import os
import runpy
from pathlib import Path


def main() -> int:
    raw = os.environ.get("OPERATIONS_CROSSFIRE_RUNNER", "").strip()
    if not raw:
        raise SystemExit("private Operations CrossFire runner is not mounted")
    path = Path(raw).resolve()
    if not path.is_file():
        raise SystemExit("private Operations CrossFire runner is unavailable")
    result = runpy.run_path(str(path), run_name="__main__")
    return int(result.get("EXIT_CODE", 0) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
