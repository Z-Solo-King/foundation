"""HTTP request/response models."""

from dataclasses import dataclass, field
from typing import Any, Literal


MAX_RESEARCH_SOURCES = 500
MAX_RESEARCH_EVIDENCE_ITEMS = 5_000
MAX_SOURCE_URL_LENGTH = 8_192
MAX_RESEARCH_QUESTION_LENGTH = 16_384
MAX_METADATA_FIELDS = 32
MAX_METADATA_KEY_LENGTH = 128
MAX_METADATA_VALUE_LENGTH = 4_096
MAX_HISTORY_TURNS = 20
MAX_HISTORY_TEXT_LENGTH = 12_000
MAX_HISTORY_TOTAL_TEXT_LENGTH = 100_000
MAX_CHAT_INPUT_RECORDS = 200
MAX_CHAT_RECORD_FIELDS = 64


@dataclass(frozen=True)
class ResearchRequest:
    question: str
    depth: Literal["quick", "standard", "deep"] | None = None
    require_citations: bool = True
    max_sources: int = 20
    max_evidence_items: int = 100
    strict_zero_cost_only: bool = True
    source_urls: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question required and must not be empty")
        if len(self.question) > MAX_RESEARCH_QUESTION_LENGTH:
            raise ValueError("question exceeds the supported length")
        if not isinstance(self.max_sources, int) or isinstance(self.max_sources, bool):
            raise ValueError("max_sources must be an integer")
        if not isinstance(self.max_evidence_items, int) or isinstance(self.max_evidence_items, bool):
            raise ValueError("max_evidence_items must be an integer")
        if self.max_sources < 1 or self.max_evidence_items < 1:
            raise ValueError("budgets must be positive")
        if self.max_sources > MAX_RESEARCH_SOURCES:
            raise ValueError("max_sources exceeds the supported safety ceiling")
        if self.max_evidence_items > MAX_RESEARCH_EVIDENCE_ITEMS:
            raise ValueError("max_evidence_items exceeds the supported safety ceiling")
        if not self.strict_zero_cost_only:
            raise ValueError("strict $0 cost mode is mandatory: strict_zero_cost_only must be true")
        if len(self.source_urls) > self.max_sources:
            raise ValueError("source_urls exceeds max_sources")
        for url in self.source_urls:
            if not isinstance(url, str) or not url.strip():
                raise ValueError("source_urls entries must be non-empty strings")
            if len(url) > MAX_SOURCE_URL_LENGTH:
                raise ValueError("source URL exceeds the supported length")


@dataclass(frozen=True)
class ChatRequest:
    chat_id: str
    request_id: str
    message: str
    mode: Literal["chat"] = "chat"
    strict_zero_cost_only: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
    history: tuple[dict[str, str], ...] = ()
    operation: str | None = None
    input_records: Any = ()

    def validate(self) -> None:
        if not self.chat_id.strip():
            raise ValueError("chat_id required and must not be empty")
        if not self.request_id.strip():
            raise ValueError("request_id required and must not be empty")
        if not self.message.strip():
            raise ValueError("message required and must not be empty")
        if len(self.message) > 16_384:
            raise ValueError("message exceeds the supported length")
        if self.mode != "chat":
            raise ValueError("Heroic AI public chat contract accepts mode=chat only")
        if not self.strict_zero_cost_only:
            raise ValueError("strict $0 cost mode is mandatory: strict_zero_cost_only must be true")
        if len(self.metadata) > MAX_METADATA_FIELDS:
            raise ValueError("metadata exceeds the supported field count")
        for key, value in self.metadata.items():
            if not isinstance(key, str) or len(key) > MAX_METADATA_KEY_LENGTH:
                raise ValueError("metadata key exceeds the supported length")
            if not isinstance(value, str) or len(value) > MAX_METADATA_VALUE_LENGTH:
                raise ValueError("metadata value exceeds the supported length")
        if self.operation is not None:
            allowed_operations = {
                "extract",
                "map",
                "extract_and_map",
                "image_analyze",
                "platform_access",
                "knowledge",
                "research",
                "infrastructure_verify",
            }
            if not isinstance(self.operation, str) or self.operation not in allowed_operations:
                raise ValueError("unsupported chat operation")
        if self.input_records not in ((), None):
            if not isinstance(self.input_records, (list, tuple)):
                raise ValueError("input_records must be a list or tuple")
            if len(self.input_records) > MAX_CHAT_INPUT_RECORDS:
                raise ValueError("input_records exceeds the supported record count")
            for record in self.input_records:
                if not isinstance(record, dict):
                    raise ValueError("input_records entries must be objects")
                if len(record) > MAX_CHAT_RECORD_FIELDS:
                    raise ValueError("input_record exceeds the supported field count")
        if len(self.history) > MAX_HISTORY_TURNS:
            raise ValueError("history exceeds the supported turn count")
        total_history_text = 0
        for turn in self.history:
            if not isinstance(turn, dict):
                raise ValueError("history entries must be objects")
            if turn.get("role") not in {"user", "assistant"}:
                raise ValueError("history role must be user or assistant")
            text = str(turn.get("text", ""))
            if not text.strip():
                raise ValueError("history text must not be empty")
            if len(text) > MAX_HISTORY_TEXT_LENGTH:
                raise ValueError("history text exceeds the supported length")
            total_history_text += len(text)
        if total_history_text > MAX_HISTORY_TOTAL_TEXT_LENGTH:
            raise ValueError("history exceeds the supported aggregate text length")


@dataclass(frozen=True)
class APIResponse:
    ok: bool
    error: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
