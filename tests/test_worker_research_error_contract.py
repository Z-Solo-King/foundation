from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_research_persistence_error_path_initializes_run_id_before_try():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    marker = 'event_id = _idempotency_key(request, f"research:{uuid.uuid4().hex}")\n            if raw_key is not None and event_id is None:\n                return _authenticated_json({"ok": False, "error": "invalid_idempotency_key"}, status=400)\n            decision, lease = await _public_admit(self.env, AdmissionRoute.RESEARCH, subject_fingerprint, event_id)\n            denied = _admission_response(decision)\n            if denied is not None:\n                return denied\n            run_id = None\n            phase = "submit_research"\n            persistence = None\n            try:'
    assert marker in source
    assert 'if run_id is not None and persistence is not None:\n                    try:\n                        await persistence.set_run_status(run_id, "failed")' in source
