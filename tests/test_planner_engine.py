from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planner_engine import (
    apply_field_preferences,
    build_task_plan,
    classify_task,
    generate_query_portfolio,
    method_utility,
    recovery_actions,
)
from backend.intelligence.planner_models import (
    Coverage,
    CoverageState,
    FailureClass,
    FieldRequirement,
    MethodCandidate,
    ResourceEnvelope,
    TaskMode,
)
from backend.intelligence.planner_runtime import plan_fingerprint, topological_order, validate_dag
from backend.intelligence.route_memory import RouteKey, RouteState


def test_classifies_common_modes():
    assert classify_task("compare two monitors") == TaskMode.COMPARISON
    assert classify_task("what is the current price") == TaskMode.PRICE_AVAILABILITY
    assert classify_task("check official specifications") == TaskMode.SPECIFICATION


def test_query_portfolio_is_bounded_and_diverse():
    queries = generate_query_portfolio(
        "Widget X specs",
        (),
        languages=("en", "zh"),
        source_families=("example.com",),
        max_queries=8,
    )
    assert len(queries) <= 8
    purposes = {q.purpose for q in queries}
    assert "exact" in purposes
    assert "primary-source" in purposes


def test_method_utility_rewards_quality_and_penalizes_risk():
    good = MethodCandidate("good", "s", "structured", expected_success=.9, expected_completeness=.9,
                           evidence_directness=.9, authority=.9, resource_cost=.5)
    bad = MethodCandidate("bad", "s", "browser", expected_success=.5, expected_completeness=.4,
                          evidence_directness=.4, authority=.5, resource_cost=5, risk_penalty=2)
    assert method_utility(good) > method_utility(bad)


def test_field_preferences_change_method_order():
    api = MethodCandidate("api", "s", "api", expected_success=.8, evidence_directness=.8)
    structured = MethodCandidate("structured", "s", "structured", expected_success=.8, evidence_directness=.8)
    fields = (FieldRequirement("refresh", "refresh_rate", preferred_representations=("structured",)),)
    ranked = apply_field_preferences((api, structured), fields)
    assert ranked[0].method_id == "structured"
    assert apply_field_preferences((api, structured), ()) == (api, structured)


def test_planner_excludes_blocked_empirical_routes_and_keeps_unseen_routes():
    blocked = MethodCandidate("api", "source-a", "api", expected_success=.8)
    unseen = MethodCandidate("feed", "source-b", "feed", expected_success=.7)
    memory = {RouteKey("source-a", "api", "api"): RouteState(quarantined_until=500.0)}
    plan = build_task_plan(
        "facts",
        methods=(blocked, unseen),
        route_memory=memory,
        now=100.0,
        envelope=ResourceEnvelope(search_units=3, wall_seconds=20),
        max_queries=3,
    )
    assert tuple(method.method_id for method in plan.methods) == ("feed",)


def test_recovery_targets_gap_type():
    actions = recovery_actions((
        Coverage("c1", CoverageState.CONTRADICTED),
        Coverage("c2", CoverageState.STALE),
        Coverage("c3", CoverageState.BLOCKED),
    ))
    purposes = {a.purpose for a in actions}
    assert any("independent" in p for p in purposes)
    assert any("freshness" in p for p in purposes)
    assert any("alternate" in p for p in purposes)


def test_plan_fingerprint_is_stable():
    plan = build_task_plan(
        "compare widgets",
        output_type="comparison",
        claims=("price", "weight"),
        languages=("en",),
        source_families=("official",),
        envelope=ResourceEnvelope(search_units=5, wall_seconds=30),
        max_queries=5,
    )
    assert plan_fingerprint(plan) == plan_fingerprint(plan)


def test_dag_rejects_cycles_and_orders_dependencies():
    plan = build_task_plan("facts", envelope=ResourceEnvelope(search_units=3, wall_seconds=20), max_queries=3)
    validate_dag(plan.actions)
    assert len(topological_order(plan.actions)) == len(plan.actions)


def test_contract_extended_fields_validate():
    contract = ResearchContract(question="latest specs", max_search_actions=12)
    contract.validate()
    assert contract.zero_cost_required is True


def test_failure_enum_covers_transport_recovery_classes():
    assert FailureClass.RATE_LIMITED.value == "429"
    assert FailureClass.ENCODING.value == "encoding_error"