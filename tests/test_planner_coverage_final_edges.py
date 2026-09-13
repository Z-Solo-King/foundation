from dataclasses import replace
from math import inf

import pytest

from backend.evaluation.receipt import EvaluationReceipt
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.field_routing import FieldRequirement, PaginationPlan, Representation, RepresentationRoute, choose_routes
from backend.intelligence.observations import Observation
from backend.intelligence.pagination import PaginationKind, PaginationState
from backend.intelligence.planner_engine import build_task_plan, classify_task, decompose_claims, generate_query_portfolio, infer_fact_type
from backend.intelligence.planner_models import ClaimRequirement, FactType, ResourceEnvelope, StopReason, TaskMode
from backend.intelligence.planner_runtime import choose_stop, explain_plan, plan_fingerprint, reserve
from backend.intelligence.strategy_evaluation import StrategyExperiment, StrategyMetrics, candidate_beats_baseline
from backend.stage_receipt import StageReceipt
from backend.token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency


def test_remaining_contract_validation_and_empty_optional_paths():
    with pytest.raises(ValueError): ResearchContract("q", max_sources=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_evidence_items=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_search_actions=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_browser_actions=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_ai_actions=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_wall_time=-1).validate()
    with pytest.raises(ValueError): ResearchContract("q", field_requirements=(FieldRequirement("", "x"),)).validate()
    with pytest.raises(ValueError): ResearchContract("q", field_requirements=(FieldRequirement("x", ""),)).validate()
    with pytest.raises(ValueError): ResearchContract("q", field_requirements=(FieldRequirement("x", "x"), FieldRequirement("x", "x2"))).validate()
    assert ResearchContract("q", max_wall_time=0, resource_envelope=ResourceEnvelope(search_units=12)).validate() is None


def test_remaining_planner_branches_and_query_budget():
    assert classify_task("spec") == TaskMode.SPECIFICATION
    assert infer_fact_type("plain") == FactType.IDENTITY
    assert infer_fact_type("spec size weight") == FactType.SPECIFICATION
    claims = decompose_claims("tiny")
    assert claims and claims[0].text == "tiny"
    assert generate_query_portfolio("", claims=(), max_queries=0) == ()
    assert generate_query_portfolio("thing", claims=(ClaimRequirement("c", "thing"),), max_queries=1)[0].purpose == "exact"
    plan = build_task_plan("thing", envelope=ResourceEnvelope(search_units=1), max_queries=1)
    assert plan_fingerprint(plan) == plan_fingerprint(plan)
    assert explain_plan(plan).startswith("mode=")


def test_remaining_field_route_and_pagination_boundaries():
    fields = (FieldRequirement("title", "title", required=False),)
    routes = (
        RepresentationRoute(Representation.API, ("price",), .5, .5, 1),
        RepresentationRoute(Representation.HTML, ("title",), .9, .9, 1),
    )
    chosen = choose_routes(fields, routes)
    assert chosen[0].representation == Representation.HTML
    assert PaginationPlan(PaginationKind.PAGE, expected_total=0, page_size=0, max_pages=0).bounded().max_pages == 1
    state = PaginationState(PaginationKind.PAGE, pages_seen=1, expected_total=1).observe(items=0)
    assert state.stop_reason(10) is None


def test_remaining_observation_fingerprint_optional_timestamps_and_invalid_json():
    obs = Observation("o", "https://x", "payload", __import__("datetime").datetime.now(__import__("datetime").timezone.utc))
    assert obs.fingerprint()
    full = Observation(
        "o2", source_url="https://x", content="payload", observed_at=obs.observed_at, source_id="s", source_family_id="f", document_version_id="d",
        retrieved_at=obs.observed_at, published_at=obs.observed_at, author="a", language="en", title="t",
        extraction_method="e", acquisition_method="a", raw_artifact_ref="r", normalized_sha256="n",
        policy_state="allowed", extractor_version="1",
    )
    assert full.fingerprint()
    with pytest.raises(ValueError): replace(full, author=123).validate()
    with pytest.raises(ValueError): replace(full, content_sha256="0" * 64).validate()


def test_remaining_evaluation_receipt_metric_guards():
    base = dict(receipt_id="r", candidate_fingerprint="c", baseline_fingerprint="b", corpus_fingerprint="f", oracle_fingerprint="o", suite_version="1", benchmark_count=1, metrics=(("x", 1.0),), passed=True, created_at="t", evaluator_version="e", artifact_hash="a")
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), metrics=(("x", 1.0), ("x", .5))).validate()
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), metrics=(("", 1.0),)).validate()
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), metrics=(("x", inf),)).validate()
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), benchmark_count=0).validate()


def test_remaining_runtime_stop_and_resource_paths():
    plan = build_task_plan("thing", envelope=ResourceEnvelope(search_units=1), max_queries=1)
    assert choose_stop(plan, 1, False, contradiction_open=True) is None
    assert choose_stop(plan, 0, False, contradiction_open=True) == StopReason.BUDGET_EXHAUSTED
    with pytest.raises(ValueError): reserve(ResourceEnvelope(search_units=1), ResourceEnvelope(search_units=-1))


def test_remaining_strategy_and_public_receipt_guards():
    metrics = StrategyMetrics(.9, .9, .9, .9, .9, .1, .1, .1)
    exp = StrategyExperiment("e", "b", "c", "fp", metrics, metrics)
    assert not candidate_beats_baseline(exp, {"correctness": .95})
    StageReceipt("id", "req", "run", "method", "provider", "hash")
    obs = TokenEfficiencyObservation(10, 5, 2, 1, 100, 20, 2, accepted=True)
    with pytest.raises(ValueError): replace(obs, estimated_input_tokens=-1).validate()
    assert compare_efficiency(obs, obs, gate=EfficiencyGate())[0]
