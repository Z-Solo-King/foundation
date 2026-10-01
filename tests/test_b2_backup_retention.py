from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cleanup_b2_backup_generations.py"


def _module():
    spec = importlib.util.spec_from_file_location("cleanup_b2_backup_generations", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deletion_plan_keeps_only_latest_verified_generation():
    module = _module()
    payload = {
        "Versions": [
            {"Key": "repository-backup/new/a.tar.gz", "VersionId": "v-new", "IsLatest": True},
            {"Key": "repository-backup/new/a.tar.gz", "VersionId": "v-old", "IsLatest": False},
            {"Key": "repository-backup/old/a.tar.gz", "VersionId": "v-legacy", "IsLatest": True},
        ],
        "DeleteMarkers": [
            {"Key": "repository-backup/old/b.json", "VersionId": "m-legacy", "IsLatest": True},
        ],
    }
    deletions = module.deletion_plan(payload, {"repository-backup/new/a.tar.gz"})
    assert {"Key": "repository-backup/new/a.tar.gz", "VersionId": "v-old"} in deletions
    assert {"Key": "repository-backup/old/a.tar.gz", "VersionId": "v-legacy"} in deletions
    assert {"Key": "repository-backup/old/b.json", "VersionId": "m-legacy"} in deletions
    assert {"Key": "repository-backup/new/a.tar.gz", "VersionId": "v-new"} not in deletions


def test_keep_file_rejects_keys_outside_backup_prefix(tmp_path):
    module = _module()
    keep = tmp_path / "uploaded.tsv"
    keep.write_text("other-prefix/file\tlocal\tsha\t1\n", encoding="utf-8")
    try:
        module.load_keep_keys(keep)
    except SystemExit as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("expected prefix guard")
