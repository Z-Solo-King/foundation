from datetime import datetime, timedelta, timezone

import pytest

from backend.intelligence.agentic import ResearchAgent, ResearchTask, TaskObservation, research
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.evidence import EvidenceKnowledgeStore, EvidenceRecord, canonical_url
from backend.intelligence.knowledge import ResearchMemory, SourceVisit
from backend.intelligence.planning import create_plan

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def evidence(evidence_id="e1", result="useful", ttl=3600, observed_at=NOW, contradicts=()):
    return EvidenceRecord(evidence_id=evidence_id, claim="battery lasts long", entity="Widget X", source_url="HTTPS://Example.COM/product#section", source_family="retailer", observed_at=observed_at, result=result, confidence=0.8, freshness_ttl_seconds=ttl, contradicts=contradicts)


def test_canonical_url_and_evidence_store():
    assert canonical_url("HTTPS://Example.COM:443/a/") == "https://example.com/a/"
    with pytest.raises(ValueError):
        canonical_url("ftp://example.com/a")
    store = EvidenceKnowledgeStore()
    assert store.add(evidence()) is True
    assert store.add(evidence()) is False
    assert store.get("e1") is not None
    assert len(store.search("Widget X", ("battery",))) == 1
    assert store.search("Widget X", ("missing",)) == []
    assert store.search("Widget X", ("battery",), source_family="other") == []
    assert len(store.reusable("Widget X", ("battery",), NOW)) == 1
    assert len(store.stale("Widget X", ("battery",), NOW + timedelta(hours=2))) == 1
    permanent = evidence("permanent", ttl=None)
    assert store.add(permanent) is True
    assert store.is_fresh(permanent, NOW + timedelta(days=99)) is True
    naive = evidence("naive", observed_at=datetime(2026, 9, 14, 12, 0))
    assert store.add(naive) is True
    assert store.is_fresh(naive, NOW) is True
    auto_now = evidence("auto-now")
    assert store.is_fresh(auto_now) is True
    with pytest.raises(ValueError):
        EvidenceRecord(evidence_id="bad", claim="a", entity="Widget", source_url="https://e.test", source_family="x", observed_at=NOW, freshness_ttl_seconds=-1)
    assert store.export()


def test_evidence_validation_and_contradictions():
    with pytest.raises(ValueError):
        EvidenceRecord(evidence_id="x", claim="", entity="Widget", source_url="https://e.test", source_family="x", observed_at=NOW)
    with pytest.raises(ValueError):
        EvidenceRecord(evidence_id="x", claim="a", entity="Widget", source_url="not-a-url", source_family="x", observed_at=NOW)
    with pytest.raises(ValueError):
        EvidenceRecord(evidence_id="x", claim="a", entity="Widget", source_url="https://e.test", source_family="x", observed_at=NOW, confidence=2)
    store = EvidenceKnowledgeStore()
    row = EvidenceRecord(evidence_id="c1", claim="battery is poor", entity="Widget X", source_url="https://e.test", source_family="review", observed_at=NOW, result="contradictory", contradicts=("e1",))
    plain = evidence("plain", result="useful", contradicts=())
    store.add(row)
    store.add(plain)
    assert store.contradictions("Widget X") == [row]
    assert store.is_fresh(row, NOW) is True


