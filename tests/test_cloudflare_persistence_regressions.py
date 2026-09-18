from types import SimpleNamespace
import hashlib

import pytest

from backend.persistence.cloudflare import (
    CloudflarePersistence,
    IDEMPOTENCY_CONTRACT_REVISION,
    IdempotencyConflictError,
    execution_scope_fingerprint,
    request_fingerprint,
)
from backend.api.models import ResearchRequest


class FakeStatement:
    def __init__(self, value=None):
        self.value = value
        self.args = ()

    def bind(self, *args):
        self.args = args
        return self

    async def first(self):
        return self.value

    async def run(self):
        return SimpleNamespace(meta={"changes": 1})


class FakeDB:
    def __init__(self, run=None):
        self.run = run
        self.batch_result = [SimpleNamespace(results=[]), SimpleNamespace(results=[]), SimpleNamespace(results=[])]
        self.idempotency_row = None

    def prepare(self, sql):
        if sql.startswith("SELECT * FROM research_runs"):
            return FakeStatement(self.run)
        if sql.startswith("SELECT run_id, request_hash, subject_fingerprint"):
            value = self.idempotency_row
            if value is None and self.batch_result[2].results:
                value = self.batch_result[2].results[0]
            return FakeStatement(value)
        return FakeStatement()


class FakeArtifacts:
    async def put(self, key, content, **kwargs):
        return None
