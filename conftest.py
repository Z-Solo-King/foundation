"""Pytest configuration and fixtures.

This ensures test isolation and enforces $0 cost constraints during testing.
"""

import pytest
from backend.execution.resources import ResourceBudget
from backend.intelligence.contracts import ResearchContract


@pytest.fixture
def test_resource_budget():
    """Bounded resource budget for tests."""
    return ResourceBudget(requests=5, evidence_items=10, inference_calls=2)


@pytest.fixture
def test_contract():
    """Standard test research contract."""
    return ResearchContract(question="test question")
