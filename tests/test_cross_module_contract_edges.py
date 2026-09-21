from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_operations_public_core_materialization_contract():
    operations = ROOT / 'operations'
    if not operations.exists():
        return
    sync = operations / 'scripts' / 'sync_public_core.py'
    core = operations / 'foundation_core' / '__init__.py'
    assert sync.exists()
    assert 'FOUNDATION_COMMIT' in sync.read_text(encoding='utf-8')
    assert core.exists()

def test_public_worker_and_private_operations_contract_edges_are_present():
    operations = ROOT / 'operations'
    if not operations.exists():
        return
    assert (operations / 'private' / 'chatbot' / 'live_answer.py').exists()
    assert (operations / 'extractor_mapper' / 'fast_engine_run.py').exists()
    assert (ROOT / 'worker.py').exists()

def test_operations_resource_boundary_references_the_canonical_reservation_type():
    operations = ROOT / 'operations'
    if not operations.exists():
        return
    text = (operations / 'extractor_mapper' / 'resource_envelope.py').read_text(encoding='utf-8')
    assert 'from private.protected_execution import ResourceReservation' in text
    assert 'await ledger.reserve(' in text
    assert 'await ledger.consume(' in text
