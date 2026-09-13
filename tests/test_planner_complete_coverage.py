from dataclasses import replace
from math import nan

import pytest

from backend.evaluation.receipt import EvaluationReceipt
from backend.intelligence.adaptive_planning import PlanContextFingerprint, ReplanTrigger, filter_permitted_methods, needs_replan
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
    normalize_fields,
    recovery_actions,
)
from backend.intelligence.planner_models import (
    Action,
    ClaimRequirement,
    Coverage,
    CoverageState,
    FailureClass,
    FieldRequirement,
    MethodCandidate,
    PaginationKind,
    ResourceEnvelope,
    SourceProfileHint,
    StopReason,
    TaskMode,
    as_sequence,
)
from backend.intelligence.planner_runtime import BudgetLedger, _add, canonical_json, choose_stop, operational_capacity, recovery_holdback, reserve, topological_order, validate_dag
from backend.intelligence.replay import make_replay_bundle, replay_compatible
from backend.intelligence.source_profiles import MethodObservation, SourceProfile, update_profile
from backend.intelligence.strategy_evaluation import StrategyExperiment, StrategyMetrics, candidate_beats_baseline
from backend.stage_receipt import StageReceipt
from backend.token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency


def test_adaptive_replan_matrix_and_method_filter():
    base = PlanContextFingerprint("c1", "p1", "s1", "q1", "f1")
    current = PlanContextFingerprint("c2", "p2", "s2", "q2", "f2")
    coverages = tuple(Coverage(f"c{i}", state) for i, state in enumerate((CoverageState.CONTRADICTED, CoverageState.PARTIAL, CoverageState.STALE)))
    decision = needs_replan(base, current, coverages, tuple(FailureClass))
    assert decision.required
    assert set(decision.triggers) >= {
        ReplanTrigger.CAPABILITY_CHANGED, ReplanTrigger.POLICY_CHANGED, ReplanTrigger.SOURCE_DEGRADED,
        ReplanTrigger.QUOTA_CHANGED, ReplanTrigger.FRESHNESS_EXPIRED, ReplanTrigger.CONTRADICTION,
        ReplanTrigger.GAP, ReplanTrigger.METHOD_FAILED, ReplanTrigger.LOW_YIELD,
    }
    assert decision.preferred_actions
    methods = (MethodCandidate("m1", "s1", "api"), MethodCandidate("m2", "s2", "html"))
    assert filter_permitted_methods(methods, ("m1",)) == (methods[1],)


def test_planner_generation_recovery_and_fields():
    claims = decompose_claims("price, stock and review quality", ("price", "stock"))
    fields = (FieldRequirement("price", "price", exact=True), FieldRequirement("stock", "stock", preferred_representations=("api",)))
    assert normalize_fields(fields) == fields
    with pytest.raises(ValueError):
        normalize_fields((FieldRequirement("", "price"),))
    with pytest.raises(ValueError):
        normalize_fields((FieldRequirement("x", "price"), FieldRequirement("x", "stock")))
    coverages = coverage_map(claims, {"claim-1": Coverage("claim-1", CoverageState.UNSUPPORTED), "claim-2": Coverage("claim-2", CoverageState.STALE)})
    assert recovery_actions(coverages)
    assert choose_stop_reason((Coverage("c", CoverageState.SATISFIED),), 1) == StopReason.QUALITY_FLOOR
    assert choose_stop_reason((Coverage("c", CoverageState.UNSUPPORTED),), 0) == StopReason.BUDGET_EXHAUSTED
    assert choose_stop_reason((Coverage("c", CoverageState.UNSUPPORTED),), 0.01) == StopReason.LOW_INFORMATION_GAIN


def test_planner_task_modes_queries_profiles_and_plan():
    for text, expected in (
        ("specification ports", TaskMode.SPECIFICATION),
        ("price and best", TaskMode.MIXED),
        ("community experience", TaskMode.COMMUNITY),
        ("official source", TaskMode.PRIMARY_SOURCE),
        ("same product match", TaskMode.ENTITY_RESOLUTION),
        ("pdf document", TaskMode.DOCUMENT),
        ("video transcript", TaskMode.MEDIA),
        ("csv spreadsheet", TaskMode.DATA),
        ("python repository bug", TaskMode.CODE),
        ("simple fact", TaskMode.FACT),
    ):
        assert classify_task(text) == expected
    methods = (MethodCandidate("m1", "s1", "api", expected_success=.9), MethodCandidate("m2", "s2", "html"))
    profiles = {"s1": SourceProfileHint("s1", supported_representations=("html",), health=.1, sample_size=10), "s2": SourceProfileHint("s2", health=.8, sample_size=10)}
    assert apply_source_profiles(methods, profiles)
    assert generate_query_portfolio("thing", claims=(ClaimRequirement("c", "thing"),), languages=("en", "zh"), source_families=("official",))
    plan = build_task_plan(
        "thing",
        fields=(FieldRequirement("price", "price"),),
        source_families=("official",),
        methods=methods,
        envelope=ResourceEnvelope(search_units=4),
    )
    assert plan.fields[0].field_id == "price"
    assert all("price" in action.field_ids for action in plan.actions)


