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
        # workers-py can be installed without exposing a normal CPython
        # ``workers`` module; both that case and its JS-runtime dependency are
        # expected in ordinary unit-test execution.
        if exc.name not in {"workers", "js"}:
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
