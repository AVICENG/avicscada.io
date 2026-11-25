# IQVISION 2.30 → AVIC: сравнение первых 30 разделов

**Источники:** IQVISION Configuration Manual TE201382 Issue 7 (22.11.2019), IQVISION User Manual TE201434 Issue 1, DEV62 source tree, API, UI и тесты. Срез кода — DEV62; изменения визуальной темы и release guards — DEV63.

## Как считаются «первые 30»

В Configuration Manual только **20 основных нумерованных глав**. После них идут приложения. Чтобы дать требуемые 30 пунктов без выдумывания глав 21–30, здесь используются главы 1–20 и приложения A1–A10 как позиции 21–30. Это не означает, что приложения являются главами оригинального руководства. User Manual рассматривается как дополнительный источник операторских сценариев (его главы 1–6 перекрывают темы 2, 17–20 Configuration Manual).

Статусы: **Частично** — есть часть работающего кода, но не закрыт полный пользовательский сценарий; **Не реализовано** — рабочая функция не найдена; **Необязательно** — владелец продукта исключил её из блокирующих требований AVIC; **Запланировано** — направление закреплено, но реализации нет. Ни один статус «Частично» не считается завершением.

## Главы 1–20 Configuration Manual

| № | Раздел оригинала | Что требуется | Состояние AVIC по DEV62 | Что требуется для закрытия / приоритет DEV63+ |
|---:|---|---|---|---|
| 1 | About This Manual | Согласованные руководства, ссылки, терминология, обучение | Частично: отдельные русские документы есть, единого полного набора нет | Единая справка, индекс, версии документов, инструкции по каждому экрану и сценарию |
| 2 | About IQVISION | Platform/Station, Workbench, Nav Tree, Palette, Locator, View Pane, tabs, client devices | Частично: Workbench, дерево, Locator/вкладки и редакторы есть; Platform Manager и полноценная Palette неполны | Единая модель объектов/views, Palette с реальным добавлением, инспектор, адаптивный web UI и проверка всех переходов |
| 3 | Securing IQVISION | Hardening, физическая/сетевая защита, обновления, учётные записи, аутентификация, GDPR | Частично: SecretStore, auth/RBAC/MFA foundations, аудит и break-glass; enforcement не на всех API | Server-side RBAC на каждом изменяющем endpoint, сессии, TLS/cert lifecycle, hardening checklist, negative authorization matrix |
| 4 | Engineering Procedure | Полный путь инженерии от установки/сети до ввода в эксплуатацию и резервирования | Частично: Engineering Workflow диагностирует этапы; не является мастером ввода | Wizard, Discovery→preview→import→FBD→graphics→simulation→commissioning report/sign-off; все ветви и откаты |
| 5 | Install IQVISION | Установка, Platform Daemon/service, firewall, upgrade | Частично: Python package/CLI; нет полноценного Windows installer/service lifecycle | Windows clean install/upgrade/uninstall/rollback, firewall rules, service recovery и acceptance на чистой машине |
| 6 | License IQVISION | Лицензия, сертификат, установка/проверка лицензии | Частично: AVIC Host-ID/offline signed license foundation; нет полного эксплуатационного UI активации/переноса/отзыва | UI activation, offline request/response, revoke/transfer, лимиты точек, expiry и tamper tests |
| 7 | Initial Setup | Первый запуск, platform/station, базовые сервисы и credentials | Частично: CLI init и Project/Station foundation | First-run wizard, проверка директорий/прав/сети, безопасное создание администратора, повторный запуск без повреждения данных |
| 8 | Build a Trend Site | Trend System/Module discovery, импорт, reconnect, миграция | Необязательная интеграция по решению владельца продукта | Не блокирует AVIC. Общие Discovery/identity/import должны работать независимо от Trend; Trend-specific миграция не входит в обязательный паритет |
| 9 | Connect to TONNs | TONN/TONN8 discovery, Allowed Hosts, импорт точек | Не реализовано; стратегическое направление AVIC Linux Controller Agent | Не имитировать TONN. Спроектировать собственный Linux Agent/northbound protocol, secure provisioning, identity, points, diagnostics, OTA и offline autonomy отдельным этапом |
| 10 | Connect to Third Party Systems | Driver packages/configuration, BACnet discovery, device/point import | Частично: BACnet/IP, Modbus TCP foundations, Discovery, import preview, Driver Manager foundation | Multi-protocol job manager, Modbus import, driver SDK/package signature/versioning, reconnect, polling, subscription, lifecycle, negative network paths |
| 11 | Configure Time Schedule Control | Individual/Master/Calendar schedules, execution, special events, export, time management | Частично: schedule service/API, weekly events, special events, copy day, evaluation | Полный visual week/calendar editor, typed values, priorities/conflicts, master schedule, import/export, executor, DST/timezone tests |
| 12 | Configure Alarm Handling | Ingestion, alarm classes/priorities/filters, recipients, email, sound, portals | Частично: lifecycle, acknowledge, notes, history, console foundation | BACnet/network ingestion, class/filter ordering, routing, delivery adapters, escalation, sound controls, multi-station portal, authorization |
| 13 | Create Schematics (PX Pages) | PX folders/pages/templates, static/dynamic widgets, animation, sliders/buttons, links, history, schedule, dashboards, reuse | Частично: Graphics Workbench, HVAC assets, point bindings, page services, FBD links | Complete widget catalog, SVG import/editor/sanitizer, dynamic runtime renderer, authorized actions, history/schedule widgets, template relativisation |
| 14 | Set Up IQVISION Users | Categories, roles, users, NAV files, PIN levels | Частично: security primitives and role concepts; full administration UI and universal enforcement absent | User/group/category CRUD, role inheritance, object scopes, navigation scopes, PIN/password policy, server enforcement, session expiry tests |
| 15 | Backup and Restore | Station/config backup, Backup Service, Station Copier, restore from archive | Частично: backup archive/preview/restore primitives | Consistent station backup, manifest/checksum, secret policy, compatibility preview, restore drill, schedule, failure recovery and audit |
| 16 | Using IQVISION | Complete day-to-day operator/engineer usage instructions | Частично: scattered Russian docs and workflows | Role-based operator/engineer/admin manuals, training station, troubleshooting and end-to-end exercises |
| 17 | Access IQVISION | Desktop/web launch, login/logout | Частично: local Workbench route; production session lifecycle incomplete | Login/logout, idle timeout, session invalidation, browser refresh/reconnect, denied route tests, audit trail |
| 18 | Use IQVISION | PX, dashboards, Nav Tree, point value changes, schedules, history | Частично: tree/editors and data services; production operator command path incomplete | Runtime rendering, point commands via Command Manager/interlocks, read-back, schedules/history from operator pages, all permissions |
| 19 | Points List View | Live/Engineering modes, sort/group/filter/favorites, adjust/override, CSV, histories, schedules | Частично: DEV52 persistent favorites/filter/sort/pagination/CSV/history navigation; no full adjustment workflow | Grouping/modes, quality filters, adjust/override with priority/interlock/audit, schedule edit, details, export quality and pagination paths |
| 20 | Viewing Alarms | Console, Alarm History, Alarm Portal, acknowledge | Частично: Alarm Console/state/history/notes/ack foundation | Full history query, portal, multi-station scope, filters, role enforcement, mass operations, sound/routing and browser workflows |

