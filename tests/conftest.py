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

    class Headers(dict):
        def get(self, key, default=None):
            return super().get(key, default)

        def set(self, key, value):
            self[key] = value

    class Response:
        def __init__(self, body="", status=200, headers=None, payload=None):
            if payload is not None:
                body = payload
            self.body = body
            self.payload = body
            self.status = status
            self.headers = Headers(headers or {})

        @staticmethod
        def json(payload, status=200):
            return Response(payload=payload, status=status)

        def __repr__(self):
            return repr(self.payload)


    class WorkerEntrypoint:
        pass

    workers.Response = Response
    workers.WorkerEntrypoint = WorkerEntrypoint
    sys.modules["workers"] = workers


_install_workers_compat()
