from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_public_foundation_does_not_own_private_claim_migrations() -> None:
    assert not (ROOT / "migrations").exists()
    assert not (ROOT / "backend").exists()


def test_claim_storage_implementation_remains_outside_public_checkout() -> None:
    forbidden = [ROOT / "worker.py", ROOT / "private", ROOT / "operations"]
    assert all(not path.exists() for path in forbidden)
