# AVIC Core 1.0 — DEV49 IQVISION Parity Foundation

## Цель

На основе DEV48 расширить платформу от отдельного Scheduler Editor к реестру инженерных служб и набору рабочих интерфейсов по функциональному охвату IQVISION 2.30.

## Что добавлено

### Core services
- `EventService`: persistent operational event journal, severity, station/source, correlation ID, time filtering and retention operation.
- `HistoryService`: persistent point samples, quality-aware query and numeric rollup (average/sum/min/max/median/last/count).
- `DependencyService`: explicit dependency edges, reverse lookup and deletion preview.
- `AnalyticsService`: persistent point tags, dictionary names, hierarchy path search, aggregation and missing-data policies.
- `NotificationService`: persistent route registry and delivery outbox. No transport adapter is activated.
- `TimeManagementService`: persistent station timezone/NTP policy and explicit per-device time-sync permission with approver and reason.
- `ModuleCatalog`: 37 functional service descriptors with source references, service owner, capabilities and conservative readiness status.

### Alarm / event / history / point interfaces
- Alarm Console now reads persistent alarms, acknowledges and returns alarms to normal, and displays transition history.
- Event Manager displays operational event stream separately from alarm history and Audit.
- History Manager queries point samples and rollup.
- Point Manager lists point inventory with station/search/quality filters.
- Cleanup Manager displays registered dependencies before removal; it does not yet scan every editor's documents automatically.
- Analytics page supports point tagging and aggregate calculations.
- Notification Manager manages routes and outbox records; sending is not enabled.
- Time Manager edits station timezone/NTP policy and reads local/UTC time.
- Module Manager displays 37 service areas, capability descriptions, source references and actual readiness status.

### Integration
- Alarm transitions are published to the operational EventService via the durable alarm outbox.
- Significant mutations in the new API surfaces are written to AuditService.
- Existing BACnet/Modbus field command restrictions remain in force. DEV49 does not add field write operations.

## What is not complete
- Production authentication and server-side RBAC.
- Actual Email/Telegram/Push/Webhook transport adapters.
- Full electronic signature workflow and qualification.
- Full IQVISION PX widget/palette editor parity and relative template binding.
- Full FBD / Program editors.
- Automatic dependency discovery from every graphic, logic, alarm, history, analytics and favorite reference.
- Full KNN analytics, predefined algorithm library and smart-alert configuration UI.
- Full master schedule export/import, complete Alarm Classes/filters/Alarm Portal parity.
- Full Windows browser acceptance.

## Tests

DEV49 test report: 253 passed. `compileall` and JavaScript syntax checks pass. FastAPI smoke tests cover Workbench, Module Catalog, Alarm API, Event API, History API, Dependency API, Notification API and Time Manager API. These are automated tests in the development environment; Windows browser acceptance remains outstanding.

## Safety notes

- Event, Audit, Alarm History and History Samples remain separate data domains.
- Scheduler remains a schedule-intent service; it does not write field values.
- Notification outbox records are queued but not sent.
- Time synchronization permissions are stored but no device clock write is performed.
- Dependency deletion preview blocks deletion only for dependencies explicitly registered in DependencyService. It is not yet a complete automatic scanner.
- User-selectable UI role profiles are not treated as authorization.
