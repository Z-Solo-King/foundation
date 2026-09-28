successfully downloaded text file (SHA: 0bd6c01b61c89b1b8dc811f37ef1364eb4053223)
def test_legacy_worker_retirement_skips_empty_worker_names():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'if [ -n "$legacy_worker" ] && [ "$legacy_worker" != "foundation" ] && [ "$legacy_worker" != "operations" ]; then' in deployment
    assert deployment.count('if [ -n "$legacy_worker" ] && [ "$legacy_worker" != "foundation" ] && [ "$legacy_worker" != "operations" ]; then') == 2