## Позиции 21–30: приложения A1–A10

| № | Приложение | Что описано в IQVISION | Состояние AVIC по DEV62 | Что требуется / решение |
|---:|---|---|---|---|
| 21 | A1 — Migrate Existing Trend Sites into IQVISION | Экспорт из 963/IQSET, Migration Tool, проверка устройств/точек/PX | Не реализовано | Trend-specific миграция необязательна и не блокирует AVIC. В DEV63 только фиксируется как исключённая интеграция; общий импорт AVIC обязан иметь preview, mapping, validation, rollback |
| 22 | A2 — Use IQ4's B-BC Features | IQ4 BACnet schedules, schedule export/PX, BACnet backup/restore, alarm acknowledgement | Частично по общим BACnet/schedule foundations; IQ4 B-BC workflow не реализован | Отдельный IQ4 adapter/profile, schedule export/import, backup/restore over BACnet и alarm ack; не считать generic BACnet поддержкой этих функций |
| 23 | A3 — Use the Extended Support Options | Платные расширения: Alarm Portal на удалённом ПК, интеграции с Excel/CSV, MySQL, Oracle 11G и SQL | Частично: есть отдельные лицензирование/Alarm/CSV foundations, но нет полного набора entitlement-gated интеграций | Матрица лицензий/возможностей, удалённый Alarm Portal, Excel/CSV и SQL/MySQL/Oracle adapters, секреты в SecretStore, проверки лицензии/истечения/отказа соединения |
| 24 | A4 — Facets | Units, min/max ranges, precision | Частично: базовые metadata/validation есть, сквозной facets editor и единое отображение не подтверждены | Общая schema units/range/precision, преобразование единиц, validation, UI inspector, trend/CSV consistency |
| 25 | A5 — Using the Lexicon Tool | Переводы/лексиконы интерфейса | Не реализовано как управляемая система | Translation catalog, fallback language, missing-key detector, terminology register, Russian-first and English fallback tests |
| 26 | A6 — IQVISION Memory Allocation | Распределение памяти и ресурсные настройки | Не реализовано как инженерный инструмент | Runtime memory budgets, per-station limits, load profile, leak/soak tests, alerts and safe limits; not just display process RAM |
| 27 | A7 — Printing from IQVISION | Печать из Workbench | Не реализовано как сквозной сценарий | Print styles for graphics/points/alarms/reports, page breaks, headers/footers, print preview and PDF/browser print acceptance |
| 28 | A8 — Application Director | Start/restart station, application lifecycle | Частично: CLI init/health and runtime foundations; UI lifecycle manager absent | Start/stop/restart with RBAC, watchdog, restart policy, logs, stale process handling, crash recovery and idempotent commands |
| 29 | A9 — Export Histories to an SQL Database | SQL connection, schema/user setup, history export | Не реализовано | SQL export adapter, credentials in SecretStore, checkpoints/retries, duplicate protection, schema migration and data integrity tests |
| 30 | A10 — Export Histories to a CSV File | Export historical data to CSV | Частично: point inventory CSV exists; history CSV export is not established | Time-range history CSV with timestamps/timezone, units, quality, encoding, escaping, size limits, audit and round-trip tests |

