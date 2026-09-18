import pytest

from backend.intelligence.language import (
    TranslationArtifact,
    build_claim_language_alignment,
    build_normalization,
    normalize_text,
)


def test_normalization_is_deterministic_without_becoming_source_evidence():
    result = build_normalization(
        "  Hello\u00a0WORLD  ",
        source_span_ids=("span-1",),
        source_language="EN_us",
    )
    assert result.normalized_text == "hello world"
    assert result.derived is True
    assert len(result.text_fingerprint) == 64


def test_translation_must_preserve_critical_semantics():
    translation = TranslationArtifact(
        translation_id="tr-1",
        source_span_ids=("span-1",),
        source_language="en",
        target_language="hi",
        method="verified",
        version="2026-09",
        derived_fingerprint="a" * 64,
        preserves_qualifiers=True,
        preserves_negation=True,
        preserves_units=True,
    )
    alignment = build_claim_language_alignment(
        alignment_id="a-1",
        source_claim_id="claim-en",
        target_claim_id="claim-hi",
        translation=translation,
        status="aligned",
    )
    assert alignment.provenance_preserved is True


def test_alignment_cannot_promote_unprovenanced_positive_claim():
    translation = TranslationArtifact(
        translation_id="tr-1",
        source_span_ids=("span-1",),
        source_language="en",
        target_language="de",
        method="verified",
        version="2026-09",
        derived_fingerprint="b" * 64,
        preserves_qualifiers=True,
        preserves_negation=True,
        preserves_units=True,
    )
    with pytest.raises(ValueError, match="positive alignment"):
        build_claim_language_alignment(
            alignment_id="a-1",
            source_claim_id="claim-en",
            target_claim_id="claim-de",
            translation=translation,
            status="aligned",
            provenance_preserved=False,
        )


def test_translation_cannot_drop_negation_units_or_qualifiers():
    translation = TranslationArtifact(
        translation_id="tr-1",
        source_span_ids=("span-1",),
        source_language="en",
        target_language="fr",
        method="model",
        version="1",
        derived_fingerprint="c" * 64,
        preserves_qualifiers=True,
        preserves_negation=False,
        preserves_units=True,
    )
    with pytest.raises(ValueError, match="evidence strength"):
        translation.validate()
