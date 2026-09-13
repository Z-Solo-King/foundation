from dataclasses import replace
from math import inf

import pytest

from backend.evaluation.receipt import EvaluationReceipt
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.field_routing import FieldRequirement, PaginationPlan, Representation, RepresentationRoute, choose_routes
from backend.intelligence.observations import Observation
from backend.intelligence.pagination import PaginationKind, PaginationState
from backend.intelligence.planner_engine import apply_source_profiles, build_task_plan, classify_task, create_task_plan, decompose_claims, generate_query_portfolio, infer_fact_type, recovery_actions
from backend.intelligence.planner_evaluation import PlannerMetrics, candidate_improves
from backend.intelligence.planner_models import Action, ClaimRequirement, Coverage, CoverageState, FactType, MethodCandidate, ResourceEnvelope, SourceProfileHint, StopReason, TaskMode
from backend.intelligence.planner_runtime import choose_stop, explain_plan, plan_fingerprint, reserve, topological_order
from backend.intelligence.source_profiles import SourceProfile
from backend.intelligence.strategy_evaluation import StrategyExperiment, StrategyMetrics, candidate_beats_baseline
from backend.run_record import ChatbotRunRecord, ResourceUsage, RunResult
from backend.stage_receipt import StageReceipt, fingerprint
from backend.token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency


def _run_record(request_fingerprint="req", stage_request_fingerprint="req"):
    receipt = StageReceipt(stage_request_fingerprint, "plan", fingerprint("in"), fingerprint("out"), "method", "provider")
    return ChatbotRunRecord(
        "1", "run", "2026-09-13T00:00:00Z", request_fingerprint, {}, "method", "reason", (receipt,),
        RunResult("success"), {"version": "test"}, ResourceUsage(),
    )


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
    assert ResearchContract("q", max_search_actions=1, resource_envelope=ResourceEnvelope(search_units=1, recovery_reserve_ratio=0)).validate() is None


def test_remaining_planner_branches_and_query_budget():
    assert classify_task("spec") == TaskMode.SPECIFICATION
    assert classify_task("latest") == TaskMode.TEMPORAL
    assert classify_task("compare vs buy") == TaskMode.MIXED
    assert infer_fact_type("plain") == FactType.IDENTITY
    assert infer_fact_type("spec size weight") == FactType.SPECIFICATION
    assert infer_fact_type("price") == FactType.COMMERCIAL
    assert infer_fact_type("available") == FactType.AVAILABILITY
    assert infer_fact_type("historical") == FactType.TEMPORAL
    assert infer_fact_type("compatible") == FactType.RELATIONAL
    assert infer_fact_type("quality") == FactType.QUALITATIVE
    assert infer_fact_type("policy") == FactType.NORMATIVE
    assert infer_fact_type("model") == FactType.IDENTITY
    claims = decompose_claims("tiny")
    assert claims and claims[0].text == "tiny"
    assert decompose_claims("one and two", required=("", "  "))[0].text == "one and two"
    assert generate_query_portfolio("", claims=(), max_queries=0) == ()
    assert generate_query_portfolio("thing", claims=(ClaimRequirement("c", "thing"),), max_queries=1)[0].purpose == "exact"
    assert generate_query_portfolio("thing", claims=(), languages=("en", "english", "hi"), source_families=("official",), max_queries=12)
    assert len(generate_query_portfolio("thing", claims=(ClaimRequirement("c1", "thing"), ClaimRequirement("c2", "thing")), max_queries=2)) == 2
    plan = build_task_plan("thing", envelope=ResourceEnvelope(search_units=1), max_queries=1, source_families=("official", "community"))
    assert plan_fingerprint(plan) == plan_fingerprint(plan)
    assert explain_plan(plan).startswith("mode=")
    contract_plan = create_task_plan(ResearchContract("thing", max_search_actions=2, resource_envelope=ResourceEnvelope(search_units=2)))
    assert contract_plan.envelope.search_units == 2
    assert recovery_actions((Coverage("b", CoverageState.BLOCKED), Coverage("i", CoverageState.INACCESSIBLE)))


