"""Tests for HTTP API surface."""

import pytest
from backend.api.main import health_endpoint, readiness_endpoint, submit_research
from backend.api.models import ResearchRequest, APIResponse


def test_health_endpoint():
    """GET /health returns system status."""
    response = health_endpoint()
    assert response["ok"] is True
    assert response["status"] == "ok"
    assert response["app"] == "Research Intelligence Engine"
    assert response["version"] == "0.1.0"


def test_readiness_endpoint():
    """GET /readiness indicates research readiness."""
    response = readiness_endpoint()
    assert response["ready"] is True


def test_submit_research_valid_contract():
    """POST /api/v1/research accepts valid contract."""
    request = ResearchRequest(
        question="What is quantum computing?",
        depth="quick",
        max_sources=10,
        strict_zero_cost_only=True,
    )
    response = submit_research(request)
    assert response.ok is True
    assert response.run_id is not None
    assert response.error is None


def test_submit_research_empty_question():
    """POST /api/v1/research rejects empty question."""
    request = ResearchRequest(
        question="",
        strict_zero_cost_only=True,
    )
    response = submit_research(request)
    assert response.ok is False
    assert "question" in response.error.lower()


def test_submit_research_fails_closed_on_cost_flag():
    """POST /api/v1/research enforces strict_zero_cost_only."""
    request = ResearchRequest(
        question="test",
        strict_zero_cost_only=False,
    )
    response = submit_research(request)
    assert response.ok is False
    assert "$0" in response.error


def test_submit_research_negative_budget():
    """POST /api/v1/research rejects negative budgets."""
    request = ResearchRequest(
        question="test",
        max_sources=-1,
        strict_zero_cost_only=True,
    )
    response = submit_research(request)
    assert response.ok is False
    assert "positive" in response.error.lower()
