from benchmark.multi_agent.baseline import compare


def _summary(*, completed=2, useful=4, high=1, execution="completed", signals=None):
    return {"schema": "project-improvement-research/v1", "research_id": "nightly-current", "execution_state": execution, "program_count": completed, "status_counts": {"completed": completed}, "project_snapshot": {"revision": "current-sha"}, "programs": [{"measurement": {"useful_findings": useful}}], "improvement_signals": signals if signals is not None else [{"type": "gap", "severity": "high"}] * high}


def test_missing_baseline_is_explicit():
    result = compare(_summary(), None)
    assert result["schema"] == "project-improvement-baseline/v1"
    assert result["available"] is False
    assert result["decision"] == "NO_BASELINE"


def test_regression_when_execution_degrades():
    result = compare(_summary(completed=1, useful=1, execution="partial_or_failed"), _summary(completed=2, useful=4, execution="completed"))
    assert result["decision"] == "REGRESSED"
    assert result["metrics"]["completed_programs_delta"] < 0


def test_regression_wins_when_mixed_signals_conflict():
    result = compare(_summary(completed=3, useful=8, high=3), _summary(completed=2, useful=4, high=1))
    assert result["decision"] == "REGRESSED"


def test_improvement_when_execution_recovers():
    result = compare(_summary(completed=2, useful=4, high=0, execution="completed"), _summary(completed=1, useful=4, high=1, execution="partial_or_failed"))
    assert result["decision"] == "IMPROVED"


def test_improvement_when_useful_findings_increase():
    result = compare(_summary(completed=2, useful=5, high=1), _summary(completed=2, useful=4, high=1))
    assert result["decision"] == "IMPROVED"


def test_stable_when_metrics_are_equal():
    result = compare(_summary(completed=2, useful=4, high=1, signals=[{"type": "gap", "severity": "high"}]), _summary(completed=2, useful=4, high=1, signals=[{"type": "gap", "severity": "high"}]))
    assert result["decision"] == "STABLE"


def test_signal_type_changes_are_recorded():
    result = compare(_summary(signals=[{"type": "new", "severity": "medium"}]), _summary(signals=[{"type": "old", "severity": "medium"}]))
    assert result["signal_type_changes"]["added"] == ["new"]
    assert result["signal_type_changes"]["resolved"] == ["old"]


def test_summary_with_missing_signal_lists_is_supported():
    current = _summary()
    previous = _summary()
    current.pop("improvement_signals")
    previous.pop("improvement_signals")
    result = compare(current, previous)
    assert result["decision"] == "STABLE"
