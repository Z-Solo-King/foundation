import json
from pathlib import Path
from tools.validate_operations_pins import MANIFEST
def test_manifest_version_and_scopes():
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"]=="operations-pin-manifest/v1"
    assert set(data["purpose_scoped_pins"])=={"production_runtime","nightly_research","utility_validation"}
    for item in data["purpose_scoped_pins"].values():
        assert len(item["revision"])==40 and item["mutable_ref_forbidden"] is True
def test_release_consumes_manifest():
    text=Path("scripts/production_release.sh").read_text(encoding="utf-8")
    assert "OPERATIONS_PIN_MANIFEST" in text and "jq -r" in text
