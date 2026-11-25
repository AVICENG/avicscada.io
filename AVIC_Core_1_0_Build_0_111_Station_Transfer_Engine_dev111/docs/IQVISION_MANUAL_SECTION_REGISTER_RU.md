# Реестр пораздельной реконструкции IQVISION 2.30 → AVIC

**Источники:** IQVISION User Manual TE201434 Issue 1 (22.11.2019); IQVISION Configuration Manual TE201382 Issue 7 (22.11.2019); материалы Point Database Manager и E-Signature, переданные в проекте.

Этот реестр — план обязательного разбора руководств, а не заявление о готовности. Каждый подраздел должен получить: перечень объектов и действий; модель данных; UI-путь; API/права; позитивные и негативные сценарии; документацию инженера; запись в матрице паритета.

## Очерёдность User Manual

| Раздел руководства | Содержание | Состояние до DEV52 | План приёмки |
|---|---|---|---|
| 2 About IQVISION | Nav Tree, Locator Bar, View Pane/Changer, PX Pages, Client Devices | Workbench shell частично | Навигация по всем типам объектов, locator parser, вкладки, смена представлений, PX runtime |
| 3 Access IQVISION | Клиент, вход/выход, web browser | Частично; полноценная пользовательская сессия/RBAC UI не завершены | login/logout, session expiry, запрет доступа, audit |
| 4 Use IQVISION | PX Pages, Dashboard, дерево, значения точек, occupation, history graph | Частично | Сквозные сценарии операторского и инженерного просмотра |
| 5 Points List View | Режимы, сортировка, группы, фильтр, избранное, adjust/override, CSV, history, schedule | DEV52: список/фильтр/сортировка/избранное/CSV/переход к истории | Группировка, режимы Live/Engineering, безопасные команды, журнал изменения, schedule editor, настройки списка |
| 13 Create Schematics (PX Pages) | PX folders/pages, canvas/background, static/dynamic elements, widgets, bindings, reuse, Easy Widgets | DEV54: station-scoped graphic documents, HVAC symbol palette, fan demo, point binding roles/value+quality display, page assignment APIs, transactional save validation | Full PX widget set, images/palette import, trends/history widgets, schedules on page, sliders and command widgets, generic page relativisation, full Niagara kitPx/Easy Widgets parity |
| 6 Viewing Alarms | Console, History, Portal, acknowledge, notes | DEV53: консоль, карточка, фильтры, групповое подтверждение, заметки, журнал переходов | Portal process, recipients, routing, sound/silence, период истории, распределённые консоли |

## Очерёдность Configuration Manual

| Раздел | Содержание | Текущий статус | Обязательные проверки |
|---|---|---|---|
| 2 About IQVISION | Niagara architecture, Trend N4, drivers, Platform, Station, UI | Частично | Границы Platform/Station, lifecycle, сервисы и view model |
| 3 Securing IQVISION | Hardening, disaster recovery, network, users, auth, GDPR | Частично | Threat model, RBAC server-side, session, secret storage, backup/recovery |
| 4 Engineering Procedure | Инженерный процесс | Не оформлен единым workflow | Из discovery до импорта, графики, логики, тестирования и publish |
| 5 Install IQVISION | Установка, daemon, firewall, upgrade | CLI/package есть; полноценный установщик отсутствует | Windows clean install/upgrade/uninstall, firewall, rollback |
| 6 License IQVISION | License, certificate management | AVIC имеет отдельную модель Host-ID; не копирует IQVISION licensing | Offline signing, activation/revocation/transfer, limits, trust |
| 7 Initial Setup | Platform, Station creation/configuration | Частично | Первый запуск, станция, службы, credentials, persistence |
| 8 Connect to Trend Networks | Trend networks/sites/modules/points | Частично | Discovery, identity evidence, import, reconnect, network loss |
| 9 Connect to TONNs | TONN/TONN8, allowed hosts, point database | Не реализовано | Отдельный адаптер и acceptance; не выдавать за BACnet |
| 10 Third Party Systems | Driver packages, BACnet, discovery, points | Частично | Driver lifecycle, discovery, import preview, dedupe, read-only safety |
| 11 Time Schedule Control | Individual/Master/Calendar, execution, export, time sync | Частично | Typed schedules, weekly grid, exceptions, priorities, execution simulation, sync permission |
| 12 Alarm Handling | Trend/BACnet alarms, classes, filters, recipients, email, portal | Частично | Ingestion, class/filter ordering, recipients, notification outbox, history, acknowledge |
| 13 PX Pages | Templates, assets, palettes, widgets, bindings, graphs, schedules, reuse, relativisation | Частично | Canvas editor, widget catalog, typed bindings, actions, renderer, template instances |
| 14 Set Up IQVISION Users | Categories, roles, users, NAV files | Частично | User/group/category, role inheritance, navigation scopes, server enforcement |
| 15 Backup Station | Backup/restore | Частично | Consistent backup, integrity, preview, restore drill, audit |
| 16 Using IQVISION | Operating procedures | Не оформлен единым руководством AVIC | Ролевые сценарии, troubleshooting, training project |
| 17 Access IQVISION | Desktop/web login/logout | Частично | Browser/client lifecycle and session security |
| 18 Use IQVISION | PX, Nav Tree, point values, schedule, history | Частично | Operator UX end-to-end |
| 19 Points List View | Расширенный список, adjust/override, properties, modes | DEV52 базовые функции списка | Остальные пункты по acceptance matrix |
| 20 Viewing Alarms | Console/history/portal | Частично | Full operator alarm workflow |
| A1 Migration | Migration from Trend 963/IQSET | Не реализовано | Import adapters, preview, mapping, migration report |
| A2 IQ4 B-BC | BACnet schedules, backup/restore, alarms | Не реализовано | Explicitly separate IQ4 B-BC integration tests |
| A3 Extended Support | Support tooling | Не реализовано | Diagnostics bundle without secrets |
| A4 Facets | Units, ranges, precision | Частично | Metadata schema, validation, display/engineering precision |
| A5 Lexicon | Localization dictionaries | Не реализовано | Translation catalogs, fallback, consistency checks |
| A6 Memory Allocation | Resource sizing | Не реализовано | Runtime budgets and load tests |
| A7 Printing | Print output | Не реализовано | Print stylesheet and export QA |
| A8 Application Director | Station process lifecycle | Частично | Start/stop/restart, watchdog, logs, permission boundaries |
| A9 SQL History Export | SQL export | Не реализовано | Export adapter, retry, checkpoint, data integrity |
| A10 CSV History Export | CSV export | Частично for point list only | History range export, encoding, timestamps, quality columns |
| A11 SNMP | Driver/recipients/MIB | Не реализовано | Decide support scope, then protocol tests |
| A12 E-Signature | Customer, reason sets, secure zones, users, alarms, histories, dual signatures, audit | Частично / architecture only | Re-auth, reason policy, dual approval, immutable evidence; no Part 11 claim without validation |
| A13 Analytics | Analytics | Частично | Rules, missing data, tags, evidence, UI and reports |

