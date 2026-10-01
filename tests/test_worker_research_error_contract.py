from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_research_persistence_error_path_initializes_run_id_before_try():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    admission_marker = "admission_result = await _public_admit("
    policy_marker = "return_policy=True,"
    decision_marker = "decision, lease = admission_result[:2]"
    assert admission_marker in source
    assert policy_marker in source
    assert decision_marker in source
    assert "run_id = None" in source
    assert source.index("run_id = None") < source.index('phase = "submit_research"')
    assert 'if run_id is not None and persistence is not None:' in source
    assert 'await persistence.set_run_status(run_id, "failed")' in source