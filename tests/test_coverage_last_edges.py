from datetime import datetime, timedelta, timezone

import pytest


def test_entailment_ai_positive_adjudication():
    from backend.evaluation.entailment import EntailmentResult, EntailmentStatus, adjudicate_ambiguous
    result = adjudicate_ambiguous(EntailmentResult(EntailmentStatus.AMBIGUOUS, 0.7, "ambiguous"), True)
    assert result.status == EntailmentStatus.SUPPORTED


def test_engine_invalid_lifecycle_branches():
    from backend.execution.engine import complete_research, create_run, start_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    contract = ResearchContract(question="q")
    plan = ResearchPlan(question="q", stages=(), source_budget=1, evidence_budget=1)
    planned = create_run("r", contract, plan)
    with pytest.raises(ValueError):
        start_research(planned.__class__(planned.run_id, planned.contract, planned.plan, "completed"))
    running = start_research(planned)
    assert complete_research(running, success=False).status == "failed"
    with pytest.raises(ValueError):
        complete_research(planned)


def test_worker_task_validation_all_remaining_rejections(monkeypatch):
    from backend.execution.worker_boundary import WorkerTask, WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator()
    base = validator.create_task("fetch", {}, "p")

    assert validator.validate_task(WorkerTask("", base.nonce, base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, "2.0", base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, base.schema_version, "unknown", base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False

    huge = {"x": "a" * 17000}
    with pytest.raises(ValueError, match="metadata exceeds"):
        validator.create_task("fetch", {}, "p", huge)

    active = validator.create_task("fetch", {}, "p")
    assert validator.validate_task(active)[0] is True
    conflicting = WorkerTask(active.task_id + "2", active.nonce, active.schema_version, active.task_type, active.input_hash, active.provenance, active.created_at, active.expires_at, active.metadata)
    assert validator.validate_task(conflicting)[0] is False

    completed = validator.create_task("fetch", {}, "p")
    validator.validate_task(completed)
    validator._completed_nonces.add(completed.nonce)
    assert validator.validate_task(completed)[0] is False

    expired = WorkerTask(base.task_id + "x", "nonce-expired", base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, datetime.now(timezone.utc) - timedelta(hours=1), base.metadata)
    assert validator.validate_task(expired)[0] is False

    good = validator.create_task("fetch", {"x": 1}, "p")
    now = datetime.now(timezone.utc)
    for status in ("bogus",):
        result = WorkerResult(good.task_id, good.nonce, status, None, None, 1, "worker", now)
        assert validator.validate_result(good, result, None)[0] is False
    for status in ("failure", "timeout", "invalid"):
        task = validator.create_task("fetch", {status: 1}, "p")
        result = WorkerResult(task.task_id, task.nonce, status, None, None, 1, "worker", now)
        ok, reason = validator.validate_result(task, result, None)
        assert ok is True and reason == "valid"


def test_typed_contradiction_remaining_unknown_type():
    from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction
    a = TypedClaim("a", "E", "P", "x", "unknown", unit=None, qualifier=None)
    b = TypedClaim("b", "E", "P", "y", "unknown", unit=None, qualifier=None)
    assert detect_typed_contradiction(a, b) is None


def test_lineage_invalid_type_and_missing_origin_validation():
    from backend.intelligence.lineage import SourceLineage
    with pytest.raises(ValueError):
        SourceLineage("s", "f", lineage_type="bogus").validate()
    with pytest.raises(ValueError):
        SourceLineage("s", "f", lineage_type="derived").validate()


def test_observation_invalid_span_order_and_creation():
    from backend.intelligence.observations import EvidenceSpan, Observation
    obs = Observation.create("o", "sid", "https://e", "abc")
    with pytest.raises(ValueError):
        EvidenceSpan("o", 3, 2).text_from(obs)
    with pytest.raises(ValueError):
        EvidenceSpan("wrong", 0, 1).text_from(obs)


def test_verifier_inaccessible_and_semantic_rejection_branches():
    from backend.intelligence.claims import Claim
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.observations import EvidenceSpan, Observation
    from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier
    claim = Claim.create("c", "text")
    obs = Observation.create("o", "s", "https://e", "other")
    cert = create_certificate(obs, EvidenceSpan("o", 0, 5))
    verifier = EvidenceVerifier(semantic_strict=True)
    result = verifier.verify_claim(claim, (cert,), {"o": obs}, {}, ())
    assert result.status in {ClaimStatus.UNSUPPORTED, ClaimStatus.INACCESSIBLE}


def test_http_invalid_runtime_and_redirect_without_location(monkeypatch):
    import backend.sources.http as http
    monkeypatch.delitem(__import__('sys').modules, "workers", raising=False)
    with pytest.raises(RuntimeError):
        http._workers_fetch()

    class Response:
        status = 302
        headers = {}
        async def arrayBuffer(self):
            return b""
    async def fetcher(_url, _opts):
        return Response()
    import asyncio
    with pytest.raises(RuntimeError, match="redirect"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
