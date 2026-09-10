from dataclasses import dataclass
@dataclass(frozen=True)
class ProviderCapability: provider:str; capability:str; enabled:bool=True; free_eligible:bool=True; priority:int=100
class ProviderRegistry:
    def __init__(self): self._items=[]
    def register(self,x): self._items.append(x)
    def eligible(self,capability,free_only=True): return sorted([x for x in self._items if x.enabled and x.capability==capability and (not free_only or x.free_eligible)],key=lambda x:x.priority)
    def best(self,capability,free_only=True):
        items=self.eligible(capability,free_only); return items[0] if items else None
registry=ProviderRegistry()
