from backend.artifacts.manifest import ArtifactManifest, create_manifest


def test_manifest_defaults_are_versioned_and_backward_compatible():
    manifest = create_manifest("a1", "answer.json", "json", b"payload", "research")
    assert manifest.schema_version == "artifact-manifest/v1"
    assert manifest.execution_fingerprint is None
    assert manifest.policy_version is None
    assert manifest.result_digest == manifest.content_hash


def test_manifest_records_execution_and_policy_identity():
    manifest = create_manifest(
        "a2",
        "answer.json",
        "json",
        b"payload",
        "research",
        execution_fingerprint="exec-123",
        policy_version="policy-7",
    )
    assert manifest.execution_fingerprint == "exec-123"
    assert manifest.policy_version == "policy-7"
    assert len(manifest.result_digest) == 64


def test_artifact_manifest_dataclass_preserves_existing_positional_shape():
    manifest = ArtifactManifest("a3", "out.txt", "text", "hash", __import__("datetime").datetime.now(__import__("datetime").timezone.utc), "source")
    assert manifest.artifact_id == "a3"
    assert manifest.schema_version == "artifact-manifest/v1"
