import asyncio
import builtins
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


def test_harness_regression_paths():
    from backend.evaluation.harness import BenchmarkCase, EvaluationCategory, EvaluationHarness, EvaluationResult

    harness = EvaluationHarness()
    case = BenchmarkCase("reg", EvaluationCategory.RETRIEVAL, "d", "q", "a")
    harness.register_case(case)
    result = harness.regression_test("reg", lambda c: EvaluationResult(c.case_id, True))
    assert result.passed is True
    with pytest.raises(ValueError):
        harness.regression_test("missing", lambda c: EvaluationResult(c.case_id, True))


def test_lineage_remaining_validation_and_observation_default_time():
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.observations import Observation

    with pytest.raises(ValueError, match="invalid lineage_type"):
        SourceLineage("s", "f", lineage_type="invalid").validate()
    with pytest.raises(ValueError, match="must identify its origin"):
        SourceLineage("s", "f", lineage_type="republished", origin_fingerprint="fp").validate()

    obs = Observation("o", "https://e", "x", None)
    assert obs.observed_at.tzinfo is not None


def test_http_success_transport_and_wikipedia_worker_export(monkeypatch):
    import backend.sources.http as http
    import backend.sources.wikipedia as wikipedia

    class Response:
        status = 200
        headers = {"content-type": "text/plain", "etag": "etag-1"}

        async def arrayBuffer(self):
            return b"hello"

    async def fetcher(_url, _opts):
        return Response()

    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
    assert result.status == 200
    assert result.content == b"hello"
    assert result.etag == "etag-1"

    fake_workers = SimpleNamespace(fetch=lambda *_args, **_kwargs: None)
    monkeypatch.setitem(sys.modules, "workers", fake_workers)
    assert callable(wikipedia._workers_fetch())


def test_contradiction_remaining_scope_quantity_and_text_paths():
    from backend.intelligence.contradiction import (
        TypedClaim,
        _scopes_overlap,
        detect_typed_contradiction,
    )

    assert _scopes_overlap(None, "x") is True
    assert _scopes_overlap("A", "a") is True
    assert _scopes_overlap("A", "B") is False

    def c(cid, value, value_type, **changes):
        data = dict(
            entity="E",
            predicate="P",
            scope=None,
            valid_from=None,
            valid_until=None,
            unit="u",
            qualifier="q",
            version=None,
        )
        data.update(changes)
        return TypedClaim(
            cid,
            data.pop("entity"),
            data.pop("predicate"),
            value,
            value_type,
            **data,
        )

    assert detect_typed_contradiction(
        c("a", 1, "numeric", valid_from=datetime(2024, 1, 2)),
        c("b", 2, "numeric", valid_until=datetime(2024, 1, 1)),
    ) is None
    assert detect_typed_contradiction(c("a", 1, "quantity"), c("b", 2, "quantity")) is not None
    assert detect_typed_contradiction(c("a", "x", "text", qualifier="A"), c("b", "x", "text", qualifier="B")) is not None
    assert detect_typed_contradiction(c("a", "x", "text"), c("b", "x", "text")) is None


def test_worker_boundary_remaining_result_guards():
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator

    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")
    now = datetime.now(timezone.utc)

    for status, execution_time, worker_id in (("success", -1, "worker"), ("success", 1, ""), ("bogus", 1, "worker")):
        result = WorkerResult(task.task_id, task.nonce, status, None, None, execution_time, worker_id, now)
        ok, _ = validator.validate_result(task, result, None)
        assert ok is False

    active = validator.create_task("fetch", {}, "p")
    validator._active_tasks[active.nonce] = "different-task"
    active_result = WorkerResult(active.task_id, active.nonce, "failure", None, None, 1, "worker", now)
    ok, reason = validator.validate_result(active, active_result, None)
    assert ok is False and "different task" in reason

    hashed = validator.create_task("fetch", {}, "p")
    payload = {"x": 1}
    bad_hash = hashlib.sha256(b"wrong").hexdigest()
    result = WorkerResult(hashed.task_id, hashed.nonce, "success", bad_hash, payload, 1, "worker", now)
    ok, reason = validator.validate_result(hashed, result, payload)
    assert ok is False and "hash mismatch" in reason


def test_verifier_remaining_control_flow():
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.claims import Claim
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.observations import EvidenceSpan, Observation
    from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier

    obs = Observation.create("o", "sid", "https://e", "banana")
    cert = create_certificate(obs, EvidenceSpan("o", 0, 6))
    claim = Claim.create("c", "banana")
    other = Claim.create("other", "apple")
    verifier = EvidenceVerifier()

    result = verifier.verify_claim(claim, (cert,), {"o": obs}, {"sid": SourceLineage("sid", "family")}, (claim, other))
    assert result.status == ClaimStatus.SUPPORTED

    inaccessible = verifier.verify_claim(
        claim,
        (cert,),
        {},
        {},
        (claim,),
    )
    assert inaccessible.status == ClaimStatus.INACCESSIBLE
