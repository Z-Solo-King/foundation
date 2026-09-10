from dataclasses import dataclass


@dataclass(frozen=True)
class Contradiction:
    claim_a: str
    claim_b: str
    reason: str


def detect_contradiction(claim_a: str, claim_b: str):
    a = claim_a.strip().lower()
    b = claim_b.strip().lower()

    if not a or not b or a == b:
        return None

    for positive, negative in (
        ("true", "false"),
        ("yes", "no"),
        ("enabled", "disabled"),
        ("available", "unavailable"),
    ):
        if positive in a.split() and negative in b.split():
            return Contradiction(claim_a, claim_b, f"opposing marker: {positive}/{negative}")
        if negative in a.split() and positive in b.split():
            return Contradiction(claim_a, claim_b, f"opposing marker: {positive}/{negative}")

    if a.startswith("not ") and a[4:] == b:
        return Contradiction(claim_a, claim_b, "explicit negation")
    if b.startswith("not ") and b[4:] == a:
        return Contradiction(claim_a, claim_b, "explicit negation")

    return None
