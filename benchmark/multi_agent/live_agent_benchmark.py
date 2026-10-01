#!/usr/bin/env python3
"""Public invocation bridge; live agent benchmark implementation is private Operations."""
from __future__ import annotations
import os, runpy

def main() -> int:
    runner = os.environ.get("OPERATIONS_AGENT_BENCHMARK_RUNNER", "").strip()
    if not runner or not os.path.isfile(runner):
        raise SystemExit("private Operations agent benchmark is unavailable")
    runpy.run_path(runner, run_name="__main__")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
