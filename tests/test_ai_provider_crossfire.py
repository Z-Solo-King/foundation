import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "benchmark" / "ai_provider_crossfire.py"
SPEC = importlib.util.spec_from_file_location("ai_provider_crossfire", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

def test_cloudflare_native_response_parser():
    payload = {"result": {"response": '{"answer":"PASS"}'}}
    assert MODULE.extract_response_text("cloudflare_workers_ai", payload) == '{"answer":"PASS"}'

def test_openai_compatible_response_parser():
    payload = {"choices": [{"message": {"content": '{"answer":"PASS"}'}}]}
    assert MODULE.extract_response_text("siliconflow", payload) == '{"answer":"PASS"}'

def test_quality_contract():
    assert MODULE.quality_pass("instruction", '{"answer":"PASS"}')
    assert MODULE.quality_pass("arithmetic", "111563")
