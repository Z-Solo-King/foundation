from types import SimpleNamespace

import pytest

from backend.execution.synthesis import (
    SynthesisClaimProjection,
    SynthesisProjection,
    _projection_answer,
    build_synthesis_projection,
)
from backend.intelligence.verifier import ClaimStatus


def verified(claim_id, text, status, evidence_ids=()):
    result = SimpleNamespace(
        status=status,
        supporting_evidence=tuple(
            SimpleNamespace(observation_id=value) for value in evidence_ids
        ),
    )
    claim = SimpleNamespace(claim_id=claim_id, text=text)
    return claim, result


def test_build_projection_preserves_supported_and_corroborated_claims():
    projection = build_synthesis_projection(
        (
            verified("c1", "Supported fact.", ClaimStatus.SUPPORTED, ("obs-1",)),
            verified("c2", "Corroborated fact.", ClaimStatus.CORROBORATED, ("obs-2", "obs-3")),
        ),
        question="What is true?",
        required_claim_ids=("c1", "c2"),
    )
    projection.validate()
    assert [item.claim_id for item in projection.claims] == ["c1", "c2"]
    assert projection.gaps == ()
    assert "Supported fact." in _projection_answer(projection)
    assert "Corroborated fact." in _projection_answer(projection)


def test_partial_claim_is_qualified_and_gap_states_are_not_rendered_as_facts():
    projection = build_synthesis_projection(
        (
            verified("partial", "Partly supported.", ClaimStatus.PARTIAL, ("obs-1",)),
            verified("contradicted", "Conflicting fact.", ClaimStatus.CONTRADICTED, ("obs-2",)),
            verified("unknown", "Unknown fact.", ClaimStatus.UNKNOWN),
            verified("inaccessible", "Missing source.", ClaimStatus.INACCESSIBLE),
            verified("stale", "Old fact.", ClaimStatus.STALE, ("obs-3",)),
            verified("inferred", "Inference.", ClaimStatus.INFERRED),
        ),
        question="Explain the state.",
    )
    answer = _projection_answer(projection)
    assert "This claim is only partially supported" in answer
    assert "Partly supported." in answer
    assert "Unresolved aspects:" in answer
    assert "contradicted" in answer
    assert "unknown" in answer


def test_projection_answer_empty_is_explicitly_insufficient():
    projection = SynthesisProjection("Question?", ())
    assert _projection_answer(projection) == "Evidence is insufficient to answer this question."


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"claim_id": "", "text": "x", "status": ClaimStatus.SUPPORTED}, "identity"),
        ({"claim_id": "c", "text": "", "status": ClaimStatus.SUPPORTED}, "identity"),
        ({"claim_id": "c", "text": "x", "status": "made_up"}, "unsupported"),
        ({"claim_id": "c", "text": "x", "status": ClaimStatus.SUPPORTED}, "supported synthesis claims require evidence"),
        ({"claim_id": "c", "text": "x", "status": ClaimStatus.PARTIAL}, "partial synthesis claims require a qualifier"),
    ],
)
def test_claim_projection_validation_is_fail_closed(kwargs, message):
    with pytest.raises(ValueError, match=message):
        SynthesisClaimProjection(**kwargs).validate()


def test_claim_projection_rejects_duplicate_evidence_ids():
    with pytest.raises(ValueError, match="unique"):
        SynthesisClaimProjection(
            "c",
            "text",
            ClaimStatus.SUPPORTED,
            ("obs-1", "obs-1"),
        ).validate()


def test_synthesis_projection_validation_is_fail_closed():
    with pytest.raises(ValueError, match="question"):
        SynthesisProjection("", ()).validate()

    with pytest.raises(ValueError, match="unique"):
        SynthesisProjection(
            "q",
            (
                SynthesisClaimProjection("c", "text", ClaimStatus.UNKNOWN),
                SynthesisClaimProjection("c", "other", ClaimStatus.UNKNOWN),
            ),
        ).validate()

    with pytest.raises(ValueError, match="non-empty"):
        SynthesisProjection("q", (), gaps=("",)).validate()


def test_builder_rejects_invalid_question_and_duplicate_required_ids():
    with pytest.raises(ValueError, match="question"):
        build_synthesis_projection((), question="")

    with pytest.raises(ValueError, match="required claim IDs"):
        build_synthesis_projection(
            (),
            question="q",
            required_claim_ids=("c1", "c1"),
        )


@pytest.mark.parametrize(
    "item, message",
    [
        ((SimpleNamespace(claim_id="", text="text"), SimpleNamespace(status=ClaimStatus.SUPPORTED, supporting_evidence=())), "identity"),
        ((SimpleNamespace(claim_id="c", text=""), SimpleNamespace(status=ClaimStatus.SUPPORTED, supporting_evidence=())), "identity"),
        ((SimpleNamespace(claim_id="c", text="text"), SimpleNamespace(status="unknown_status", supporting_evidence=())), "unsupported status"),
    ],
)
def test_builder_rejects_malformed_verified_claims(item, message):
    with pytest.raises(ValueError, match=message):
        build_synthesis_projection((item,), question="q")


def test_builder_rejects_missing_required_claims():
    with pytest.raises(ValueError, match="required verified claims"):
        build_synthesis_projection(
            (verified("other", "Fact", ClaimStatus.SUPPORTED, ("obs",)),),
            question="q",
            required_claim_ids=("required",),
        )


def test_builder_handles_nonempty_required_claims_and_projection_validation():
    projection = build_synthesis_projection(
        (verified("c", "Fact", ClaimStatus.SUPPORTED, ("obs",)),),
        question="q",
        required_claim_ids=("c",),
    )
    assert projection.question == "q"
    projection.validate()


def test_research_synthesizer_preserves_explicit_gap_state():
    from backend.execution.synthesis import ResearchSynthesizer

    run = SimpleNamespace(
        contract=SimpleNamespace(question="Question?"),
        verified_claims=(
            verified("c1", "Unknown fact.", ClaimStatus.UNKNOWN),
        ),
        observations=(),
    )
    synthesized = ResearchSynthesizer().synthesize(run)
    assert "Unresolved aspects:" in synthesized.answer


def test_legacy_synthesis_answer_formats_contradictions_unknowns_and_empty():
    from backend.execution.synthesis import _answer
    from types import SimpleNamespace

    claim = lambda text: SimpleNamespace(text=text)
    buckets = {
        "corroborated": [(claim("Corroborated."), None)],
        "supported": [(claim("Supported."), None)],
        "partial": [(claim("Partial."), None)],
        "contradicted": [(claim("Contradicted."), None)],
        "unknown": [(claim("Unknown."), None)],
    }
    answer = _answer(buckets)
    assert "Corroborated." in answer
    assert "Contradictory evidence exists for:" in answer
    assert "Unresolved aspects:" in answer

    empty = {key: [] for key in buckets}
    assert _answer(empty) == "Evidence is insufficient to answer this question."
