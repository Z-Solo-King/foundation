from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_v175_harness_is_decomposed_without_losing_facade() -> None:
    modules = (
        "woocommerce_v175_contracts.py",
        "woocommerce_v175_discovery.py",
        "woocommerce_v175_transport.py",
        "woocommerce_v175_runner.py",
    )
    facade = ROOT / "tools" / "woocommerce_v175_plugin_fingerprint_22.py"
    assert len(facade.read_text(encoding="utf-8").splitlines()) < 100
    for name in modules:
        path = ROOT / "tools" / name
        assert path.exists()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert tree is not None
        assert len(path.read_text(encoding="utf-8").splitlines()) < 550
