from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    enabled: bool = True
    description: str = ""
