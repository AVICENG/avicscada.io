# DEV50 — обязательная программа продолжения

DEV49 — не завершённая IQVISION-копия. Это первый платформенный прирост: добавлены несколько реально работающих служб и интерфейсов, а весь оставшийся функциональный охват внесён в Parity Register.

## Приоритет 1 — завершить вертикальные инженерные цепочки
1. Канонические связи Point ↔ Graphics ↔ Logic ↔ Alarm ↔ History ↔ Analytics ↔ Schedule.
2. Автоматическая регистрация зависимостей при создании/изменении привязок.
3. Полный Point Database Manager: usage selectors (graphics, links, alarm extensions, history, favorites, analytics, linked plots), label criteria, saved criteria, backup-before-delete, audit log and restore path.
4. Подключить Runtime acquisition к History и Event Manager с quality transitions.

## Приоритет 2 — интерфейсы IQVISION parity
1. Graphics/PX Editor: page size/background, static text/image, dynamic value, animated image, slider/buttons, page link, history graph, schedule widget, dashboard widgets.
2. Palettes: symbol folders, custom palette builder, import/version compatibility, relative bindings.
3. Scheduler: master schedules, calendar schedules, export/import special events, execution time, occupation calendars, timezone/DST acceptance.
4. Alarm Manager: alarm classes, priority policy, ordered modification filters, recipients, email transport adapter, warning configuration and multi-station portal.
5. Analytics: dictionaries, hierarchy editor, KNN missing-data strategy, algorithm/block library, smart alerts and reports/charts.

## Приоритет 3 — платформа и безопасность
- Electronic Signature: reason sets, secured zones/points, single/dual approval, signer identity and immutable signed records.
- Users/Categories/Roles, session management and server-side object RBAC.
- Backup/Restore workflow, backup verification, station copy and recovery acceptance.
- Driver/Module Manager: module metadata, runtime/workbench/UX/docs separation, dependencies and signature policy.
- Time Manager: NTP monitoring and explicit BACnet time-sync action after separate authorization.

## Критерии готовности
- No workspace may be labeled implemented unless a real service/API, persistence, authorization, documentation and acceptance test exist.
- Every page in the unified Workbench uses the same object IDs and shared property/binding model.
- No field command may bypass Command Manager and equipment interlocks.
- Windows acceptance must cover all visible editors and service screens, not just pytest.
