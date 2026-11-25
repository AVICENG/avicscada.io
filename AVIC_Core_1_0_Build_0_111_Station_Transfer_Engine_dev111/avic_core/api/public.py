from __future__ import annotations
from dataclasses import dataclass
from avic_core.runtime.manager import RuntimeManager, RuntimeState
from avic_core.security.rbac import AuthorizationService, Principal, Scope

@dataclass(frozen=True)
class StationRuntimeView:
    station_id: str
    state: str
    generation: int
    last_error: str | None

class CorePublicAPI:
    """Stable, versioned service boundary for UI, SDKs and future AI assistants."""
    api_version = "1.0"
    def __init__(self, runtimes: RuntimeManager, authorization: AuthorizationService):
        self._runtimes = runtimes
        self._authorization = authorization

    def get_station_runtime(self, principal: Principal, station_id: str) -> StationRuntimeView:
        self._authorization.require(principal, "station.read", scope=Scope.STATION, station_id=station_id)
        status = self._runtimes.get(station_id)
        return StationRuntimeView(status.station_id, status.state.value, status.generation, status.last_error)

    def start_station(self, principal: Principal, station_id: str) -> StationRuntimeView:
        self._authorization.require(principal, "station.start", scope=Scope.STATION, station_id=station_id)
        status = self._runtimes.start(station_id)
        return StationRuntimeView(status.station_id, status.state.value, status.generation, status.last_error)

    def stop_station(self, principal: Principal, station_id: str) -> StationRuntimeView:
        self._authorization.require(principal, "station.stop", scope=Scope.STATION, station_id=station_id)
        status = self._runtimes.stop(station_id)
        return StationRuntimeView(status.station_id, status.state.value, status.generation, status.last_error)
