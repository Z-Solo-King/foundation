from tools.validate_operations_pin_manifest import load_manifest

def test_operations_pin_manifest():
    data=load_manifest()
    assert set(data["pins"]) == {"production_runtime","research_runtime","secret_sync_utility"}
