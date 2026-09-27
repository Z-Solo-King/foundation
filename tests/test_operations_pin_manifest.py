import json
from tools.validate_operations_pin_manifest import load_manifest

def test_operations_pin_manifest():
    data=load_manifest()
    assert set(data["pins"]) == {"production_runtime","research_runtime","secret_sync_utility"}


def test_secret_sync_manifest_matches_current_operations_utility():
    manifest = json.loads((ROOT / "docs" / "OPERATIONS_PIN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["pins"]["secret_sync_utility"]["sha"] == "849b71d0395536456266e39a1837a97944998bf2"
