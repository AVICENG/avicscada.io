"""Trend IQ3 read-only integration profile and catalog orchestration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bacnet_ip import BacnetObjectIdentifier, BacnetProtocolError
from .bacnet_properties import BacnetObjectReader, BacnetObjectSnapshot, trend_iq3_role


@dataclass(frozen=True)
class TrendIQ3Profile:
    """Known test target; BACnet instance IDs are discovered, never guessed."""
    device_instance: int = 1001
    expected_binary_inputs: int = 1
    expected_analog_outputs: int = 2
    expected_schedules: int = 2
    physical_input_labels: tuple[str, ...] = ("I1",)
    analog_output_labels: tuple[str, ...] = ("D1", "D2")
    schedule_labels: tuple[str, ...] = ("Z1", "Z2")
    read_only: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.device_instance <= 4_194_302:
            raise ValueError("invalid BACnet Device Instance")
        if not self.read_only:
            raise ValueError("Trend IQ3 onboarding profile is read-only")


@dataclass(frozen=True)
class TrendIQ3Catalog:
    device_instance: int
    objects: tuple[BacnetObjectIdentifier, ...]
    snapshots: tuple[BacnetObjectSnapshot, ...]
    counts: dict[str, int]
    expected_counts_match: bool
    warnings: tuple[str, ...] = ()

    @property
    def complete_reads(self) -> int:
        return sum(1 for item in self.snapshots if item.quality != "unknown")


class TrendIQ3Integration:
    """Orchestrates Object_List + property reads without any write service."""
    def __init__(self, client: Any, profile: TrendIQ3Profile | None = None,
                 reader: BacnetObjectReader | None = None):
        self.client = client
        self.profile = profile or TrendIQ3Profile()
        self.reader = reader or BacnetObjectReader(client)

    def inspect(self, address: tuple[str, int], *, max_objects: int = 4096) -> TrendIQ3Catalog:
        objects = self.client.read_object_list(address, self.profile.device_instance,
                                               max_objects=max_objects)
        relevant = tuple(obj for obj in objects if obj.object_type in (1, 3, 17))
        counts = {
            "binary_input": sum(obj.object_type == 3 for obj in relevant),
            "analog_output": sum(obj.object_type == 1 for obj in relevant),
            "schedule": sum(obj.object_type == 17 for obj in relevant),
        }
        expected = {
            "binary_input": self.profile.expected_binary_inputs,
            "analog_output": self.profile.expected_analog_outputs,
            "schedule": self.profile.expected_schedules,
        }
        warnings = []
        for key, value in expected.items():
            if counts[key] != value:
                warnings.append(f"{key}: expected {value}, discovered {counts[key]}")
        snapshots = tuple(self.reader.read_catalog(address, self.profile.device_instance,
                                                   list(relevant)))
        return TrendIQ3Catalog(self.profile.device_instance, relevant, snapshots,
                               counts, not warnings, tuple(warnings))

    @staticmethod
    def classify(obj: BacnetObjectIdentifier) -> str:
        return trend_iq3_role(obj)
