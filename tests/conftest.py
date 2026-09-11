"""CPython test bootstrap for Cloudflare-only Workers runtime imports."""
from __future__ import annotations

import importlib
import sys
import types


def _install_workers_compat() -> None:
    try:
        importlib.import_module("workers")
        return
    except ModuleNotFoundError as exc:
        if exc.name != "js":
            raise

    workers = types.ModuleType("workers")

    class Response:
        @staticmethod
        def json(payload, status=200):
            return types.SimpleNamespace(status=status, payload=payload)

    class WorkerEntrypoint:
        pass

    workers.Response = Response
    workers.WorkerEntrypoint = WorkerEntrypoint
    sys.modules["workers"] = workers


_install_workers_compat()
