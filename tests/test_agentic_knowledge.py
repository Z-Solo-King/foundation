from datetime import datetime, timedelta, timezone

import pytest

from backend.intelligence.agentic import ResearchAgent, ResearchTask, TaskObservation
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.evidence import EvidenceKnowledgeStore, EvidenceRecord, canonical_url
from backend.intelligence.knowledge import ResearchMemory, SourceVisit


NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def evidence(evidence_id="e1", result="useful", ttl=3600):
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim="battery lasts long",
        entity="Widget X",
        source_url="HTTPS://Example.COM/product#section",
        source_family="retailer",
        observed_at=NOW,
        result=result,
        confidence=0.8,
        freshness_ttl_seconds=ttl,
    )


def test_canonical_url_and_evidence_store():
    assert canonical_url("HTTPS://Example.COM:443/a/") == "https://example.com/a/"
    store = EvidenceKnowledgeStore()
    assert store.add(evidence()) is True
    assert store.add(evidence()) is False
    assert store.get("e1") is not None
    assert len(store.search("Widget X", ("battery",))) == 1
    assert len(store.reusable("Widget X", ("battery",), NOW)) == 1
    assert len(store.stale("Widget X", ("battery",), NOW + timedelta(hours=2))) == 1


def test_evidence_validation_and_contradictions():
    with pytest.raises(ValueError):
        EvidenceRecord(evidence_id="x", claim="", entity="Widget", source_url="https://e.test", source_family="x", observed_at=NOW)
    with pytest.raises(ValueError):
        EvidenceRecord(evidence_id="x", claim="a", entity="Widget", source_url="https://e.test", source_family="x", observed_at=NOW, confidence=2)
    store = EvidenceKnowledgeStore()
    row = EvidenceRecord(evidence_id="c1", claim="battery is poor", entity="Widget X", source_url="https://e.test", source_family="review", observed_at=NOW, result="contradictory", contradicts=("e1",))
    store.add(row)
    assert store.contradictions("Widget X") == [row]
    assert store.is_fresh(row, NOW) is True


def test_research_memory_visit_policy_and_roundtrip():
    memory = ResearchMemory()
    visit = SourceVisit(
        task_id="T1",
        url="HTTPS://Example.COM/a#x",
        source_family="retailer",
        purpose="price",
        method="search",
        result="useful",
        visited_at=NOW,
        finding="new price",
        revisit_after=NOW + timedelta(days=1),
    )
    assert memory.record_visit(visit) is True
    assert memory.record_visit(visit) is False
    assert memory.should_visit("T1", "https://example.com/a", NOW) is False
    assert memory.should_visit("T1", "https://example.com/a", NOW + timedelta(days=2)) is True
    assert memory.unseen_domains("T1", ["https://example.com/b", "https://new.example/b"]) == ["https://new.example/b"]
    memory.add_evidence(evidence())
    restored = ResearchMemory.from_json(memory.to_json())
    assert len(restored.prior_visits("T1")) == 1
    assert restored.reusable_evidence("Widget X", ("battery",), NOW)
    with pytest.raises(ValueError):
        ResearchMemory.from_json('{"schema":"unknown"}')


def test_agent_without_executor_blocks():
    agent = ResearchAgent(max_iterations=2)
    state = agent.create_state(ResearchContract(question="test", depth="quick"))
    next_state = agent.step(state)
    assert next_state.status == "blocked"


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


def test_agent_failure_and_iteration_guard():
    def failing(task, store):
        return TaskObservation(task_id=task.task_id, status="failed")

    agent = ResearchAgent(executor=failing, max_iterations=1)
    state = agent.run(agent.create_state(ResearchContract(question="test")))
    assert state.status == "blocked"
    assert state.failed
