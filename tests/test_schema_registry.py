import json
from pathlib import Path
import jsonschema

ROOT=Path(__file__).resolve().parents[1]

def test_registry_is_single_discoverable_authority():
    r=json.loads((ROOT/"schemas/registry.json").read_text(encoding="utf-8"))
    assert r["schema_version"]=="family-schema-registry/v1"
    assert len(r["schemas"])==6

def test_all_registered_schemas_compile_and_are_strict():
    r=json.loads((ROOT/"schemas/registry.json").read_text(encoding="utf-8"))
    for item in r["schemas"]:
        s=json.loads((ROOT/item["path"]).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(s)
        assert s["additionalProperties"] is False

def test_breaking_change_requires_new_major_version():
    r=json.loads((ROOT/"schemas/registry.json").read_text(encoding="utf-8"))
    assert r["compatibility"]["breaking_changes"]=="require a new major version"
