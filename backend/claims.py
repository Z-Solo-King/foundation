from dataclasses import dataclass


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
