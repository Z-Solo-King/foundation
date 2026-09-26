from pathlib import Path
from tools.check_continuity_freshness import REQUIRED_DOCS,is_canonical_change

def test_canonical_path_classifier():
    assert is_canonical_change("backend/api/main.py")
    assert is_canonical_change("foundation_core/product_mapping.py")
    assert is_canonical_change("polyglot/edge-worker/src/sse.ts")
    assert is_canonical_change(".github/workflows/example.yml")
    assert is_canonical_change("worker.py")
    assert is_canonical_change("CAPABILITIES.json")
    assert is_canonical_change("REPOSITORY_MAP.json")
    assert not is_canonical_change("tests/test_example.py")
    assert not is_canonical_change("docs/example.md")

def test_required_docs_are_exact_living_pair():
    assert [str(p) for p in REQUIRED_DOCS] == ["docs/CURRENT_SOURCE_OF_TRUTH.md","docs/FAMILY_SYNC_STATE.json"]
    assert all(p.exists() for p in REQUIRED_DOCS)


def test_changed_files_fetches_missing_base_revision(monkeypatch):
    import tools.check_continuity_freshness as module
    calls = []
    class Fake:
        returncode = 0
        stdout = ""
        stderr = ""
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[:3] == ["git", "cat-file", "-e"]:
            class Missing:
                returncode = 1
                stdout = ""
                stderr = ""
            return Missing()
        if cmd[:3] == ["git", "fetch", "--no-tags"]:
            return Fake()
        return Fake()
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module.changed_files("deadbeef", "head")
    assert any(cmd[:3] == ["git", "fetch", "--no-tags"] for cmd in calls)