def test_resource_runtime_and_dag_edges():
    env = ResourceEnvelope(search_units=5, wall_seconds=20)
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert BudgetLedger.empty().reserved.search_units == 0
    assert _add(env, ResourceEnvelope(search_units=1)).search_units == 6
    assert reserve(env, ResourceEnvelope(search_units=2)).search_units == 3
    assert recovery_holdback(env).search_units == 1
    assert operational_capacity(env).search_units == 4
    assert reserve(env, ResourceEnvelope(search_units=5), allow_recovery=True).search_units == 0
    with pytest.raises(ValueError): reserve(env, ResourceEnvelope(search_units=6))
    with pytest.raises(ValueError): reserve(env, ResourceEnvelope(search_units=5))
    with pytest.raises(ValueError): validate_dag((Action("a", "x", "x", prerequisites=("missing",)),))
    with pytest.raises(ValueError): validate_dag((Action("a", "x", "x"), Action("a", "x", "x")))
    with pytest.raises(ValueError): validate_dag((Action("a", "x", "x", prerequisites=("b",)), Action("b", "x", "x", prerequisites=("a",))))
    assert topological_order((Action("a", "x", "x"), Action("b", "x", "x", prerequisites=("a",)))) == ("a", "b")
    assert choose_stop(build_task_plan("thing"), 1, True) == StopReason.QUALITY_FLOOR
    assert choose_stop(build_task_plan("thing"), 0, False) == StopReason.BUDGET_EXHAUSTED


def test_pagination_terminal_states():
    state = PaginationState(PaginationKind.PAGE)
    progressed = state.observe(items=1, fingerprint="a", cursor="c", expected_total=4)
    repeated = progressed.observe(items=1, fingerprint="a", cursor="c")
    empty = repeated.observe(items=0)
    partial = empty.observe(items=1, partial=True)
    assert progressed.observation == PageObservation.PROGRESSED
    assert repeated.observation == PageObservation.REPEATED
    assert empty.observation == PageObservation.EMPTY
    assert partial.observation == PageObservation.PARTIAL
    complete = PaginationState(PaginationKind.PAGE).observe(items=2, expected_total=2)
    assert complete.observation == PageObservation.COMPLETE
    assert complete.stop_reason(10) == StopReason.QUALITY_FLOOR
    assert repeated.stop_reason(10) == StopReason.LOW_INFORMATION_GAIN
    assert PaginationState(PaginationKind.PAGE, pages_seen=2).stop_reason(2, True) == StopReason.BUDGET_EXHAUSTED


def test_profiles_strategy_contracts_and_replay():
    profile = SourceProfile("s", "family", failure_by_class={"404": 1, "future": 2})
    assert FailureClass.NOT_FOUND in profile.hint().known_failures
    updated = update_profile(profile, MethodObservation("m", False, completeness=2, failure=FailureClass.PARSER))
    assert updated.sample_size == 1 and updated.failure_by_class[FailureClass.PARSER.value] == 1
    metrics = StrategyMetrics(.9, .9, .9, .9, .9, .1, .1, .1)
    exp = StrategyExperiment("e", "b", "c", "fp", metrics, metrics)
    assert candidate_beats_baseline(exp, {"correctness": .8})
    assert not candidate_beats_baseline(replace(exp, pre_registered=False))
    contract = ResearchContract(question="Compare two models")
    plan = build_task_plan(contract.question, envelope=contract.resource_envelope)
    bundle = make_replay_bundle(contract, plan, capability_version="c1", policy_version="p1", source_profile_version="s1", planner_version="1", created_at="t")
    assert replay_compatible(bundle, capability_version="c1", policy_version="p1", source_profile_version="s1")
    assert not replay_compatible(bundle, capability_version="c2", policy_version="p1", source_profile_version="s1")


def test_model_and_contract_validation_edges():
    with pytest.raises(ValueError): ResourceEnvelope(recovery_reserve_ratio=1).validate()
    with pytest.raises(ValueError): ResourceEnvelope(concurrency=0).validate()
    with pytest.raises(ValueError): ResourceEnvelope(search_units=-1).validate()
    assert as_sequence(None) == ()
    assert as_sequence(("a",)) == ("a",)
    with pytest.raises(ValueError): ResearchContract("").validate()
    with pytest.raises(ValueError): ResearchContract("q", max_sources=0).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_evidence_items=0).validate()
    with pytest.raises(ValueError): ResearchContract("q", freshness_requirement=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_search_actions=5, resource_envelope=ResourceEnvelope(search_units=2)).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_wall_time=50, resource_envelope=ResourceEnvelope(search_units=12, wall_seconds=20)).validate()
    receipt = EvaluationReceipt(
        receipt_id="r",
        candidate_fingerprint="c",
        baseline_fingerprint="b",
        corpus_fingerprint="f",
        oracle_fingerprint="o",
        suite_version="1",
        benchmark_count=1,
        metrics=(("x", 1.0),),
        passed=True,
        created_at="t",
        evaluator_version="e",
        artifact_hash="a",
    )
    assert receipt.fingerprint()
    with pytest.raises(ValueError): replace(receipt, metrics=(("x", nan),)).validate()


def test_observation_stage_and_token_edges():
    obs = Observation("o", "https://x", "text", content_sha256=None, quality=1.0, provenance={"a": 1}, title="t")
    assert obs.title == "t"
    with pytest.raises(TypeError): Observation("o", "https://x", "text", unexpected=True)
    with pytest.raises(ValueError): replace(obs, quality=2).validate()
    with pytest.raises(ValueError): StageReceipt("id", "req", "run", "method", "provider", "", 0).validate()
    baseline = TokenEfficiencyObservation(10, 5, 2, 1, 100, 20, 2, accepted=True)
    candidate = TokenEfficiencyObservation(10, 5, 2, 1, 100, 20, 2, accepted=True)
    assert compare_efficiency(baseline, candidate, gate=EfficiencyGate())[0]
    bad = replace(candidate, estimated_input_tokens=120, estimated_output_tokens=50)
    assert not compare_efficiency(baseline, bad, gate=EfficiencyGate(max_input_token_growth_ratio=.1, max_total_token_growth_ratio=.1))[0]