from dataclasses import replace

import pytest

from backend.execution.code_sandbox import (
    CodeExecutionPolicy,
    CodeExecutionRequest,
    CodeExecutionResult,
    CodeExecutionStatus,
)


def request():
    return CodeExecutionRequest(
        "req-1", "artifact-1", "0" * 64, "python", "main.py", sandbox_ref="sandbox-1"
    )


def test_code_upload_never_implies_execution_and_request_requires_sandbox():
    req = request()
    req.validate()
    with pytest.raises(ValueError):
        replace(req, sandbox_ref=None).validate()
    with pytest.raises(ValueError):
        replace(req, artifact_hash="short").validate()


def test_policy_rejects_network_bypass_and_invalid_limits():
    with pytest.raises(ValueError):
        CodeExecutionPolicy(sandbox_required=False).validate()
    with pytest.raises(ValueError):
        CodeExecutionPolicy(max_runtime_seconds=0).validate()
    with pytest.raises(ValueError):
        CodeExecutionPolicy(max_output_bytes=0).validate()
    with pytest.raises(ValueError):
        replace(request(), requested_network=True).validate()
    network_req = replace(request(), policy=CodeExecutionPolicy(network_allowed=True), requested_network=True)
    network_req.validate()


def test_execution_result_states_and_failure_reasons():
    success = CodeExecutionResult("req-1", CodeExecutionStatus.SUCCEEDED, exit_code=0, sandbox_ref="sandbox-1")
    success.validate()
    with pytest.raises(ValueError):
        CodeExecutionResult("req-1", CodeExecutionStatus.SUCCEEDED, exit_code=1, sandbox_ref="sandbox-1").validate()
    for status in (CodeExecutionStatus.FAILED, CodeExecutionStatus.REJECTED, CodeExecutionStatus.TIMED_OUT):
        with pytest.raises(ValueError):
            CodeExecutionResult("req-1", status, sandbox_ref="sandbox-1").validate()
    failure = CodeExecutionResult("req-1", CodeExecutionStatus.FAILED, sandbox_ref="sandbox-1", failure_reason="exit 1")
    failure.validate()
    with pytest.raises(ValueError):
        CodeExecutionResult("req-1", CodeExecutionStatus.RUNNING).validate()


def test_result_numeric_guards_and_not_requested():
    with pytest.raises(ValueError):
        replace(CodeExecutionResult("req-1", CodeExecutionStatus.NOT_REQUESTED), stdout_bytes=-1).validate()
    with pytest.raises(ValueError):
        replace(CodeExecutionResult("req-1", CodeExecutionStatus.NOT_REQUESTED), runtime_seconds=-1).validate()
    CodeExecutionResult("req-1", CodeExecutionStatus.NOT_REQUESTED).validate()