def test_remaining_source_profile_paths():
    methods = (
        MethodCandidate("missing", "missing", "api"),
        MethodCandidate("unsupported", "s1", "api"),
        MethodCandidate("sampled", "s2", "html", expected_success=.8),
        MethodCandidate("well_sampled", "s3", "html", expected_success=.8),
    )
    profiles = {
        "s1": SourceProfileHint("s1", supported_representations=("html",), health=.8, sample_size=10),
        "s2": SourceProfileHint("s2", health=.2, sample_size=2),
        "s3": SourceProfileHint("s3", health=.8, sample_size=10),
    }
    ranked = apply_source_profiles(methods, profiles)
    assert ranked and {m.method_id for m in ranked} == {"missing", "sampled", "well_sampled"}
    assert SourceProfile("s", "family", sample_size=0).hint().sample_size == 0


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


def test_remaining_observation_and_certificate_guards():
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
    with pytest.raises(ValueError): replace(full, title="x" * 4097).validate()
    with pytest.raises(ValueError): replace(full, content_sha256="0" * 64).validate()
    with pytest.raises(ValueError): replace(full, observation_id="").validate()
    with pytest.raises(ValueError): replace(full, source_url="x" * 4097).validate()
    with pytest.raises(ValueError): replace(full, content="x" * 2_000_001).validate()


def test_remaining_evaluation_receipt_and_planner_evaluation_guards():
    base = dict(receipt_id="r", candidate_fingerprint="c", baseline_fingerprint="b", corpus_fingerprint="f", oracle_fingerprint="o", suite_version="1", benchmark_count=1, metrics=(("x", 1.0),), passed=True, created_at="t", evaluator_version="e", artifact_hash="a")
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), metrics=(("x", 1.0), ("x", .5))).validate()
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), metrics=(("", 1.0),)).validate()
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), metrics=(("x", inf),)).validate()
    with pytest.raises(ValueError): replace(EvaluationReceipt(**base), benchmark_count=0).validate()
    base_metrics = PlannerMetrics(task_coverage=.8, claim_coverage=.8, retrieval_recall=.8, citation_entailment=.8, primary_source_coverage=.8, independent_origin_coverage=.8, contradiction_recall=.8, freshness=.8, research_regret=.2, evidence_gain_per_unit=.5, latency=1, resource_consumption=1)
    assert not candidate_improves(base_metrics, base_metrics, {"task_coverage": .7})
    worse = replace(base_metrics, research_regret=.3)
    assert not candidate_improves(base_metrics, worse, {"task_coverage": .7})
    faster = replace(base_metrics, latency=.5)
    assert candidate_improves(base_metrics, faster, {"task_coverage": .7})


def test_remaining_runtime_stop_and_resource_paths():
    plan = build_task_plan("thing", envelope=ResourceEnvelope(search_units=1), max_queries=1)
    assert choose_stop(plan, 1, False, contradiction_open=True) is None
    assert choose_stop(plan, 0, False, contradiction_open=True) == StopReason.BUDGET_EXHAUSTED
    with pytest.raises(ValueError): reserve(ResourceEnvelope(search_units=1), ResourceEnvelope(search_units=-1))
    import backend.intelligence.planner_runtime as runtime
    original = runtime.validate_dag
    try:
        runtime.validate_dag = lambda actions: None
        cyclic = (Action("a", "x", "x", prerequisites=("b",)), Action("b", "x", "x", prerequisites=("a",)))
        with pytest.raises(ValueError): topological_order(cyclic)
    finally:
        runtime.validate_dag = original


def test_remaining_stage_token_run_and_strategy_guards():
    metrics = StrategyMetrics(.9, .9, .9, .9, .9, .1, .1, .1)
    exp = StrategyExperiment("e", "b", "c", "fp", metrics, metrics)
    assert not candidate_beats_baseline(exp, {"correctness": .95})
    with pytest.raises(ValueError): StageReceipt("id", "req", "run", "method", "provider", "hash", parent_receipt_fingerprint=" ")
    with pytest.raises(ValueError): StageReceipt("id", "req", "run", "method", "provider", "hash", attempt=0)
    StageReceipt("id", "req", "run", "method", "provider", "hash")
    obs = TokenEfficiencyObservation(10, 5, 2, 1, 100, 20, 2, accepted=True)
    with pytest.raises(ValueError): replace(obs, estimated_input_tokens=-1).validate()
    bad = replace(obs, estimated_input_tokens=inf, estimated_output_tokens=inf)
    assert not compare_efficiency(obs, bad, gate=EfficiencyGate())[0]
    assert compare_efficiency(obs, obs, gate=EfficiencyGate())[0]
    assert _run_record().validate() is None
    with pytest.raises(ValueError): _run_record(stage_request_fingerprint="other").validate()
    with pytest.raises(ValueError): ResourceEnvelope(recovery_reserve_ratio=.5, search_units=1, concurrency=0).validate()
