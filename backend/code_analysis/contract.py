from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import re


CODE_ANALYSIS_CONTRACT_VERSION = "code-analysis/v1"
_SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|password|secret|private[_-]?key)\s*[:=]\s*[^\s,;]+")


class CodeAnalysisOperation(StrEnum):
    INSPECT = "inspect"
    STRUCTURE = "structure"
    DEPENDENCY = "dependency"
    STATIC_VALIDATE = "static_validate"
    PATCH_CANDIDATE = "patch_candidate"
    TEST_PLAN = "test_plan"


@dataclass(frozen=True)
class CodeAnalysisRequest:
    repository: str
    revision: str
    operation: CodeAnalysisOperation
    execution_requested: bool = False
    input_fingerprint: str | None = None

    def validate(self) -> None:
        if not self.repository.strip() or not self.revision.strip():
            raise ValueError("repository and revision are required")
        if self.execution_requested:
            raise ValueError("public code analysis cannot execute repository code")


@dataclass(frozen=True)
class CodeAnalysisResult:
    schema_version: str
    repository: str
    revision: str
    operation: CodeAnalysisOperation
    executable: bool
    findings: tuple[str, ...] = ()
    candidate_patch_digest: str | None = None
    redacted_secret_count: int = 0
    provenance_fingerprint: str = ""

    def validate(self) -> None:
        if self.schema_version != CODE_ANALYSIS_CONTRACT_VERSION:
            raise ValueError("unsupported code-analysis contract version")
        if not self.repository.strip() or not self.revision.strip():
            raise ValueError("repository and revision are required")
        if self.executable:
            raise ValueError("public Foundation code analysis result cannot authorize execution")
        if self.redacted_secret_count < 0:
            raise ValueError("redacted_secret_count must be non-negative")
        if self.candidate_patch_digest is not None and len(self.candidate_patch_digest) != 64:
            raise ValueError("candidate_patch_digest must be SHA-256")


def redact_repository_secrets(text: str) -> tuple[str, int]:
    if not isinstance(text, str):
        raise TypeError("repository content must be text")
    matches = list(_SECRET_RE.finditer(text))
    redacted = _SECRET_RE.sub(lambda m: m.group(1) + "=<REDACTED>", text)
    return redacted, len(matches)


def patch_digest(patch: str) -> str:
    if not isinstance(patch, str):
        raise TypeError("patch must be text")
    return hashlib.sha256(patch.encode("utf-8")).hexdigest()
