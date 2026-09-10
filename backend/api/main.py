"""HTTP API application logic shared by local tests and the Python Worker."""

import json
import uuid
from typing import Any

from backend.api.models import ResearchRequest, APIResponse
from backend.health.check import check_health
from backend.intelligence.contracts import ResearchContract
from backend.execution.pipeline import start_run


def health_endpoint() -> dict[str, Any]:
    health = check_health()
    return {"ok": True, "status": health.status, "app": health.app,
            "version": health.version, "environment": health.environment}


def readiness_endpoint() -> dict[str, Any]:
    health = check_health()
    return {"ready": health.status == "ok", "version": health.version}


def submit_research(request: ResearchRequest) -> APIResponse:
    try:
        request.validate()
        if not request.strict_zero_cost_only:
            return APIResponse(ok=False, error="strict $0 cost mode is mandatory: strict_zero_cost_only must be true")
        contract = ResearchContract(
            question=request.question,
            depth=request.depth or "standard",
            require_citations=request.require_citations,
            max_sources=request.max_sources,
            max_evidence_items=request.max_evidence_items,
        )
        contract.validate()
        run = start_run(contract)
        return APIResponse(
            ok=True,
            run_id=str(uuid.uuid4()),
            metadata={
                "question": run.contract.question,
                "stages": len(run.plan_stages),
                "source_budget": run.plan.source_budget,
                "evidence_budget": run.plan.evidence_budget,
                "strict_zero_cost_only": True,
            },
        )
    except ValueError as e:
        return APIResponse(ok=False, error=str(e))
    except Exception as e:
        return APIResponse(ok=False, error=f"Internal error: {e}")


def api_response_to_json(response: APIResponse) -> str:
    data: dict[str, Any] = {"ok": response.ok}
    if response.error:
        data["error"] = response.error
    if response.run_id:
        data["run_id"] = response.run_id
    if response.metadata:
        data["metadata"] = response.metadata
    return json.dumps(data, default=str)
