from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class ModuleDescriptor:
    id: str
    name: str
    group: str
    purpose: str
    status: str
    service: str
    source: str
    capabilities: tuple[str, ...]

# Status is intentionally conservative: implemented means a callable Core service/API exists;
# partial means some operations exist but the complete engineering workflow is not accepted;
# interface means only the Workbench destination/contract exists; planned means no operational UI yet.
_MODULES = (
("platform","Platform Manager","Platform","Host, installation, platform daemon and system configuration.","partial","CoreApplication","IQVISION Configuration Manual §2, §5–7",("platform health","installation identity","station hosting")),
("projects","Project & Station Manager","Engineering","Projects, stations, lifecycle, configuration and object tree.","partial","CoreObjectService / ProjectStationService","IQVISION Configuration Manual §7–8",("project CRUD","station CRUD","engineering tree")),
("network","Network Manager","Connectivity","Physical networks, interfaces, protocol channels and topology.","partial","Network services","IQVISION Configuration Manual §8–10",("interface inventory","BACnet/IP","Modbus TCP")),
("discovery","Discovery Manager","Connectivity","Read-only discovery, device inspection, import and point selection.","partial","BACnetIpClient / DeviceImportService","IQVISION Configuration Manual §8–10",("BACnet discovery","device identity","point import")),
("drivers","Driver Manager","Connectivity","Driver catalog, configuration, lifecycle and protocol adapters.","partial","DriverCatalog / RuntimeManager","IQVISION Configuration Manual §2.1.3, §10",("driver catalog","BACnet/IP","Modbus TCP","Trend IQ3")),
("points","Point Manager","Engineering","Point database, typed values, quality, labels, filters and imports.","partial","CoreObjectService / DeviceImportService","IQVISION Configuration Manual §8–10; Point Database Manager Manual §2–4",("point inventory","typed points","quality metadata")),
("cleanup","Point Database Cleanup","Engineering","Search unused points, inspect references, backup and controlled cleanup.","partial","DependencyService","Point Database Manager Manual §2–6",("dependency preview","label search","safe deletion gate")),
("graphics","Graphics / PX Editor","Engineering","Schematics, widgets, images, dynamic text, sliders, links and charts.","partial","GraphicsService","IQVISION Configuration Manual §13; docGraphics",("graphics documents","typed bindings","widget tree")),
("palettes","Graphics Palettes","Engineering","Reusable symbols, widget palettes, Easy Widgets and custom libraries.","interface","ModuleCatalog","IQVISION Configuration Manual §13.5, §13.12; IQVISION2.30 palette archive",("symbol library","custom palettes","relative bindings")),
("web-pages","Web Pages","Engineering","Web page tree, page composition, URLs and graphics assignment.","partial","WebPagesService","IQVISION User Manual §2; AVIC DEV44–48",("page tree","CRUD/move","graphic assignment")),
("logic","Logic / Wiresheet","Engineering","Persistent FBD editor, typed links, validation and offline simulation.","partial","FBDService","docKitControl; Niagara module inventory",("block library contract","links","validation")),
("programs","Program Editor","Engineering","Text-based programs and script modules.","interface","EngineeringLifecycleService","Niagara module inventory: program, bajaScript",("program documents","validation contract")),
("scheduler","Schedule Manager","Operations","Weekly Boolean/Enum/Numeric/String schedules, calendar exceptions, master schedules and time management.","partial","ScheduleService","IQVISION Configuration Manual §11; docScheduling",("weekly schedules","special events","copy day","evaluation")),
("alarms","Alarm Manager","Operations","Alarm classes, priorities, filters, source transitions, recipients and Alarm Portal.","partial","AlarmService","IQVISION Configuration Manual §12; IQVISION User Manual",("alarm state machine","acknowledgement","alarm history")),
("events","Event Manager","Operations","Operational event journal for station, device, runtime, schedule and system events.","implemented","EventService","Niagara module inventory: logHistory; AVIC architecture separation",("persistent events","filters","correlation")),
("history","History Manager","Operations","Point histories, quality-aware samples, query, rollup and retention.","implemented","HistoryService","docHistories; IQVISION Configuration Manual §8.5, §13.9.9",("sample persistence","quality","aggregation rollup")),
("audit","Audit Manager","Security","Actor/action/object/old-new/result journal and integrity verification.","partial","AuditService","docStationSecurity; Electronic Signature manuals",("append-only audit","hash chain","actor/action")),
("analytics","Analytics Manager","Intelligence","Tags, hierarchies, aggregation, rollup, missing-data strategies, algorithms and smart alerts.","partial","Analytics primitives / ModuleCatalog","Analytics Data Sheet TA201430",("tag/hierarchy contract","aggregation","rollup","alerts contract")),
("notifications","Notification Manager","Operations","Alarm recipients, email routing, delivery queue and escalation policies.","partial","NotificationService","IQVISION Configuration Manual §12.1.14–17; alarm module docs",("recipient routes","durable outbox","delivery status")),
("security","Security Manager","Security","Users, roles, categories, authentication, access policies and secured operations.","partial","Security services","IQVISION Configuration Manual §3, §14; docStationSecurity",("RBAC foundations","MFA foundations","role model")),
("signature","Electronic Approval","Security","Reason sets, signed changes, dual approval and protected operation records.","interface","Approval contract","Niagara Electronic Signature Module V2.1 User Guide; Part 11 analysis",("reason sets","single approval","dual approval")),
("backup","Backup & Restore","Platform","Installation/project backup, restore preview and recovery; Station transfer is a separate service.","partial","ProjectBackupManager / StationTransferManager","IQVISION Configuration Manual §15; docBackupRestore",("legacy project backup archive","restore preview","integrity check","Station export/import is separate")),
("licensing","License Manager","Platform","Host identity, signed license, point capacity and feature entitlements.","partial","LicenseService","IQVISION Configuration Manual §6; AVIC licensing specification",("host identity","signed license","point usage")),
("time","Time Manager","Platform","Timezone, station clock, NTP and explicitly permitted device time synchronization.","interface","TimeManagementService","IQVISION Configuration Manual §11.9; TONN8 Configuration Manual §8",("timezone policy","clock status","per-device permission")),
("runtime","Station Runtime","Runtime","Station lifecycle, workers, watchdog and isolated execution.","partial","RuntimeManager","IQVISION Configuration Manual §2.1.6; TONN8 Configuration Manual §2.3",("station lifecycle","health","controlled startup")),
("supervisor","Supervisor","Distributed","Central monitoring of multiple stations and global views.","interface","Supervisor contract","Niagara module inventory: dashboard, cloud, station services",("station overview","global alarms","published data")),
("backup-replication","Cloud / Remote Backup","Distributed","Remote backup, station synchronization and recovery workflows.","interface","Backup contracts","Niagara module inventory: cloudBackup, cloudConnector",("remote backup contract","replication policy")),
("asset","Asset Manager","Engineering","Asset hierarchy, equipment passport, work orders and maintenance references.","partial","EngineeringLifecycleService","Niagara module inventory: docAssetManager; AVIC lifecycle contracts",("asset hierarchy","passport","work order")),
("relations","Relations Manager","Engineering","Explicit object relationships and dependency navigation.","partial","DependencyService","docRelations; Point Database Manager Manual §4",("dependency edges","delete preview","reference lookup")),
("tags","Tagging & Hierarchies","Engineering","Tag dictionaries, custom tags and searchable asset/point hierarchy.","interface","Analytics contract","Analytics Data Sheet TA201430; docTagging; docHierarchies",("tag dictionaries","hierarchy","tag search")),
("reports","Reports & Dashboards","Intelligence","Tables, charts, dashboards, report viewer and export.","interface","Reporting contract","Analytics Data Sheet TA201430; IQVISION Configuration Manual §13.9.11",("dashboard widgets","chart types","report viewer")),
("integrations","Integrations & API","Integration","External drivers, OPC, MQTT, oBIX, SNMP and API endpoints.","partial","Public API / DriverCatalog","Niagara module inventory and docDrivers",("REST API","driver extension points","protocol catalog")),
("commissioning","Commissioning","Operations","Online/offline engineering, commissioning wizard and test records.","partial","EngineeringLifecycleService","TONN8 Configuration Manual §5, §7",("offline workflow","commissioning phases","test records")),
("iptools","IP Tools","Connectivity","Network interface inventory and safe diagnostics.","partial","network.interfaces","IQVISION Configuration Manual §3, §8–10; AVIC network design",("interface list","read-only network tools")),
("deployment","Deployment & Updates","Platform","Station-scoped engineering transfer, portable project packages, compatibility checks and staged import.","partial","StationTransferManager / DeploymentManager","Niagara Platform Guide: Station Copier; AVIC deployment design",(".avicstation Station export","engineering object ID preservation","target Project rebinding","site endpoint sanitization","auxiliary configuration transfer","staged import and explicit commit","activation and rollback not yet implemented")),
("modules","Module Manager","Platform","Installed module inventory, versions, dependencies, signatures and enablement.","partial","ModuleCatalog","Niagara module inventory: *-rt, *-ux, *-wb, *-doc",("module catalog","layer separation","compatibility metadata")),
("diagnostics","Diagnostics & Health","Platform","Health, service status, logs, performance and diagnostics.","partial","CoreHealthService","IQVISION Configuration Manual §3.9; Niagara System Monitor",("core health","runtime status","service catalog")),
)

_MODULES = tuple(ModuleDescriptor(*row) for row in _MODULES)

class ModuleCatalog:
    def list(self) -> list[dict]: return [asdict(m) for m in _MODULES]
    def get(self,module_id:str)->dict|None:
        for item in _MODULES:
            if item.id==module_id: return asdict(item)
        return None
    def summary(self)->dict:
        counts={s:sum(1 for m in _MODULES if m.status==s) for s in ('implemented','partial','interface','planned')}
        return {'total':len(_MODULES),'status_counts':counts,'modules':self.list()}
