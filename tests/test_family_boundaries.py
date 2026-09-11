from pathlib import Path


def test_public_foundation_does_not_import_private_family_members():
    root = Path(__file__).resolve().parents[1] / "backend"
    forbidden_imports = (
        "from private ",
        "import private.",
        "from extractor_mapper ",
        "import extractor_mapper.",
    )
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden_imports), path
