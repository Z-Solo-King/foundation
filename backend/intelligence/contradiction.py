from dataclasses import dataclass


@dataclass(frozen=True)
class Contradiction:
    claim_a: str
    claim_b: str
    reason: str


def detect_contradiction(claim_a: str, claim_b: str) -> Contradiction | None:
    a = claim_a.strip().lower()
    b = claim_b.strip().lower()
    if not a or not b or a == b:
        return None
    pairs = {
        ("true", "false"),
        ("yes", "no"),
        ("enabled", "disabled"),
        ("available", "unavailable"),
    }
    wa, wb = set(a.split()), set(b.split())
    for pos, neg in pairs:
        if pos in wa and neg in wb:
            return Contradiction(claim_a, claim_b, f"opposing marker: {pos}/{neg}")
    if a.startswith("not ") and a[4:] == b:
        return Contradiction(claim_a, claim_b, "explicit negation")
    if b.startswith("not ") and b[4:] == a:
        return Contradiction(claim_a, claim_b, "explicit negation")
    return None
