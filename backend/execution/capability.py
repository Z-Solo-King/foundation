"""Compatibility exports for the canonical capability model and registry."""

from backend.capabilities.model import Capability
from backend.capabilities.registry import CapabilityRegistry

CapabilityState = Capability

__all__ = ["CapabilityState", "CapabilityRegistry"]
