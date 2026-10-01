from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
FACADE = ROOT / "tools" / "woocommerce_v175_plugin_fingerprint_22.py"
MODULES = [
    ROOT / "tools" / "woocommerce_fingerprint_config.py",
    ROOT / "tools" / "woocommerce_fingerprint_discovery.py",
    ROOT / "tools" / "woocommerce_fingerprint_runtime.py",
    ROOT / "tools" / "woocommerce_fingerprint_advisory.py",
    ROOT / "tools" / "woocommerce_fingerprint_passive.py",
]

def test_v175_facade_preserves_canonical_entrypoints():
    namespace = {}
    exec(compile(FACADE.read_text(encoding="utf-8"), str(FACADE), "exec"), namespace)
    for name in ("probe_site", "main", "native_google_valid", "plugin_family_confidence", "ai_advisory", "passive_public_discovery"):
        assert name in namespace

def test_v175_modules_parse_and_facade_is_small():
    for path in [FACADE, *MODULES]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert len(FACADE.read_text(encoding="utf-8").splitlines()) < 260
    assert all(len(path.read_text(encoding="utf-8").splitlines()) < 500 for path in MODULES)
