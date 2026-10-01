"""Synthetic Operations policy service for public-worker tests only."""
from __future__ import annotations

from types import SimpleNamespace


class _Response:
    status = 200

    async def json(self):
        return {
            "ok": True,
            "policy_version": "public-admission/v1",
            "policy": {
                "version": "public-admission/v1",
                "window_seconds": 60,
                "max_requests_per_subject": 7,
                "max_requests_global": 70,
                "max_concurrent_per_subject": 4,
                "max_concurrent_global": 8,
                "retry_after_seconds": 3,
                "protected_routes": ["chat", "research", "stream"],
            },
            "protected_rule_digest": "synthetic-test-digest",
        }


class FakePolicyBinding:
    async def fetch(self, request):
        return _Response()


def policy_binding():
    return FakePolicyBinding()
