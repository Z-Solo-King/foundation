import pytest
from types import SimpleNamespace


def test_api_models_capabilities_and_serialization(monkeypatch):
    from backend.api.main import api_response_to_json, submit_research
    from backend.api.models import APIResponse, ResearchRequest
    from backend.capabilities.model import Capability
    from backend.capabilities.registry import CapabilityRegistry
    assert Capability("x").remaining_today is None and Capability("x").usable() is True
    assert Capability("x", enabled=False).usable() is False
    assert Capability("x", daily_limit=2, used_today=3).remaining_today == 0
    assert Capability("x", free_eligible=False).usable() is False
    with pytest.raises(ValueError): ResearchRequest("").validate()
    with pytest.raises(ValueError): ResearchRequest("q", max_sources=0).validate()
    with pytest.raises(ValueError): ResearchRequest("q", max_evidence_items=0).validate()
    with pytest.raises(ValueError): ResearchRequest("q", strict_zero_cost_only=False).validate()
    with pytest.raises(ValueError): ResearchRequest("q", max_sources=1, source_urls=("a","b")).validate()
    reg=CapabilityRegistry(); reg.register(Capability("a")); assert reg.get("a") and reg.usable("a") and reg.usable("missing") is False
    assert len(reg.all()) == 1 and reg.snapshot() == (reg.get("a"),)
    assert api_response_to_json(APIResponse(False,error="bad")) == '{"ok": false, "error": "bad"}'
    assert "run_id" in api_response_to_json(APIResponse(True,run_id="r",metadata={"x":1}))
    assert submit_research(ResearchRequest("q",strict_zero_cost_only=False)).ok is False
    class Broken:
        def validate(self): raise ValueError("bad")
    assert submit_research(Broken()).ok is False
    from backend.api import main as api_main
    monkeypatch.setattr(api_main,"start_run",lambda contract: (_ for _ in ()).throw(RuntimeError("boom")))
    assert "Internal error" in submit_research(ResearchRequest("q")).error


def test_api_success_and_engine_lifecycle():
    from backend.api.main import submit_research
    from backend.api.models import ResearchRequest
    from backend.execution.engine import create_run, complete_research, transition_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    response=submit_research(ResearchRequest("q")); assert response.ok is True and response.run_id
    assert submit_research(SimpleNamespace(strict_zero_cost_only=False,validate=lambda:None)).ok is False
    run=create_run("r",ResearchContract("q"),ResearchPlan("q",("a",),1,1)); running=transition_research(run,"running")
    assert running.status=="running" and complete_research(running).status=="completed" and complete_research(running,success=False).status=="failed"


def test_api_request_boundary_does_not_claim_private_runtime():
    from backend.api.models import ResearchRequest
    request=ResearchRequest("q")
    assert request.strict_zero_cost_only is True
