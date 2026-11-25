"""Named permission policy for AVIC graphics and equipment operations.

Authentication passwords establish identity; role permissions and explicit resource
scopes decide what the authenticated principal may do.
"""
from __future__ import annotations

from avic_core.security.rbac import AuthorizationService, Principal, Scope


PERMISSIONS = {
    "graphics.read": "Просмотр мнемосхем",
    "graphics.configure": "Изменение мнемосхем",
    "graphics.binding.configure": "Создание и изменение привязок",
    "graphics.publish": "Публикация мнемосхем",
    "equipment.command.start": "Запуск оборудования",
    "equipment.command.stop": "Остановка оборудования",
    "equipment.manual_mode": "Перевод оборудования в ручной режим",
    "setpoint.write": "Изменение уставок",
    "alarm.acknowledge": "Подтверждение аварий",
    "schedule.configure": "Изменение расписаний",
    "logic.edit": "Изменение алгоритмов",
    "logic.deploy": "Публикация алгоритмов",
    "user.manage": "Управление пользователями",
    "role.assign": "Назначение ролей",
    "security.configure": "Настройка безопасности",
}


class GraphicsSecurityPolicy:
    """Fail-closed station-scoped authorization facade used by graphics/API adapters."""
    def __init__(self, authorization: AuthorizationService | None = None):
        self.authorization = authorization or AuthorizationService()

    def require(self, principal: Principal, permission_id: str, station_id: str) -> None:
        if permission_id not in PERMISSIONS:
            raise ValueError(f"Неизвестное разрешение AVIC: {permission_id}")
        self.authorization.require(principal, permission_id, scope=Scope.STATION, station_id=station_id)

    def require_graphics_read(self, principal: Principal, station_id: str) -> None:
        self.require(principal, "graphics.read", station_id)

    def require_graphics_configure(self, principal: Principal, station_id: str) -> None:
        self.require(principal, "graphics.configure", station_id)

    def require_binding_configure(self, principal: Principal, station_id: str) -> None:
        self.require(principal, "graphics.binding.configure", station_id)

    def require_publish(self, principal: Principal, station_id: str) -> None:
        self.require(principal, "graphics.publish", station_id)

    def require_equipment_command(self, principal: Principal, station_id: str, *, action: str) -> None:
        if action not in {"start", "stop"}:
            raise ValueError("Поддерживаются только явные команды start/stop")
        self.require(principal, f"equipment.command.{action}", station_id)

    def require_setpoint_write(self, principal: Principal, station_id: str) -> None:
        self.require(principal, "setpoint.write", station_id)
