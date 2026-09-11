from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    """Canonical capability state used by runtime and registry code."""

    name: str
    enabled: bool = True
    description: str = ""
    free_eligible: bool = True
    daily_limit: int | None = None
    used_today: int = 0

    @property
    def remaining_today(self) -> int | None:
        if self.daily_limit is None:
            return None
        return max(0, self.daily_limit - self.used_today)

    def usable(self) -> bool:
        remaining = self.remaining_today
        return self.enabled and self.free_eligible and (remaining is None or remaining > 0)
