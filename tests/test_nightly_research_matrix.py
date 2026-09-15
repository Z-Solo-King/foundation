from benchmark.multi_agent.programs import NIGHTLY_PROGRAMS


def test_nightly_matrix_has_three_complete_lanes():
    assert len(NIGHTLY_PROGRAMS) == 24
    for lane in range(3):
        programs = [program for program in NIGHTLY_PROGRAMS if program.lane == lane]
        assert len(programs) == 8
        assert {program.slot for program in programs} == set(range(8))


def test_nightly_matrix_program_ids_are_unique():
    ids = [program.program_id for program in NIGHTLY_PROGRAMS]
    assert len(ids) == len(set(ids))
