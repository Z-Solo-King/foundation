from backend.intelligence.planner_engine import apply_source_profiles
from backend.intelligence.planner_models import FailureClass, MethodCandidate, SourceProfileHint, coerce_failure_class
from backend.intelligence.source_profiles import SourceProfile


def test_failure_class_coercion_matrix():
    assert coerce_failure_class(None) is None
    assert coerce_failure_class(FailureClass.RATE_LIMITED) is FailureClass.RATE_LIMITED
    assert coerce_failure_class("429") is FailureClass.RATE_LIMITED
    assert coerce_failure_class("rate_limit") is FailureClass.RATE_LIMIT
    assert coerce_failure_class("future") is FailureClass.FRESHNESS
    assert coerce_failure_class("unknown_failure") is None


def test_source_profile_hint_normalizes_duplicates_and_unknowns():
    profile = SourceProfile(
        "s",
        "family",
        failure_by_class={"429": 2, "rate_limit": 1, "future": 1, "unknown_failure": 3},
    )
    hint = profile.hint()
    assert hint.known_failures == (FailureClass.RATE_LIMITED, FailureClass.RATE_LIMIT, FailureClass.FRESHNESS)


def test_apply_source_profiles_covers_supported_match_and_unbounded_representation():
    methods = (
        MethodCandidate("m-empty", "empty", "api"),
        MethodCandidate("m-match", "match", "api", expected_success=.7),
        MethodCandidate("m-sampled", "sampled", "api", expected_success=.7),
    )
    profiles = {
        "empty": SourceProfileHint("empty", supported_representations=(), health=.8, sample_size=10),
        "match": SourceProfileHint("match", supported_representations=("api",), health=.8, sample_size=10),
        "sampled": SourceProfileHint("sampled", supported_representations=("api",), health=.8, sample_size=5),
    }
    ranked = apply_source_profiles(methods, profiles)
    assert {item.method_id for item in ranked} == {"m-empty", "m-match", "m-sampled"}
