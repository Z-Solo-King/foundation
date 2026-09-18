from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_research_persistence_error_path_initializes_run_id_before_try():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    marker = 'idempotency_key = request.headers.get("Idempotency-Key")\n            run_id = None\n            phase = "create_run"\n            try:'
    assert marker in source
    assert 'if run_id is not None:\n                    try:\n                        await persistence.set_run_status(run_id, "failed")' in source
