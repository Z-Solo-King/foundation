from pathlib import Path


FORBIDDEN_PUBLIC_IMPORTS = (
    "from private ",
    "import private.",
    "from extractor_mapper ",
    "import extractor_mapper.",
)


def test_public_foundation_does_not_import_private_family_members():
    root = Path(__file__).resolve().parents[1]
    for path in root.rglob("*.py"):
        if ".venv" in path.parts or path.parts[-2:] == ("tests", "__pycache__"):
            continue
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in FORBIDDEN_PUBLIC_IMPORTS), path
