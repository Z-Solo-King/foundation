"""Compatibility exports for the canonical research planner."""

from backend.intelligence.planning import create_plan
from backend.intelligence.contracts import ResearchPlan

__all__ = ["ResearchPlan", "create_plan"]
