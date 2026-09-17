from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceTier(str, Enum):
    """Evidence strength of a benchmark execution environment."""

    DETERMINISTIC_CONTRACT = "deterministic_contract"
    SIMULATED_PROVIDER = "simulated_provider"
    LIVE_SOURCE_ACQUISITION = "live_source_acquisition"
    LIVE_PROVIDER = "live_provider"
    INTEGRATION_RUNTIME = "integration_runtime"
    PRODUCTION = "production"


_ORDER = {
    EvidenceTier.DETERMINISTIC_CONTRACT: 0,
    EvidenceTier.SIMULATED_PROVIDER: 1,
    EvidenceTier.LIVE_SOURCE_ACQUISITION: 2,
    EvidenceTier.LIVE_PROVIDER: 3,
    EvidenceTier.INTEGRATION_RUNTIME: 4,
    EvidenceTier.PRODUCTION: 5,
}


@dataclass(frozen=True)
class EvidenceTierContract:
    tier: EvidenceTier

    @property
    def rank(self) -> int:
        return _ORDER[self.tier]

    @property
    def provider_execution(self) -> str:
        if self.tier in {
            EvidenceTier.DETERMINISTIC_CONTRACT,
            EvidenceTier.SIMULATED_PROVIDER,
            EvidenceTier.LIVE_SOURCE_ACQUISITION,
        }:
            return "not_live"
        return "live"

    @property
    def source_acquisition(self) -> str:
        if self.tier is EvidenceTier.DETERMINISTIC_CONTRACT:
            return "not_executed"
        if self.tier is EvidenceTier.SIMULATED_PROVIDER:
            return "simulated"
        return "live"

    @property
    def integration_execution(self) -> bool:
        return self.rank >= _ORDER[EvidenceTier.INTEGRATION_RUNTIME]

    @property
    def production_execution(self) -> bool:
        return self.tier is EvidenceTier.PRODUCTION

    def allows(self, claim: str) -> bool:
        """Return whether this benchmark tier may support the named claim class."""
        normalized = claim.strip().lower().replace("-", "_")
        if normalized in {"deterministic_contract", "contract_coverage", "benchmark_regression"}:
            return True
        if normalized in {"simulated_provider", "mocked_provider"}:
            return self.rank >= _ORDER[EvidenceTier.SIMULATED_PROVIDER]
        if normalized in {"live_source_acquisition", "source_retrieval", "transport"}:
            return self.rank >= _ORDER[EvidenceTier.LIVE_SOURCE_ACQUISITION]
        if normalized in {"live_provider", "provider_availability", "provider_latency", "provider_fallback"}:
            return self.rank >= _ORDER[EvidenceTier.LIVE_PROVIDER]
        if normalized in {"integration_runtime", "end_to_end_runtime"}:
            return self.rank >= _ORDER[EvidenceTier.INTEGRATION_RUNTIME]
        if normalized in {"production", "production_readiness", "production_capability"}:
            return self.production_execution
        raise ValueError(f"unknown benchmark claim class: {claim}")

    def assert_allows(self, *claims: str) -> None:
        blocked = [claim for claim in claims if not self.allows(claim)]
        if blocked:
            raise ValueError(
                f"evidence tier {self.tier.value!r} cannot support claims: {', '.join(blocked)}"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "tier": self.tier.value,
            "rank": self.rank,
            "provider_execution": self.provider_execution,
            "source_acquisition": self.source_acquisition,
            "integration_execution": self.integration_execution,
            "production_execution": self.production_execution,
            "production_readiness_claim_allowed": self.production_execution,
            "claim_policy": {
                "contract_coverage": self.allows("contract_coverage"),
                "simulated_provider": self.allows("simulated_provider"),
                "live_source_acquisition": self.allows("live_source_acquisition"),
                "live_provider": self.allows("live_provider"),
                "integration_runtime": self.allows("integration_runtime"),
                "production": self.allows("production"),
            },
        }


def parse_evidence_tier(value: str) -> EvidenceTierContract:
    try:
        tier = EvidenceTier(value.strip().lower())
    except ValueError as exc:
        supported = ", ".join(item.value for item in EvidenceTier)
        raise ValueError(f"unsupported evidence tier {value!r}; expected one of: {supported}") from exc
    return EvidenceTierContract(tier)
