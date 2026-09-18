import pytest

from backend.artifacts.contract import (
    ArtifactKind,
    ArtifactPolicy,
    ArtifactSafety,
    ArtifactValidation,
    AdapterContract,
    AdapterResult,
    ExtractionMode,
    create_artifact,
    deterministic_artifact_id,
)
from backend.code_analysis.contract import (
    CODE_ANALYSIS_CONTRACT_VERSION,
    CodeAnalysisOperation,
    CodeAnalysisRequest,
    CodeAnalysisResult,
    patch_digest,
    redact_repository_secrets,
)


def test_artifact_contract_is_deterministic_and_public_safe():
    first = create_artifact(
        "hello",
        kind=ArtifactKind.TEXT,
        media_type="text/plain",
        parser_version="text/v1",
        owner_scope="public",
        safety=ArtifactSafety.PUBLIC,
        validation=ArtifactValidation.VALID,
        publication_eligible=True,
    )
    second = create_artifact(
        "hello",
        kind=ArtifactKind.TEXT,
        media_type="text/plain",
        parser_version="text/v1",
        owner_scope="public",
        safety=ArtifactSafety.PUBLIC,
        validation=ArtifactValidation.VALID,
        publication_eligible=True,
    )
    assert first == second
    assert first.artifact_id == deterministic_artifact_id(None, first.content_fingerprint, "text/v1")


def test_private_and_invalid_artifacts_fail_closed_for_publication():
    with pytest.raises(ValueError):
        create_artifact(
            "secret",
            kind=ArtifactKind.TEXT,
            media_type="text/plain",
            parser_version="text/v1",
            owner_scope="private",
            safety=ArtifactSafety.PRIVATE,
            validation=ArtifactValidation.VALID,
            publication_eligible=True,
        )
    with pytest.raises(ValueError):
        create_artifact(
            "bad",
            kind=ArtifactKind.PDF,
            media_type="application/pdf",
            parser_version="pdf/v1",
            owner_scope="public",
            validation=ArtifactValidation.MALFORMED,
            publication_eligible=True,
        )
    with pytest.raises(ValueError):
        create_artifact(
            "blocked",
            kind=ArtifactKind.IMAGE,
            media_type="image/png",
            parser_version="image/v1",
            owner_scope="public",
            safety=ArtifactSafety.BLOCKED,
            validation=ArtifactValidation.UNSUPPORTED,
            publication_eligible=True,
        )


def test_artifact_policy_and_identity_validation():
    with pytest.raises(ValueError):
        ArtifactPolicy(max_size_bytes=0).validate()
    with pytest.raises(ValueError):
        ArtifactPolicy(max_depth=0).validate()
    with pytest.raises(ValueError):
        deterministic_artifact_id("", "", "v1")
    with pytest.raises(ValueError):
        create_artifact(
            b"x",
            kind=ArtifactKind.TEXT,
            media_type="text/plain",
            parser_version="v1",
            owner_scope="public",
            policy=ArtifactPolicy(max_size_bytes=0),
        )
    with pytest.raises(ValueError):
        create_artifact(
            b"x" * 10,
            kind=ArtifactKind.TEXT,
            media_type="text/plain",
            parser_version="v1",
            owner_scope="public",
            policy=ArtifactPolicy(max_size_bytes=5),
        )


def test_adapter_contract_and_result_fail_closed():
    with pytest.raises(ValueError):
        AdapterContract(ArtifactKind.PDF, (), "pdf/v1").validate()
    with pytest.raises(ValueError):
        AdapterContract(ArtifactKind.PDF, ("application/pdf",), "",).validate()
    adapter = AdapterContract(ArtifactKind.PDF, ("application/pdf",), "pdf/v1", ExtractionMode.OCR)
    adapter.validate()
    result = AdapterResult("artifact-adapter/v1", "a" * 64, "b" * 64, ExtractionMode.OCR, warnings=("ocr",), stable_region_ids=("r1",))
    result.validate()
    with pytest.raises(ValueError):
        AdapterResult("", "a" * 10, None, ExtractionMode.DETERMINISTIC).validate()


