from __future__ import annotations

from pathlib import Path
import ipaddress
import re
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from tempfile import gettempdir
import os
from urllib.parse import urlsplit
import shutil
import tempfile
from uuid import uuid4
from time import monotonic

from avic_core.application.container import CoreApplication
from avic_core.transfer import StationTransferError
from avic_core.repository.sqlite_repository import ConcurrencyConflict, EntityNotFound
from avic_core.domain.models import Point, PointQuality, PhysicalNetwork, ProtocolChannel
from avic_core.network.bacnet_ip import BacnetObjectIdentifier
from avic_core.ui.project_station import ProjectStationService
from avic_core.ui.device_import import DeviceImportService
from avic_core.ui.protocol_point_import import ProtocolDeviceImportService
from avic_core.ui.engineering_tree import EngineeringTreeService
from avic_core.graphics import GraphicsService
from avic_core.graphics.svg_library import SVG_SYMBOLS, list_symbols, read_symbol_svg
from avic_core.graphics.custom_svg_library import SvgImportError
from avic_core.drivers import DriverManagerService
from avic_core.logic_fbd import FBDService
from avic_core.runtime.fbd_execution import FBDExecutionService
from avic_core.logic_fbd_studio import FBDStudioService
from avic_core.engineering.workflow import EngineeringWorkflowService
from avic_core.web_pages import WebPagesService
from avic_core.ui.drafts import EngineeringDraftStore, DraftError, DraftConflict, DraftNotFound
from avic_core.commands import CommandManagerService, CommandRejected
from avic_core.scheduling import ScheduleConflict, ScheduleError, ScheduleNotFound
from fastapi.responses import HTMLResponse, Response
from fastapi.encoders import jsonable_encoder
from avic_core.network import (BacnetIpNetworkConfig, BacnetIpClient, DiscoveryPolicy, ModbusTcpClient, decode_registers, DeviceIdentityResolver, BacnetDeviceInspector)
from avic_core.network.interfaces import list_ipv4_interfaces, get_interface
from avic_core.network import DiscoveryHistory, NetworkPlan, assess_deployment_binding, ping_ipv4

_UI_DIR = Path(__file__).with_name("static")

# This is the product navigation contract, not a claim that every workspace is implemented.
WORKSPACES = [
    ("dashboard", "Главная", "Общее состояние инженерной среды и быстрые сценарии", "⌂", "implemented"),
    ("projects", "Проекты и объекты", "Иерархия Company → Site → Building → Project → Station", "▣", "partial"),
    ("stations", "Станции", "Независимые конфигурации, версии и жизненный цикл", "▤", "partial"),
    ("station-transfer", "Перенос станций", "Экспорт, проверка, перенос и безопасное клонирование", "⇄", "implemented"),
    ("equipment", "Оборудование", "Системы, установки, агрегаты и паспорта оборудования", "▦", "planned"),
    ("documents", "Документы и AI-анализ", "Реестр, ревизии, извлечение данных и доказательные замечания", "▧", "designed"),
    ("network", "Сети и топология", "Сегменты, интерфейсы, шлюзы и карта связности", "⌘", "partial"),
    ("devices", "Устройства и Discovery", "Безопасное обнаружение и инвентаризация контроллеров", "▥", "partial"),
    ("points", "Точки и Point Manager", "Каталог, фильтры, классификация, проверка и импорт", "⌗", "partial"),
    ("drivers", "Драйверы", "BACnet, Modbus и управление конфигурациями драйверов", "⇄", "partial"),
    ("driver-sdk", "Driver SDK", "Контракты, шаблоны, тестирование и упаковка драйверов", "⌘", "planned"),
    ("modules", "Модули и библиотеки", "Плагины, блоки, символы, версии и совместимость", "▧", "partial"),
    ("resources", "Ресурсы", "Файлы, каталоги, ссылки, шаблоны и пространства ресурсов", "▤", "planned"),
    ("graphics", "Мнемосхемы", "Редактор графики, слои, привязки и динамические состояния", "▱", "partial"),
    ("web-pages", "Web Application · Page Builder", "Дерево страниц, визуальный редактор, ресурсы станции, привязки точек и публикация", "▤", "partial"),
    ("symbols", "SVG-библиотека", "Локальные SVG-символы HVAC/P&ID, каталог, поиск и вставка в Graphics Editor", "◇", "implemented"),
    ("logic", "FBD / Logic", "Редактор блок-схем, портовые связи, проверка типов и офлайн-симуляция", "⌁", "partial"),
    ("simulation", "Симуляция и тесты", "Offline Simulation, Watch, сценарии и регрессионные тесты", "▷", "planned"),
    ("properties", "Свойства и связи", "Контекстный Property Inspector и граф связей", "☷", "partial"),
    ("alarms", "Аварии", "Классы, приоритеты, подтверждения и жизненный цикл", "⚑", "partial"),
    ("events", "Журнал событий", "Операционные события станции, сети и сервисов", "≡", "implemented"),
    ("history", "История и тренды", "Архивы точек, качество, запросы и rollup", "⌁", "implemented"),
    ("analytics", "Analytics", "Теги, иерархии, агрегирование и стратегии пропусков", "∑", "partial"),
    ("notifications", "Уведомления", "Маршруты получателей и очередь доставки", "✉", "partial"),
    ("cleanup", "Очистка базы точек", "Зависимости, предварительная проверка и безопасное удаление", "⌫", "partial"),
    ("signature", "Электронное согласование", "Причины, подписи и двойное подтверждение критичных операций", "✎", "interface"),
    ("trends", "Архивы и тренды", "История, графики, агрегаты, retention и сравнение", "⌁", "partial"),
    ("schedules", "Расписания", "Календарные графики, исключения и расписания оборудования", "◷", "partial"),
    ("commands", "Команды и управление", "Приоритеты, арбитраж, подтверждения и read-back", "⇧", "partial"),
    ("quality", "Качество сигналов", "Quality, stale data, reliability и диагностика источников", "◉", "partial"),
    ("commissioning", "Пусконаладка", "Пошаговые проверки, I/O-тесты и протоколы", "✓", "partial"),
    ("service", "Сервис и обслуживание", "Диагностика, заявки, обслуживание и история оборудования", "⚒", "partial"),
    ("changes", "Управление изменениями", "Diff, согласование, применение и откат конфигураций", "⇆", "partial"),
    ("runtime", "Station Runtime", "Состояние, workers, scheduler, watchdog и автономность", "◉", "partial"),
    ("supervisor", "Supervisor", "Несколько объектов, глобальные аварии и обзор станций", "▦", "partial"),
    ("sites", "Сеть станций", "Inter-SCADA, peer links и распределённые площадки", "⌘", "planned"),
    ("mobile", "Mobile и уведомления", "Мобильные рабочие места, Email, Telegram и Push", "▯", "partial"),
    ("ai", "AI Engineering Assistant", "Помощь инженеру, анализ, объяснения и контролируемые предложения", "✳", "partial"),
    ("reports", "Отчёты и протоколы", "Технические отчёты, ведомости, акты и экспорт", "▤", "planned"),
    ("integrations", "Интеграции и API", "Внешние системы, API, шлюзы и SDK", "⇄", "planned"),
    ("security", "Безопасность и доступ", "Пользователи, MFA, RBAC, scopes и сессии", "▣", "partial"),
    ("audit", "Аудит", "История действий, корреляция и проверка целостности", "≡", "partial"),
    ("backup", "Резервирование", "Backup, restore preview, восстановление и DR", "⤓", "partial"),
    ("licensing", "Лицензии", "Host ID, активация, пакеты точек и возможности", "▤", "partial"),
    ("diagnostics", "Диагностика платформы", "Health Center, журналы, фоновые задачи и производительность", "⌁", "partial"),
    ("time", "Время и синхронизация", "Часы станций, NTP и контролируемая BACnet time sync", "◷", "partial"),
    ("iptools", "IP-инструменты", "Безопасная диагностика адресации и доступности сети", "⌘", "partial"),
    ("deployment", "Развёртывание и обновления", "Установка, обновления, миграции и rollback", "⇧", "planned"),
    ("admin", "Администрирование", "Настройки установки, пользователи и системные политики", "⚙", "partial"),
    ("learning", "Обучение и справка", "Пошаговые руководства, учебные проекты и контекстная помощь", "?", "planned"),
]

ROLES = ["Главный инженер", "Инженер", "Пусконаладчик", "Сервисный инженер", "Оператор", "Администратор", "Заказчик / Аудитор"]


class ProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class StationInput(ProjectInput):
    project_id: str


class StationTransferExportInput(BaseModel):
    station_id: str = Field(min_length=1, max_length=80)


class StationTransferStageInput(BaseModel):
    upload_token: str = Field(min_length=32, max_length=32)
    package_id: str = Field(min_length=24, max_length=24)
    acknowledge_unsigned: bool = False


class StationTransferCommitInput(BaseModel):
    stage_token: str = Field(min_length=32, max_length=32)
    package_id: str = Field(min_length=24, max_length=24)
    target_project_id: str = Field(min_length=1, max_length=80)
    mode: str = Field(pattern="^(transfer|clone)$")
    clone_station_name: str | None = Field(default=None, min_length=1, max_length=160)
    confirmation: str = Field(min_length=1, max_length=16)


class BacnetDiscoveryInput(BaseModel):
    network_id: str = Field(min_length=1, max_length=80)
    interface_id: str = Field(min_length=1, max_length=120)
    udp_port: int = Field(default=47808, ge=1, le=65535)
    timeout_seconds: float = Field(default=3.0, ge=1.0, le=10.0)
    low_limit: int | None = Field(default=None, ge=0, le=4194302)
    high_limit: int | None = Field(default=None, ge=0, le=4194302)

class BacnetInspectInput(BaseModel):
    network_id: str = Field(min_length=1, max_length=80)
    interface_id: str = Field(min_length=1, max_length=120)
    address: str
    device_instance: int = Field(ge=0, le=4194302)
    udp_port: int = Field(default=47808, ge=1, le=65535)
    timeout_seconds: float = Field(default=2.0, ge=0.2, le=5.0)
    max_objects: int = Field(default=512, ge=1, le=4096)

class DeviceImportInput(BaseModel):
    station_id: str = Field(min_length=1, max_length=80)
    address: str = Field(min_length=1, max_length=64)
    device_instance: int = Field(ge=0, le=4194302)
    network_id: str = Field(default="workbench-lan", max_length=80)
    interface_id: str = Field(min_length=1, max_length=120)
    selected_native_ids: list[str] | None = None
    import_all: bool = False
    engineering_description: str = Field(default="", max_length=2000)
    timeout_seconds: float = Field(default=2.0, ge=0.2, le=5.0)
    max_objects: int = Field(default=512, ge=1, le=4096)
    udp_port: int = Field(default=47808, ge=1, le=65535)

class DriverInstanceCreateInput(BaseModel):
    driver_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=160)
    config: dict = Field(default_factory=dict)


class DriverStartInput(BaseModel):
    poll_interval_seconds: float | None = Field(default=None, ge=0.1, le=86400)


class DriverStopInput(BaseModel):
    timeout_seconds: float = Field(default=5.0, gt=0, le=60)

class AccessLeaseInput(BaseModel):
    duration_seconds: int = Field(default=300, ge=1, le=900)

class CommandRequestInput(BaseModel):
    point_id: str = Field(min_length=1, max_length=80)
    lease_id: str = Field(min_length=1, max_length=80)
    command: str = Field(pattern="^(START|STOP|start|stop)$")
    reason: str = Field(min_length=1, max_length=500)
    interlock_point_ids: list[str] = Field(default_factory=list, max_length=32)

class SimulatedFeedbackInput(BaseModel):
    value: bool
    quality: str = Field(default="GOOD", pattern="^GOOD$")

class EngineeringDraftInput(BaseModel):
    base_revision: int = Field(default=0, ge=0)
    expected_draft_revision: int = Field(default=0, ge=0)
    content: dict


class GraphicCreateInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    width: int = Field(default=1600, ge=100, le=10000)
    height: int = Field(default=900, ge=100, le=10000)

class GraphicSaveInput(BaseModel):
    expected_revision: int = Field(ge=1)
    elements: list[dict] = Field(max_length=2000)

class SvgImportInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(default="Пользовательские", min_length=1, max_length=80)
    filename: str = Field(min_length=1, max_length=180)
    svg: str = Field(min_length=1, max_length=1_100_000)

class WebNodeCreateInput(BaseModel):
    station_id: str
    name: str = Field(min_length=1, max_length=160)
    kind: str
    parent_id: str | None = None
    slug: str | None = Field(default=None, max_length=80)
    description: str = Field(default="", max_length=2000)

class WebNodeUpdateInput(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    html: str | None = Field(default=None, max_length=1_000_000)
    css: str | None = Field(default=None, max_length=500_000)
    javascript: str | None = Field(default=None, max_length=500_000)
    graphic_ids: list[str] | None = None
    layout: list[dict] | None = None
    navigation_order: int | None = None

class WebNodeMoveInput(BaseModel):
    parent_id: str | None = None

class WebNodeReorderInput(BaseModel):
    direction: str = Field(pattern="^(up|down)$")

class WebPagePublishInput(BaseModel):
    expected_revision: int = Field(ge=1)

class WebPageRollbackInput(WebPagePublishInput):
    target_published_revision: int = Field(ge=1)

class WebGraphicAssignInput(BaseModel):
    expected_revision: int = Field(ge=1)
    graphic_id: str

class ModbusReadInput(BaseModel):
    host: str
    port: int = Field(default=502, ge=1, le=65535)
    unit_id: int = Field(default=1, ge=0, le=247)
    function: int = Field(default=3, ge=3, le=4)
    address: int = Field(ge=0, le=65535)
    count: int = Field(default=1, ge=1, le=125)
    data_type: str | None = None
    byte_order: str = "big"
    word_order: str = "big"
    timeout_seconds: float = Field(default=2.0, ge=0.1, le=10.0)

class PhysicalNetworkInput(BaseModel):
    station_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    addressing_mode: str = "auto"
    interface_id: str | None = Field(default=None, max_length=120)
    station_ipv4: str | None = None
    subnet_cidr: str | None = None
    gateway_ipv4: str | None = None
    dns_servers: list[str] = Field(default_factory=list, max_length=4)
    description: str = Field(default="", max_length=2000)

class NetworkPingInput(BaseModel):
    address: str
    timeout_seconds: float = Field(default=2.0, ge=0.1, le=3.0)

class ProtocolChannelInput(BaseModel):
    station_id: str = Field(min_length=1, max_length=80)
    network_id: str = Field(min_length=1, max_length=80)
    protocol: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)

class ScheduleCreateInput(BaseModel):
    station_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    value_type: str
    timezone: str = "UTC"
    default_value: object = False
    effective_start: str | None = None
    effective_end: str | None = None
    enabled: bool = True

class ScheduleCopyDayInput(BaseModel):
    source_day: int = Field(ge=0, le=6)
    target_days: list[int] = Field(min_length=1, max_length=6)
    expected_revision: int = Field(ge=1)

class ScheduleWeeklyInput(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_minute: int = Field(ge=0, le=1440)
    end_minute: int = Field(ge=0, le=1440)
    value: object
    expected_revision: int | None = Field(default=None, ge=1)

class ScheduleSpecialInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    start_date: str
    end_date: str
    start_minute: int = Field(default=0, ge=0, le=1440)
    end_minute: int = Field(default=1440, ge=0, le=1440)
    priority: int = Field(default=1, ge=1, le=16)
    value: object
    expected_revision: int | None = Field(default=None, ge=1)

class ScheduleOverrideInput(BaseModel):
    value: object
    duration_seconds: int = Field(ge=1, le=604800)
    reason: str = Field(min_length=1, max_length=1000)

class AlarmCreateInput(BaseModel):
    station_id: str
    source_id: str
    alarm_key: str
    name: str
    message: str
    category: str = "CUSTOM"
    priority: int = 3
    metadata: dict = Field(default_factory=dict)

class AlarmAcknowledgeInput(BaseModel):
    actor_id: str = "local-engineer"
    comment: str = ""

class AlarmReturnInput(BaseModel):
    message: str = "Условие аварии нормализовано"
    details: dict = Field(default_factory=dict)

class AlarmNoteInput(BaseModel):
    actor_id: str = Field(default="local-engineer", min_length=1, max_length=160)
    note: str = Field(min_length=1, max_length=4000)

class EventCreateInput(BaseModel):
    event_type: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=4000)
    station_id: str | None = None
    severity: str = "INFO"
    source_id: str | None = None
    actor_id: str | None = None
    correlation_id: str | None = None
    details: dict = Field(default_factory=dict)

class HistoryCreateInput(BaseModel):
    station_id: str
    point_id: str
    value: object
    quality: str = "GOOD"
    recorded_at: str | None = None
    source: str = "manual-import"

