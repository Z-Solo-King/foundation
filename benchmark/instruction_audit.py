"""Deterministic audit helpers for agent instruction and skill files."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence

@dataclass(frozen=True, slots=True)
class InstructionFinding:
    kind: str
    document: str
    line: int
    detail: str

def _normalized(line: str) -> str:
    text = line.strip().lower()
    while text.startswith("-") or text.startswith("*"):
        text = text[1:].strip()
    return " ".join(text.split())

def audit_instruction_documents(documents: Mapping[str, str], *, deprecated_terms: Sequence[str] = ()) -> list[InstructionFinding]:
    findings: list[InstructionFinding] = []
    seen: dict[str, tuple[str, int]] = {}
    directives: defaultdict[str, list[tuple[str, int, bool]]] = defaultdict(list)
    for document, content in sorted(documents.items()):
        for line_number, raw in enumerate(content.splitlines(), 1):
            normalized = _normalized(raw)
            if not normalized or normalized.startswith("```"):
                continue
            if len(normalized) >= 24:
                prior = seen.get(normalized)
                if prior and prior[0] != document:
                    findings.append(InstructionFinding("duplicate", document, line_number, f"matches {prior[0]}:{prior[1]}"))
                else:
                    seen[normalized] = (document, line_number)
            marker = "must not "
            if marker in normalized:
                directives[normalized.split(marker, 1)[1]].append((document, line_number, False))
            elif "must " in normalized:
                directives[normalized.split("must ", 1)[1]].append((document, line_number, True))
            for term in deprecated_terms:
                if term.lower() in normalized:
                    findings.append(InstructionFinding("stale_term", document, line_number, term))
    for subject, entries in directives.items():
        if {entry[2] for entry in entries} == {True, False}:
            for document, line_number, _allowed in entries:
                findings.append(InstructionFinding("conflict", document, line_number, f"must/must-not conflict for: {subject}"))
    return sorted(findings, key=lambda item: (item.document, item.line, item.kind))

def audit_instruction_files(paths: Sequence[str], *, deprecated_terms: Sequence[str] = ()) -> list[InstructionFinding]:
    documents: dict[str, str] = {}
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                documents[path] = handle.read()
        except FileNotFoundError:
            continue
    return audit_instruction_documents(documents, deprecated_terms=deprecated_terms)
