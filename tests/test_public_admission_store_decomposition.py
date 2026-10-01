from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
CORE = ROOT / "tests" / "test_public_admission_store_admission.py"
IDEMP = ROOT / "tests" / "test_public_admission_store_idempotency.py"
SUPPORT = ROOT / "tests" / "admission_store_support.py"
ORIGINAL = None

def test_split_preserves_all_original_test_functions():
    names = []
    source = CORE.read_text(encoding="utf-8") + "\n" + IDEMP.read_text(encoding="utf-8")
    names = re.findall(r"^(?:async\s+def|def)\s+(test_[A-Za-z0-9_]+)\s*\(", source, re.M)
    assert len(names) == 42
    assert len(set(names)) == 42

def test_split_surfaces_stay_under_large_test_threshold():
    assert len(CORE.read_text(encoding="utf-8").splitlines()) < 800
    assert len(IDEMP.read_text(encoding="utf-8").splitlines()) < 800
    assert len(SUPPORT.read_text(encoding="utf-8").splitlines()) < 250
