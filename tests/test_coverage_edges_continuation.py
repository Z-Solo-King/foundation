import asyncio

import pytest


def test_api_success_and_engine_lifecycle():
    from backend.api.main import submit_research
    from backend.api.models import ResearchRequest
    from backend.execution.engine import create_run, complete_research, transition_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan

    response = submit_research(ResearchRequest("q"))
    assert response.ok is True
    assert response.run_id

    run = create_run("r", ResearchContract("q"), ResearchPlan("q", ("a",), 1, 1))
    running = transition_research(run, "running")
    assert running.status == "running"
    assert transition_research(running, "completed").status == "completed"
    assert transition_research(running, "failed").status == "failed"
    with pytest.raises(ValueError):
        transition_research(complete_research(running), "running")


def test_acquisition_and_strategy_no_available(monkeypatch):
    import backend.execution.acquisition as acquisition
    import backend.execution.adaptive as adaptive
    from backend.execution.acquisition import choose_method
    from backend.execution.adaptive import choose_strategy, AcquisitionStrategy
    from backend.intelligence.sources import Source, SourcePolicy, SourceType

    source = Source("s", "https://example.com", SourceType.WEB)
    monkeypatch.setattr(acquisition, "DEFAULT_METHODS", ())
    with pytest.raises(RuntimeError):
        choose_method(source, SourcePolicy())

    monkeypatch.setattr(
        adaptive,
        "DEFAULT_STRATEGIES",
        (AcquisitionStrategy("disabled", 1, enabled=False),),
    )
    with pytest.raises(RuntimeError):
        choose_strategy(False)


def test_router_free_gate_and_non_consuming_execute():
    from backend.execution.providers import ProviderCapability, ProviderRegistry
    from backend.execution.resources import ResourceBudget
    from backend.execution.router import ProviderRouter

    registry = ProviderRegistry()
    registry.register(ProviderCapability("paid", "x", free_eligible=False))
    router = ProviderRouter(registry, ResourceBudget(inference_calls=1))
    assert router.route("x").approved is False
    assert router.route("x", strict_zero_cost_only=False).approved is True
    assert router.execute("x", lambda: "ok", consume_inference=False, strict_zero_cost_only=False) == "ok"


def test_entailment_remaining_statuses():
    from backend.evaluation.entailment import EntailmentStatus, verify_claim_entailment
    from backend.intelligence.observations import EvidenceSpan, Observation

    obs = Observation.create("o", "https://e", "product is available now")
    assert verify_claim_entailment("product is available", obs, EvidenceSpan("o", 0, 24)).status == EntailmentStatus.SUPPORTED
    assert verify_claim_entailment("product available", obs, EvidenceSpan("o", 0, 24), supported_threshold=1.1).status == EntailmentStatus.AMBIGUOUS
    assert verify_claim_entailment("banana", obs, EvidenceSpan("o", 0, 24)).status == EntailmentStatus.UNSUPPORTED


def test_lineage_observation_and_http_edges():
    from datetime import datetime, timezone
    from backend.intelligence.lineage import SourceLineage, is_independent
    from backend.intelligence.observations import Observation
    import backend.sources.http as http

    assert is_independent(SourceLineage("a", "f"), SourceLineage("b", "f")) is False
    assert is_independent(SourceLineage("a", "f1"), SourceLineage("b", "f2")) is True
    now = datetime.now(timezone.utc)
    assert Observation.create("o", "sid", "https://e", "x", now).observed_at == now

    for url in ("ftp://example.com", "https://user:pass@example.com", "https://example.com:8443"):
        with pytest.raises(ValueError):
            http.validate_url(url)

    class Resp:
        status = 302
        headers = {"location": "https://example.com"}

        async def arrayBuffer(self):
            return b""

    async def redirect(_url, _opts):
        return Resp()

    with pytest.raises(RuntimeError, match="too many redirects"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=redirect))


def test_wikipedia_http_failure_and_result_filtering():
    import backend.sources.wikipedia as wikipedia

    class Resp:
        def __init__(self, status, payload):
            self.status = status
            self.payload = payload

        async def json(self):
            return self.payload

    async def bad_fetch(_url, _opts):
        return Resp(500, {})

    with pytest.raises(RuntimeError, match="HTTP 500"):
        asyncio.run(wikipedia._implementation("q", 2, fetcher=bad_fetch))

    async def good_fetch(_url, _opts):
        return Resp(
            200,
            {
                "query": {
                    "search": [
                        {"title": "A", "pageid": 1, "snippet": "a"},
                        {"title": "", "pageid": 2, "snippet": "skip"},
                        {"title": "B", "pageid": 0, "snippet": "skip"},
                    ]
                }
            },
        )

    results = asyncio.run(wikipedia._implementation("q", 50, fetcher=good_fetch))
    assert len(results) == 1 and results[0].title == "A"
