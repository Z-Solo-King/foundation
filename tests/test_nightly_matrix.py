from benchmark.nightly.nightly_matrix import AGENTS, CASES, build_matrix

def test_matrix_is_exactly_19_research_jobs_plus_aggregator():
    rows=build_matrix()
    assert len(rows)==20
    assert len({r['job_id'] for r in rows})==20
    assert [r['case_id'] for r in rows[:-1]]==list(CASES)
    assert rows[-1]['case_id']=='aggregate'
    assert {r['agent_budget'] for r in rows[:-1]} >= set(AGENTS)
    assert all(r['strict_zero_cost_only'] for r in rows)
    assert all(not r['production_controls_mutable'] for r in rows)

def test_matrix_digests_are_stable():
    assert [r['matrix_digest'] for r in build_matrix()] == [r['matrix_digest'] for r in build_matrix()]