## Вывод по приоритетам

- Trend-specific главы/приложения (§8, A1) не блокируют самостоятельную AVIC.
- TONN (§9) не заменяется BACnet; будущий Linux Controller Agent должен иметь отдельный проектный контракт и испытания.
- Самые опасные функциональные разрывы: server-side RBAC, реальный station/runtime lifecycle, безопасные команды, полные driver lifecycles, execution schedule, alarm routing, PX runtime, backup/restore, history export.
- Приложения A2–A10 нельзя пропускать только потому, что они расположены после основных глав: они содержат реальные эксплуатационные функции.

## DEV63 release gates

1. Сохранность DEV55–DEV62: ни один ранее существовавший пакет, публичный API, экран или тест не удаляется без явной миграции/замены и записи в changelog.
2. Все четыре Workbench HTML entrypoints (`/`, `/pages`, `/logic`, `/graphics`) должны отвечать 200, иметь общую тему и не содержать сломанных внутренних ссылок.
3. Каждая зарегистрированная API route должна быть учтена в route inventory; каждый изменяющий endpoint должен иметь позитивный, негативный, ownership и authorization test. Пока серверный RBAC не интегрирован, это фиксируется как blocker, а не маскируется тестом UI.
4. Тесты сервиса, API, UI, negative paths, boundary cases, persistence/restart, cross-station isolation и rollback должны считаться отдельно.
5. Полный `pytest -q` должен завершиться; если нет — сборка получает статус «регрессия не завершена», независимо от количества целевых тестов.
6. Windows acceptance и browser interaction acceptance — отдельные обязательные стадии; Python TestClient не заменяет реальный браузер.
7. Сборка не может быть объявлена без тупиков, пока не проверены переходы от объекта к его views/actions и обратно, а также ошибки/отказы каждого шага.
