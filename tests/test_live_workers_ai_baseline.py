import json
from pathlib import Path

def test_live_workers_ai_baseline_is_retained():
    data=json.loads(Path('benchmark/multi_agent/live_workers_ai_baseline_2026-09-26.json').read_text(encoding='utf-8'))
    assert data['schema']=='live-workers-ai-baseline/v2'
    assert data['total_calls']==16
    assert data['successful_http_200']==16
    assert data['usable_text']==16
    assert data['models'][0]['calls']==8 and data['models'][1]['calls']==8
    assert data['thinking_off_control_probe']['glm']['usable_text'] is True
    assert data['thinking_off_control_probe']['gemma']['usable_text'] is True