def test_code_analysis_is_analysis_only_and_redacts_secrets():
    request = CodeAnalysisRequest("owner/repo", "abc123", CodeAnalysisOperation.INSPECT)
    request.validate()
    with pytest.raises(ValueError):
        CodeAnalysisRequest("owner/repo", "abc123", CodeAnalysisOperation.INSPECT, execution_requested=True).validate()

    redacted, count = redact_repository_secrets("api_key: SECRET123 password=hello")
    assert "<REDACTED>" in redacted
    assert count == 2

    patch = patch_digest("diff --git a/a b/a")
    result = CodeAnalysisResult(
        CODE_ANALYSIS_CONTRACT_VERSION,
        "owner/repo",
        "abc123",
        CodeAnalysisOperation.PATCH_CANDIDATE,
        False,
        candidate_patch_digest=patch,
        redacted_secret_count=count,
        provenance_fingerprint=patch,
    )
    result.validate()
    assert len(patch) == 64
    with pytest.raises(ValueError):
        CodeAnalysisResult("v0", "owner/repo", "abc123", CodeAnalysisOperation.INSPECT, True).validate()


def test_code_analysis_input_validation():
    with pytest.raises(ValueError):
        CodeAnalysisRequest("", "rev", CodeAnalysisOperation.INSPECT).validate()
    with pytest.raises(TypeError):
        redact_repository_secrets(None)
    with pytest.raises(TypeError):
        patch_digest(None)


def test_code_analysis_result_validation_rejects_invalid_fields():
    with pytest.raises(ValueError, match="repository and revision"):
        CodeAnalysisResult(CODE_ANALYSIS_CONTRACT_VERSION, "", "rev", CodeAnalysisOperation.INSPECT, False).validate()
    with pytest.raises(ValueError, match="cannot authorize execution"):
        CodeAnalysisResult(CODE_ANALYSIS_CONTRACT_VERSION, "owner/repo", "rev", CodeAnalysisOperation.INSPECT, True).validate()
    with pytest.raises(ValueError, match="non-negative"):
        CodeAnalysisResult(CODE_ANALYSIS_CONTRACT_VERSION, "owner/repo", "rev", CodeAnalysisOperation.INSPECT, False, redacted_secret_count=-1).validate()
    with pytest.raises(ValueError, match="SHA-256"):
        CodeAnalysisResult(CODE_ANALYSIS_CONTRACT_VERSION, "owner/repo", "rev", CodeAnalysisOperation.PATCH_CANDIDATE, False, candidate_patch_digest="bad").validate()


def test_code_analysis_execution_is_rejected_for_all_operations():
    with pytest.raises(ValueError, match="cannot execute"):
        CodeAnalysisRequest("owner/repo", "rev", CodeAnalysisOperation.PATCH_CANDIDATE, execution_requested=True).validate()


def test_artifact_ref_validation_rejects_remaining_identity_and_fingerprint_edges():
    from backend.artifacts.contract import ArtifactRef
    base = create_artifact(
        "x",
        kind=ArtifactKind.TEXT,
        media_type="text/plain",
        parser_version="v1",
        owner_scope="public",
    )
    cases = [
        {"artifact_id": " "},
        {"kind": "unsupported"},
        {"media_type": " "},
        {"content_fingerprint": "bad"},
        {"schema_fingerprint": "bad"},
        {"retention_days": -1},
        {"safety": ArtifactSafety.BLOCKED, "publication_eligible": True},
    ]
    for changes in cases:
        broken = ArtifactRef(**{**base.__dict__, **changes})
        with pytest.raises(ValueError):
            broken.validate()


def test_adapter_validation_rejects_remaining_branches():
    with pytest.raises(ValueError):
        AdapterContract("unsupported", ("x",), "v1").validate()
    with pytest.raises(ValueError):
        AdapterContract(ArtifactKind.TEXT, ("text/plain",), "v1", max_input_bytes=0).validate()

    with pytest.raises(ValueError):
        AdapterResult("v1", "a" * 63, None, ExtractionMode.DETERMINISTIC).validate()
    with pytest.raises(ValueError):
        AdapterResult("v1", "a" * 64, "b" * 63, ExtractionMode.DETERMINISTIC).validate()
    with pytest.raises(ValueError):
        AdapterResult("v1", "a" * 64, None, ExtractionMode.DETERMINISTIC, warnings=("",)).validate()
