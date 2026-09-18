import pytest

from backend.artifacts.contract import (
    ArtifactKind,
    ArtifactSafety,
    ArtifactValidation,
    authorize_artifact_execution,
    create_artifact,
    derive_artifact,
    ArtifactExecutionState,
)


def _private_artifact():
    return create_artifact(
        b"private",
        kind=ArtifactKind.TEXT,
        media_type="text/plain",
        parser_version="p1",
        owner_scope="owner-1",
        safety=ArtifactSafety.PRIVATE,
        validation=ArtifactValidation.VALID,
    )


def test_private_artifact_cannot_cross_scope_without_authorization():
    artifact = _private_artifact()
    decision = authorize_artifact_execution(artifact, target_scope="external")
    assert decision.state is ArtifactExecutionState.REQUIRES_AUTHORIZATION


def test_private_artifact_can_cross_scope_only_with_explicit_authorization():
    artifact = _private_artifact()
    decision = authorize_artifact_execution(
        artifact,
        target_scope="external",
        explicit_authorization=True,
    )
    assert decision.state is ArtifactExecutionState.AUTHORIZED


def test_malformed_artifact_is_blocked_from_execution():
    artifact = create_artifact(
        b"broken",
        kind=ArtifactKind.ARCHIVE,
        media_type="application/zip",
        parser_version="p1",
        owner_scope="owner-1",
        validation=ArtifactValidation.MALFORMED,
    )
    decision = authorize_artifact_execution(artifact, target_scope="owner-1")
    assert decision.state is ArtifactExecutionState.BLOCKED


def test_derived_artifact_preserves_parent_lineage_and_scope():
    parent = _private_artifact()
    child = derive_artifact(
        parent,
        b"converted",
        kind=ArtifactKind.TEXT,
        media_type="text/plain",
        parser_version="p2",
        validation=ArtifactValidation.VALID,
    )
    assert child.provenance_parent == parent.artifact_id
    assert child.owner_scope == parent.owner_scope
    assert child.execution_identity == parent.execution_identity


def test_blocked_artifact_and_empty_scope_fail_closed():
    artifact = _private_artifact()
    with pytest.raises(ValueError, match="target_scope"):
        authorize_artifact_execution(artifact, target_scope=" ")
    blocked = create_artifact(
        b"blocked",
        kind=ArtifactKind.TEXT,
        media_type="text/plain",
        parser_version="p1",
        owner_scope="owner-1",
        safety=ArtifactSafety.BLOCKED,
        validation=ArtifactValidation.VALID,
    )
    decision = authorize_artifact_execution(blocked, target_scope="owner-1")
    assert decision.state is ArtifactExecutionState.BLOCKED
    assert decision.to_dict()["schema_version"] == "artifact-execution/v1"
