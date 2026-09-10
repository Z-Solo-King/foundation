from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ResearchContract:
    question: str
    depth: Literal["quick", "standard", "deep"] = "standard"
    require_citations: bool = True