class DependencyCreateInput(BaseModel):
    dependent_id: str
    dependency_id: str
    relation_type: str
    station_id: str | None = None
    metadata: dict = Field(default_factory=dict)

class NotificationRouteInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    channel: str
    recipient: str = Field(min_length=1, max_length=512)
    filters: dict = Field(default_factory=dict)
    enabled: bool = True

class NotificationEnqueueInput(BaseModel):
    payload: dict
    event_ref: str | None = None
    route_id: str | None = None

class AnalyticsTagInput(BaseModel):
    point_id: str
    tag: str
    dictionary: str = "AVIC"
    hierarchy_path: str | None = None
    metadata: dict = Field(default_factory=dict)

class TimeStationInput(BaseModel):
    timezone: str = "UTC"
    ntp_enabled: bool = False
    ntp_servers: list[str] = Field(default_factory=list)

class TimeDevicePermissionInput(BaseModel):
    allowed: bool
    approved_by: str = Field(min_length=1)
    reason: str = Field(min_length=1)

class ObjectPatch(BaseModel):
    expected_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    archived: bool | None = None


def create_ui_app(*, title: str = "AVIC Engineering Workbench", data_dir: str | None = None) -> FastAPI:
    """Create the DEV148 local-only Workbench host. Drivers and OT commands remain stopped."""
    app = FastAPI(title=title, version="1.0.0.dev148")
    root = data_dir or os.environ.get("AVIC_DATA_DIR") or os.path.join(os.path.expanduser("~"), ".avic", "data")
    app.state.core = CoreApplication(root)
    app.state.project_station = ProjectStationService(app.state.core)
    app.state.device_import = DeviceImportService(app.state.core)
    app.state.protocol_point_import = ProtocolDeviceImportService(app.state.core)
    app.state.engineering_tree = EngineeringTreeService(app.state.core)
    app.state.graphics = GraphicsService(app.state.core)
    app.state.driver_manager = app.state.core.driver_manager
    app.state.fbd = FBDService(app.state.core)
    app.state.fbd_execution = FBDExecutionService(app.state.core)
    app.state.fbd_studio = FBDStudioService(app.state.core)
    app.state.engineering_workflow = EngineeringWorkflowService(app.state.core)
    app.state.web_pages = WebPagesService(app.state.core)
    app.state.engineering_drafts = EngineeringDraftStore(app.state.core.paths.databases / "engineering_drafts.sqlite3")
    app.state.command_manager = CommandManagerService(app.state.core, app.state.core.paths.databases / "commands.sqlite3")
    app.state.discovery_history = DiscoveryHistory(app.state.core.paths.databases / "discovery_history.sqlite3")
    app.state.station_transfer_tokens = {}
    # Staging tokens are process-local; clean abandoned work from a previous process.
    for transfer_dir in ("station-transfer-inbox", "station-transfer-staging"):
        stale_dir = app.state.core.paths.backups / transfer_dir
        if stale_dir.exists():
            shutil.rmtree(stale_dir, ignore_errors=True)
        stale_dir.mkdir(parents=True, exist_ok=True)

    def require_local_operator(request: Request) -> None:
        # DEV25 mutations are intentionally restricted to loopback until session/RBAC
        # authentication is integrated. Browser role selection is never treated as auth.
        host = request.client.host if request.client else ""
        if host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
            raise HTTPException(status_code=403, detail="Изменение доступно только локальному оператору Workbench")
        origin = request.headers.get("origin")
        if origin:
            parsed_origin = urlsplit(origin)
            if (parsed_origin.scheme not in {"http", "https"}
                    or parsed_origin.hostname not in {"127.0.0.1", "localhost", "::1"}
                    or parsed_origin.username is not None or parsed_origin.password is not None
                    or parsed_origin.path not in {"", "/"} or parsed_origin.query or parsed_origin.fragment):
                raise HTTPException(status_code=403, detail="Недопустимый Origin")

    def expire_station_transfer_tokens() -> None:
        now = monotonic()
        for token, item in list(app.state.station_transfer_tokens.items()):
            if now - item.get("created_at", now) > 900:
                app.state.station_transfer_tokens.pop(token, None)
                item["package_path"].unlink(missing_ok=True)
                if item.get("stage_path") is not None:
                    shutil.rmtree(item["stage_path"], ignore_errors=True)

    def render_workspace(filename: str, active: str) -> str:
        html = (_UI_DIR / filename).read_text(encoding="utf-8")
        nav_items = [
            ("/?page=dashboard", "⌂", "Главная", "home"),
            ("/?page=projects", "▣", "Проекты", "projects"),
            ("/station-transfer", "⇄", "Перенос и клонирование станции", "transfer"),
            ("/?page=network", "⌘", "Сети", "network"),
            ("/?page=devices", "▥", "Устройства и Discovery", "devices"),
            ("/?page=points", "⌗", "Точки", "points"),
            ("/graphics", "▱", "Мнемосхемы", "graphics"),
            ("/logic", "⌁", "FBD / Logic", "logic"),
            ("/repository", "▧", "Репозиторий", "repository"),
            ("/?page=alarms", "⚑", "Аварии и события", "alarms"),
            ("/?page=trends", "▤", "Архивы и тренды", "trends"),
            ("/?page=security", "♙", "Безопасность", "security"),
            ("/?page=diagnostics", "⚙", "Диагностика", "diagnostics"),
        ]
        rail_links = ''.join(
            f'<a class="rail-btn avic-global-rail-link{" active" if key == active else ""}" href="{href}" '
            f'title="{label}" aria-label="{label}" data-rail-page="{key}"'
            f'{" aria-current=page" if key == active else ""}>{icon}</a>'
            for href, icon, label, key in nav_items
        )
        tree_toggle = '<button class="rail-btn avic-global-rail-link" id="avicSharedTreeToggle" type="button" title="Общее инженерное дерево" aria-label="Общее инженерное дерево" aria-expanded="false">☷</button>'
        shared_rail = f'<nav class="avic-global-rail avic-shared-rail" aria-label="Общая навигация AVIC">{tree_toggle}{rail_links}</nav>'
        shared_tree = """<aside id="avic-shared-tree" aria-label="Общее инженерное дерево" hidden>
          <header><strong>Инженерное дерево</strong><button type="button" id="avicSharedTreeRefresh" title="Обновить">↻</button><button type="button" id="avicSharedTreeClose" title="Закрыть">×</button></header>
          <input id="avicSharedTreeSearch" type="search" placeholder="Поиск проектов, устройств и точек">
          <div id="avicSharedTreeContent"><div class="tree-empty">Загрузка дерева…</div></div>
          <footer>Перетащите физическую точку на FBD-доску</footer>
        </aside>
        <style id="avic-shared-tree-style">
          #avic-shared-tree{position:fixed;z-index:10049;left:54px;top:0;bottom:0;width:330px;max-width:calc(100vw - 54px);
            background:#fff;border-right:1px solid #dce5e9;box-shadow:8px 0 24px rgba(20,40,55,.12);display:flex;flex-direction:column;
            color:#243746;font:12px/1.45 "Segoe UI",Arial,sans-serif}
          #avic-shared-tree[hidden]{display:none!important}
          #avic-shared-tree header{height:48px;flex:0 0 48px;display:flex;align-items:center;gap:8px;padding:0 12px;border-bottom:1px solid #e4eaee}
          #avic-shared-tree header strong{flex:1;font-size:13px}
          #avic-shared-tree button{border:1px solid #dce5e9;background:#fff;border-radius:6px;padding:4px 8px;cursor:pointer}
          #avic-shared-tree input{margin:9px 10px;padding:8px;border:1px solid #dce5e9;border-radius:6px;width:calc(100% - 20px);box-sizing:border-box}
          #avicSharedTreeContent{overflow:auto;flex:1;padding:4px 8px 12px}
          #avic-shared-tree details{margin:1px 0 1px 8px}
          #avic-shared-tree summary{cursor:pointer;list-style:none;padding:5px 5px;border-radius:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
          #avic-shared-tree summary:hover,#avic-shared-tree [draggable=true]:hover{background:#f1f6f8}
          #avic-shared-tree summary::-webkit-details-marker{display:none}
          #avic-shared-tree .tree-row{display:flex;align-items:center;gap:6px;padding:4px 5px 4px 18px;margin-left:8px;border-radius:5px;cursor:pointer;min-width:0}
          #avic-shared-tree .tree-row[draggable=true]{cursor:grab}
          #avic-shared-tree .tree-row small{color:#70818d;margin-left:auto;white-space:nowrap}
          #avic-shared-tree .tree-row .row-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
          #avic-shared-tree .tree-empty{padding:12px;color:#71818d}
          #avic-shared-tree footer{padding:9px 12px;border-top:1px solid #e4eaee;color:#71818d;font-size:11px}
          .avic-tree-context{display:none;position:fixed;z-index:10060;min-width:210px;padding:4px;background:#fff;border:1px solid #d7e1e7;border-radius:7px;box-shadow:0 8px 24px rgba(20,40,55,.18)}.avic-tree-context button{display:block;width:100%;text-align:left;border:0;background:#fff;padding:8px 10px;border-radius:5px;color:#334b5e}.avic-tree-context button:hover{background:#eef5f6}
          @media(max-width:620px){#avic-shared-tree{left:46px;width:calc(100vw - 46px)}}
        </style>
        <script id="avic-shared-tree-script">
        (()=>{const $=s=>document.querySelector(s),panel=$('#avic-shared-tree'),toggle=$('#avicSharedTreeToggle'),content=$('#avicSharedTreeContent');
          if(!panel||!toggle||!content)return;let cached=null;
          const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
          const row=(id,name,kind,extra='',drag='')=>`<div class="tree-row" data-kind="${kind}" data-id="${esc(id)}" ${drag} title="${esc(name)}"><span class="point-live-value">${extra}</span><span class="row-name">${esc(name)}</span></div>`;
          function render(data){
            const projects=data.projects||[];
            const projectHtml=projects.map(pr=>{
              const stationHtml=(pr.stations||[]).map(st=>{
                const networkHtml=(st.networks||[]).map(net=>{
                  const channelHtml=(net.channels||[]).map(ch=>{
                    const deviceHtml=(ch.devices||[]).map(dev=>{
                      const points=(dev.points||[]).map(pt=>row(pt.id,pt.name,'physical-point',`${pt.value===null||pt.value===undefined?'—':pt.value}${pt.unit?' '+pt.unit:''} · ${pt.quality||'UNCERTAIN'}`,`draggable="true" data-point-id="${esc(pt.id)}"`)).join('');
                      return `<details><summary>▥ ${esc(dev.name)} <small>${(dev.points||[]).length}</small></summary>${points}</details>`;
                    }).join('');
                    return `<details><summary>◈ ${esc(ch.name)}</summary>${deviceHtml}</details>`;
                  }).join('');
                  return `<details><summary>⌘ ${esc(net.name)}</summary>${channelHtml}</details>`;
                }).join('');
                const fbdHtml=(st.fbd_projects||[]).map(doc=>{
                  const pages=(doc.pages||[]).map(pg=>`<div class="tree-row" data-kind="fbd-page" data-station="${esc(st.id)}" data-document="${esc(doc.id)}" data-page="${esc(pg.id)}"><span>▤</span><span class="row-name">${esc(pg.code)} · ${esc(pg.name)}</span></div>`).join('');
                  const points=(doc.points||[]).map(pt=>row(pt.id,pt.tag||pt.name,'fbd-point',`${pt.value===null||pt.value===undefined?'—':pt.value}${pt.unit?' '+pt.unit:''} · ${pt.quality||'UNCERTAIN'}`,`draggable="true" data-fbd-point-id="${esc(pt.id)}" data-document="${esc(doc.id)}" data-station="${esc(st.id)}"`)).join('');
                  return `<details><summary>⌁ ${esc(doc.name)}</summary><div class="tree-row" data-kind="fbd-open" data-station="${esc(st.id)}" data-document="${esc(doc.id)}"><span>▱</span><span class="row-name">Открыть FBD-проект</span></div>${pages}${points}</details>`;
                }).join('');
                const repository=st.repository||{id:'avic.repository',name:'Репозиторий',children:[]};
                const repoIcon={'WebApplication':'▤','GraphicsRepository':'▱','GraphicsPages':'▧','GraphicsComponents':'◫','GraphicsSymbols':'◇','GraphicsAssets':'▧','GraphicsTemplates':'▦','Documentation':'▥'};
                const repoNode=(node,depth=0)=>{const children=node.children||[];const nodeIcon=node.type==='WebPageNode'?(node.kind==='site'?'▣':node.kind==='folder'?'▰':'▤'):(repoIcon[node.type]||'▫');const suffix=node.type==='WebPageNode'&&node.kind==='page'?(node.published?' · опубликована':' · черновик'):'';const row=`<div class="tree-row repository-child" data-kind="repository-item" data-station="${esc(st.id)}" data-repository-item="${esc(node.id)}" data-section="${esc(node.type)}" title="${esc(node.name)}"><span>${nodeIcon}</span><span class="row-name">${esc(node.name)}</span><small>${suffix}</small></div>`;return children.length?`<details ${depth===0?'open':''}><summary data-kind="repository-item" data-station="${esc(st.id)}" data-repository-item="${esc(node.id)}" data-section="${esc(node.type)}">${nodeIcon} ${esc(node.name)}${suffix}</summary>${children.map(child=>repoNode(child,depth+1)).join('')}</details>`:row;};
                const repositoryHtml=`<details class="repository-branch"><summary data-kind="repository" data-station="${esc(st.id)}" data-repository="${esc(repository.id)}" title="Ресурсы станции"><span>▧ ${esc(repository.name||'Репозиторий')}</span></summary>${(repository.children||[]).map(node=>repoNode(node)).join('')}</details>`;
                return `<details open><summary data-kind="station" data-id="${esc(st.id)}" data-project="${esc(pr.id)}" data-name="${esc(st.name)}">▦ ${esc(st.name)} <small>${st.point_count||0}</small></summary>${networkHtml}${fbdHtml}${repositoryHtml}</details>`;
              }).join('');
              return `<details open><summary data-kind="project" data-id="${esc(pr.id)}" data-name="${esc(pr.name)}">▣ ${esc(pr.name)}</summary>${stationHtml}</details>`;
            }).join('');
            content.innerHTML=`<details open class="tree-root"><summary data-kind="root">⌂ AVIC</summary>${projectHtml||'<div class="tree-empty">Нет проектов. Создайте проект и станцию.</div>'}</details>`;
            content.querySelectorAll('[data-kind="physical-point"]').forEach(el=>{el.addEventListener('dragstart',e=>{e.dataTransfer.setData('point',el.dataset.pointId);e.dataTransfer.effectAllowed='copy'});});
            content.querySelectorAll('[data-kind="fbd-point"]').forEach(el=>{el.addEventListener('dragstart',e=>{e.dataTransfer.setData('fbd-point',el.dataset.fbdPointId);e.dataTransfer.effectAllowed='copy'});});
            content.querySelectorAll('[data-kind="fbd-open"],[data-kind="fbd-page"]').forEach(el=>el.addEventListener('click',()=>{const q=new URLSearchParams({station:el.dataset.station,document:el.dataset.document});if(el.dataset.page)q.set('page',el.dataset.page);location.href='/logic?'+q.toString();}));
            content.querySelectorAll('[data-kind="repository-item"]').forEach(el=>el.addEventListener('click',()=>{const q=new URLSearchParams({station:el.dataset.station,section:el.dataset.section});if(el.dataset.section==='WebPageNode')q.set('node',el.dataset.repositoryItem);location.href='/repository?'+q.toString();}));
            content.querySelectorAll('[data-kind="repository"]').forEach(el=>el.addEventListener('click',()=>{const q=new URLSearchParams({station:el.dataset.station,section:'WebApplication'});location.href='/repository?'+q.toString();}));
          }
          async function api(url,method='GET',body){const r=await fetch(url,{method,headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});const data=await r.json().catch(()=>({}));if(!r.ok)throw Error(data.detail?.message||data.detail||('HTTP '+r.status));return data;}
          async function createProject(){const name=prompt('Название проекта AVIC:');if(!name?.trim())return;await api('/api/projects','POST',{name:name.trim(),description:''});cached=null;await load();}
          async function createStation(projectId){const name=prompt('Название станции:');if(!name?.trim())return;await api('/api/stations','POST',{project_id:projectId,name:name.trim(),description:''});cached=null;await load();}
          async function renameObject(kind,id){const name=prompt('Новое название:');if(!name?.trim())return;const list=await api('/api/projects/tree');const obj=[...(list.projects||[]),...(list.stations||[])].find(x=>x.id===id);if(!obj)throw Error('Объект больше не существует');await api('/api/'+(kind==='project'?'projects':'stations')+'/'+encodeURIComponent(id),'PATCH',{expected_version:obj.version,name:name.trim()});cached=null;await load();}
          function contextMenu(x,y,items){let menu=document.getElementById('avicTreeContext');if(!menu){menu=document.createElement('div');menu.id='avicTreeContext';menu.className='avic-tree-context';document.body.appendChild(menu);}menu.innerHTML=items.map((it,i)=>`<button data-i="${i}">${esc(it.label)}</button>`).join('');menu.style.display='block';menu.style.left='0px';menu.style.top='0px';const r=menu.getBoundingClientRect();menu.style.left=Math.max(4,Math.min(x,innerWidth-r.width-4))+'px';menu.style.top=Math.max(4,Math.min(y,innerHeight-r.height-4))+'px';menu.querySelectorAll('button').forEach(b=>b.onclick=async()=>{menu.style.display='none';try{await items[Number(b.dataset.i)].run();}catch(e){alert('Операция не выполнена: '+e.message);}});}
          content.addEventListener('contextmenu',e=>{const n=e.target.closest('summary[data-kind]');if(!n)return;e.preventDefault();const kind=n.dataset.kind,id=n.dataset.id;const items=kind==='root'?[{label:'Создать проект',run:createProject}]:kind==='project'?[{label:'Создать станцию',run:()=>createStation(id)},{label:'Изменить название проекта',run:()=>renameObject('project',id)}]:kind==='station'?[{label:'Изменить название станции',run:()=>renameObject('station',id)}]:[];if(items.length)contextMenu(e.clientX,e.clientY,items);});
          document.addEventListener('click',e=>{if(!e.target.closest('#avicTreeContext')){const m=document.getElementById('avicTreeContext');if(m)m.style.display='none';}});
          function liveLabel(point){const v=point.value===null||point.value===undefined?'—':point.value;return `${v}${point.unit?' '+point.unit:''} · ${point.quality||'UNCERTAIN'}`}
          async function refreshPointValues(){if(panel.hidden)return;try{const r=await fetch('/api/engineering/tree');if(!r.ok)return;const data=await r.json(),values=new Map();for(const project of data.projects||[])for(const station of project.stations||[]){for(const network of station.networks||[])for(const channel of network.channels||[])for(const device of channel.devices||[])for(const point of device.points||[])values.set(point.id,liveLabel(point));for(const doc of station.fbd_projects||[])for(const point of doc.points||[])values.set(point.id,liveLabel(point));}content.querySelectorAll('[data-kind="physical-point"],[data-kind="fbd-point"]').forEach(el=>{const id=el.dataset.pointId||el.dataset.fbdPointId;const target=el.querySelector('.point-live-value');if(target&&values.has(id))target.textContent=values.get(id);});}catch(_){/* keep last known values visible on transient polling errors */}}
          async function load(){content.innerHTML='<div class="tree-empty">Загрузка дерева…</div>';try{const r=await fetch('/api/engineering/tree');if(!r.ok)throw Error('HTTP '+r.status);cached=await r.json();render(cached);}catch(e){content.innerHTML='<div class="tree-empty">Не удалось загрузить дерево: '+esc(e.message)+'</div>';}}
          document.querySelector('[data-rail-page=\"home\"]')?.addEventListener('contextmenu',e=>{e.preventDefault();contextMenu(e.clientX,e.clientY,[{label:'Создать проект',run:createProject}]);});
          toggle.addEventListener('click',()=>{panel.hidden=!panel.hidden;toggle.setAttribute('aria-expanded',String(!panel.hidden));if(!panel.hidden&&!cached)load();else if(!panel.hidden)refreshPointValues();});
          window.setInterval(refreshPointValues,2000);
          $('#avicSharedTreeRefresh')?.addEventListener('click',load);$('#avicSharedTreeClose')?.addEventListener('click',()=>{panel.hidden=true;toggle.setAttribute('aria-expanded','false');});
          $('#avicSharedTreeSearch')?.addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();content.querySelectorAll('.tree-row,summary').forEach(el=>{const match=el.textContent.toLowerCase().includes(q);el.style.display=!q||match?'':'none';if(q){let d=el.closest('details');while(d){d.open=true;d=d.parentElement.closest('details');}}});});
        })();
        </script>
        """
        styles = """<style id="avic-global-navigation-style">
        .avic-global-rail{position:fixed;z-index:10050;left:0;top:0;bottom:0;width:54px;
          display:flex;flex-direction:column;align-items:center;gap:7px;padding:9px 5px;
          background:#fff;border-right:1px solid #dce5e9;box-shadow:1px 0 3px rgba(25,45,60,.025)}
        .avic-global-rail .rail-btn,.avic-global-rail-link{width:40px;height:40px;flex:0 0 40px;display:grid;
          place-items:center;border:0;border-radius:9px;text-decoration:none;background:transparent;
          color:#526779;font:19px/1 "Segoe UI",Arial,sans-serif;cursor:pointer}
        .avic-global-rail .rail-btn:hover,.avic-global-rail-link:hover{background:#f0f5f6;color:#203b50}
        .avic-global-rail .rail-btn.active,.avic-global-rail-link.active{background:#eaf1f8;color:#145d83;box-shadow:inset 3px 0 #2563b8}
        .avic-workspace-logic,.avic-workspace-pages{margin-left:54px!important;width:calc(100% - 54px)!important}
        .avic-workspace-logic .layout{height:calc(100vh - 105px)!important}
        .avic-workspace-home .app{margin-left:54px!important;width:calc(100% - 54px)!important}
        .avic-workspace-home .layout{grid-template-columns:minmax(300px,1fr)!important}
        .avic-workspace-home .layout>.left{display:none!important}
        .avic-workspace-home .layout>.center{grid-column:1!important}
        .avic-workspace-logic .core-left{display:none!important}
        .avic-workspace-logic .layout{grid-template-columns:minmax(360px,1fr) 300px!important}
        .avic-workspace-logic .center{grid-column:1!important}
        @media(max-width:620px){.avic-global-rail{width:46px;padding:7px 4px}.avic-global-rail .rail-btn,.avic-global-rail-link{width:36px;height:36px;flex-basis:36px}.avic-workspace-logic,.avic-workspace-pages{margin-left:46px!important;width:calc(100% - 46px)!important}}
        </style>"""
        # Remove legacy rails first: every workspace receives the same generated navigation.
        html = re.sub(r'<nav(?=[^>]*class=["\'][^"\']*avic-global-rail)[^>]*>.*?</nav>', '', html,
                      count=1, flags=re.IGNORECASE | re.DOTALL)
        if "</head>" in html:
            html = html.replace("</head>", styles + "</head>", 1)
        body_match = re.search(r"<body[^>]*>", html, flags=re.IGNORECASE)
        if body_match:
            body_tag = body_match.group(0)
            workspace_class = f"avic-workspace-{active}"
            if re.search(r"\bclass=", body_tag, flags=re.IGNORECASE):
                body_tag = re.sub(r"""\bclass=(["\'])(.*?)\1""",
                                  lambda m: f'class={m.group(1)}{m.group(2)} {workspace_class}{m.group(1)}',
                                  body_tag, count=1, flags=re.IGNORECASE)
            else:
                body_tag = body_tag[:-1] + f' class="{workspace_class}">'
            insertion = shared_rail + shared_tree
            html = html[:body_match.start()] + body_tag + insertion + html[body_match.end():]
        if active in {"graphics", "logic", "repository"}:
            html = html.replace("</head>",
                '<script src="/avic-static/save-manager.js" defer></script></head>', 1)
        return html

    @app.get("/avic-static/save-manager.js", include_in_schema=False)
    def engineering_save_manager_script() -> Response:
        source = (_UI_DIR / "save-manager.js").read_text(encoding="utf-8")
        return Response(content=source, media_type="application/javascript",
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> str:
        return render_workspace("index.html", "home")

    @app.get("/pages", response_class=HTMLResponse, include_in_schema=False)
    def legacy_pages_workspace() -> str:
        # Legacy Pages workspace is no longer exposed as the Repository editor.
        return render_workspace("graphics.html", "graphics")

    @app.get("/repository", response_class=HTMLResponse, include_in_schema=False)
    def repository_workspace(section: str | None = None) -> str:
        # Web Application has its own page-authoring workspace; Graphics retains the Core Graphics Workbench.
        if section in {"WebApplication", "WebPageNode"}:
            return render_workspace("repository.html", "repository")
        return render_workspace("graphics.html", "graphics")

    @app.get("/logic", response_class=HTMLResponse, include_in_schema=False)
    def logic_workspace() -> str:
        return render_workspace("logic.html", "logic")

    @app.get("/graphics", response_class=HTMLResponse, include_in_schema=False)
    def graphics_workspace() -> str:
        return render_workspace("graphics.html", "graphics")

    @app.get("/api/stations/{station_id}/web-pages")
    def web_pages_tree(station_id: str) -> dict:
        try: return app.state.web_pages.list_tree(station_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция или узел не найдены") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/web-pages", status_code=201)
    def web_page_create(payload: WebNodeCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.create(payload.station_id,payload.name,payload.kind,payload.parent_id,payload.slug,payload.description)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция или родитель не найдены") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/web-pages/{node_id}")
    def web_page_get(node_id: str) -> dict:
        try: return app.state.web_pages.get(node_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Узел не найден") from exc
        except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail="Некорректный идентификатор узла") from exc

    @app.get("/api/stations/{station_id}/repository-assets")
    def repository_assets(station_id: str) -> dict:
        try: return {"assets": app.state.web_pages.list_assets(station_id)}
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/repository-assets", status_code=201)
    async def repository_asset_upload(station_id: str, request: Request, filename: str) -> dict:
        require_local_operator(request)
        try:
            declared_length = request.headers.get("content-length")
            if declared_length and int(declared_length) > 3 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Размер изображения превышает 3 МБ")
            content = await request.body()
            return app.state.web_pages.create_asset(station_id, filename, request.headers.get("content-type", "").split(";")[0], content)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/repository-assets/{asset_id}")
    def repository_asset_get(asset_id: str, request: Request) -> Response:
        import base64
        try:
            asset = app.state.web_pages.read_asset(asset_id)
            local = request.client.host in {"127.0.0.1", "::1", "localhost", "testclient"} if request.client else False
            referenced = False
            for row in app.state.core.repository.list_records(entity_type="WebPageNode", station_id=asset.station_id):
                node, _ = app.state.web_pages._get(row["entity_id"])
                if node.published and any(block.get("src") == f"/api/repository-assets/{asset.id}" for block in node.published_layout):
                    referenced = True
                    break
            if not local and not referenced:
                raise HTTPException(status_code=404, detail="Ресурс не опубликован")
            return Response(content=base64.b64decode(asset.content_base64), media_type=asset.media_type,
                            headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=3600" if referenced else "no-store"})
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Изображение не найдено") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail="Некорректный идентификатор ресурса") from exc

    @app.post("/api/web-pages/{node_id}/publish")
    def web_page_publish(node_id: str, payload: WebPagePublishInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.publish(node_id, payload.expected_revision)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.post("/api/web-pages/{node_id}/unpublish")
    def web_page_unpublish(node_id: str, payload: WebPagePublishInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.unpublish(node_id, payload.expected_revision)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.post("/api/web-pages/{node_id}/rollback")
    def web_page_rollback(node_id: str, payload: WebPageRollbackInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.rollback_publication(node_id, payload.expected_revision, payload.target_published_revision)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.get("/published/{station_id}/{page_path:path}", response_class=HTMLResponse, include_in_schema=False)
    def published_web_page(station_id: str, page_path: str) -> HTMLResponse:
        import html as html_escape
        try:
            page = app.state.web_pages.published_page(station_id, page_path)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Опубликованная страница не найдена") from exc
        blocks = []
        for block in page["layout"]:
            kind = block.get("type", "text")
            x, y, width, height = (int(block.get(k, d)) for k, d in (("x", 0), ("y", 0), ("width", 280), ("height", 80)))
            style = f"position:absolute;left:{x}px;top:{y}px;width:{width}px;min-height:{height}px;box-sizing:border-box;"
            style += f"color:{block.get('color', '#243746')};background:{block.get('background', 'transparent')};text-align:{block.get('align', 'left')};font-size:{int(block.get('font_size', 16))}px;padding:8px;"
            content = ""
            if kind == "heading": content = f"<h2>{html_escape.escape(str(block.get('text') or block.get('label') or 'Заголовок'))}</h2>"
            elif kind in {"text", "card", "button"}: content = html_escape.escape(str(block.get("text") or block.get("label") or block.get("title") or "Текст"))
            elif kind == "image":
                src = str(block.get("src") or "")
                content = f'<img src="{html_escape.escape(src, quote=True)}" alt="{html_escape.escape(str(block.get("alt") or ""), quote=True)}" style="width:100%;height:100%;object-fit:contain">'
            elif kind == "value":
                point_id = str(block.get("point_id") or "")
                unit = ""
                try:
                    value = app.state.core.point_runtime.read(point_id)
                    unit = value.unit if value.quality == "GOOD" else ""
                    value_text = str(value.value) if value.quality == "GOOD" else f"— ({value.quality})"
                    value_text += (" " + unit) if unit else ""
                except Exception:
                    value_text = "— (BAD)"
                safe_point_id = html_escape.escape(point_id, quote=True)
                content = f'<div><small>{html_escape.escape(str(block.get("label") or "Значение"))}</small><div data-point-id="{safe_point_id}" style="font-size:1.7em;font-weight:650">{html_escape.escape(value_text)}</div></div>'
            elif kind == "divider": content = '<hr style="border:0;border-top:1px solid #9aaab5">'
            elif kind == "graphic":
                gid = str(block.get("graphic_id") or "")
                page_id = str(page.get("id") or "")
                frame_url = f"/published-graphics/{html_escape.escape(station_id, quote=True)}/{html_escape.escape(gid, quote=True)}?page_id={html_escape.escape(page_id, quote=True)}"
                content = (f'<iframe title="Мнемосхема" src="{frame_url}" '
                           'sandbox="allow-scripts allow-same-origin" loading="lazy" '
                           'style="display:block;width:100%;height:100%;min-height:260px;border:0;background:#fff"></iframe>')
            blocks.append(f'<section style="{style}">{content}</section>')
        title = html_escape.escape(page["name"])
        import secrets
        nonce = secrets.token_urlsafe(18)
        live_script = """<script nonce="__NONCE__">
(async()=>{const nodes=[...document.querySelectorAll('[data-point-id]')];const station='__STATION__';async function update(){try{const r=await fetch('/api/engineering/points/runtime?station_id='+encodeURIComponent(station),{cache:'no-store'});if(!r.ok)throw Error('unavailable');const data=await r.json();const values=new Map((data.points||[]).map(p=>[p.point_id,p]));for(const el of nodes){const p=values.get(el.dataset.pointId);if(!p){el.textContent='— (COMM_LOST)';continue}if(String(p.quality).toUpperCase()==='GOOD'){el.textContent=(p.value??'—')+(p.unit?' '+p.unit:'')}else{el.textContent='— ('+String(p.quality||'BAD')+')'}}}catch(_){for(const el of nodes)el.textContent='— (COMM_LOST)'}}await update();setInterval(update,2000)})();
</script>""".replace("__NONCE__", nonce).replace("__STATION__", html_escape.escape(station_id, quote=True))
        document = f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title><style>body{{margin:0;background:#eef3f6;color:#243746;font-family:Segoe UI,Arial,sans-serif}}header{{padding:14px 22px;background:#fff;border-bottom:1px solid #d6e0e6;font-weight:650}}main{{position:relative;min-height:900px;max-width:1600px;margin:18px auto;background:#fff;border:1px solid #d6e0e6;border-radius:10px;overflow:hidden}}</style></head><body><header>{title}</header><main>{''.join(blocks)}</main>{live_script}</body></html>"
        return HTMLResponse(document, headers={"Content-Security-Policy": f"default-src 'self' https: data:; img-src 'self' https: data:; style-src 'unsafe-inline'; script-src 'nonce-{nonce}'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"})

    @app.get("/published-graphics/{station_id}/{document_id}", response_class=HTMLResponse, include_in_schema=False)
    def published_graphic_runtime(station_id: str, document_id: str, page_id: str) -> HTMLResponse:
        """Render a frozen graphics snapshot only when referenced by a published page."""
        import html as html_escape
        import json
        try:
            page_node, _ = app.state.core.repository.get(page_id, __import__("avic_core.web_pages.models", fromlist=["WebPageNode"]).WebPageNode)
            if page_node.station_id != station_id or not page_node.published:
                raise HTTPException(status_code=404, detail="Опубликованная мнемосхема не найдена")
            snapshot = next((item.get("graphic_snapshot") for item in page_node.published_layout
                             if isinstance(item, dict) and item.get("type") == "graphic"
                             and item.get("graphic_id") == document_id), None)
            if not isinstance(snapshot, dict) or snapshot.get("station_id") != station_id:
                raise HTTPException(status_code=404, detail="Мнемосхема отсутствует в опубликованной версии страницы")
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Опубликованная страница не найдена") from exc

        elements = []
        for element in sorted(snapshot.get("elements", []), key=lambda item: (int(item.get("layer", 0)), item.get("id", ""))):
            symbol_key = str(element.get("symbol_key") or "")
            if symbol_key.startswith("custom_"):
                symbol_url = f"/api/graphics/custom-symbols/{html_escape.escape(symbol_key, quote=True)}/svg"
            else:
                symbol_url = f"/api/graphics/library/{html_escape.escape(symbol_key, quote=True)}/svg"
            x, y = float(element.get("x", 0)), float(element.get("y", 0))
            width, height = float(element.get("width", 100)), float(element.get("height", 80))
            rotation = float(element.get("rotation", 0))
            style = (f"left:{x:g}px;top:{y:g}px;width:{width:g}px;height:{height:g}px;"
                     f"z-index:{int(element.get('layer', 0))};transform:rotate({rotation:g}deg)")
            eid = html_escape.escape(str(element.get("id", "")), quote=True)
            label = html_escape.escape(str(element.get("name") or element.get("symbol_name") or ""))
            elements.append(
                f'<div class="graphic-element" data-element-id="{eid}" style="{style}">'
                f'<img class="symbol" src="{symbol_url}" alt="{label}" draggable="false">'
                f'<div class="element-label">{label}</div><div class="binding-values"></div></div>'
            )
        width = max(100, min(10000, int(snapshot.get("width", 1600))))
        height = max(100, min(10000, int(snapshot.get("height", 900))))
        doc_title = html_escape.escape(str(snapshot.get("name") or "Мнемосхема"))
        import secrets
        nonce = secrets.token_urlsafe(18)
        runtime_js = """<script nonce="__NONCE__">
(async()=>{
 const root=document.getElementById('canvas');
 const update=async()=>{
  try{
   const r=await fetch(root.dataset.bindingsUrl,{cache:'no-store'});
   if(!r.ok)throw Error('runtime'); const payload=await r.json();
   const grouped=new Map();
   for(const b of Object.values(payload.bindings||{})){const a=grouped.get(b.element_id)||[];a.push(b);grouped.set(b.element_id,a)}
   for(const el of root.querySelectorAll('[data-element-id]')){
    const rows=grouped.get(el.dataset.elementId)||[]; const values=el.querySelector('.binding-values'); values.replaceChildren();
    let spinning=false;
    for(const b of rows){
      if(b.target_property==='animation' && b.animation_allowed && b.quality==='GOOD')spinning=true;
      if(b.display_text){const line=document.createElement('div');line.className='binding-value '+(b.quality==='GOOD'?'good':'bad');line.textContent=b.display_text;values.appendChild(line)}
      if(b.target_property==='color' && typeof b.value==='string' && /^#[0-9a-fA-F]{6}$/.test(b.value))el.style.setProperty('--binding-color',b.value);
    }
    el.classList.toggle('running',spinning);
   }
  }catch(_){for(const el of root.querySelectorAll('.binding-values')){el.textContent='Нет связи с Point Runtime';el.classList.add('bad')}}
 };
 await update(); window.setInterval(update,2000);
})();
</script>""".replace("__NONCE__", nonce)
        document = ("<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                    f"<title>{doc_title}</title><style>"
                    "*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:auto;background:#f7fafb;color:#263b4a;font:12px Segoe UI,Arial,sans-serif}"
                    f"#canvas{{position:relative;width:{width}px;height:{height}px;min-width:{width}px;min-height:{height}px;background:#fff;overflow:hidden}}"
                    ".graphic-element{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2px;overflow:visible}"
                    ".symbol{width:100%;height:calc(100% - 20px);object-fit:contain;transform-origin:center center}"
                    ".element-label{font-size:11px;text-align:center;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#526879}"
                    ".binding-values{position:absolute;left:50%;top:100%;transform:translateX(-50%);display:flex;flex-direction:column;gap:2px;align-items:center;white-space:nowrap;z-index:5}"
                    ".binding-value{padding:2px 5px;border-radius:4px;background:#edf5f7;font-weight:650;color:#28475a}.binding-value.bad{background:#fff0ef;color:#b33}"
                    ".graphic-element{--binding-color:#168b80}.graphic-element.running .symbol{animation:fan-rotation 1.1s linear infinite;filter:drop-shadow(0 0 2px var(--binding-color))}"
                    "@keyframes fan-rotation{to{transform:rotate(360deg)}}"
                    "</style></head><body>"
                    f"<main id='canvas' data-document-id='{html_escape.escape(document_id, quote=True)}' data-bindings-url='/published-graphics/{html_escape.escape(station_id, quote=True)}/{html_escape.escape(document_id, quote=True)}/bindings?page_id={html_escape.escape(page_id, quote=True)}'>{''.join(elements)}</main>"
                    f"{runtime_js}</body></html>")
        return HTMLResponse(document, headers={
            "Content-Security-Policy": f"default-src 'self'; img-src 'self' data:; style-src 'unsafe-inline'; script-src 'nonce-{nonce}'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'",
            "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})

    @app.get("/published-graphics/{station_id}/{document_id}/bindings")
    def published_graphic_bindings(station_id: str, document_id: str, page_id: str) -> dict:
        """Evaluate the frozen binding configuration against live Core Point Runtime samples."""
        from dataclasses import asdict
        from avic_core.web_pages.models import WebPageNode
        from avic_core.graphics.binding_engine import evaluate_binding
        try:
            page_node, _ = app.state.core.repository.get(page_id, WebPageNode)
            if page_node.station_id != station_id or not page_node.published:
                raise HTTPException(status_code=404, detail="Опубликованная страница не найдена")
            snapshot = next((item.get("graphic_snapshot") for item in page_node.published_layout
                             if isinstance(item, dict) and item.get("type") == "graphic"
                             and item.get("graphic_id") == document_id), None)
            if not isinstance(snapshot, dict) or snapshot.get("station_id") != station_id:
                raise HTTPException(status_code=404, detail="Мнемосхема отсутствует в опубликованной версии")
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Опубликованная страница не найдена") from exc
        results = {}
        for element in snapshot.get("elements", []):
            for binding in element.get("bindings", []):
                binding_id = str(binding.get("id") or "")
                point_id = str(binding.get("point_id") or "")
                try:
                    sample = app.state.core.point_runtime.read(point_id)
                    result = evaluate_binding(
                        binding_type=binding.get("binding_type", "value"),
                        target_property=binding.get("target_property", "value"),
                        settings=binding.get("settings", {}), value=sample.value, quality=sample.quality)
                    row = asdict(result)
                    row.update({"binding_id": binding_id, "element_id": element.get("id"),
                                "point_id": point_id, "timestamp": sample.timestamp.isoformat() if sample.timestamp else None,
                                "unit": sample.unit, "source": sample.source, "revision": sample.revision})
                except Exception:
                    row = {"binding_id": binding_id, "element_id": element.get("id"), "point_id": point_id,
                           "target_property": binding.get("target_property", "value"), "value": None,
                           "display_text": "NOT_CONNECTED", "quality": "NOT_CONNECTED", "degraded": True,
                           "visible": True, "animation_allowed": False, "interaction_allowed": False,
                           "diagnostic": "POINT_RUNTIME_UNAVAILABLE"}
                results[binding_id] = row
        return {"document_id": document_id, "published": True, "bindings": results}

    @app.put("/api/web-pages/{node_id}")
    def web_page_update(node_id: str,payload: WebNodeUpdateInput,request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.update(node_id,payload.expected_revision,**payload.model_dump(exclude={"expected_revision"}))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Узел не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400,detail=str(exc)) from exc

    @app.post("/api/web-pages/{node_id}/move")
    def web_page_move(node_id: str,payload: WebNodeMoveInput,request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.move(node_id,payload.parent_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Узел не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

    @app.post("/api/web-pages/{node_id}/reorder")
    def web_page_reorder(node_id: str,payload: WebNodeReorderInput,request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.reorder(node_id,payload.direction)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Узел не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

    @app.delete("/api/web-pages/{node_id}")
    def web_page_delete(node_id: str,expected_revision: int,request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.delete(node_id,expected_revision)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Узел не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400,detail=str(exc)) from exc

    @app.post("/api/web-pages/{node_id}/graphics")
    def web_page_assign_graphic(node_id: str,payload: WebGraphicAssignInput,request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.assign_graphic(node_id,payload.graphic_id,payload.expected_revision)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница или мнемосхема не найдены") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400,detail=str(exc)) from exc

    @app.delete("/api/web-pages/{node_id}/graphics/{graphic_id}")
    def web_page_unassign_graphic(node_id: str,graphic_id: str,expected_revision: int,request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.web_pages.unassign_graphic(node_id,graphic_id,expected_revision)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400,detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/graphics")
    def list_graphics(station_id: str) -> dict:
        try: return {"documents": app.state.graphics.list_for_station(station_id)}
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/graphics", status_code=201)
    def create_graphic(station_id: str, payload: GraphicCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.graphics.create(station_id, payload.name, payload.description, payload.width, payload.height)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/graphics/fan-demo", status_code=201)
    def create_fan_demo(station_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.graphics.create_fan_demo(station_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/graphics/ahu-demo", status_code=201)
    def create_modular_ahu_demo(station_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.graphics.create_modular_ahu_demo(station_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/graphics/library")
    def graphics_symbol_library() -> dict:
        items = list_symbols()
        categories = sorted({item["category"] for item in items})
        return {"version": "2.0.0", "style": "isometric-3d", "count": len(items), "categories": categories, "items": items}

    @app.get("/api/stations/{station_id}/graphics/symbols")
    def graphics_symbol_catalog(station_id: str) -> dict:
        try:
            items = app.state.graphics.symbol_catalog(station_id)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"station_id": station_id, "count": len(items),
                "categories": sorted({x["category"] for x in items}), "items": items}

    @app.get("/api/stations/{station_id}/graphics/svg-assets")
    def custom_svg_assets(station_id: str) -> dict:
        try:
            row = app.state.core.repository.get_record(station_id)
            if row["entity_type"] != "Station":
                raise ValueError("Целевой объект не является станцией")
            items = app.state.core.custom_svg.list_for_station(station_id)
            return {"station_id": station_id, "count": len(items), "items": items}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/graphics/svg-assets", status_code=201)
    def import_custom_svg(station_id: str, payload: SvgImportInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            row = app.state.core.repository.get_record(station_id)
            if row["entity_type"] != "Station":
                raise ValueError("Целевой объект не является станцией")
            asset = app.state.core.custom_svg.import_svg(
                station_id, name=payload.name, category=payload.category,
                filename=payload.filename, svg=payload.svg)
            app.state.core.audit.append(
                actor_id="local-engineer", action="graphics.svg_imported", resource_type="svg_symbol",
                resource_id=asset["id"], details={"station_id": station_id, "filename": asset["filename"],
                                                   "category": asset["category"], "sha256": asset["sha256"]})
            return asset
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except SvgImportError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/graphics/custom-symbols/{symbol_id}/svg")
    def custom_svg_content(symbol_id: str) -> Response:
        try:
            svg = app.state.core.custom_svg.read_svg(symbol_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Импортированный SVG не найден") from exc
        return Response(content=svg, media_type="image/svg+xml", headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
            "Cache-Control": "private, max-age=3600",
        })

    @app.delete("/api/stations/{station_id}/graphics/svg-assets/{symbol_id}")
    def delete_custom_svg(station_id: str, symbol_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            row = app.state.core.repository.get_record(station_id)
            if row["entity_type"] != "Station":
                raise ValueError("Целевой объект не является станцией")
            asset = app.state.core.custom_svg.get(symbol_id, station_id=station_id)
            for item in app.state.core.repository.list_records(entity_type="GraphicElement"):
                if item["payload"].get("symbol_key") == symbol_id:
                    doc_id = item["payload"].get("document_id")
                    try:
                        doc, _ = app.state.core.repository.get(doc_id, __import__("avic_core.graphics.models", fromlist=["GraphicDocument"]).GraphicDocument)
                    except EntityNotFound:
                        continue
                    if doc.station_id == station_id:
                        raise HTTPException(status_code=409, detail="Символ используется в мнемосхемах станции; сначала удалите его со всех листов")
            if not app.state.core.custom_svg.delete(symbol_id, station_id):
                raise HTTPException(status_code=404, detail="Импортированный SVG не найден")
            app.state.core.audit.append(
                actor_id="local-engineer", action="graphics.svg_deleted", resource_type="svg_symbol",
                resource_id=symbol_id, details={"station_id": station_id, "name": asset["name"], "sha256": asset["sha256"]})
            return {"deleted": symbol_id, "name": asset["name"]}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Импортированный SVG не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/graphics/library/{symbol_id}/svg")
    def graphics_symbol_svg(symbol_id: str) -> Response:
        try:
            svg = read_symbol_svg(symbol_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="SVG-символ не найден") from exc
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=500, detail="SVG-библиотека повреждена или содержит недопустимый файл") from exc
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
                "Cache-Control": "public, max-age=3600",
            },
        )

    @app.get("/api/graphics/{document_id}/bindings/evaluate")
    def evaluate_graphics_bindings(document_id: str) -> dict:
        try: return app.state.graphics.evaluate_bindings(document_id)
        except Exception as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/graphics/{document_id}/logic-bindings/evaluate")
    def evaluate_graphics_logic_bindings(document_id: str) -> dict:
        try: return app.state.fbd.evaluate_graphic_bindings(document_id)
        except Exception as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/engineering-drafts")
    def list_engineering_drafts(station_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            return {"drafts": app.state.engineering_drafts.list_station(station_id)}
        except DraftError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/engineering-drafts/{editor}/{station_id}/{resource_id}")
    def get_engineering_draft(editor: str, station_id: str, resource_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.engineering_drafts.get(editor, station_id, resource_id)
        except DraftNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except DraftError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/api/engineering-drafts/{editor}/{station_id}/{resource_id}")
    def save_engineering_draft(editor: str, station_id: str, resource_id: str,
                               payload: EngineeringDraftInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.engineering_drafts.save(
                editor, station_id, resource_id, content=payload.content,
                base_revision=payload.base_revision,
                expected_draft_revision=payload.expected_draft_revision,
            )
        except DraftConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except DraftError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/engineering-drafts/{editor}/{station_id}/{resource_id}")
    def delete_engineering_draft(editor: str, station_id: str, resource_id: str,
                                 expected_draft_revision: int, request: Request) -> dict:
        require_local_operator(request)
        try:
            deleted = app.state.engineering_drafts.delete(
                editor, station_id, resource_id,
                expected_draft_revision=expected_draft_revision,
            )
            return {"deleted": deleted}
        except DraftConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except DraftError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/graphics/{document_id}")
    def get_graphic(document_id: str) -> dict:
        try: return app.state.graphics.get(document_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Мнемосхема не найдена") from exc

    @app.get("/api/stations/{station_id}/graphics-points")
    def graphic_points(station_id: str) -> dict:
        try: return {"points": app.state.graphics.points(station_id)}
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/api/graphics/{document_id}")
    def save_graphic(document_id: str, payload: GraphicSaveInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.graphics.save(document_id, payload.expected_revision, payload.elements)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Мнемосхема или точка не найдена") from exc
        except ConcurrencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            code = 409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400
            raise HTTPException(status_code=code, detail=str(exc)) from exc

    @app.get("/api/drivers/catalog")
    def driver_catalog() -> dict:
        return {"drivers": app.state.driver_manager.catalog(), "field_io_enabled": False}

    @app.get("/api/stations/{station_id}/drivers")
    def list_station_drivers(station_id: str) -> dict:
        try: return {"instances": app.state.driver_manager.list_instances(station_id)}
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/drivers", status_code=201)
    def create_station_driver(station_id: str, payload: DriverInstanceCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.driver_manager.create_instance(station_id, payload.driver_id, payload.name, payload.config)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/driver-instances/{instance_id}")
    def get_driver_instance(instance_id: str) -> dict:
        try: return app.state.driver_manager.get_instance(instance_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Экземпляр драйвера не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/api/driver-instances/{instance_id}/config")
    def update_driver_instance_config(instance_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        config = payload.get("config")
        expected_version = payload.get("expected_version")
        if not isinstance(config, dict) or not isinstance(expected_version, int):
            raise HTTPException(status_code=400, detail="Требуются config и expected_version")
        try:
            return app.state.driver_manager.update_config(
                instance_id, config, expected_version=expected_version)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Экземпляр драйвера не найден") from exc
        except ConcurrencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/driver-instances/{instance_id}/start")
    def start_driver_instance(instance_id: str, payload: DriverStartInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.driver_manager.start_instance(
                instance_id, poll_interval_seconds=payload.poll_interval_seconds)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Экземпляр драйвера не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/driver-instances/{instance_id}/stop")
    def stop_driver_instance(instance_id: str, payload: DriverStopInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.driver_manager.stop_instance(
                instance_id, timeout=payload.timeout_seconds)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Экземпляр драйвера не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (RuntimeError, TimeoutError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/driver-instances/{instance_id}/diagnostics")
    def driver_instance_diagnostics(instance_id: str) -> dict:
        try:
            return app.state.driver_manager.diagnostics(instance_id)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Экземпляр драйвера не найден") from exc

    @app.get("/api/stations/{station_id}/engineering-workflow")
    def engineering_workflow(station_id: str) -> dict:
        try:
            return app.state.engineering_workflow.inspect(station_id)
        except EntityNotFound:
            raise HTTPException(status_code=404, detail="Станция не найдена")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/stations/{station_id}/fbd-studio")
    def fbd_studio_list(station_id: str) -> dict:
        try: return app.state.fbd_studio.list_for_station(station_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/fbd-studio", status_code=201)
    def fbd_studio_create(station_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd_studio.create(station_id, str(payload.get("name") or "FBD Project"), payload.get("data") or {})
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/fbd-studio/{document_id}")
    def fbd_studio_delete(document_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            app.state.fbd_studio.delete(document_id, int(request.query_params.get("expected_revision", "-1")))
            return {"deleted": True, "document_id": document_id}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="FBD Studio проект не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.get("/api/fbd-studio/{document_id}")
    def fbd_studio_get(document_id: str) -> dict:
        try: return app.state.fbd_studio.get(document_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD Studio проект не найден") from exc

    @app.post("/api/fbd-studio/{document_id}/compile-preview")
    def fbd_studio_compile_preview(document_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try:
            expected = payload.get("expected_revision")
            return app.state.fbd_studio.compile_preview(document_id, int(expected) if expected is not None else None)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="FBD Studio проект не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.post("/api/fbd-studio/{document_id}/compile")
    def fbd_studio_compile(document_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try:
            expected = int(payload.get("expected_revision", -1))
            return app.state.fbd_studio.compile_to_core(document_id, expected)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="FBD Studio проект или связанный объект не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.put("/api/fbd-studio/{document_id}")
    def fbd_studio_save(document_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.fbd_studio.save(document_id, int(payload.get("expected_revision", -1)),
                payload.get("data"), payload.get("name"))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD Studio проект не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.get("/api/fbd/library")
    def fbd_library() -> dict:
        return {"blocks": app.state.fbd.library(), "categories": sorted({x["category"] for x in app.state.fbd.library()})}

    @app.get("/api/stations/{station_id}/fbd")
    def fbd_list(station_id: str) -> dict:
        try: return {"documents": app.state.fbd.list_for_station(station_id)}
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/fbd", status_code=201)
    def fbd_create(station_id: str, payload: GraphicCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.create(station_id, payload.name, payload.description)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/fbd/fan-demo", status_code=201)
    def fbd_fan_demo(station_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.create_fan_demo(station_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/fbd/{document_id}")
    def fbd_get(document_id: str) -> dict:
        try: return app.state.fbd.get(document_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD-схема не найдена") from exc

    @app.put("/api/fbd/{document_id}")
    def fbd_save(document_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.save(document_id, int(payload.get("expected_revision", -1)), payload.get("nodes"), payload.get("links"))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD-схема или блок не найдены") from exc
        except ValueError as exc: raise HTTPException(status_code=409 if str(exc).startswith("CONCURRENCY_CONFLICT") else 400, detail=str(exc)) from exc

    @app.post("/api/fbd/{document_id}/points/{point_id}", status_code=201)
    def fbd_add_point(document_id: str, point_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.fbd.add_point_node(document_id, point_id,
                page_id=payload.get("page_id"), x=payload.get("x", 40), y=payload.get("y", 40))
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Точка или FBD-схема не найдены") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/fbd/{document_id}/pages", status_code=201)
    def fbd_add_page(document_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.add_page(document_id, str(payload.get("name") or "Новая страница"))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD-стратегия не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/fbd/{document_id}/pages/{page_id}")
    def fbd_rename_page(document_id: str, page_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.rename_page(document_id, page_id, str(payload.get("name") or ""))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/fbd/{document_id}/pages/{page_id}")
    def fbd_delete_page(document_id: str, page_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.delete_page(document_id, page_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Страница не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/fbd/{document_id}/connectives", status_code=201)
    def fbd_create_connective(document_id: str, payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.create_connective(document_id, payload)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD-объект не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/fbd/{document_id}/connectives/{connective_id}")
    def fbd_delete_connective(document_id: str, connective_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.delete_connective(document_id, connective_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Connective не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/fbd/{document_id}/simulate")
    def fbd_simulate(document_id: str, payload: dict | None = None) -> dict:
        try: return app.state.fbd.simulate(document_id, (payload or {}).get("inputs"))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="FBD-схема не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/fbd-runtime/{document_id}/start")
    def fbd_runtime_start(document_id: str, request: Request, payload: dict | None = None) -> dict:
        if request is not None: require_local_operator(request)
        try:
            return app.state.fbd_execution.start(document_id, interval_ms=(payload or {}).get("interval_ms"), background=bool((payload or {}).get("background", True)))
        except (ValueError, RuntimeError, EntityNotFound) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/fbd-runtime/{document_id}/stop")
    def fbd_runtime_stop(document_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd_execution.stop(document_id)
        except (ValueError, RuntimeError, EntityNotFound) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/fbd-runtime/{document_id}/status")
    def fbd_runtime_status(document_id: str) -> dict:
        return app.state.fbd_execution.status(document_id)

    @app.post("/api/fbd-runtime/{document_id}/tick")
    def fbd_runtime_tick(document_id: str, request: Request, payload: dict | None = None) -> dict:
        if request is not None: require_local_operator(request)
        try: return app.state.fbd_execution.tick_once(document_id, inputs=(payload or {}).get("inputs"))
        except (ValueError, RuntimeError, KeyError, EntityNotFound) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/fbd/graphics-bindings", status_code=201)
    def fbd_graphics_bind(payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.fbd.bind_graphic_output(payload.get("graphic_element_id", ""), payload.get("logic_node_id", ""), payload.get("output_port", "OUT"))
        except EntityNotFound as exc: raise HTTPException(status_code=404, detail="Объект привязки не найден") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/schedules")
    def list_schedules(station_id: str) -> dict:
        try:
            station = app.state.core.repository.get_record(station_id)
            if station.get("entity_type") != "Station":
                raise HTTPException(status_code=404, detail="Станция не найдена")
            return {"schedules": app.state.core.schedules.list(station_id=station_id)}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc

    @app.post("/api/schedules", status_code=201)
    def create_schedule(payload: ScheduleCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            station = app.state.core.repository.get_record(payload.station_id)
            if station.get("entity_type") != "Station":
                raise HTTPException(status_code=404, detail="Станция не найдена")
            data = payload.model_dump()
            data["timezone_name"] = data.pop("timezone")
            return app.state.core.schedules.create(**data, actor_id="local-engineer")
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ScheduleConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/schedules/{schedule_id}/weekly-events", status_code=201)
    def add_schedule_weekly(schedule_id: str, payload: ScheduleWeeklyInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.add_weekly_event(schedule_id, **payload.model_dump(), actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание или событие не найдено") from exc
        except ScheduleConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/schedules/{schedule_id}/weekly-days/copy")
    def copy_schedule_day(schedule_id: str, payload: ScheduleCopyDayInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.copy_weekly_day(
                schedule_id, **payload.model_dump(), actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc
        except ScheduleConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/schedules/{schedule_id}/weekly-events/{event_id}")
    def delete_schedule_weekly(schedule_id: str, event_id: str, request: Request, expected_revision: int | None = None) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.delete_weekly_event(schedule_id, event_id, expected_revision=expected_revision, actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание или событие не найдено") from exc
        except ScheduleConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/schedules/{schedule_id}/special-events", status_code=201)
    def add_schedule_special(schedule_id: str, payload: ScheduleSpecialInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.add_special_event(schedule_id, **payload.model_dump(), actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc
        except ScheduleConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/schedules/{schedule_id}/special-events/{event_id}")
    def delete_schedule_special(schedule_id: str, event_id: str, request: Request, expected_revision: int | None = None) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.delete_special_event(schedule_id, event_id, expected_revision=expected_revision, actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание или исключение не найдено") from exc
        except ScheduleConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/schedules/{schedule_id}/evaluate")
    def evaluate_schedule(schedule_id: str) -> dict:
        try:
            return app.state.core.schedules.evaluate(schedule_id)
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/schedule-points")
    def list_schedule_points(station_id: str, value_type: str) -> dict:
        try:
            station = app.state.core.repository.get_record(station_id)
            if station.get("entity_type") != "Station":
                raise HTTPException(status_code=404, detail="Станция не найдена")
            return {"points": app.state.core.schedules.list_bindable_points(station_id, value_type)}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/schedules/{schedule_id}/points/{point_id}")
    def bind_schedule_point(schedule_id: str, point_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.bind_point(schedule_id, point_id, actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/schedules/{schedule_id}/points/{point_id}")
    def unbind_schedule_point(schedule_id: str, point_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.unbind_point(schedule_id, point_id, actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc

    @app.post("/api/schedules/{schedule_id}/override")
    def set_schedule_override(schedule_id: str, payload: ScheduleOverrideInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.core.schedules.set_override(schedule_id, **payload.model_dump(), actor_id="local-engineer")
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc
        except ScheduleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/schedules/{schedule_id}/override")
    def clear_schedule_override(schedule_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            app.state.core.schedules.clear_override(schedule_id, actor_id="local-engineer")
            return {"cleared": True, "schedule_id": schedule_id}
        except ScheduleNotFound as exc:
            raise HTTPException(status_code=404, detail="Расписание не найдено") from exc

    @app.get("/api/projects/tree")
    def project_tree(include_archived: bool = False) -> dict:
        return app.state.project_station.tree(include_archived=include_archived)

    @app.get("/api/engineering/tree")
    def engineering_tree(include_archived: bool = False) -> dict:
        """Unified navigator: Project → Station → Physical Network → Protocol → Device → Point."""
        return app.state.engineering_tree.build(include_archived=include_archived)

    @app.get("/api/licensing/point-usage")
    def licensing_point_usage() -> dict:
        """Project/installation point counters; no license activation is implied."""
        from avic_core.licensing import summarize_point_usage
        records = app.state.core.repository.list_records(entity_type="Point")
        return summarize_point_usage(records, point_limit=None)

    @app.post("/api/engineering/devices/{device_id}/read-values")
    def read_device_point_values(device_id: str, request: Request) -> dict:
        """Explicit, bounded, read-only BACnet Present_Value refresh for one imported device."""
        require_local_operator(request)
        try:
            device_row = app.state.core.repository.get_record(device_id)
            if device_row["entity_type"] != "Device":
                raise ValueError("Объект не является устройством")
            device = device_row["payload"]
            if str(device.get("protocol", "")).lower() != "bacnet/ip":
                raise ValueError("Для этого устройства пока нет подключённого циклического драйвера чтения")
            driver_row = app.state.core.repository.get_record(device.get("driver_instance_id", ""))
            cfg = driver_row.get("payload", {}).get("configuration", {})
            interface_id = cfg.get("interface_id")
            if not interface_id:
                raise ValueError("Для устройства не сохранён сетевой интерфейс. Повторно импортируйте его из Discovery")
            adapter = get_interface(interface_id)
            address = str(device.get("address", ""))
            if ipaddress.ip_address(address) not in ipaddress.ip_network(adapter["subnet_cidr"], strict=False):
                raise ValueError("Адрес устройства вне подсети выбранного интерфейса")
            native = str(device.get("native_identity", ""))
            try:
                device_instance = int(native.split(":device:", 1)[1].split("@", 1)[0])
            except (IndexError, ValueError):
                raise ValueError("Не удалось определить BACnet Device Instance")
            points = [r for r in app.state.core.repository.list_records(entity_type="Point")
                      if r.get("payload", {}).get("device_id") == device_id]
            if len(points) > 40:
                raise ValueError("Опрос ограничен 40 точками за один запуск. Разбейте устройство на группы")
            config = BacnetIpNetworkConfig(str(device.get("network_id") or "workbench-lan"),
                adapter["name"], adapter["ipv4"], adapter["subnet_cidr"], udp_port=int(cfg.get("udp_port", 47808)))
            results = []
            with BacnetIpClient(config, DiscoveryPolicy(request_timeout_seconds=1.5, max_requests_per_second=2.0)) as client:
                for row in points:
                    payload = row.get("payload", {})
                    native_point = str(payload.get("native_identity", ""))
                    try:
                        prefix, object_type, instance = native_point.split(":")[-3:]
                        if prefix != "object":
                            raise ValueError("unsupported native identity")
                        obj_type, obj_instance = int(object_type), int(instance)
                        value = client.read_property((address, int(cfg.get("udp_port", 47808))), device_instance,
                            obj_type, obj_instance, 85, timeout_seconds=1.5)
                        try:
                            unit_code = client.read_property((address, int(cfg.get("udp_port", 47808))), device_instance,
                                obj_type, obj_instance, 117, timeout_seconds=1.0)
                            unit = {62: "°C", 64: "°F", 98: "%"}.get(unit_code, payload.get("unit", ""))
                        except Exception:
                            unit = payload.get("unit", "")
                        point, version = app.state.core.repository.get(row["entity_id"], Point)
                        point.unit = unit or point.unit
                        point.update_value(value, PointQuality.GOOD)
                        app.state.core.repository.save(point, expected_version=version)
                        results.append({"point_id": point.id, "value": value, "unit": point.unit, "quality": "GOOD"})
                    except Exception as exc:
                        try:
                            point, version = app.state.core.repository.get(row["entity_id"], Point)
                            point.quality = PointQuality.BAD_COMMUNICATION
                            point.timestamp = point.timestamp
                            app.state.core.repository.save(point, expected_version=version)
                        except Exception:
                            pass
                        results.append({"point_id": row["entity_id"], "quality": "COMM_LOST", "error": str(exc)})
            app.state.core.audit.append(actor_id="local-engineer", action="device.point_values.read",
                resource_type="device", resource_id=device_id,
                details={"read_only": True, "points_read": sum(1 for x in results if x.get("quality") == "GOOD"),
                         "points_failed": sum(1 for x in results if x.get("quality") != "GOOD")})
            return {"device_id": device_id, "mode": "read_only", "write_enabled": False, "results": results}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Устройство или драйвер не найдены") from exc
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(status_code=400, detail=f"Опрос значений не выполнен: {exc}") from exc

    @app.post("/api/projects", status_code=201)
    def create_project(payload: ProjectInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.project_station.create_project(payload.name, payload.description)
        except (ValueError, ConcurrencyConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/stations", status_code=201)
    def create_station(payload: StationInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.project_station.create_station(payload.project_id, payload.name, payload.description)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Проект не найден") from exc
        except (ValueError, ConcurrencyConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/engineering/objects/{entity_id}/delete-preview")
    def preview_project_station_delete(entity_id: str) -> dict:
        try:
            return app.state.project_station.delete_preview(entity_id)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Объект не найден") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/engineering/objects/{entity_id}")
    def delete_project_station(entity_id: str, request: Request, cascade: bool = False) -> dict:
        require_local_operator(request)
        try:
            dependency_preview = app.state.core.dependencies.delete_preview(entity_id)
            if not dependency_preview["safe_to_delete"]:
                raise HTTPException(status_code=409, detail={"message":"Нельзя удалить проект/станцию: есть зарегистрированные зависимые объекты", "blocking_dependents":dependency_preview["blocking_dependents"]})
            result = app.state.project_station.delete(entity_id, cascade=cascade)
            app.state.core.dependencies.remove_object_edges(entity_id)
            return result
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Объект не найден") from exc
        except ConcurrencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.patch("/api/projects/{entity_id}")
    @app.patch("/api/stations/{entity_id}")
    def update_project_station(entity_id: str, payload: ObjectPatch, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.project_station.update(entity_id, expected_version=payload.expected_version,
                name=payload.name, description=payload.description, archived=payload.archived)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Объект не найден") from exc
        except ConcurrencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/networks", status_code=201)
    def create_physical_network(station_id: str, payload: PhysicalNetworkInput, request: Request) -> dict:
        require_local_operator(request)
        if payload.station_id != station_id:
            raise HTTPException(status_code=400, detail="Station ID не совпадает с адресом запроса")
        try:
            station = app.state.core.repository.get_record(station_id)
            if station["entity_type"] != "Station":
                raise ValueError("Родительский объект не является станцией")
            mode = payload.addressing_mode.strip().lower()
            if mode == "auto":
                if not payload.interface_id:
                    raise ValueError("Для автоматической привязки выберите сетевой интерфейс")
                adapter = get_interface(payload.interface_id)
                station_ip, subnet = adapter["ipv4"], adapter["subnet_cidr"]
                gateway, dns = "", []
                interface_id, interface_name = adapter["id"], adapter["name"]
            elif mode == "manual":
                if not payload.station_ipv4 or not payload.subnet_cidr:
                    raise ValueError("Для ручного проектирования укажите IP будущей станции и подсеть")
                plan = NetworkPlan(payload.name.strip(), payload.subnet_cidr, payload.station_ipv4,
                    payload.gateway_ipv4, tuple(payload.dns_servers), "manual")
                values = plan.as_dict()
                station_ip, subnet = values["station_ipv4"], values["subnet_cidr"]
                gateway, dns = values["gateway_ipv4"] or "", values["dns_servers"]
                interface_id, interface_name = "", "Не привязан — проектная конфигурация"
            else:
                raise ValueError("addressing_mode должен быть auto или manual")
            entity = PhysicalNetwork(name=payload.name.strip(), description=payload.description.strip(),
                station_id=station_id, interface_id=interface_id, interface_name=interface_name,
                ipv4=station_ip, subnet_cidr=subnet, network_kind="ethernet",
                addressing_mode=mode, station_ipv4=station_ip, gateway_ipv4=gateway, dns_servers=dns)
            app.state.core.repository.save(entity)
            app.state.core.audit.append(actor_id="local-engineer", action="physical_network.created",
                resource_type="physical_network", resource_id=entity.id,
                details={"station_id": station_id, "addressing_mode": mode, "station_ipv4": station_ip,
                         "subnet_cidr": subnet, "interface_id": interface_id})
            return {"id": entity.id, "type": "PhysicalNetwork", "name": entity.name, "station_id": station_id,
                "addressing_mode": mode, "interface_id": entity.interface_id, "interface_name": entity.interface_name,
                "ipv4": entity.ipv4, "station_ipv4": entity.station_ipv4, "subnet_cidr": entity.subnet_cidr,
                "gateway_ipv4": entity.gateway_ipv4 or None, "dns_servers": entity.dns_servers,
                "deployment_binding": "BOUND" if mode == "auto" else "PLANNED_NOT_PRESENT",
                "description": entity.description}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/network/{network_id}/channels", status_code=201)
    def create_protocol_channel(network_id: str, payload: ProtocolChannelInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            network = app.state.core.repository.get_record(network_id)
            if network["entity_type"] != "PhysicalNetwork" or network["payload"].get("station_id") != payload.station_id:
                raise ValueError("Физическая сеть не принадлежит выбранной станции")
            protocol = payload.protocol.strip().lower()
            if protocol not in {"bacnet/ip", "modbus/tcp"}:
                raise ValueError("В этой сборке доступны каналы BACnet/IP и Modbus TCP")
            existing = [r for r in app.state.core.repository.list_records(entity_type="ProtocolChannel")
                if r["payload"].get("network_id") == network_id and r["payload"].get("protocol") == protocol]
            if existing:
                raise ValueError("Канал этого протокола уже создан в выбранной сети")
            entity = ProtocolChannel(name=payload.name.strip(), station_id=payload.station_id,
                network_id=network_id, protocol=protocol, mode="read_only")
            app.state.core.repository.save(entity)
            app.state.core.audit.append(actor_id="local-engineer", action="protocol_channel.created",
                resource_type="protocol_channel", resource_id=entity.id,
                details={"network_id": network_id, "protocol": protocol, "mode": "read_only"})
            return {"id": entity.id, "type": "ProtocolChannel", "name": entity.name, "protocol": protocol,
                "network_id": network_id, "station_id": payload.station_id, "mode": "read_only"}
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Физическая сеть не найдена") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/network/interfaces")
    def network_interfaces() -> dict:
        """Read-only list of active IPv4 adapters; no discovery is started."""
        try:
            return {"interfaces": list_ipv4_interfaces()}
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/network/{network_id}/deployment-check")
    def network_deployment_check(network_id: str, request: Request) -> dict:
        """Compare a saved deployment plan with local adapters; never changes addressing."""
        require_local_operator(request)
        try:
            record = app.state.core.repository.get_record(network_id)
            if record["entity_type"] != "PhysicalNetwork":
                raise ValueError("Объект не является физической сетью")
            p = record["payload"]
            plan = NetworkPlan(record["name"], p.get("subnet_cidr") or "", p.get("station_ipv4") or p.get("ipv4") or "",
                p.get("gateway_ipv4") or None, tuple(p.get("dns_servers") or ()), p.get("addressing_mode", "auto"))
            interfaces = list_ipv4_interfaces()
            result = assess_deployment_binding(plan, interfaces)
            result.update({"network_id": network_id, "addressing_mode": p.get("addressing_mode", "auto")})
            return result
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Сеть не найдена") from exc
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/network/ping")
    def network_ping(payload: NetworkPingInput, request: Request) -> dict:
        """One explicit bounded ICMP probe; no subnet sweep and no config writes."""
        require_local_operator(request)
        try:
            return ping_ipv4(payload.address, payload.timeout_seconds)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/network/bacnet/discover")
    def bacnet_discover(payload: BacnetDiscoveryInput, request: Request) -> dict:
        """Explicitly requested BACnet/IP Who-Is; read-only and never runs at startup."""
        require_local_operator(request)
        if payload.low_limit is not None and payload.high_limit is not None and payload.low_limit > payload.high_limit:
            raise HTTPException(status_code=400, detail="low_limit не может быть больше high_limit")
        try:
            adapter = get_interface(payload.interface_id)
            config = BacnetIpNetworkConfig(payload.network_id, adapter["name"],
                adapter["ipv4"], adapter["subnet_cidr"], udp_port=payload.udp_port)
            policy = DiscoveryPolicy(request_timeout_seconds=payload.timeout_seconds)
            with BacnetIpClient(config, policy) as client:
                found = client.discover(payload.timeout_seconds, payload.low_limit, payload.high_limit)
                diagnostics = dict(getattr(client, "last_discovery_diagnostics", {}))
            diagnostics["interface_ipv4"] = adapter["ipv4"]
            diagnostics["subnet_cidr"] = adapter["subnet_cidr"]
            diagnostics["interface_mac"] = adapter.get("mac")
            resolver = DeviceIdentityResolver()
            devices = []
            for x in found:
                identity = resolver.resolve(protocol="bacnet/ip", vendor_id=x.vendor_id)
                devices.append({"device_instance": x.device_instance, "ip_address": x.source[0],
                    "udp_port": x.source[1], "max_apdu": x.max_apdu, "segmentation": x.segmentation,
                    "vendor_id": x.vendor_id, "manufacturer": identity.manufacturer,
                    "manufacturer_source": identity.manufacturer_source,
                    "identity_confidence": identity.confidence.value,
                    "model_name": None, "model_status": "not_read"})
            session = app.state.discovery_history.record_completed(network_id=payload.network_id,
                protocol="BACnet/IP", devices=devices, diagnostics=diagnostics)
            return {"protocol": "BACnet/IP", "mode": "read_only", "write_enabled": False,
                "interface": adapter, "count": len(found), "diagnostics": diagnostics, "devices": devices,
                "session": {"session_id": session["session_id"], "state": session["state"],
                            "created_at": session["created_at"]}}
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(status_code=400, detail=f"BACnet Discovery не выполнен: {exc}") from exc

    @app.get("/api/network/discovery-sessions")
    def discovery_sessions(limit: int = 100) -> dict:
        try:
            return {"sessions": app.state.discovery_history.list(limit), "write_enabled": False}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/network/discovery-sessions/{session_id}")
    def discovery_session(session_id: str) -> dict:
        try:
            return app.state.discovery_history.get(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Сеанс обнаружения не найден") from exc

    @app.post("/api/network/bacnet/inspect")
    def bacnet_inspect(payload: BacnetInspectInput, request: Request) -> dict:
        """Explicit read-only BACnet device/object inspection; no field writes."""
        require_local_operator(request)
        try:
            adapter = get_interface(payload.interface_id)
            if payload.address != payload.address.strip():
                raise ValueError("invalid device address")
            config = BacnetIpNetworkConfig(payload.network_id, adapter["name"],
                adapter["ipv4"], adapter["subnet_cidr"], udp_port=payload.udp_port)
            target_address = ipaddress.ip_address(payload.address)
            if target_address.version != 4:
                raise ValueError("BACnet/IP endpoint должен быть IPv4")
            # Explicit unicast inspection may reach a routed subnet through the host
            # routing table. Broadcast discovery remains limited to the selected LAN.
            routed_target = target_address not in ipaddress.ip_network(adapter["subnet_cidr"], strict=False)
            policy = DiscoveryPolicy(request_timeout_seconds=payload.timeout_seconds,
                                     max_requests_per_second=2.0)
            with BacnetIpClient(config, policy) as client:
                inspector = BacnetDeviceInspector(client)
                result = inspector.inspect((payload.address, payload.udp_port),
                    payload.device_instance, max_objects=payload.max_objects)
            ident = result.device_identity
            resolver = DeviceIdentityResolver()
            resolved = resolver.resolve(protocol="bacnet/ip", vendor_id=ident.get("vendor_id"),
                vendor_name=ident.get("vendor_name"), model_name=ident.get("model_name"),
                device_type="BACnet Device", firmware_revision=ident.get("firmware_revision"),
                mac_address=adapter.get("mac"))
            return {"protocol": "BACnet/IP", "mode": "read_only", "write_enabled": False,
                "address": payload.address, "network_id": payload.network_id,
                "address_scope": "routed_unicast" if routed_target else "local_subnet",
                "routing_note": "Используется таблица маршрутизации компьютера; доступность зависит от маршрутизатора/BBMD и настроек BACnet/IP." if routed_target else "Устройство находится в локальной подсети выбранного интерфейса.",
                "device_identity": {"device_instance": payload.device_instance,
                    "vendor_id": ident.get("vendor_id"),
                    "identity_sources": {"manufacturer": resolved.manufacturer_source, "model": resolved.model_source,
                        "firmware_revision": "BACnet Device.Firmware_Revision" if ident.get("firmware_revision") else ""},
                    "manufacturer": resolved.manufacturer, "model": resolved.model,
                    "device_type": resolved.device_type, "firmware_revision": resolved.firmware_revision,
                    "manufacturer_source": resolved.manufacturer_source,
                    "model_source": resolved.model_source, "confidence": resolved.confidence.value,
                    "property_errors": ident.get("property_errors", {})},
                "objects": list(result.objects),
                "point_snapshots": [{"object_type": x.object_identifier.type_name,
                    "instance": x.object_identifier.instance, "native_identity": x.native_identity,
                    "quality": x.quality, "properties": {k: {"value": v.value, "error": v.error}
                        for k, v in x.properties.items()}} for x in result.point_snapshots],
                "warnings": list(result.warnings), "object_count": len(result.objects)}
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(status_code=400, detail=f"BACnet Object Discovery не выполнен: {exc}") from exc

    @app.post("/api/stations/{station_id}/devices/import-preview")
    def preview_discovered_device_import(station_id: str, payload: dict, request: Request) -> dict:
        """Preview a supplied inspection snapshot; never contacts or changes field equipment."""
        require_local_operator(request)
        inspection = payload.get("inspection")
        if not isinstance(inspection, dict):
            raise HTTPException(status_code=400, detail="inspection должен быть объектом")
        try:
            return app.state.device_import.preview_bacnet(station_id, inspection,
                payload.get("selected_native_ids"), bool(payload.get("import_all", False)))
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/projects/stations/devices/import")
    def import_discovered_device(payload: DeviceImportInput, request: Request) -> dict:
        """Re-inspect a BACnet device and import the device plus explicitly selected objects."""
        require_local_operator(request)
        try:
            network_record = None
            try:
                candidate = app.state.core.repository.get_record(payload.network_id)
                if candidate["entity_type"] == "PhysicalNetwork":
                    network_record = candidate
            except (EntityNotFound, ValueError):
                network_record = None
            if network_record is not None:
                if network_record["payload"].get("station_id") != payload.station_id:
                    raise ValueError("Физическая сеть не принадлежит целевой станции")
                network_payload = network_record["payload"]
                if network_payload.get("addressing_mode", "auto") == "auto":
                    if network_payload.get("interface_id") != payload.interface_id:
                        raise ValueError("Выбранный интерфейс не совпадает с интерфейсом физической сети")
            adapter = get_interface(payload.interface_id)
            if network_record is not None and network_payload.get("addressing_mode") == "manual":
                if network_payload.get("subnet_cidr") != adapter["subnet_cidr"] or network_payload.get("station_ipv4") != adapter["ipv4"]:
                    raise ValueError("Проектная сеть ещё не привязана: IP и подсеть текущего компьютера должны совпасть с планом")
            target_address = ipaddress.ip_address(payload.address)
            if target_address.version != 4:
                raise ValueError("BACnet/IP endpoint должен быть IPv4")
            # A manually addressed device may be routed. Direct unicast uses the
            # OS routing table; broadcast discovery itself remains local-subnet only.
            config = BacnetIpNetworkConfig(payload.network_id, adapter["name"], adapter["ipv4"], adapter["subnet_cidr"], udp_port=payload.udp_port)
            policy = DiscoveryPolicy(request_timeout_seconds=payload.timeout_seconds, max_requests_per_second=2.0)
            with BacnetIpClient(config, policy) as client:
                result = BacnetDeviceInspector(client).inspect((payload.address, 47808), payload.device_instance,
                    max_objects=payload.max_objects)
            ident = result.device_identity
            resolved = DeviceIdentityResolver().resolve(protocol="bacnet/ip", vendor_id=ident.get("vendor_id"),
                vendor_name=ident.get("vendor_name"), model_name=ident.get("model_name"),
                device_type="BACnet Device", firmware_revision=ident.get("firmware_revision"))
            inspection = {"address": payload.address, "network_id": payload.network_id,
                "device_identity": {"device_instance": payload.device_instance, "vendor_id": ident.get("vendor_id"),
                    "manufacturer": resolved.manufacturer, "model": resolved.model,
                    "firmware_revision": resolved.firmware_revision,
                    "identity_sources": {"manufacturer": resolved.manufacturer_source, "model": resolved.model_source,
                        "firmware_revision": "BACnet Device.Firmware_Revision" if ident.get("firmware_revision") else ""}},
                "objects": [{"type_name": x["type_name"], "instance": x["instance"],
                    "object_name": x["object_name"], "native_identity": x["native_identity"]}
                    for x in result.objects if int(x["object_type"]) in {0, 1, 2, 3, 4, 5, 17}]}
            return app.state.device_import.import_bacnet(payload.station_id, inspection,
                payload.selected_native_ids, payload.import_all, payload.engineering_description,
                payload.interface_id, payload.udp_port)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(status_code=400, detail=f"Импорт устройства не выполнен: {exc}") from exc


    @app.post("/api/stations/{station_id}/protocol-devices/import-preview")
    def preview_protocol_device_import(station_id: str, payload: dict, request: Request) -> dict:
        """Preview normalized discovery data for any implemented protocol; performs no field I/O."""
        require_local_operator(request)
        inspection = payload.get("inspection")
        if not isinstance(inspection, dict):
            raise HTTPException(status_code=400, detail="inspection должен быть объектом")
        try:
            return app.state.protocol_point_import.preview(
                station_id, str(payload.get("driver_instance_id") or ""), inspection,
                payload.get("selected_native_ids"), bool(payload.get("import_all", False)))
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция или драйвер не найдены") from exc
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/protocol-devices/import")
    def import_protocol_device(station_id: str, payload: dict, request: Request) -> dict:
        """Transactionally import selected normalized device points; never writes to field devices."""
        require_local_operator(request)
        inspection = payload.get("inspection")
        if not isinstance(inspection, dict):
            raise HTTPException(status_code=400, detail="inspection должен быть объектом")
        try:
            return app.state.protocol_point_import.import_points(
                station_id, str(payload.get("driver_instance_id") or ""), inspection,
                payload.get("selected_native_ids"), bool(payload.get("import_all", False)))
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция или драйвер не найдены") from exc
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/device-tree")
    def station_device_tree(station_id: str) -> dict:
        try:
            return app.state.device_import.station_tree(station_id)
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/engineering/entities/{entity_id}")
    def engineering_entity_details(entity_id: str) -> dict:
        """Read-only property inspector for project, station, imported device and point."""
        try:
            row = app.state.core.repository.get_record(entity_id)
        except (EntityNotFound, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Объект не найден") from exc
        payload = row.get("payload", {})
        allowed = {"Project", "Station", "PhysicalNetwork", "ProtocolChannel", "Device", "Point"}
        if row["entity_type"] not in allowed:
            raise HTTPException(status_code=400, detail="Тип объекта не поддерживается инспектором")
        fields = {
            "description": payload.get("description", payload.get("engineering_description", "")),
            "project_id": payload.get("project_id"), "station_id": payload.get("station_id"),
            "interface_id": payload.get("interface_id"), "interface_name": payload.get("interface_name"),
            "ipv4": payload.get("ipv4"), "subnet_cidr": payload.get("subnet_cidr"),
            "network_id": payload.get("network_id"), "protocol": payload.get("protocol"), "mode": payload.get("mode"),
            "device_id": payload.get("device_id"), "address": payload.get("address"),
            "manufacturer": payload.get("manufacturer"), "model": payload.get("model"),
            "firmware_revision": payload.get("firmware_revision"), "vendor_id": payload.get("vendor_id"),
            "native_identity": payload.get("native_identity"), "object_type": payload.get("object_type"),
            "data_type": payload.get("data_type"), "unit": payload.get("unit"),
            "direction": getattr(payload.get("direction"), "value", payload.get("direction")),
            "value": payload.get("value"),
            "quality": getattr(payload.get("quality"), "value", payload.get("quality", "UNCERTAIN")),
            "timestamp": payload.get("timestamp"), "archived": bool(payload.get("archived", False)),
        }
        return {"id": row["entity_id"], "type": row["entity_type"], "name": row["name"],
                "version": int(row["version"]), "created_at": row["created_at"],
                "updated_at": row["updated_at"], "properties": {k: v for k, v in fields.items() if v is not None}}

    @app.delete("/api/engineering/entities/{entity_id}")
    def delete_engineering_entity(entity_id: str, request: Request) -> dict:
        """Remove only imported Point/Device configuration from AVIC; never writes to field equipment."""
        require_local_operator(request)
        try:
            row = app.state.core.repository.get_record(entity_id)
        except (EntityNotFound, ValueError) as exc:
            raise HTTPException(status_code=404, detail="Объект не найден") from exc
        entity_type = row["entity_type"]
        repo = app.state.core.repository
        dependency_preview = app.state.core.dependencies.delete_preview(entity_id)
        if not dependency_preview["safe_to_delete"]:
            raise HTTPException(status_code=409, detail={"message":"Нельзя удалить объект: есть зарегистрированные зависимые объекты", "blocking_dependents":dependency_preview["blocking_dependents"]})
        if entity_type == "Device":
            for point_row in repo.list_records(entity_type="Point"):
                if point_row.get("payload", {}).get("device_id") == entity_id:
                    point_preview = app.state.core.dependencies.delete_preview(point_row["entity_id"])
                    if not point_preview["safe_to_delete"]:
                        raise HTTPException(status_code=409, detail={"message":"Нельзя удалить устройство: его точка используется другими объектами", "point_id":point_row["entity_id"], "blocking_dependents":point_preview["blocking_dependents"]})
        if entity_type in {"PhysicalNetwork", "ProtocolChannel"}:
            dependents = []
            if entity_type == "PhysicalNetwork":
                dependents = [r for r in repo.list_records() if
                    (r["entity_type"] == "ProtocolChannel" and r["payload"].get("network_id") == entity_id) or
                    (r["entity_type"] == "Device" and r["payload"].get("network_id") == entity_id)]
            elif entity_type == "ProtocolChannel":
                dependents = [r for r in repo.list_records(entity_type="Device") if
                    r["payload"].get("network_id") == row["payload"].get("network_id") and
                    str(r["payload"].get("protocol", "")).lower() == str(row["payload"].get("protocol", "")).lower()]
            if dependents:
                raise HTTPException(status_code=409, detail="Нельзя удалить объект: к нему привязаны каналы или устройства")
        elif entity_type not in {"Device", "Point"}:
            raise HTTPException(status_code=400, detail="Тип объекта нельзя удалить из этого контекста")
        repo = app.state.core.repository
        removed_points = []
        if entity_type == "Device":
            for point in repo.list_records(entity_type="Point"):
                if point.get("payload", {}).get("device_id") == entity_id:
                    repo.delete(point["entity_id"], expected_version=int(point["version"]))
                    app.state.core.dependencies.remove_object_edges(point["entity_id"])
                    removed_points.append(point["entity_id"])
        repo.delete(entity_id, expected_version=int(row["version"]))
        app.state.core.dependencies.remove_object_edges(entity_id)
        app.state.core.audit.append(actor_id="local-engineer", action=f"{entity_type.lower()}.removed_from_station",
            resource_type=entity_type.lower(), resource_id=entity_id,
            details={"removed_point_ids": removed_points, "field_device_unchanged": True})
        return {"removed": True, "entity_id": entity_id, "entity_type": entity_type,
                "removed_points": removed_points, "field_device_unchanged": True}

    @app.post("/api/network/modbus/read")
    def modbus_read(payload: ModbusReadInput, request: Request) -> dict:
        """One explicit read-only Modbus TCP request; no write function exists."""
        require_local_operator(request)
        try:
            client = ModbusTcpClient(payload.host, payload.port, unit_id=payload.unit_id,
                                     timeout=payload.timeout_seconds)
            if payload.function == 3:
                registers = client.read_holding_registers(payload.address, payload.count)
            else:
                registers = client.read_input_registers(payload.address, payload.count)
            decoded = None
            if payload.data_type:
                decoded = decode_registers(registers, payload.data_type,
                    byte_order=payload.byte_order, word_order=payload.word_order)
            return {"protocol": "Modbus TCP", "mode": "read_only", "write_enabled": False,
                "host": payload.host, "port": payload.port, "unit_id": payload.unit_id,
                "function": payload.function, "address": payload.address,
                "registers": registers, "data_type": payload.data_type, "decoded_value": decoded}
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(status_code=400, detail=f"Modbus read не выполнен: {exc}") from exc

    @app.post("/api/network/modbus/identify")
    def modbus_identify(payload: ModbusReadInput, request: Request) -> dict:
        """Explicit read-only Modbus MEI 0x0E identification request."""
        require_local_operator(request)
        try:
            client = ModbusTcpClient(payload.host, payload.port, unit_id=payload.unit_id,
                                     timeout=payload.timeout_seconds)
            raw = client.read_device_identification(read_code=1, max_objects=32)
            identity = DeviceIdentityResolver().resolve(protocol="modbus/tcp",
                vendor_name=raw.get("0"), model_name=raw.get("1"),
                firmware_revision=raw.get("2"), device_type="Modbus device")
            return {"protocol": "Modbus TCP", "mode": "read_only", "write_enabled": False,
                "manufacturer": identity.manufacturer, "model": identity.model,
                "firmware_revision": identity.firmware_revision,
                "manufacturer_source": identity.manufacturer_source,
                "model_source": identity.model_source,
                "confidence": identity.confidence.value,
                "objects": raw}
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(status_code=400, detail=f"Modbus identification не выполнена: {exc}") from exc

    @app.post("/api/stations/{station_id}/control/access-lease")
    def acquire_control_lease(station_id: str, payload: AccessLeaseInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.command_manager.acquire_lease(station_id, "local-engineer", payload.duration_seconds)
        except (ValueError, EntityNotFound) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/control/access-lease/{lease_id}")
    def revoke_control_lease(lease_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.command_manager.revoke_lease(lease_id, "local-engineer")
        except CommandRejected as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/stations/{station_id}/control/commands", status_code=202)
    def request_control_command(station_id: str, payload: CommandRequestInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.command_manager.request(station_id=station_id, point_id=payload.point_id,
                actor_id="local-engineer", lease_id=payload.lease_id, command=payload.command,
                reason=payload.reason, interlock_point_ids=payload.interlock_point_ids)
        except CommandRejected as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (ValueError, EntityNotFound) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/control/commands")
    def list_control_commands(station_id: str, request: Request, limit: int = 100) -> dict:
        require_local_operator(request)
        try:
            return {"station_id": station_id, "commands": app.state.command_manager.list_station(station_id, limit)}
        except CommandRejected as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/control/commands/{command_id}")
    def get_control_command(command_id: str, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.command_manager.get(command_id)
        except CommandRejected as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/control/commands/{command_id}/simulated-feedback")
    def confirm_simulated_control_feedback(command_id: str, payload: SimulatedFeedbackInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            return app.state.command_manager.confirm_simulated_feedback(command_id, value=payload.value, quality=payload.quality)
        except CommandRejected as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/engineering/points/runtime")
    def engineering_point_runtime(station_id: str | None = None) -> dict:
        """Read current point values from the shared runtime registry."""
        try:
            values = app.state.core.point_runtime.snapshot(station_id=station_id)
            return {"station_id": station_id, "count": len(values), "points": jsonable_encoder(values)}
        except (ValueError, EntityNotFound) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/points/{point_id}/runtime")
    def point_runtime_value(point_id: str) -> dict:
        try:
            return jsonable_encoder(app.state.core.point_runtime.read(point_id))
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Точка не найдена") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/engineering/points")
    def engineering_points(station_id: str | None = None, search: str | None = None, quality: str | None = None,
                           limit: int = 1000, offset: int = 0, sort_by: str = "name", sort_dir: str = "asc",
                           favorites_only: bool = False) -> dict:
        rows=app.state.core.repository.list_records(entity_type="Point")
        rows.extend(app.state.core.repository.list_records(entity_type="FBDExposedPoint"))
        devices={r["entity_id"]:r.get("payload",{}) for r in app.state.core.repository.list_records(entity_type="Device")}
        normalized=[]
        for row in rows:
            payload=dict(row.get("payload",{})); device=devices.get(payload.get("device_id"),{})
            payload["device"]={"station_id":device.get("station_id") or payload.get("station_id"),"id":payload.get("device_id"),"name":device.get("name") or ("FBD Runtime" if row.get("entity_type")=="FBDExposedPoint" else None),"address":device.get("address"),"protocol":device.get("protocol") or ("AVIC FBD" if row.get("entity_type")=="FBDExposedPoint" else None),"manufacturer":device.get("manufacturer"),"model":device.get("model")}
            payload["object_type"] = payload.get("object_type") or row.get("entity_type")
            normalized.append({**row,"payload":payload})
        favorites=app.state.core.point_views.favorite_ids(user_id="local-engineer")
        try:
            return app.state.core.point_views.query(normalized,favorite_ids=favorites,station_id=station_id,
                search=search,quality=quality,favorites_only=favorites_only,sort_by=sort_by,sort_dir=sort_dir,
                offset=offset,limit=limit)
        except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

    @app.post("/api/engineering/points/{point_id}/favorite")
    def favorite_point(point_id: str, request: Request) -> dict:
        require_local_operator(request)
        try: row=app.state.core.repository.get_record(point_id)
        except EntityNotFound as exc: raise HTTPException(status_code=404,detail="Точка не найдена") from exc
        if row["entity_type"]!="Point": raise HTTPException(status_code=404,detail="Точка не найдена")
        try:
            device=app.state.core.repository.get_record(row["payload"].get("device_id","")) if row["payload"].get("device_id") else {}
        except EntityNotFound:
            device={}
        return app.state.core.point_views.add_favorite(point_id,user_id="local-engineer",station_id=device.get("payload",{}).get("station_id"))

    @app.delete("/api/engineering/points/{point_id}/favorite")
    def unfavorite_point(point_id: str, request: Request) -> dict:
        require_local_operator(request)
        return app.state.core.point_views.remove_favorite(point_id,user_id="local-engineer")

    @app.get("/api/engineering/points/export.csv")
    def export_engineering_points(station_id: str | None = None, search: str | None = None, quality: str | None = None,
                                  favorites_only: bool = False) -> Response:
        import csv, io
        data=engineering_points(station_id=station_id,search=search,quality=quality,limit=5000,offset=0,
                                favorites_only=favorites_only)
        stream=io.StringIO(newline="")
        writer=csv.writer(stream,delimiter=";")
        writer.writerow(["ID","Название","Станция","Тип","Значение","Единица","Качество","Избранное","Native identity"])
        for x in data["points"]:
            writer.writerow([x["id"],x["name"],x["station_id"],x["data_type"],x["value"],x["unit"],x["quality"],"Да" if x["favorite"] else "Нет",x["native_identity"]])
        content="\ufeff"+stream.getvalue()
        return Response(content,media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=avic-points.csv"})

    @app.get("/api/platform/catalog")
    def platform_catalog() -> dict:
        return app.state.core.module_catalog.summary()

    @app.get("/api/platform/catalog/{module_id}")
    def platform_module(module_id: str) -> dict:
        item = app.state.core.module_catalog.get(module_id)
        if item is None: raise HTTPException(status_code=404, detail="Модуль не найден")
        return item

    @app.get("/api/alarms")
    def alarms_list(station_id: str | None = None, state: str | None = None, priority: int | None = None, search: str | None = None, limit: int = 200) -> dict:
        try:
            states=[state] if state else None; priorities=[priority] if priority is not None else None
            return {"alarms":jsonable_encoder(app.state.core.alarms.list_alarms(station_id=station_id,states=states,priorities=priorities,search=search,limit=limit))}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/alarms", status_code=201)
    def alarms_create(payload: AlarmCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            alarm=app.state.core.alarms.raise_alarm(**payload.model_dump())
            app.state.core.audit.append(actor_id="local-engineer", action="alarm.raised", resource_type="alarm", resource_id=alarm.alarm_id, details={"station_id":alarm.station_id,"source_id":alarm.source_id,"priority":alarm.priority})
            return jsonable_encoder(alarm)
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/alarms/{alarm_id}/acknowledge")
    def alarms_acknowledge(alarm_id: str, payload: AlarmAcknowledgeInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            alarm=app.state.core.alarms.acknowledge(alarm_id,**payload.model_dump())
            app.state.core.audit.append(actor_id=payload.actor_id, action="alarm.acknowledged", resource_type="alarm", resource_id=alarm_id, details={"comment":payload.comment,"state":alarm.state.value})
            return jsonable_encoder(alarm)
        except KeyError as exc: raise HTTPException(status_code=404, detail="Авария не найдена") from exc
        except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/alarms/{alarm_id}/return-to-normal")
    def alarms_return(alarm_id: str, payload: AlarmReturnInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            alarm=app.state.core.alarms.return_to_normal(alarm_id,**payload.model_dump())
            app.state.core.audit.append(actor_id="local-engineer", action="alarm.returned_to_normal", resource_type="alarm", resource_id=alarm_id, details={"state":alarm.state.value})
            return jsonable_encoder(alarm)
        except KeyError as exc: raise HTTPException(status_code=404, detail="Авария не найдена") from exc
        except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/alarms/{alarm_id}")
    def alarm_get(alarm_id: str) -> dict:
        try: return jsonable_encoder(app.state.core.alarms.get_alarm(alarm_id))
        except KeyError as exc: raise HTTPException(status_code=404, detail="Авария не найдена") from exc

    @app.get("/api/alarms/{alarm_id}/notes")
    def alarm_notes_list(alarm_id: str) -> dict:
        try: return {"notes": app.state.core.alarms.list_notes(alarm_id)}
        except KeyError as exc: raise HTTPException(status_code=404, detail="Авария не найдена") from exc

    @app.post("/api/alarms/{alarm_id}/notes", status_code=201)
    def alarm_notes_add(alarm_id: str, payload: AlarmNoteInput, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.core.alarms.add_note(alarm_id, **payload.model_dump())
        except KeyError as exc: raise HTTPException(status_code=404, detail="Авария не найдена") from exc
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/alarm-history")
    def alarms_history(station_id: str | None = None, alarm_id: str | None = None, limit: int = 500) -> dict:
        try: return {"events":jsonable_encoder(app.state.core.alarms.history(station_id=station_id,alarm_id=alarm_id,limit=limit))}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/events")
    def events_list(station_id: str | None = None, event_type: str | None = None, severity: str | None = None, since: str | None = None, until: str | None = None, search: str | None = None, limit: int = 200) -> dict:
        try: return {"events": [e.__dict__ if hasattr(e, "__dict__") else {k:getattr(e,k) for k in e.__dataclass_fields__} for e in app.state.core.events.list(station_id=station_id,event_type=event_type,severity=severity,since=since,until=until,search=search,limit=limit)]}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/events", status_code=201)
    def events_create(payload: EventCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            event=app.state.core.events.record(**payload.model_dump())
            app.state.core.audit.append(actor_id=payload.actor_id or "local-engineer", action="event.recorded", resource_type="event", resource_id=event.event_id, details={"event_type":event.event_type,"severity":event.severity})
            return {k:getattr(event,k) for k in event.__dataclass_fields__}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/history/samples", status_code=201)
    def history_append(payload: HistoryCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            sample=app.state.core.history.append(**payload.model_dump())
            app.state.core.audit.append(actor_id="local-engineer", action="history.sample_appended", resource_type="point", resource_id=sample.point_id, details={"station_id":sample.station_id,"quality":sample.quality,"source":sample.source})
            return {k:getattr(sample,k) for k in sample.__dataclass_fields__}
        except (ValueError, TypeError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/points/{point_id}/history")
    def history_query(station_id: str, point_id: str, since: str | None = None, until: str | None = None, limit: int = 5000, include_bad: bool = True) -> dict:
        try:
            rows=app.state.core.history.query(station_id,point_id,since=since,until=until,limit=limit,include_bad=include_bad)
            return {"samples":[{k:getattr(r,k) for k in r.__dataclass_fields__} for r in rows]}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/points/{point_id}/history/rollup")
    def history_rollup(station_id: str, point_id: str, method: str = "average", since: str | None = None, until: str | None = None) -> dict:
        try: return app.state.core.history.rollup(station_id,point_id,since=since,until=until,method=method)
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/dependencies", status_code=201)
    def dependency_add(payload: DependencyCreateInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            edge=app.state.core.dependencies.add(**payload.model_dump())
            app.state.core.audit.append(actor_id="local-engineer", action="dependency.created", resource_type="dependency", resource_id=edge.edge_id, details={"dependent_id":edge.dependent_id,"dependency_id":edge.dependency_id,"relation_type":edge.relation_type})
            return {k:getattr(edge,k) for k in edge.__dataclass_fields__}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/engineering/objects/{object_id}/dependencies")
    def dependency_list(object_id: str) -> dict:
        return {"edges":[{k:getattr(e,k) for k in e.__dataclass_fields__} for e in app.state.core.dependencies.list_for(object_id)],"delete_preview":app.state.core.dependencies.delete_preview(object_id)}

    @app.get("/api/engineering/objects/{object_id}/cleanup-preview")
    def cleanup_preview(object_id: str) -> dict:
        return app.state.core.dependencies.delete_preview(object_id)

    @app.post("/api/notifications/routes", status_code=201)
    def notification_route_add(payload: NotificationRouteInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            route=app.state.core.notifications.add_route(**payload.model_dump())
            app.state.core.audit.append(actor_id="local-engineer", action="notification.route_created", resource_type="notification_route", resource_id=route["route_id"], details={"channel":route["channel"],"enabled":route["enabled"]})
            return route
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/notifications/routes")
    def notification_routes() -> dict: return {"routes":app.state.core.notifications.list_routes()}

    @app.post("/api/notifications/outbox", status_code=201)
    def notification_enqueue(payload: NotificationEnqueueInput, request: Request) -> dict:
        require_local_operator(request)
        item=app.state.core.notifications.enqueue(**payload.model_dump())
        app.state.core.audit.append(actor_id="local-engineer", action="notification.enqueued", resource_type="notification", resource_id=item["message_id"], details={"route_id":item["route_id"],"event_ref":item["event_ref"]})
        return item

    @app.get("/api/notifications/outbox")
    def notification_outbox(limit: int = 200) -> dict:
        try: return {"messages":app.state.core.notifications.list_outbox(limit)}
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/analytics/tags", status_code=201)
    def analytics_tag(payload: AnalyticsTagInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            item=app.state.core.analytics.tag_point(**payload.model_dump())
            app.state.core.audit.append(actor_id="local-engineer", action="analytics.point_tagged", resource_type="point", resource_id=item["point_id"], details={"tag":item["tag"],"dictionary":item["dictionary"]})
            return item
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/analytics/tags/{tag}")
    def analytics_find(tag: str, dictionary: str = "AVIC", hierarchy_prefix: str | None = None) -> dict:
        return {"tag":tag,"dictionary":dictionary,"point_ids":app.state.core.analytics.find_points(tag,dictionary=dictionary,hierarchy_prefix=hierarchy_prefix)}

    @app.post("/api/analytics/aggregate")
    def analytics_aggregate(payload: dict, request: Request) -> dict:
        require_local_operator(request)
        try: return app.state.core.analytics.aggregate(payload.get("values",[]),payload.get("method","average"),missing_strategy=payload.get("missing_strategy","ignore_point"))
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/api/stations/{station_id}/time")
    def time_configure(station_id: str, payload: TimeStationInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            item=app.state.core.time_management.configure_station(station_id,payload.timezone,ntp_enabled=payload.ntp_enabled,ntp_servers=payload.ntp_servers)
            app.state.core.audit.append(actor_id="local-engineer", action="time.station_policy_updated", resource_type="station", resource_id=station_id, details={"timezone":payload.timezone,"ntp_enabled":payload.ntp_enabled})
            return item
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/time")
    def time_station(station_id: str) -> dict: return app.state.core.time_management.station_time(station_id)

    @app.put("/api/stations/{station_id}/devices/{device_id}/time-sync-permission")
    def time_device_permission(station_id: str, device_id: str, payload: TimeDevicePermissionInput, request: Request) -> dict:
        require_local_operator(request)
        try:
            item=app.state.core.time_management.set_device_sync_permission(station_id,device_id,**payload.model_dump())
            app.state.core.audit.append(actor_id=payload.approved_by, action="time.device_sync_permission_changed", resource_type="device", resource_id=device_id, details={"station_id":station_id,"allowed":payload.allowed,"reason":payload.reason})
            return item
        except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/stations/{station_id}/devices/{device_id}/time-sync-permission")
    def time_device_permission_get(station_id: str, device_id: str) -> dict: return app.state.core.time_management.device_sync_permission(station_id,device_id)

    @app.get("/station-transfer", response_class=HTMLResponse, include_in_schema=False)
    def station_transfer_workspace() -> str:
        return render_workspace("station-transfer.html", "transfer")

    @app.get("/api/station-transfer/catalog")
    def station_transfer_catalog(request: Request) -> dict:
        require_local_operator(request)
        records = app.state.core.repository.list_records()
        projects = [row for row in records if row.get("entity_type") == "Project"]
        stations = [row for row in records if row.get("entity_type") == "Station"]
        result = []
        for project in sorted(projects, key=lambda row: row.get("name", "").casefold()):
            result.append({"id": project["entity_id"], "name": project["name"],
                "archived": bool(project.get("payload", {}).get("archived", False)),
                "stations": [{"id": row["entity_id"], "name": row["name"]}
                    for row in sorted(stations, key=lambda item: item.get("name", "").casefold())
                    if row.get("payload", {}).get("project_id") == project["entity_id"]]})
        return {"projects": result, "core_version": "1.0.0.dev148"}

    @app.post("/api/station-transfer/export")
    def station_transfer_export(payload: StationTransferExportInput, request: Request) -> Response:
        require_local_operator(request)
        core = app.state.core
        try:
            station_record = core.repository.get_record(payload.station_id)
            if station_record.get("entity_type") != "Station":
                raise StationTransferError("Выбранный объект не является станцией")
            try:
                runtime = core.runtime.get(payload.station_id)
            except KeyError:
                runtime = None
            if runtime is not None and runtime.state.value != "STOPPED":
                raise StationTransferError("Перед экспортом остановите Station Runtime")
            if any(x.get("state") != "STOPPED" or x.get("enabled")
                   for x in core.driver_manager.list_instances(payload.station_id)):
                raise StationTransferError("Перед экспортом остановите все драйверы станции")
            export_dir = Path(tempfile.mkdtemp(prefix="avic-station-export-"))
            try:
                package_path = export_dir / "station.avicstation"
                core.station_transfer.export_station(
                    core, payload.station_id, package_path, source_core_version="1.0.0.dev148")
                content = package_path.read_bytes()
            finally:
                shutil.rmtree(export_dir, ignore_errors=True)
            return Response(content=content, media_type="application/vnd.avic.station+zip",
                headers={"Content-Disposition": "attachment; filename=avic-station.avicstation",
                         "Cache-Control": "no-store"})
        except StationTransferError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Станция не найдена") from exc

    @app.post("/api/station-transfer/inspect")
    async def station_transfer_inspect(request: Request) -> dict:
        require_local_operator(request)
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > app.state.core.station_transfer.MAX_PACKAGE_BYTES):
            raise HTTPException(status_code=413, detail="Размер пакета превышает допустимый предел")
        expire_station_transfer_tokens()
        if len(app.state.station_transfer_tokens) >= 16:
            raise HTTPException(status_code=429, detail="Слишком много незавершённых операций переноса; завершите или перезапустите Workbench")
        inbox = app.state.core.paths.backups / "station-transfer-inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        token = uuid4().hex
        package_path = inbox / (token + ".avicstation")
        total = 0
        try:
            with package_path.open("xb") as stream:
                async for chunk in request.stream():
                    total += len(chunk)
                    if total > app.state.core.station_transfer.MAX_PACKAGE_BYTES:
                        raise HTTPException(status_code=413, detail="Размер пакета превышает допустимый предел")
                    stream.write(chunk)
            if total == 0:
                raise HTTPException(status_code=400, detail="Пустой пакет станции")
            preview = app.state.core.station_transfer.inspect_package(
                package_path, target_core_version="1.0.0.dev148")
        except HTTPException:
            package_path.unlink(missing_ok=True)
            raise
        except StationTransferError as exc:
            package_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            package_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Не удалось прочитать пакет станции") from exc
        if not preview.compatible:
            package_path.unlink(missing_ok=True)
        else:
            app.state.station_transfer_tokens[token] = {
                "package_path": package_path, "package_id": preview.package_id,
                "stage_path": None, "created_at": monotonic()}
        warnings = list(preview.warnings) + [
            "Пакет не имеет цифровой подписи издателя. Его происхождение не подтверждено; проверьте источник файла."]
        return {
            "upload_token": token if preview.compatible else None, "package_id": preview.package_id,
            "station_id": preview.station_id, "station_name": preview.station_name,
            "source_project_id": preview.source_project_id,
            "source_core_version": preview.source_core_version,
            "target_core_version": "1.0.0.dev148",
            "entity_count": preview.entity_count,
            "auxiliary_record_count": preview.auxiliary_record_count,
            "compatible": preview.compatible, "warnings": warnings,
            "trust_status": "UNSIGNED_UNVERIFIED",
            "requires_unsigned_acknowledgement": True,
            "activation": "NOT_ACTIVATED"}

    @app.post("/api/station-transfer/stage")
    def station_transfer_stage(payload: StationTransferStageInput, request: Request) -> dict:
        require_local_operator(request)
        expire_station_transfer_tokens()
        item = app.state.station_transfer_tokens.get(payload.upload_token)
        if not item or item.get("package_id") != payload.package_id:
            raise HTTPException(status_code=404, detail="Загрузка пакета не найдена или устарела")
        if not payload.acknowledge_unsigned:
            raise HTTPException(status_code=400, detail="Требуется явное подтверждение, что пакет не подписан издателем")
        if item.get("stage_path") is not None:
            raise HTTPException(status_code=409, detail="Этот пакет уже подготовлен к импорту")
        try:
            stage_path = app.state.core.station_transfer.stage_import(
                item["package_path"], app.state.core.paths.backups / "station-transfer-staging",
                expected_package_id=payload.package_id, target_core_version="1.0.0.dev148")
            item["stage_path"] = stage_path
            return {"stage_token": payload.upload_token, "package_id": payload.package_id,
                    "state": "STAGED_NOT_ACTIVATED", "activation": "NOT_ACTIVATED"}
        except StationTransferError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/station-transfer/commit")
    def station_transfer_commit(payload: StationTransferCommitInput, request: Request) -> dict:
        require_local_operator(request)
        expire_station_transfer_tokens()
        item = app.state.station_transfer_tokens.get(payload.stage_token)
        if not item or item.get("package_id") != payload.package_id or item.get("stage_path") is None:
            raise HTTPException(status_code=404, detail="Подготовленный пакет не найден или устарел")
        expected = "CLONE" if payload.mode == "clone" else "IMPORT"
        if payload.confirmation != expected:
            raise HTTPException(status_code=400, detail="Для подтверждения введите " + expected)
        if payload.mode == "clone" and not payload.clone_station_name:
            raise HTTPException(status_code=400, detail="Для клона требуется новое имя станции")
        try:
            target = app.state.core.repository.get_record(payload.target_project_id)
            if target.get("entity_type") != "Project" or target.get("payload", {}).get("archived", False):
                raise StationTransferError("Выберите действующий целевой проект")
            if payload.mode == "clone":
                duplicate = [row for row in app.state.core.repository.list_records(entity_type="Station")
                    if row.get("payload", {}).get("project_id") == payload.target_project_id
                    and row.get("name", "").casefold() == payload.clone_station_name.strip().casefold()]
                if duplicate:
                    raise StationTransferError("В целевом проекте уже есть станция с таким именем")
            result = app.state.core.station_transfer.commit_import(
                app.state.core, item["stage_path"], expected_package_id=payload.package_id,
                target_project_id=payload.target_project_id, actor="local-engineer",
                clone=payload.mode == "clone", clone_station_name=payload.clone_station_name)
            package_path, stage_path = item["package_path"], item["stage_path"]
            app.state.station_transfer_tokens.pop(payload.stage_token, None)
            package_path.unlink(missing_ok=True)
            shutil.rmtree(stage_path, ignore_errors=True)
            return {**result, "activation": "NOT_ACTIVATED",
                "message": "Импорт завершён. Станция остановлена; выполните привязку площадки и пусконаладку вручную."}
        except StationTransferError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except EntityNotFound as exc:
            raise HTTPException(status_code=404, detail="Целевой проект не найден") from exc

    @app.get("/api/platform/status")
    def platform_status() -> dict:
        records = app.state.core.repository.list_records()
        counts = {}
        for row in records:
            counts[row["entity_type"]] = counts.get(row["entity_type"], 0) + 1
        runtime = [{"station_id": item.station_id, "state": item.state.value,
                    "generation": item.generation, "last_error": item.last_error}
                   for item in app.state.core.runtime.all()]
        backup_files = sorted(p.name for p in app.state.core.paths.backups.glob("*.avicbackup.zip") if p.is_file())
        return {"product": "AVIC Engineering & Automation Platform", "version": "1.0.0.dev77",
                "core_open": not app.state.core.closed, "object_counts": counts,
                "runtime_stations": runtime, "backup_archives": backup_files,
                "safety": {"driver_autostart": False, "field_writes_enabled": False,
                           "discovery_mode": "explicit-read-only", "simulation_is_offline": True,
                           "trend_integration_required": False, "tonn_linux_agent_implemented": False}}

    @app.get("/api/ui/manifest")
    def manifest() -> dict:
        return {
            "product": "AVIC Engineering & Automation Platform",
            "version": "1.0.0.dev77",
            "mode": "engineering-workbench-project-station",
            "execution_enabled": False,
            "network_discovery_enabled": False,
            "field_commands_enabled": False,
            "workspace_count": len(WORKSPACES),
            "module_catalog": app.state.core.module_catalog.summary(),
            "workspaces": [
                {"id": item[0], "title": item[1], "description": item[2], "icon": item[3], "status": item[4]}
                for item in WORKSPACES
            ],
            "roles": ROLES,
            "capabilities": {
                "command_palette": True,
                "workspace_search": True,
                "tabbed_workspaces": True,
                "collapsible_panels": True,
                "guided_onboarding_preview": True,
                "persistent_layout_preferences": "browser-local",
                "project_station_persistence": True,
                "project_station_api": True,
                "bacnet_ip_discovery": "explicit-read-only-manual-trigger",
                "discovery_history": "persistent-session-journal",
                "point_import_preview": "non-mutating-preview-before-import",
                "modbus_tcp_read": "explicit-read-only",
                "physical_network_protocol_topology": True,
                "audit_trail": True,
                "mutation_security": "loopback-only-development-guard",
                "server_rbac_integration": False,
                "web_pages_tree_persistence": True,
                "web_pages_crud_move_delete": True,
                "web_pages_url_collision_validation": True,
                "web_pages_graphic_assignment": True,
                "web_pages_visual_layout_model": True,
                "web_pages_customer_publishing": False,
                "web_pages_local_operator_publishing": True,
                "web_pages_visual_page_editor": True,
                "web_pages_versioned_publish_snapshot": True,
                "svg_symbol_library": True,
                "svg_symbol_count": len(SVG_SYMBOLS),
                "graphics_svg_insertion": True,
                "modular_ahu_section_count": 7,
                "modular_ahu_sections": True,
                "svg_binary_state_animation": True,
                "ahu_airflow_visualization": "fan-running-and-outdoor-damper-open",
                "ahu_local_animation_preview": True,
                "fbd_station_picker": True,
                "fbd_document_open": True,
                "fbd_port_to_port_wiring": True,
                "fbd_offline_simulation": True,
            },
        }

    @app.get("/api/ui/health")
    def ui_health() -> dict:
        return {"status": "ok", "ui": "available", "version": "1.0.0.dev109", "mode": "safe-workbench-project-station"}

    return app