def test_research_memory_visit_policy_and_roundtrip():
    memory = ResearchMemory()
    visit = SourceVisit(task_id="T1", url="HTTPS://Example.COM/a#x", source_family="retailer", purpose="price", method="search", result="useful", visited_at=NOW, finding="new price", revisit_after=NOW + timedelta(days=1))
    assert memory.record_visit(visit) is True
    assert memory.record_visit(visit) is False
    assert memory.should_visit("T1", "https://example.com/a", NOW) is False
    assert memory.should_visit("T1", "https://example.com/a", NOW + timedelta(days=2)) is True
    assert memory.unseen_domains("T1", ["https://example.com/b", "https://new.example/b", "https://new.example/b"]) == ["https://new.example/b"]
    blocked = SourceVisit(task_id="T2", url="https://blocked.example", source_family="retailer", purpose="price", method="search", result="blocked", visited_at=NOW)
    assert blocked.reusable(NOW) is False
    permanent = SourceVisit(task_id="T3", url="https://fresh.example", source_family="retailer", purpose="price", method="search", result="useful", visited_at=NOW)
    assert permanent.reusable(NOW + timedelta(days=1)) is True
    with pytest.raises(ValueError):
        SourceVisit(task_id="", url="https://e.test", source_family="x", purpose="x", method="x", result="failed", visited_at=NOW)
    memory.add_evidence(evidence())
    restored = ResearchMemory.from_json(memory.to_json())
    assert len(restored.prior_visits("T1")) == 1
    assert restored.reusable_evidence("Widget X", ("battery",), NOW)
    with pytest.raises(ValueError):
        ResearchMemory.from_json('{"schema":"unknown"}')


def test_agent_validation_and_terminal_states():
    with pytest.raises(ValueError):
        ResearchAgent(max_iterations=0)
    agent = ResearchAgent(max_iterations=2)
    state = agent.create_state(ResearchContract(question="test", depth="quick"))
    assert agent._reuse(state.tasks[0]) is None
    finished = agent.step(state)
    assert finished.status == "blocked"
    done = agent.step(finished)
    assert done == finished

    executor_agent = ResearchAgent(executor=lambda task, store: TaskObservation(task.task_id, "completed"), max_iterations=32)
    no_tasks = executor_agent.step(state.__class__(question=state.question, plan=state.plan, tasks=(), iterations=0))
    assert no_tasks.status == "completed"
    blocked_state = executor_agent.step(state.__class__(question=state.question, plan=state.plan, tasks=(), failed=("x",), iterations=0))
    assert blocked_state.status == "blocked"
    maxed = state.__class__(question=state.question, plan=state.plan, tasks=state.tasks, iterations=32)
    assert executor_agent.step(maxed).status == "blocked"


def test_agent_runs_and_spawns_followup():
    calls = []

    def executor(task, store):
        calls.append(task.task_id)
        if task.stage == "define_question":
            child = ResearchTask(task_id="followup-1", objective="check conflict", stage="verify_evidence", parent_task_id=task.task_id, reason="new contradiction")
            return TaskObservation(task_id=task.task_id, status="completed", evidence=(evidence("e2"),), follow_up=(child,), note="ok")
        return TaskObservation(task_id=task.task_id, status="completed")

    agent = ResearchAgent(executor=executor, max_iterations=20)
    state = agent.run(agent.create_state(ResearchContract(question="test", depth="quick")))
    assert state.status == "completed"
    assert state.iterations >= 1
    assert "followup-1" in calls
    assert agent.evidence.get("e2") is not None


def test_agent_blocked_failed_and_convenience_research():
    def blocked(task, store):
        return TaskObservation(task_id=task.task_id, status="blocked")

    agent = ResearchAgent(executor=blocked, max_iterations=2)
    state = agent.run(agent.create_state(ResearchContract(question="test", depth="quick")))
    assert state.status == "blocked"
    assert state.failed

    result_state, result_store = research("test", lambda task, store: TaskObservation(task.task_id, "completed"), depth="quick")
    assert result_state.status == "completed"
    assert isinstance(result_store, EvidenceKnowledgeStore)


def test_agent_run_hits_max_iteration_guard():
    def always_complete_one_step(task, store):
        return TaskObservation(task_id=task.task_id, status="completed")

    agent = ResearchAgent(executor=always_complete_one_step, max_iterations=1)
    state = agent.run(agent.create_state(ResearchContract(question="test", depth="quick")))
    assert state.status == "blocked"
    assert state.iterations == 1


def test_planning_quick_and_temporal_metadata():
    quick = create_plan(ResearchContract(question="latest laptop review", depth="quick"))
    assert len(quick.stages) == 5
    assert quick.metadata["temporal_reconciliation"] == "true"


def test_planning_default_depth_path():
    standard = create_plan(ResearchContract(question="laptop review", depth="standard"))
    assert len(standard.stages) == 8
