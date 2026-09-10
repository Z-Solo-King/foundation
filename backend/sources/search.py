"""Provider-neutral search contract.

No provider is hard-coded as free. A runtime adapter must receive explicit
free-eligibility, pricing verification, and no-overage authorization before it
may execute.
"""

from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    snippet: str
    source_family: str


@dataclass(frozen=True)
class SearchAuthorization:
    provider: str
    free_eligible: bool
    pricing_verified: bool
    no_overage: bool

    def validate(self):
        if not self.free_eligible:
            raise PermissionError("search provider is not free-eligible")
        if not self.pricing_verified:
            raise PermissionError("search provider pricing is not verified")
        if not self.no_overage:
            raise PermissionError("search provider has no-overage protection disabled")


SearchFn = Callable[[str, int], Awaitable[list[SearchResult]]]


async def search(query: str, limit: int, authorization: SearchAuthorization, implementation: SearchFn) -> list[SearchResult]:
    if not query.strip():
        raise ValueError("search query must not be empty")
    if limit < 1:
        raise ValueError("search limit must be positive")
    authorization.validate()
    return await implementation(query, limit)
