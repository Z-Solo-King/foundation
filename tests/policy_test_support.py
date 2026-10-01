"""Synthetic Operations policy binding for public-worker tests."""
from __future__ import annotations


class _Response:
    status = 200

    async def json(self):
        return {
            "ok": True,
            "schema": "protected-policy-envelope/v1",
            "policy_digest": "synthetic-test-digest",
            "admission": {
                "version": "public-admission/v1",
                "window_seconds": 60,
                "max_requests_per_subject": 7,
                "max_requests_global": 70,
                "max_concurrent_per_subject": 4,
                "max_concurrent_global": 8,
                "retry_after_seconds": 3,
                "protected_routes": ["chat", "research", "stream"],
            },
            "research_planning": {
                "base_source_families": ["web_search", "retailers", "oem"],
                "category_required_source_families": {},
                "keyword_groups": {},
                "quick_stages": ["define_question", "discover_sources", "collect_observations", "verify_evidence", "synthesize_answer"],
                "standard_stages": ["define_question", "assess_constraints", "discover_sources", "collect_observations", "map_evidence", "verify_evidence", "check_independence", "synthesize_answer"],
            },
        }


class FakePolicyBinding:
    async def fetch(self, request):
        return _Response()


def policy_binding():
    return FakePolicyBinding()
