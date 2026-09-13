from .contracts import ResearchContract, ResearchPlan
from .planner_engine import create_task_plan
from .planner_runtime import explain_plan, plan_fingerprint, topological_order, validate_dag

DEFAULT_STAGES = (
    "define_question",
    "assess_constraints",
    "discover_sources",
    "collect_observations",
    "map_evidence",
    "verify_evidence",
    "check_independence",
    "synthesize_answer",
)


def create_plan(contract: ResearchContract) -> ResearchPlan:
    """Compatibility DTO plus canonical task plan metadata.

    Existing callers keep receiving ResearchPlan while richer callers can use
    planner_engine.create_task_plan() to obtain the typed execution plan.
    """
    task = create_task_plan(contract)
    stages = DEFAULT_STAGES
    if contract.depth == "quick":
        stages = (
            "define_question",
            "discover_sources",
            "collect_observations",
            "verify_evidence",
            "synthesize_answer",
        )
    validate_dag(task.actions)
    return ResearchPlan(
        question=contract.question,
        stages=stages,
        source_budget=contract.max_sources,
        evidence_budget=contract.max_evidence_items,
        metadata={
            "depth": contract.depth,
            "require_citations": str(contract.require_citations).lower(),
            "task_mode": task.task_mode.value,
            "plan_fingerprint": plan_fingerprint(task),
            "plan_explain": explain_plan(task),
            "query_count": str(len(task.queries)),
        },
    )


__all__ = [
    "DEFAULT_STAGES",
    "create_plan",
    "create_task_plan",
    "explain_plan",
    "plan_fingerprint",
    "topological_order",
    "validate_dag",
]
