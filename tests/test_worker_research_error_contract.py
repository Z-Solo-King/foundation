from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_research_persistence_error_path_initializes_run_id_before_try():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert 'policy_envelope = await _private_policy_envelope(self.env, request)' in source
    assert 'decision, lease = await _public_admit(' in source
    assert 'policy_envelope=policy_envelope' in source
    assert 'run_id = None' in source
    assert 'phase = "submit_research"' in source
    assert 'if run_id is not None and persistence is not None:' in source
    assert 'await persistence.set_run_status(run_id, "failed")' in source
