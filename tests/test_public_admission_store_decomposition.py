from pathlib import Path

ROOT = Path(__file__).parents[1]
LEGACY = ROOT / "tests" / "test_public_admission_store.py"
CORE = ROOT / "tests" / "test_public_admission_store_admission.py"
IDEMP = ROOT / "tests" / "test_public_admission_store_idempotency.py"
SUPPORT = ROOT / "tests" / "admission_store_support.py"

def test_admission_store_suite_is_decomposed():
    assert not LEGACY.exists()
    assert CORE.exists() and IDEMP.exists() and SUPPORT.exists()
    assert len(CORE.read_text(encoding="utf-8").splitlines()) < 800
    assert len(IDEMP.read_text(encoding="utf-8").splitlines()) < 600
