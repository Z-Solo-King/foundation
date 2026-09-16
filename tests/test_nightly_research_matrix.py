from pathlib import Path

from benchmark.multi_agent.programs import NIGHTLY_PROGRAMS


def _workflow_text() -> str:
    return Path('.github/workflows/nightly-multi-agent-research.yml').read_text(encoding='utf-8')


def test_nightly_matrix_has_three_complete_lanes():
    assert len(NIGHTLY_PROGRAMS) == 24
    for lane in range(3):
        programs = [program for program in NIGHTLY_PROGRAMS if program.lane == lane]
        assert len(programs) == 8
        assert {program.slot for program in programs} == set(range(8))


def test_nightly_matrix_program_ids_are_unique():
    ids = [program.program_id for program in NIGHTLY_PROGRAMS]
    assert len(ids) == len(set(ids))


def test_nightly_research_lanes_are_failure_isolated():
    workflow = _workflow_text()
    assert 'fail-fast: false' in workflow
    assert 'if: ${{ always() }}' in workflow
    assert 'id: executor' in workflow
    assert 'ready=$ready' in workflow
    assert "if: ${{ steps.executor.outputs.ready == 'true' }}" in workflow
    assert "if: ${{ inputs.test_mode == true && steps.executor.outputs.ready != 'true' }}" in workflow
    assert "status': status" in workflow
    assert 'blocked_runtime' in workflow
    assert 'failed_runtime' in workflow
    assert 'needs: research' in workflow
    assert 'project-summary:' in workflow
    assert 'runtime-diagnostic:' in workflow


def test_nightly_schedule_never_auto_enables_test_mode():
    workflow = _workflow_text()
    assert 'workflow_dispatch:' in workflow
    assert 'test_mode:' in workflow
    assert 'never enabled by schedule' in workflow
