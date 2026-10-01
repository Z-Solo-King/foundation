#!/usr/bin/env python3
"""Public bridge for the private live agent benchmark."""
from __future__ import annotations
import os, runpy
def main():
    runner=os.environ.get("OPERATIONS_AGENT_BENCHMARK_RUNNER","").strip()
    if not runner or not os.path.isfile(runner):
        raise SystemExit("private Operations live-agent benchmark is not mounted")
    runpy.run_path(runner, run_name="__main__")
if __name__=="__main__":
    main()
