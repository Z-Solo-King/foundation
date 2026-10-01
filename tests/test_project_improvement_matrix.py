import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
MATRIX = ROOT / 'docs' / 'PROJECT_IMPROVEMENT_MATRIX.json'

def test_project_improvement_matrix_covers_major_components():
    data = json.loads(MATRIX.read_text(encoding='utf-8'))
    expected = {'chatbot','extractor','mapper','research','provider_fleet','runtime_governance','cloudflare_runtime','storage_b2','security_ci','feed_recovery'}
    assert data['schema'] == 'project-improvement-matrix/v1'
    assert expected <= data['components'].keys()
    for name in expected:
        assert data['components'][name]['workflows']
        assert data['components'][name]['ai_task_families']

def test_project_improvement_matrix_points_to_existing_workflows():
    data = json.loads(MATRIX.read_text(encoding='utf-8'))
    missing = [f"{name}: {workflow}" for name, item in data['components'].items() for workflow in item['workflows'] if not (ROOT / '.github' / 'workflows' / workflow).is_file()]
    assert missing == []
