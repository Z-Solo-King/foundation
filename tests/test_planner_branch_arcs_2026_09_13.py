from backend.intelligence.planner_engine import apply_field_preferences, apply_source_profiles
from backend.intelligence.planner_models import FieldRequirement, MethodCandidate, SourceProfileHint


def test_source_profile_empty_and_singleton_control_flow():
    assert apply_source_profiles((), {}) == ()
    method = MethodCandidate("m", "s", "api")
    assert apply_source_profiles((method,), {}) == (method,)
    assert apply_source_profiles((method,), {"s": SourceProfileHint("s", supported_representations=("api",), sample_size=5)})
    assert apply_source_profiles((method,), {"s": SourceProfileHint("s", supported_representations=("html",), sample_size=5)}) == ()


def test_field_preference_empty_and_nonpreferred_control_flow():
    method = MethodCandidate("m", "s", "api")
    assert apply_field_preferences((), ()) == ()
    assert apply_field_preferences((method,), ()) == (method,)
    assert apply_field_preferences((method,), (FieldRequirement("f", "title", preferred_representations=("html",)),)) == (method,)
    preferred = MethodCandidate("p", "s", "html")
    ranked = apply_field_preferences((method, preferred), (FieldRequirement("f", "title", preferred_representations=("html",)),))
    assert ranked[0].method_id == "p"
