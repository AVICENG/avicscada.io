# DEV49 — журнал сборки и испытаний

## Изменения
- Добавлены EventService, HistoryService, DependencyService, AnalyticsService, NotificationService, TimeManagementService и ModuleCatalog.
- Подключены API/UI для Alarm Console, Event Manager, History Manager, Point Manager, Cleanup Manager, Analytics, Notification Manager, Time Manager и Module Catalog.
- Alarm transitions публикуются в EventService через alarm outbox.
- Новые изменения журналируются в AuditService.
- Delete endpoint блокирует удаление при наличии зарегистрированных зависимых объектов.
- Обновлены версия FastAPI и pyproject до 1.0.0.dev49.
- Добавлена документация IQVISION parity и перечень модулей Niagara.

## Результаты локальной проверки
- `python -m compileall -q avic_core` — PASS.
- `python -m pytest -q` — 253 passed.
- `node --check` для JS из index.html — PASS.
- FastAPI smoke: `/`, `/api/ui/manifest`, `/api/platform/catalog`, `/api/events`, `/api/alarms`, `/api/notifications/routes` — HTTP 200.
- Workbench manifest — 49 направлений.
- Module Catalog — 37 подсистем.

## Ограничения и статус
- Windows browser acceptance — NOT RUN.
- Production authentication / server RBAC — NOT COMPLETE.
- Transport senders — NOT CONNECTED.
- Electronic Signature — requirement/contract only.
- Full PX palette/widget parity, FBD editor and complete PDM scan — NOT COMPLETE.
- DependencyService blocks deletion only for explicitly registered edges; it does not yet auto-scan every document.
- Time sync permission is stored; device clock write is not implemented.
- No field writes were added.

## Приёмка
DEV49 — development foundation build. It is not approved for production OT control.
