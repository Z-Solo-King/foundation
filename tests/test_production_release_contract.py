from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "production_release.sh"


def test_persistence_gate_does_not_mask_real_400_errors():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'elif [ "$persistence_seed_status" = "404" ]' in text
    assert '.error == "unsupported persistence acceptance operation"' in text
    assert 'cat "$persistence_seed_file" || true' in text
