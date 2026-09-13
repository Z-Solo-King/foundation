"""Immutable evaluation-input and receipt binding primitives.

This module proves that a receipt corresponds to a specific public evaluation input
snapshot. It does not authorize promotion or production mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .receipt import EvaluationReceipt


def _hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvaluationInputSnapshot:
    contract_fingerprint: str
    plan_fingerprint: str
    capability_version: str
    policy_version: str
    source_profile_version: str
    corpus_fingerprint: str
    oracle_fingerprint: str
    benchmark_ids: tuple[str, ...]
    created_at: str

    def validate(self) -> None:
        values = (
            self.contract_fingerprint,
            self.plan_fingerprint,
            self.capability_version,
            self.policy_version,
            self.source_profile_version,
            self.corpus_fingerprint,
            self.oracle_fingerprint,
            self.created_at,
        )
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("evaluation input identity fields must not be empty")
        if not self.benchmark_ids:
            raise ValueError("benchmark_ids must not be empty")
        if any(not isinstance(case_id, str) or not case_id.strip() for case_id in self.benchmark_ids):
            raise ValueError("benchmark_ids must contain non-empty strings")
        if len(set(self.benchmark_ids)) != len(self.benchmark_ids):
            raise ValueError("benchmark_ids must be unique")

    def fingerprint(self) -> str:
        self.validate()
        return _hash({
            "contract_fingerprint": self.contract_fingerprint,
            "plan_fingerprint": self.plan_fingerprint,
            "capability_version": self.capability_version,
            "policy_version": self.policy_version,
            "source_profile_version": self.source_profile_version,
            "corpus_fingerprint": self.corpus_fingerprint,
            "oracle_fingerprint": self.oracle_fingerprint,
            "benchmark_ids": self.benchmark_ids,
            "created_at": self.created_at,
        })


@dataclass(frozen=True)
class EvaluationArtifact:
    inputs: EvaluationInputSnapshot
    receipt: EvaluationReceipt
    result_fingerprint: str

    def validate(self) -> None:
        self.inputs.validate()
        self.receipt.validate()
        if not self.result_fingerprint.strip():
            raise ValueError("result_fingerprint must not be empty")
        if self.receipt.benchmark_count != len(self.inputs.benchmark_ids):
            raise ValueError("receipt benchmark_count must match immutable input snapshot")
        if not self.receipt.verify_binding(
            candidate_fingerprint=self.inputs.contract_fingerprint,
            baseline_fingerprint=self.inputs.plan_fingerprint,
            corpus_fingerprint=self.inputs.corpus_fingerprint,
            oracle_fingerprint=self.inputs.oracle_fingerprint,
            min_benchmark_count=len(self.inputs.benchmark_ids),
        ):
            raise ValueError("evaluation receipt does not bind to input snapshot")

    def fingerprint(self) -> str:
        self.validate()
        return _hash({
            "inputs": self.inputs.fingerprint(),
            "receipt": self.receipt.fingerprint(),
            "result_fingerprint": self.result_fingerprint,
        })


def create_evaluation_artifact(
    inputs: EvaluationInputSnapshot,
    receipt: EvaluationReceipt,
    *,
    result_payload: object,
) -> EvaluationArtifact:
    artifact = EvaluationArtifact(inputs, receipt, _hash(result_payload))
    artifact.validate()
    return artifact


def verify_evaluation_artifact(
    artifact: EvaluationArtifact,
    *,
    expected_input_fingerprint: str,
    expected_candidate_fingerprint: str,
) -> bool:
    artifact.validate()
    return (
        artifact.inputs.fingerprint() == expected_input_fingerprint
        and artifact.receipt.candidate_fingerprint == expected_candidate_fingerprint
    )


__all__ = [
    "EvaluationInputSnapshot",
    "EvaluationArtifact",
    "create_evaluation_artifact",
    "verify_evaluation_artifact",
]