## Правило тестового счётчика

Количество тестов — только одна метрика. Параметризованные кейсы допустимы, когда меняют независимые данные/состояния и проверяют самостоятельный результат. Не засчитывать snapshot-повторы, одинаковые assert под разными именами или фиктивные browser clicks как функциональное покрытие. В отчёте указывать отдельно: собранные тесты, прошедшие, упавшие, пропущенные, браузерные сценарии, Windows acceptance и реальные OT-проверки.

## DEV52–DEV53 — первые этапы пользовательского руководства

Раздел User Manual §5: Point List View — persistent favorites, filters, sort, pagination, CSV export and history navigation. Не реализованы: live/engineering mode, point value adjust/override, audit details for point adjustments, grouping/collapse, schedule editing from list, full point view setup options.

Раздел User Manual §6: Alarm Console — фильтры, состояния, карточка, заметки оператора и история переходов. Не реализованы: отдельный Alarm Portal process, распределённые ConsoleRecipient, звуковая сигнализация и Silence. Это остаётся открытым этапом.


## DEV54 — §13 Create Schematics (PX Pages)

Reference: IQVISION Configuration Manual v2.30, §13. AVIC implements the initial authoring loop: create a station-scoped graphic, place HVAC symbols, bind station points by semantic role, save/reopen, and assign graphics to Web Pages. The fan demo is a reusable acceptance fixture. Live values are displayed only when present in the normalized point model. Command/write widgets remain deliberately disabled.

Not yet implemented from §13: asset/image upload and image palette, static text/image widgets, animated palette states, slider/adjust buttons, page links, trend graphs, schedule widgets, dashboard service, generic PX relativisation, and Niagara Easy Widgets/Palette Builder compatibility.


## DEV55 — FBD / Wiresheet и сквозная связь с PX-мнемосхемой

DEV55 реализует первый вертикальный срез инженерной логики: 9 типизированных блоков, сохранение графа и проводов, type-checking, проверку циклов/занятых портов, детерминированную симуляцию и привязку BOOL-выхода к символу вентилятора той же станции. Это начальная основа Wiresheet, не полный аналог Niagara/IQVISION.

Открытые пункты FBD: расширение до полной библиотеки категорий и функциональных блоков, timers/counters/PID, subcharts/macros, online watch, task scheduling, runtime publish/rollback, library packaging/versioning, richer diagnostics и AI Builder. Live-подсветка символа результатом симуляции и безопасный Command Manager остаются отдельными этапами.

## DEV56 — §4 Engineering Procedure и контроль §8–10

Реализован единый read-only Engineering Workflow для станции: network/channel → driver/device → points → FBD → graphics. Сервис и Workbench показывают сохранённые артефакты, станционные границы, ошибки связей и следующие действия. См. `BUILD_056_RU.md` и `BUILD_TEST_LOG_DEV56_RU.md`.

Открытые пробелы остаются существенными: §4 не имеет полного wizard/discovery/import/commissioning/sign-off; §8 не имеет полного Trend System/Module Discovery и reconnect; §9 TONN/TONN8 отсутствует; §10 не имеет полного Driver Manager/package lifecycle/SDK. Эти разделы не объявляются закрытыми.
