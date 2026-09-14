"""Multi-agent nightly research orchestration primitives."""

from .models import AgentResult, AgentSpec, ResearchProgram
from .orchestrator import MultiAgentCoordinator
from .programs import NIGHTLY_PROGRAMS, PROGRAMS_BY_LANE

__all__ = [
    "AgentResult",
    "AgentSpec",
    "ResearchProgram",
    "MultiAgentCoordinator",
    "NIGHTLY_PROGRAMS",
    "PROGRAMS_BY_LANE",
]
