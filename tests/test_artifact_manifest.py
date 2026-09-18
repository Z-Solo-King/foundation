from datetime import datetime, timezone

import pytest

from backend.artifacts.manifest import ArtifactManifest, create_manifest


NOW = datetime(2026, 9, 18, tzinfo=timezone.utc)


def test_manifest_defaults_are_versioned_and_backward_compatible():
    manifest = create_manifest("a1", "answer.json", "json", b"payload", "research", created_at=NOW)
    assert manifest.schema_version == "artifact-manifest/v1"
    assert manifest.execution_fingerprint is None
    assert manifest.policy_version is None
    assert manifest.result_digest == manifest.content_hash
    assert len(manifest.reproducibility_id) == 64
    auto_created = create_manifest("a0", "auto.json", "json", b"payload", "research")
    assert auto_created.created_at.tzinfo is not None


def test_manifest_records_full_execution_provenance():
    digest = "a" * 64
    manifest = create_manifest(
        "a2",
        "answer.json",
        "json",
        b"payload",
        "research",
        execution_fingerprint=digest,
        policy_version="policy-7",
        request_fingerprint="b" * 64,
        router_version="router-v2",
        planner_version="planner-v3",
        retriever_version="retriever-v4",
        mapper_version="mapper-v5",
        extractor_version="extractor-v6",
        adapter_version="adapter-v7",
        provider_model_identity="provider/model-v8",
        source_fingerprints=("d" * 64, "c" * 64),
        observed_at=NOW,
        freshness_state="fresh",
        budget_allocated=10,
        budget_consumed=7,
        created_at=NOW,
    )
    assert manifest.source_fingerprints == ("c" * 64, "d" * 64)
    assert manifest.provider_model_identity == "provider/model-v8"
    assert manifest.budget_consumed == 7
    assert len(manifest.reproducibility_id) == 64


def test_equivalent_runs_produce_same_reproducibility_id():
    kwargs = dict(
        execution_fingerprint="a" * 64,
        policy_version="policy-7",
        request_fingerprint="b" * 64,
        router_version="router-v2",
        planner_version="planner-v3",
        provider_model_identity="provider/model-v8",
        source_fingerprints=("c" * 64, "d" * 64),
        observed_at=NOW,
        freshness_state="fresh",
        budget_allocated=10,
        budget_consumed=7,
        created_at=NOW,
    )
    first = create_manifest("artifact-a", "a.json", "json", b"same", "research", **kwargs)
    second = create_manifest("artifact-b", "b.json", "json", b"same", "research", **kwargs)
    assert first.reproducibility_id == second.reproducibility_id


def test_policy_or_result_changes_alter_reproducibility_id():
    base = create_manifest(
        "a",
        "a.json",
        "json",
        b"same",
        "research",
        policy_version="policy-1",
        created_at=NOW,
    )
    policy_changed = create_manifest(
        "b",
        "b.json",
        "json",
        b"same",
        "research",
        policy_version="policy-2",
        created_at=NOW,
    )
    result_changed = create_manifest(
        "c",
        "c.json",
        "json",
        b"other",
        "research",
        policy_version="policy-1",
        created_at=NOW,
    )
    assert base.reproducibility_id != policy_changed.reproducibility_id
    assert base.reproducibility_id != result_changed.reproducibility_id


def test_artifact_manifest_dataclass_preserves_existing_positional_shape():
    manifest = ArtifactManifest(
        "a3",
        "out.txt",
        "text",
        "a" * 64,
        NOW,
        "source",
    )
    assert manifest.artifact_id == "a3"
    assert manifest.schema_version == "artifact-manifest/v1"


def test_manifest_rejects_invalid_identity_and_hashes():
    with pytest.raises(ValueError, match="identity"):
        ArtifactManifest("", "out.txt", "text", "a" * 64, NOW, "source")
    with pytest.raises(ValueError, match="schema_version"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, NOW, "source", schema_version="")
    with pytest.raises(ValueError, match="provenance"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, NOW, "")
    with pytest.raises(ValueError, match="SHA-256"):
        ArtifactManifest("a", "out.txt", "text", "bad", NOW, "source")
    with pytest.raises(ValueError, match="created_at"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, datetime(2026, 9, 18), "source")
    with pytest.raises(ValueError, match="observed_at"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, NOW, "source", observed_at=datetime(2026, 9, 18))
    with pytest.raises(ValueError, match="freshness_state"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, NOW, "source", freshness_state="bad")
    with pytest.raises(ValueError, match="budget"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, NOW, "source", budget_allocated=-1)
    with pytest.raises(ValueError, match="budget_consumed"):
        ArtifactManifest("a", "out.txt", "text", "a" * 64, NOW, "source", budget_allocated=1, budget_consumed=2)


def test_manifest_rejects_blank_optional_versions_and_identities():
    base = dict(
        artifact_id="a",
        filename="a.json",
        format="json",
        content_hash="a" * 64,
        created_at=NOW,
        provenance="source",
    )
    for field in (
        "router_version",
        "planner_version",
        "retriever_version",
        "mapper_version",
        "extractor_version",
        "adapter_version",
        "provider_model_identity",
    ):
        with pytest.raises(ValueError):
            ArtifactManifest(**base, **{field: " "})


def test_manifest_rejects_invalid_optional_fingerprints_and_state_values():
    base = dict(
        artifact_id="a",
        filename="a.json",
        format="json",
        content_hash="a" * 64,
        created_at=NOW,
        provenance="source",
    )
    for field in ("execution_fingerprint", "result_digest", "request_fingerprint"):
        with pytest.raises(ValueError):
            ArtifactManifest(**base, **{field: "bad"})
    with pytest.raises(ValueError):
        ArtifactManifest(**base, source_fingerprints=("bad",))

def test_manifest_factory_defaults_result_digest_to_content_hash_when_empty():
    manifest = create_manifest(
        "a4",
        "out.json",
        "json",
        b"payload",
        "source",
        result_digest="",
        created_at=NOW,
    )
    assert manifest.result_digest == manifest.content_hash
