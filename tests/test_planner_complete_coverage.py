from dataclasses import replace
from datetime import datetime, timezone
from math import nan

import pytest

from backend.evaluation.receipt import EvaluationReceipt
from backend.intelligence.adaptive_planning import (
    PlanContextFingerprint,
    ReplanTrigger,
    filter_permitted_methods,
    needs_replan,
)
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.observations import Observation
from backend.intelligence.pagination import PageObservation, PaginationState
from backend.intelligence.planner_engine import (
    apply_source_profiles,
    build_task_plan,
    choose_stop_reason,
    classify_task,
    coverage_map,
    decompose_claims,
    generate_query_portfolio,
    recovery_actions,
)
from backend.intelligence.planner_models import (
    Action,
    ClaimRequirement,
    Coverage,
    CoverageState,
    FactType,
    FailureClass,
    MethodCandidate,
    PaginationKind,
    ResourceEnvelope,
    SourceProfileHint,
    StopReason,
    TaskMode,
    as_sequence,
)
from backend.intelligence.planner_runtime import (
    BudgetLedger,
    _add,
    canonical_json,
    choose_stop,
    reserve,
    topological_order,
    validate_dag,
)
from backend.intelligence.replay import PlanContextFingerprint as ReplayContextFingerprint
from backend.intelligence.source_profiles import MethodObservation, SourceProfile, update_profile
from backend.intelligence.strategy_evaluation import StrategyExperiment, StrategyMetrics, candidate_beats_baseline
from backend.run_record import ResearchRunRecord
from backend.stage_receipt import StageReceipt
from backend.token_efficiency import TokenEfficiencyObservation, TokenEfficiencyGate, evaluate_token_efficiency


def test_replan_all_context_and_failure_triggers():
    base = PlanContextFingerprint("c1", "p1", "s1", "q1", "f1")
    current = PlanContextFingerprint("c2", "p2", "s2", "q2", "f2")
    coverages = tuple(Coverage(f"c{i}", state) for i, state in enumerate((CoverageState.CONTRADICTED, CoverageState.PARTIAL, CoverageState.STALE)))
    failures = tuple(FailureClass)
    decision = needs_replan(base, current, coverages, failures)
    assert decision.required
    assert set(decision.triggers) >= {
        ReplanTrigger.CAPABILITY_CHANGED, ReplanTrigger.POLICY_CHANGED,
        ReplanTrigger.SOURCE_DEGRADED, ReplanTrigger.QUOTA_CHANGED,
        ReplanTrigger.FRESHNESS_EXPIRED, ReplanTrigger.CONTRADICTION,
        ReplanTrigger.GAP, ReplanTrigger.METHOD_FAILED, ReplanTrigger.LOW_YIELD,
    }
    assert decision.preferred_actions


def test_planner_recovery_and_stop_matrix():
    claims = decompose_claims("price, stock and review quality", ("price", "stock"))
    coverages = coverage_map(claims, {
        "claim-1": Coverage("claim-1", CoverageState.UNSUPPORTED),
        "claim-2": Coverage("claim-2", CoverageState.STALE),
    })
    assert recovery_actions(coverages)
    assert choose_stop_reason((Coverage("c", CoverageState.SATISFIED),), 1) == StopReason.QUALITY_FLOOR
    assert choose_stop_reason((Coverage("c", CoverageState.UNSUPPORTED),), 0) == StopReason.BUDGET_EXHAUSTED
    assert choose_stop_reason((Coverage("c", CoverageState.UNSUPPORTED),), 0.01) == StopReason.LOW_INFORMATION_GAIN


def test_planner_engine_branches_and_profile_filtering():
    for text, expected in (
        ("specification ports", TaskMode.SPECIFICATION),
        ("price and stock", TaskMode.MIXED),
        ("community experience", TaskMode.COMMUNITY),
        ("official source", TaskMode.PRIMARY_SOURCE),
        ("same product match", TaskMode.ENTITY_RESOLUTION),
        ("pdf document", TaskMode.DOCUMENT),
        ("video transcript", TaskMode.MEDIA),
        ("csv dataframe", TaskMode.DATA),
        ("python repository bug", TaskMode.MIXED),
        ("simple fact", TaskMode.FACT),
    ):
        assert classify_task(text) == expected
    methods = (
        MethodCandidate("m1", "s1", "api", expected_success=.9),
        MethodCandidate("m2", "s2", "html"),
    )
    profile = SourceProfileHint("s1", supported_representations=("html",), health=.1, sample_size=10)
    assert apply_source_profiles(methods, {"s1": profile})
    assert generate_query_portfolio("thing", claims=(ClaimRequirement("c", "thing"),), languages=("en", "zh"), source_families=("official",))
    assert build_task_plan("thing", source_families=("official",), envelope=ResourceEnvelope(search_units=4))


