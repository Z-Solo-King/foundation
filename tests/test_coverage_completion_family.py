import asyncio
import hashlib
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


def test_resource_budget_all_paths():
    from backend.execution.resources import ResourceBudget, ResourceError
    budget = ResourceBudget(requests=2, evidence_items=2, ai_calls=3, inference_calls=2)
    assert budget.inference_remaining == 2
    assert budget.remaining()["inference_calls"] == 2
    budget.consume_requests(); budget.consume_evidence(); budget.consume_ai_calls(); budget.consume_inference()
    with pytest.raises(ValueError): ResourceBudget(inference_calls=-1)
    with pytest.raises(ValueError): budget.consume("requests", -1)
    with pytest.raises(ValueError): budget.consume("missing")
    budget.requests = None
    with pytest.raises(ValueError): budget.consume("requests")
    budget.requests = 0
    with pytest.raises(ResourceError): budget.consume_requests()
