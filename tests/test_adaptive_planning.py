from backend.intelligence.adaptive_planning import PlanContextFingerprint, ReplanTrigger, needs_replan
from backend.intelligence.pagination import PageObservation, PaginationState
from backend.intelligence.planner_models import Coverage, CoverageState, FailureClass, PaginationKind


def test_replan_on_gap_and_policy_change():
    base = PlanContextFingerprint("1", "1", "1", "1", "1")
    current = PlanContextFingerprint("1", "2", "1", "1", "1")
    decision = needs_replan(base, current, [Coverage("c1", CoverageState.PARTIAL)])
    assert decision.required
    assert ReplanTrigger.POLICY_CHANGED in decision.triggers
    assert ReplanTrigger.GAP in decision.triggers
    assert "revalidate_route_eligibility" in decision.preferred_actions
    assert "generate_gap_queries" in decision.preferred_actions


def test_replan_on_blocking_failures():
    fp = PlanContextFingerprint("1", "1", "1", "1", "1")
    decision = needs_replan(fp, fp, failures=[FailureClass.RATE_LIMITED, FailureClass.PARSER])
    assert decision.required
    assert ReplanTrigger.METHOD_FAILED in decision.triggers
    assert ReplanTrigger.LOW_YIELD in decision.triggers


def test_pagination_repetition_stops():
    state = PaginationState(PaginationKind.PAGE, expected_total=10, pages_seen=1, items_seen=5,
                            page_fingerprints=("abc",))
    next_state = state.observe(items=5, fingerprint="abc")
    assert next_state.observation == PageObservation.REPEATED
    assert next_state.stop_reason(max_pages=10) is not None


def test_pagination_reaches_expected_total():
    state = PaginationState(PaginationKind.CURSOR, expected_total=10)
    next_state = state.observe(items=10, cursor="c1")
    assert next_state.observation == PageObservation.COMPLETE