def test_resource_runtime_edges():
    env = ResourceEnvelope(search_units=5, wall_seconds=20)
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert BudgetLedger.empty().reserved.search_units == 0
    added = _add(env, ResourceEnvelope(search_units=1))
    assert added.search_units == 6
    assert reserve(env, ResourceEnvelope(search_units=2)).search_units == 3
    with pytest.raises(ValueError):
        reserve(env, ResourceEnvelope(search_units=6))
    with pytest.raises(ValueError):
        validate_dag((Action("a", "x", "x", prerequisites=("missing",)),))
    validate_dag((Action("a", "x", "x"), Action("b", "x", "x", prerequisites=("a",))))
    assert topological_order((Action("a", "x", "x"), Action("b", "x", "x", prerequisites=("a",)))) == ("a", "b")


def test_pagination_all_terminal_states():
    state = PaginationState(PaginationKind.PAGE)
    states = [
        state.observe(items=1, fingerprint="a", cursor="c", expected_total=3),
        state.observe(items=1, fingerprint="a", cursor="c"),
        state.observe(items=0),
        state.observe(items=1, partial=True),
    ]
    assert states[0].observation == PageObservation.PROGRESSED
    assert states[1].observation == PageObservation.REPEATED
    assert states[2].observation == PageObservation.EMPTY
    assert states[3].observation == PageObservation.PARTIAL
    complete = PaginationState(PaginationKind.PAGE).observe(items=2, expected_total=2)
    assert complete.observation == PageObservation.COMPLETE
    assert complete.stop_reason(10) == StopReason.QUALITY_FLOOR
    assert states[2].stop_reason(0) == StopReason.LOW_INFORMATION_GAIN
    assert PaginationState(PaginationKind.PAGE, pages_seen=2).stop_reason(2, True) == StopReason.BUDGET_EXHAUSTED


def test_source_profiles_and_strategy_guards():
    profile = SourceProfile("s", "family", failure_by_class={"404": 1, "future": 2})
    hint = profile.hint()
    assert FailureClass.NOT_FOUND in hint.known_failures
    updated = update_profile(profile, MethodObservation("m", False, completeness=2, failure=FailureClass.PARSER))
    assert updated.sample_size == 1 and updated.failure_by_class[FailureClass.PARSER.value] == 1
    metrics = StrategyMetrics(.9, .9, .9, .9, .9, .1, .1, .1)
    exp = StrategyExperiment("e", "b", "c", "fp", metrics, metrics)
    assert candidate_beats_baseline(exp, {"correctness": .8})
    assert not candidate_beats_baseline(replace(exp, pre_registered=False))


def test_models_validation_edges():
    with pytest.raises(ValueError):
        ResourceEnvelope(recovery_reserve_ratio=1).validate()
    with pytest.raises(ValueError):
        ResourceEnvelope(concurrency=0).validate()
    with pytest.raises(ValueError):
        ResourceEnvelope(search_units=-1).validate()
    assert as_sequence(None) == ()
    assert as_sequence(("a",)) == ("a",)


def test_contract_negative_and_envelope_guards():
    with pytest.raises(ValueError):
        ResearchContract("").validate()
    for field in ("max_sources", "max_evidence_items", "max_search_actions", "max_browser_actions", "max_ai_actions", "max_wall_time"):
        with pytest.raises(ValueError):
            ResearchContract("q", **{field: -1}).validate()
    with pytest.raises(ValueError):
        ResearchContract("q", max_sources=0).validate()
    with pytest.raises(ValueError):
        ResearchContract("q", max_evidence_items=0).validate()
    with pytest.raises(ValueError):
        ResearchContract("q", freshness_requirement=-1).validate()
    with pytest.raises(ValueError):
        ResearchContract("q", max_search_actions=5, resource_envelope=ResourceEnvelope(search_units=2)).validate()
    with pytest.raises(ValueError):
        ResearchContract("q", max_wall_time=50, resource_envelope=ResourceEnvelope(search_units=12, wall_seconds=20)).validate()


def test_evaluation_receipt_nonfinite_metric():
    receipt = EvaluationReceipt(
        receipt_id="r", benchmark_id="b", benchmark_fingerprint="f", case_count=1,
        benchmark_count=1, metrics=(("x", 1.0),), model_id="m", strategy_id="s"
    )
    assert receipt.fingerprint()
    with pytest.raises(ValueError):
        EvaluationReceipt(
            receipt_id="r2", benchmark_id="b", benchmark_fingerprint="f", case_count=1,
            benchmark_count=1, metrics=(("x", nan),), model_id="m", strategy_id="s"
        ).validate()


def test_observation_enriched_kwargs_and_validation():
    obs = Observation("o", "https://x", "text", content_sha256=None, quality=1.0, provenance={"a": 1}, title="t")
    assert obs.title == "t"
    with pytest.raises(TypeError):
        Observation("o", "https://x", "text", unexpected=True)
    with pytest.raises(ValueError):
        Observation("o", "https://x", "text", quality=2).validate()


def test_stage_and_token_edge_paths():
    with pytest.raises(ValueError):
        StageReceipt("id", "req", "run", "method", "provider", "", 0).validate()
    with pytest.raises(ValueError):
        StageReceipt("id", "req", "run", "method", "provider", "ok", -1).validate()
    baseline = TokenEfficiencyObservation(10, 20)
    candidate = TokenEfficiencyObservation(10, 20)
    gate = TokenEfficiencyGate(max_input_token_growth_ratio=0, max_total_token_growth_ratio=0)
    assert evaluate_token_efficiency(baseline, candidate, gate)[0]
