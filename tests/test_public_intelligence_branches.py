from datetime import datetime, timezone

from backend.intelligence.agentic import ResearchAgent, ResearchTask, TaskObservation
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.evidence import EvidenceKnowledgeStore, EvidenceRecord
from backend.intelligence.planning import create_plan


NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def _record(evidence_id: str, claim: str = "claim", published_at: datetime | None = NOW) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim=claim,
        entity="Widget",
        source_url=f"https://example.com/{evidence_id}",
        source_family="retailer",
        observed_at=NOW,
        published_at=published_at,
        result="useful",
        method="search",
        provenance="test",
        confidence=0.7,
        freshness_ttl_seconds=3600,
        revision="r1",
        region="IN",
        supports=("other",),
        metadata={"kind": "test"},
    )


def test_evidence_upsert_get_and_export_extended_metadata():
    store = EvidenceKnowledgeStore()
    first = _record("one")
    replacement = _record("one", claim="replacement")
    store.upsert(first)
    assert store.get("one").claim == "claim"
    store.upsert(replacement)
    assert store.get("one").claim == "replacement"
    exported = store.export()[0]
    assert exported["published_at"] == NOW.isoformat()
    assert exported["supports"] == ["other"]
    assert exported["revision"] == "r1"
    assert exported["region"] == "IN"
    assert exported["metadata"] == {"kind": "test"}

    bare = EvidenceRecord(
        evidence_id="bare",
        claim="minimal",
        entity="Widget",
        source_url="https://example.com/bare",
        source_family="retailer",
        observed_at=NOW,
    )
    store.add(bare)
    bare_export = next(row for row in store.export() if row["evidence_id"] == "bare")
    assert bare_export["published_at"] is None
    assert bare_export["revision"] is None
    assert bare_export["region"] is None
    assert bare_export["supports"] == []
    assert bare_export["metadata"] == {}


def test_planner_source_family_expansion_and_temporal_flag():
    plan = create_plan(
        ResearchContract(
            question="Amazon Flipkart Reddit YouTube Chinese Bilibili Zhihu Baidu Tieba Douban PTT teardown PCB price current revision",
            depth="standard",
        )
    )
    families = plan.metadata["required_source_families"]
    for family in ("amazon", "flipkart", "reddit", "youtube", "chinese_communities", "teardown_evidence", "price_stock"):
        assert family in families
    assert plan.metadata["temporal_reconciliation"] == "true"


def test_agent_marks_failed_observation_as_failed():
    def executor(task: ResearchTask, store: EvidenceKnowledgeStore) -> TaskObservation:
        return TaskObservation(task_id=task.task_id, status="failed", note="adapter failure")

    agent = ResearchAgent(executor=executor, max_iterations=2)
    state = agent.run(agent.create_state(ResearchContract(question="test", depth="quick")))
    assert state.status == "blocked"
    assert state.failed
