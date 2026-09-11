import asyncio
import hashlib
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


def test_resource_budget_all_paths():
    from backend.execution.resources import ResourceBudget, ResourceError
    budget = ResourceBudget(requests=2, evidence_items=2, ai_calls=3, inference_calls=1)
    assert budget.inference_remaining == 1
    assert budget.remaining()["inference_calls"] == 1
    budget.consume_requests(); budget.consume_evidence(); budget.consume_ai_calls(); budget.consume_inference()
    with pytest.raises(ValueError): ResourceBudget(inference_calls=-1)
    with pytest.raises(ValueError): budget.consume("requests", -1)
    with pytest.raises(ValueError): budget.consume("missing")
    budget.requests = None
    with pytest.raises(ValueError): budget.consume("requests")
    budget.requests = 0
    with pytest.raises(ResourceError): budget.consume_requests()


def test_contradiction_typed_and_legacy_all_markers():
    from backend.intelligence.contradiction import TypedClaim, detect_contradiction, detect_typed_contradiction
    assert detect_contradiction("", "x") is None
    assert detect_contradiction("same", "same") is None
    for pos, neg in (("true", "false"), ("yes", "no"), ("enabled", "disabled"), ("available", "unavailable")):
        assert detect_contradiction(pos, neg) is not None
        assert detect_contradiction(neg, pos) is not None
    assert detect_contradiction("not available", "available") is not None
    assert detect_contradiction("available", "not available") is not None
    base = dict(entity="E", predicate="P", scope=None, valid_from=None, valid_until=None, unit="u", qualifier="q", version=None)
    def claim(cid, value, value_type, **changes):
        data = dict(base); data.update(changes)
        return TypedClaim(cid, data.pop("entity"), data.pop("predicate"), value, value_type, **data)
    assert detect_typed_contradiction(claim("a", 1, "numeric"), claim("b", 2, "numeric")) is not None
    assert detect_typed_contradiction(claim("a", "2024-01-01", "date"), claim("b", date(2024,1,2), "date")) is not None
    assert detect_typed_contradiction(claim("a", "yes", "boolean"), claim("b", "no", "boolean")) is not None
    assert detect_typed_contradiction(claim("a", 1, "quantity"), claim("b", 2, "quantity")) is not None
    assert detect_typed_contradiction(claim("a", "alpha", "text"), claim("b", "beta", "text")) is not None
    assert detect_typed_contradiction(claim("a", "alpha", "text", qualifier="x"), claim("b", "alpha", "text", qualifier="y")) is not None
    assert detect_typed_contradiction(claim("a", 1, "numeric", unit="kg"), claim("b", 2, "numeric", unit="lb")) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", scope="a"), claim("b", 2, "numeric", scope="b")) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", valid_until=datetime(2024,1,1)), claim("b", 2, "numeric", valid_from=datetime(2024,1,2))) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", version="v1"), claim("b", 2, "numeric", version="v2")) is None


def test_worker_boundary_fail_closed_all_branches():
    from backend.execution.worker_boundary import WorkerResult, WorkerTask, WorkerTaskValidator
    validator = WorkerTaskValidator()
    with pytest.raises(ValueError): validator.create_task("", {}, "p")
    with pytest.raises(ValueError): validator.create_task("fetch", {}, "")
    with pytest.raises(ValueError): validator.create_task("fetch", {}, "p", {"x":"a"*20000})
    task = validator.create_task("fetch", {"a":1}, "p", {"m":1})
    assert validator.validate_task(task)[0]
    expired = WorkerTask(task.task_id, task.nonce+"e", task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, datetime.now(timezone.utc)-timedelta(hours=1), task.metadata)
    assert validator.validate_task(expired)[0] is False
    malformed = WorkerTask("", "", task.schema_version, task.task_type, task.input_hash, "", task.created_at, task.expires_at, task.metadata)
    assert "required" in validator.validate_task(malformed)[1]
    now = datetime.now(timezone.utc)
    backwards = WorkerTask(task.task_id, "nonce-b", task.schema_version, task.task_type, task.input_hash, task.provenance, now + timedelta(hours=2), now + timedelta(hours=1), task.metadata)
    assert "precedes" in validator.validate_task(backwards)[1]
    bad_schema = WorkerTask(task.task_id, "nonce-s", "2", task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert validator.validate_task(bad_schema)[0] is False
    bad_type = WorkerTask(task.task_id, "nonce-t", task.schema_version, "x", task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert validator.validate_task(bad_type)[0] is False
    huge_meta = WorkerTask(task.task_id, "nonce-m", task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, {"x":"a"*20000})
    assert validator.validate_task(huge_meta)[0] is False
    other = WorkerTask(task.task_id+"2", task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert "another task" in validator.validate_task(other)[1]

    def result(status="success", **kw):
        return WorkerResult(task.task_id, task.nonce, status, kw.get("output_hash"), kw.get("output_data"), kw.get("execution_time_ms", 1), kw.get("worker_id", "worker"), kw.get("completed_at", datetime.now(timezone.utc)))
    h = hashlib.sha256(b'{"x": 1}').hexdigest()
    assert validator.validate_result(task, result(output_hash=h), {"x":1})[0] is True
    task2 = validator.create_task("fetch", {}, "p")
    for r in (
        result("success", output_hash=h),
        WorkerResult("x", task2.nonce, "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, "bad", "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "weird", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", None, None, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", "bad", {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, -1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, 1, "", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)+timedelta(minutes=6)),
    ):
        validator.validate_result(task2, r, r.output_data)
    assert validator.sample_validate(result("failure"), {})[0] is False
    assert validator.sample_validate(result("success"), [1])[0] is False
    assert validator.sample_validate(result("success"), {"error":"x"})[0] is False
    assert validator.sample_validate(result("success"), {"error":"x","status":"error"})[0] is True


def test_worker_http_entrypoint_all_paths():
    import worker
    class Req:
        def __init__(self, method, url, payload=None, headers=None): self.method, self.url, self._payload, self.headers = method, url, payload, headers or {}
        async def json(self): return self._payload
    class DBStatement:
        def __init__(self, first=None, all_rows=None): self.first_value, self.all_rows = first, all_rows or []
        def bind(self,*args): return self
        async def run(self): return {"success":True}
        async def first(self): return self.first_value
        async def all(self): return self.all_rows
    class DB:
        def prepare(self, sql): return DBStatement()
    class Art:
        async def put(self,*args,**kwargs): pass
    env = SimpleNamespace(DB=DB(), ARTIFACTS=Art(), ENVIRONMENT="development", AUTH_TOKEN=None, CONTROL_PLANE=None)
    entry = worker.Default(); entry.env = env
    assert asyncio.run(entry.fetch(Req("GET", "https://x/health")))
    assert asyncio.run(entry.fetch(Req("GET", "https://x/readiness")))
    assert asyncio.run(entry.fetch(Req("GET", "https://x/nope")))
    assert asyncio.run(entry.fetch(Req("GET", "https://x/api/v1/research/r")))
    assert asyncio.run(entry.fetch(Req("POST", "https://x/api/v1/research", [])))
    assert asyncio.run(entry.fetch(Req("POST", "https://x/api/v1/research", {"question":"q"})))
