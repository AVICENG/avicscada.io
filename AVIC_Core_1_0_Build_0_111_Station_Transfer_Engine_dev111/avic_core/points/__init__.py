"""Unified live point runtime shared by protocol drivers and AVIC consumers."""
from .runtime import PointRuntimeService, PointRuntimeValue

__all__ = ["PointRuntimeService", "PointRuntimeValue"]
