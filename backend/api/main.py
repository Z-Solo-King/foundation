"""Production HTTP API entry point.

This module provides the thin Worker control plane for research submission,
health/readiness checks, and run lifecycle management.

No business logic resides here; all decisions delegate to backend.intelligence
and backend.execution layers. Contract validation is fail-closed.
"""

import json
from typing import Any

from backend.api.models import ResearchRequest, APIResponse
from backend.health.check import check_health
from backend.intelligence.contracts import ResearchContract
from backend.execution.pipeline import start_run


def health_endpoint() -> dict[str, Any]:
    """GET /health — System readiness."""
    health = check_health()
    return {
        "ok": True,
        "status": health.status,
        "app": health.app,
        "version": health.version,
        "environment": health.environment,
    }


def readiness_endpoint() -> dict[str, Any]:
    """GET /readiness — Ready to accept research contracts."""
    health = check_health()
    return {
        "ready": health.status == "ok",
        "version": health.version,
    }


def submit_research(request: ResearchRequest) -> APIResponse:
    """POST /api/v1/research — Submit a research contract.
    
    Args:
        request: ResearchRequest with question, depth, constraints
        
    Returns:
        APIResponse with run_id or error details
        
    Raises:
        ValueError: If contract validation fails (fail-closed)
    """
    try:
        # Validate and construct contract
        contract = ResearchContract(
            question=request.question,
            depth=request.depth or "standard",
            require_citations=request.require_citations,
            max_sources=request.max_sources,
            max_evidence_items=request.max_evidence_items,
        )
        contract.validate()
        
        # Strict $0 cost validation
        if not request.strict_zero_cost_only:
            return APIResponse(
                ok=False,
                error="strict_zero_cost_only must be true; engine operates at $0/month",
            )
        
        # Create run with hard resource envelope
        run = start_run(contract)
        
        return APIResponse(
            ok=True,
            run_id=run.contract.question[:16].replace(" ", "_"),
            metadata={
                "stages": len(run.plan_stages),
                "source_budget": run.plan.source_budget,
                "evidence_budget": run.plan.evidence_budget,
            },
        )
    except ValueError as e:
        return APIResponse(ok=False, error=str(e))
    except Exception as e:
        return APIResponse(ok=False, error=f"Internal error: {str(e)}")


def api_response_to_json(response: APIResponse) -> str:
    """Convert APIResponse to JSON."""
    data = {
        "ok": response.ok,
    }
    if response.error:
        data["error"] = response.error
    if response.run_id:
        data["run_id"] = response.run_id
    if response.metadata:
        data["metadata"] = response.metadata
    return json.dumps(data, default=str)
