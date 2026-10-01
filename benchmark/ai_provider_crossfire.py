#!/usr/bin/env python3
"""Public invocation bridge; live provider benchmark implementation is private Operations."""
from __future__ import annotations
import os, runpy

def main() -> int:
    runner = os.environ.get("OPERATIONS_CROSSFIRE_RUNNER", "").strip()
    if not runner or not os.path.isfile(runner):
        raise SystemExit("private Operations CrossFire runner is unavailable")
    values = runpy.run_path(runner, run_name="__main__")
    return int(values.get("EXIT_CODE", 0) or 0)

if __name__ == "__main__":
    raise SystemExit(main())
