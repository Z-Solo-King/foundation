import pytest

from backend.artifacts.ingestion import (
    ARTIFACT_INGESTION_CONTRACT_VERSION,
    ArtifactExtractionResult,
    ArtifactIngestionState,
    IngestionAdapterSpec,
    content_fingerprint,
)
from backend.intelligence.language import (
    ClaimLanguageAlignment,
    LanguageSpan,
    TranslationArtifact,
    normalize_language_tag,
    text_fingerprint,
)


def adapter(**changes):
    data = dict(
        adapter_id="html-v1",
        input_media_types=("text/html",),
        extraction_version="1",
        max_bytes=1024,
        max_depth=8,
        deterministic=True,
        model_assisted=False,
    )
    data.update(changes)
    return IngestionAdapterSpec(**data)


def test_ingestion_contract_validates_deterministic_and_derived_states():
    spec = adapter()
    spec.validate()
    assert spec.schema_version == ARTIFACT_INGESTION_CONTRACT_VERSION
    result = ArtifactExtractionResult(
        "artifact-1",
        content_fingerprint("raw"),
        content_fingerprint("normalized"),
        "text/html",
        ArtifactIngestionState.EXTRACTED,
        spec,
    )
    result.validate()
    partial = ArtifactExtractionResult(
        "artifact-2",
        content_fingerprint("raw"),
        content_fingerprint("partial"),
        "text/html",
        ArtifactIngestionState.PARTIAL,
        spec,
    )
    partial.validate()


def test_ingestion_rejects_invalid_or_unexplained_states():
    with pytest.raises(ValueError):
        adapter(adapter_id=" ").validate()
    with pytest.raises(ValueError):
        adapter(input_media_types=()).validate()
    with pytest.raises(ValueError):
        adapter(extraction_version=" ").validate()
    with pytest.raises(ValueError):
        adapter(max_bytes=0).validate()
    with pytest.raises(ValueError):
        adapter(max_depth=0).validate()
    with pytest.raises(ValueError):
        adapter(deterministic=False, model_assisted=False).validate()
    spec = adapter()
    with pytest.raises(ValueError):
        ArtifactExtractionResult("a", "bad", None, "text/html", ArtifactIngestionState.BLOCKED, spec).validate()
    with pytest.raises(ValueError):
        ArtifactExtractionResult("a", content_fingerprint("x"), None, "text/html", ArtifactIngestionState.EXTRACTED, spec).validate()
    with pytest.raises(ValueError):
        ArtifactExtractionResult("a", content_fingerprint("x"), None, "text/html", ArtifactIngestionState.UNSUPPORTED, spec).validate()
    with pytest.raises(ValueError):
        ArtifactExtractionResult("a", content_fingerprint("x"), content_fingerprint("x"), "text/html", ArtifactIngestionState.BLOCKED, spec).validate()
    with pytest.raises(ValueError):
        ArtifactExtractionResult("a", content_fingerprint("x"), content_fingerprint("x"), "text/html", ArtifactIngestionState.EXTRACTED, adapter(deterministic=True, model_assisted=True)).validate()


def test_language_tag_and_span_contract_is_deterministic():
    assert normalize_language_tag(" EN_us ") == "en-us"
    assert text_fingerprint("hello") == content_fingerprint("hello")
    span = LanguageSpan("s1", "zh-CN", 980, "artifact-1", text_fingerprint("你好"))
    span.validate()
    with pytest.raises(ValueError):
        normalize_language_tag("not a language")
    with pytest.raises(ValueError):
        LanguageSpan(" ", "en", 900, "artifact-1", text_fingerprint("x")).validate()
    with pytest.raises(ValueError):
        LanguageSpan("s", "en", 1001, "artifact-1", text_fingerprint("x")).validate()
    with pytest.raises(ValueError):
        LanguageSpan("s", "en", 900, "artifact-1", "bad").validate()


def test_translation_artifact_requires_cross_language_qualifier_safety():
    good = TranslationArtifact(
        "tr-1", ("s1",), "zh-CN", "en",
        "machine", "model-v1", text_fingerprint("hello"),
        True, True, True,
    )
    good.validate()
    with pytest.raises(ValueError):
        TranslationArtifact("tr", (), "zh", "en", "m", "v", text_fingerprint("x"), True, True, True).validate()
    with pytest.raises(ValueError):
        TranslationArtifact("tr", ("s1",), "en", "EN-us", "m", "v", text_fingerprint("x"), True, True, True).validate()
    with pytest.raises(ValueError):
        TranslationArtifact("tr", ("s1",), "zh", "en", "", "v", text_fingerprint("x"), True, True, True).validate()
    with pytest.raises(ValueError):
        TranslationArtifact("tr", ("s1",), "zh", "en", "m", "v", "bad", True, True, True).validate()
    with pytest.raises(ValueError):
        TranslationArtifact("tr", ("s1",), "zh", "en", "m", "v", text_fingerprint("x"), False, True, True).validate()


def test_alignment_requires_provenance_for_positive_states():
    aligned = ClaimLanguageAlignment("a", "c1", "c2", "tr-1", "zh", "en", "aligned", True)
    aligned.validate()
    with pytest.raises(ValueError):
        ClaimLanguageAlignment("", "c1", "c2", "tr-1", "zh", "en", "aligned", True).validate()
    with pytest.raises(ValueError):
        ClaimLanguageAlignment("a", "c1", "c2", "tr-1", "zh", "en", "bad", True).validate()
    with pytest.raises(ValueError):
        ClaimLanguageAlignment("a", "c1", "c2", "tr-1", "zh", "en", "aligned", False).validate()
