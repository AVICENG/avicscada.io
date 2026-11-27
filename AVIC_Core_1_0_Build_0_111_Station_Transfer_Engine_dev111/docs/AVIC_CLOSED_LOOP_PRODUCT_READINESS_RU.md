# AVIC SCADA — замкнутый цикл разработки и карта готовности

Статус документа: базовый процесс разработки и приёмки.  
Назначение: не допускать перекоса разработки в одну подсистему и показывать фактическую готовность всего продукта.

## 1. Основной принцип

AVIC разрабатывается замкнутым циклом. После каждого прохода по направлениям команда возвращается к началу и повторяет проверку с учётом новых изменений. Нельзя считать продукт готовым, если один раздел достиг 100%, а критические соседние разделы остались незавершёнными.

Каждый проход включает:
1. Зафиксировать текущую версию и результаты тестов.
2. Проверить состояние всех направлений по единой карте.
3. Выбрать наиболее важные незакрытые критерии в разных направлениях.
4. Реализовать улучшения небольшими согласованными пакетами.
5. Проверить unit, integration, UI/API, security и regression сценарии там, где применимо.
6. Обновить документацию, журнал сборки и доказательства приёмки.
7. Пересчитать проценты и начать следующий проход.

## 2. Карта направлений

Карта должна содержать круговую диаграмму с точками по окружности. Каждая точка соответствует направлению, показывает процент готовности и открывает подробную карточку критериев.

| ID | Направление | Что входит в оценку |
|---|---|---|
| CORE | Core / Runtime | жизненный цикл приложения, станции, изоляция, сервисы, стабильность, API/SDK, CLI, конфигурация, миграции |
| NET | Network Manager | интерфейсы, IP-инструменты, discovery, топология, диагностика, безопасные режимы, инвентаризация |
| DRV | Driver Manager и протоколы | установка/конфигурация/запуск/остановка драйверов, BACnet/IP, Modbus TCP, диагностика, reconnect, качество |
| POINT | Point Manager | импорт, каталог, стабильные ID, типы/единицы, quality, фильтры, пакетные операции, ссылки, лимиты лицензии |
| FBD | FBD Studio / Logic | редактор, библиотека блоков, соединение, типизация, компиляция, runtime, scheduler/time, ошибки и диагностика |
| GRAPH | Graphics / мнемосхемы | редактор, SVG-символы, слои, масштабирование, bindings, converters, анимации, quality overlay, библиотеки |
| WEB | Web Application / Pages | сайты/страницы, виджеты, компоновка, привязки, адаптивность, безопасный рендеринг, навигация |
| PUB | Publication / Operator UI | подготовка, проверка, immutable snapshot, публикация, версии, rollback, unpublish, live values, runtime |
| SEC | Security / RBAC | пользователи, сессии, роли, права, иерархия ресурсов, CSRF, MFA, аудит, rate limits, защищённые операции |
| LIC | Licensing | подпись лицензии, Host ID, активация/отзыв/перенос, tiers, point counting, лимиты, офлайн-проверка, прозрачность статуса |
| ALARM | Alarms / Events | alarm lifecycle, приоритеты, подтверждение, shelving/suppression, журнал событий, маршрутизация, эскалации |
| HIST | Historian / Trends | сбор, буферизация, архив, retention, запросы, тренды, экспорт, качество/временные метки |
| TIME | Time Manager / Schedule | timezone станции, NTP/clock status, явное разрешение синхронизации устройств, расписания, календарь, DST |
| ENG | Engineering Lifecycle | проектирование, review, simulation, commissioning, approvals, change management, rollback, workflow history |
| ASSET | Asset Passport / Maintenance | иерархия активов, паспорт, обслуживание, work orders, дефекты, история и отчёты |
| NOTIFY | Notification Manager | Email, Telegram, push, маршруты, эскалации, retry, quiet hours, доставка и аудит |
| DIST | Distributed SCADA / HA | центральный мониторинг, автономность станций, access leases, репликация, failover, fencing, восстановление |
| INT | Integration / Open API | API clients, webhooks, внешние системы, SDK, versioning, auth scopes, contract tests |
| AI | AI Engineering Assistant | безопасный экспорт без секретов, readiness review, FBD/graphics assistance, проверка, simulation, advisory-only |
| UX | Engineering Workbench / UX | дерево, поиск, избранное, recent, контекстные команды, состояния, навигация, доступность, скорость |
| DOC | Documentation / QA / Release | инструкции, help, примеры, тестовый журнал, release notes, миграции, воспроизводимые acceptance-сценарии |

## 3. Правила расчёта готовности

Процент нельзя назначать «на глаз», по числу файлов, строк кода, экранов или тестов.

Для каждого направления создаётся список атомарных критериев приёмки. Каждый критерий имеет:
- уникальный ID;
- описание ожидаемого поведения;
- вес по важности (обычный = 1, важный = 2, критический = 3);
- статус: NOT_STARTED, IN_PROGRESS, IMPLEMENTED_UNVERIFIED, VERIFIED, BLOCKED, NOT_APPLICABLE;
- ссылку на тест/артефакт/документацию;
- дату и версию последней проверки;
- известные ограничения.

Расчёт:
- VERIFIED: 100% веса критерия;
- IMPLEMENTED_UNVERIFIED: 50% веса, показывать как предварительный прогресс;
- IN_PROGRESS: 25% веса только если есть проверяемая реализация; иначе 0%;
- NOT_STARTED / BLOCKED: 0%;
- NOT_APPLICABLE: исключается из знаменателя с обязательным обоснованием.

Готовность направления = сумма набранных весов / сумма применимых весов × 100.

Общий процент продукта рассчитывается по направлениям с весами. Критические направления CORE, SEC, LIC, DRV, POINT, FBD, GRAPH и PUB имеют повышенный вес. Общий процент не должен скрывать критические блокеры: рядом всегда показывать число открытых критических критериев и минимальный процент среди критических направлений.

Цветовая шкала:
- 100% и все обязательные критерии VERIFIED: зелёный;
- 80–99%: бирюзовый/синий;
- 1–79%: жёлтый/оранжевый по диапазону;
- 0%: красный, если аудит подтвердил отсутствие реализации;
- не оценено: серый (не подменять нулём).

Ни один раздел не может получить 100%, если обязательные критерии не имеют проверяемого доказательства. Наличие теста без реального UI/интеграционного сценария не подтверждает пользовательскую функцию. Имитация оборудования не подтверждает физическую совместимость.

## 4. Визуальное поведение карты

Основной вид:
- круговая/радиальная карта с равномерно распределёнными точками направлений;
- цвет точки соответствует уровню готовности;
- подпись рядом с точкой: короткое имя и процент;
- размер/контур точки может показывать количество критических блокеров;
- центральный индикатор показывает общий прогресс AVIC и дату последнего аудита;
- выбор точки открывает подробности, критерии, доказательства, дефекты и следующий шаг;
- фильтры: Все, Критические, Не оценено, Есть блокеры, Изменились в последнем цикле;
- альтернативный табличный вид обязателен для доступности и большого числа направлений.

Не использовать фиктивные значения процентов. До проведения аудита показывать «Не оценено», а не случайные проценты.

## 5. Постоянный замкнутый рабочий цикл

Каждый проход должен затрагивать весь продукт, но объём работ внутри прохода может различаться.

### Проход A — фундамент и безопасность
Core/Runtime, API, изоляция станций, RBAC, сессии, CSRF, аудит, лицензирование, Host ID, восстановление.

### Проход B — подключение оборудования и точки
Network Manager, discovery, BACnet/IP, Modbus TCP, Driver Manager, импорт точек, quality, диагностика и безопасные ограничения.

### Проход C — инженерная логика
FBD editor, соединения, типы сигналов, компиляция, runtime, simulation, Scheduler, Time Manager, обработка ошибок и quality.

### Проход D — визуализация и оператор
Graphics Workbench, символы, анимация, bindings, Web Page Builder, публикация, версии, rollback, операторские права и безопасность страниц.

### Проход E — эксплуатация
Alarms, Events, Historian, Trends, Notifications, Asset Passport, Maintenance, отчёты, диагностика.

### Проход F — масштабирование и развитие
Distributed SCADA, HA, Integration API/SDK, AI Engineering Assistant, производительность, UX, миграции и обновления.

После F цикл возвращается к A. При этом в каждом проходе выполняется регрессионная проверка уже работающих сквозных сценариев.

## 6. Обязательные сквозные сценарии регрессии

1. Создать проект и станцию; пользователь видит только разрешённые ресурсы.
2. Обнаружить BACnet устройство в read-only режиме; импортировать точку без выдумывания идентификаторов.
3. Получить значение физической точки в Point Runtime с корректным quality и timestamp.
4. Передать точку в FBD, соединить блоки, скомпилировать, запустить runtime и получить виртуальную точку.
5. Привязать физическую и виртуальную точки к мнемосхеме; анимация и quality отображаются корректно.
6. Добавить мнемосхему и значения на Web Page; опубликовать, открыть оператором, проверить live update.
7. Проверить, что оператор не может редактировать FBD, Graphics, страницу или выполнять неразрешённые команды.
8. Проверить публикацию, unpublish, версионирование и rollback.
9. Проверить истечение/отзыв/несовпадение Host-ID лицензии и поведение при достижении лимита точек.
10. Проверить потерю связи, BAD_COMMUNICATION, восстановление связи и отсутствие ложного GOOD.
11. Проверить аудит успешных и запрещённых критических операций.
12. Проверить перезапуск станции/процесса, сохранность данных и восстановление runtime по документированным правилам.

Команды управления оборудованием, BACnet WriteProperty и приоритетная запись принимаются отдельно от read-only мониторинга: необходимы RBAC, разрешение на конкретный объект, безопасная политика, журналирование, read-back и аппаратная приёмка.

## 7. Правила разработки и выпуска

- Каждая функция считается законченной только при наличии кода, теста, документации и понятного пользовательского сценария.
- Отдельно фиксировать: реализовано, проверено автоматически, проверено вручную, проверено на физическом оборудовании.
- Не смешивать симуляцию и реальное оборудование.
- Не объявлять Trend parity по количеству блоков; вести матрицу совместимости по каждому блоку/модулю.
- Не допускать секреты, пользовательские проекты и закрытые материалы поставщиков в публичный репозиторий.
- После каждой сборки публиковать русскоязычный отчёт: реализовано, изменено, тесты, ограничения, проценты направлений, критические блокеры, готовность.
- Не объединять PR и не выпускать релиз только по причине зелёного CI; обязательны review и сквозная приёмка.
- Приоритет следующего действия выбирается по риску, влиянию на безопасность/надёжность и разблокированию других подсистем, а не по простоте реализации.

## 8. Первая задача после утверждения карты

Провести инвентаризацию текущего кода и тестов по всем направлениям. Для каждого критерия присвоить статус только после проверки конкретной реализации и доказательства. Сначала заполнить карту фактическими данными, затем выбрать задачи первого полного прохода.

До завершения инвентаризации все проценты остаются «Не оценено». Не переносить старые предположительные оценки в новую карту.

---
## 9. Обязательное сравнение с Niagara — контрольный стандарт

### 9.1 Какой Niagara берём за эталон

Для подтверждённого промышленного baseline сравниваем AVIC прежде всего с **Niagara 4.15** и зрелыми возможностями Niagara 4, которые Tridium публично описывает. Niagara 5 учитываем отдельно как направление развития, но не выдаём его новые функции за многолетне проверенную эксплуатационную базу Niagara 4.

Сравнение функциональное и независимое: повторяем пользовательские сценарии и наблюдаемое поведение, а не закрытый исходный код, бинарные модули или внутренние форматы Tridium.

Каждый пункт получает один из трёх классов:
- **NIAGARA_PARITY** — AVIC должен обеспечить сопоставимую законченную возможность и надёжность.
- **AVIC_IMPROVEMENT** — AVIC обеспечивает тот же результат лучше по безопасности, скорости, удобству, диагностике или восстановлению.
- **AVIC_INNOVATION** — дополнительная возможность AVIC; она не заменяет обязательную Niagara parity.

Для каждого критерия фиксируются: Niagara baseline, сценарий инженера/оператора, ожидаемое поведение, реализация AVIC, автоматический тест, UI/API проверка, аппаратная проверка, ограничения и решение о готовности. «Есть класс/файл/API» не означает parity.

### 9.2 Полный круг сравнения

| № | Направление AVIC | Что проверяем относительно Niagara | Что уже подтверждено в AVIC по текущей ветке | Открытая проверка / разрыв |
|---:|---|---|---|---|
| 1 | Platform / Core Runtime | Platform, Station lifecycle, services, module lifecycle, watchdog, restart, diagnostics | CoreApplication, Station Runtime и сервисная архитектура присутствуют в кодовой базе | Полный parity-аудит Platform/Supervisor, fault isolation, watchdog, upgrade и нагрузка |
| 2 | Object / Component Model | component tree, slots/properties, references, facets, types, tags, object identity | В AVIC есть Repository/узлы объектов и стабильные ID в ряде подсистем | Единая модель свойств/ссылок/типов/фасетов и совместимость между всеми сервисами |
| 3 | Workbench / Navigation | Nav tree, views, property sheets, search, palettes, context actions, online/offline engineering | Есть инженерное дерево, Repository и отдельные Workbench UI | Полный пользовательский проход, горячие клавиши, контекстные команды, производительность больших проектов |
| 4 | Driver Manager | Добавление, конфигурация, запуск/остановка, состояние, диагностика, provisioning, driver lifecycle | Есть Driver Manager, contracts, catalog, polling lifecycle | Crash recovery, watchdog/retry, массовое управление, SDK и реальная установка/удаление модулей |
| 5 | Protocol Drivers | Vendor-neutral connectivity, device discovery, point import, polling, COV/events, commands, diagnostics | BACnet/IP и Modbus TCP имеют ограниченный read-only путь; KNX имеет частичную read-only реализацию; Trend IP и MQTT не готовы как production drivers | Не выдавать read-only адаптер за полный драйвер. Trend vCNC, BACnet advanced services, Modbus polling/map import, KNX commissioning и hardware acceptance |
| 6 | Network Manager | IP tools, network inventory, discovery, topology, device identity, safe commissioning | Есть network contracts, diagnostics, topology, discovery history и identity resolver | Полный UI/API сценарий, безопасные лимиты, vendor confidence, IPv6, VLAN/routed networks, network change audit |
| 7 | Point Manager | Point discovery/import, folders, proxy points, facets, writable flags, bulk edit, references, point status | Общий Point Runtime и лицензируемые Point records существуют | Полный Point Manager parity, пакетный импорт/экспорт, единый источник истины, массовая проверка зависимостей |
| 8 | FBD / Wiresheet | Wire Sheet, typed blocks, ports, connect/disconnect, palette, compile, online changes, diagnostics | Есть FBD Studio, compiler, runtime; отдельные документы DEV176/185/191/192 фиксируют parity и пробелы | Полный Trend/Niagara block-by-block matrix, multi-page copy/delete/import, online apply/rollback, browser acceptance |
| 9 | Graphics / PX-equivalent | Graphic editor, SVG, symbols, bindings, dynamic colors/rotation, reusable templates, responsive display | Есть Graphics service, binding engine, SVG libraries, Graphics Workbench | Полный editor acceptance, анимации по quality, symbol library completeness, reusable templates, performance |
| 10 | Web Pages / UX Builder | HTML5 views, page composition, navigation, live values, responsive views, safe rendering | Есть Web Application/Page Builder, pages, assets, point and graphics bindings | Customer login/RBAC, full browser acceptance, mobile/responsive, page protection and command integration |
| 11 | Publication / Operator UI | Deploy/publish, immutable versions, live runtime values, role-scoped operation, rollback | Есть publication snapshots, versions, unpublish/rollback и read-only live values | Server-side operator authorization, secure deployment profile, command workflows, end-to-end acceptance |
| 12 | Alarm Service | Alarm classes, states, priorities, ack, return-to-normal, routing, escalation, archive | Есть Alarm/Events services и описанный lifecycle | Niagara-like alarm extensions: shelving/suppression, alarm classes, routing/escalation, console UX, alarm archive integration |
| 13 | Event Journal / Audit | Event history, operator actions, configuration audit, security history | Есть Event/Audit services и hash-chain подход | Durable external checkpoint, retention/export, concurrency/disk-full behavior, complete audit coverage |
| 14 | Historian / Trends | History extensions, sampling, interval/COV, archive providers, charting, export, retention | Есть History service и запросы по Station/Point | Sampling policies, buffering, archive rotation, deadband, interpolation, chart UX, export and high-load acceptance |
| 15 | Scheduler / Calendar | Boolean/numeric/enum schedules, weekly schemes, special events, calendars, overrides, import/export | Core Scheduler поддерживает типы значений, weekly/special events, timezone/DST, overrides | По DEV194: master/calendar sharing, import/export manager, BACnet schedule manager/export, Trend Schedule H не эквивалентен Core SCHEDULE |
| 16 | Time / Synchronization | Station time, NTP, timezone, DST, device clock sync | Есть TimeManagementService и явное разрешение синхронизации на устройство | Реальный NTP runtime/status, drift monitoring, device write acceptance, DST boundary tests |
| 17 | Licensing / Capacity | License activation, host binding, capacity count, feature entitlements, renewal/upgrade, audit | Есть Ed25519 offline signature verification, Host ID, point-limit guard and usage summary | Revocation/transfer workflow, issuer tooling/key rotation, tier/feature enforcement across all entry points, customer-visible license UX |
| 18 | Security / Identity | Users, roles, permissions, TLS, certificates, sessions, MFA, security dashboard, audit | Есть auth/RBAC/Gateway/SecretStore modules | Production login/session enforcement across every API/UI route, object scopes, MFA, certificate lifecycle, security dashboard, penetration tests |
| 19 | Backup / Restore / Provisioning | Station backup, platform backup, restore, provisioning, cloning, upgrade recovery | Есть encrypted System Backup, SQLite snapshots, inspect/restore; Station Transfer отдельный | Cross-database consistency barrier, scheduled/offsite backups, tested restore drills, deployment/provisioning UI, migration orchestration |
| 20 | Notifications | Alarm routing, email, acknowledgement links, delivery retries, escalation | Есть durable notification routes/outbox | Транспортные адаптеры и подтверждённая доставка отсутствуют в текущем NotificationService; retry/escalation/quiet hours требуют проверки |
| 21 | Asset / Maintenance / Analytics | Asset manager, tagging, equipment relationships, analytics, work orders, reports | Есть отдельные модули Asset/Analytics в кодовой базе | Сквозной эксплуатационный сценарий, интеграция alarms/history/asset, CMMS/work order lifecycle |
| 22 | Distributed Niagara Network / Supervisor | Station-to-station links, global indexing, central supervision, remote engineering, failover | В AVIC заложены контракты/направление distributed SCADA | Рабочие station links, global point/alarm/history indexing, remote operations, outage autonomy, failover/fencing |
| 23 | API / SDK / Extensibility | Public APIs, module SDK, driver ecosystem, versioning, signing, compatibility | Есть API/adapters/contracts в нескольких областях | Стабильный публичный SDK, compatibility policy, module signing/trust, third-party developer acceptance |
| 24 | Commissioning / Deployment | Provisioning, templates, bulk device onboarding, certificates, commissioning workflows | Есть Network Planning, Engineering Lifecycle и Station Transfer foundations | Полный guided commissioning, templates, bulk provisioning, rollback, field acceptance |
| 25 | AI Engineering Assistant | Не является обязательной Niagara parity; сравниваем как AVIC innovation | В проекте определён advisory-only принцип | Безопасный экспорт, explainable recommendations, no secrets, no autonomous control, evidence-based validation |
| 26 | Documentation / Localization / Release | Online help, module docs, training, upgrade notes, release management | В репозитории есть русские build logs, docs и audit specs | Полнота пользовательской документации по каждой функции, versioned help, reproducible installation and upgrade |

### 9.3 Первые фактические выводы по просмотренным исходникам

**Driver Manager и драйверы**
- Каталог различает PROFILE_AVAILABLE, READ_ONLY_INTEGRATION, READ_ONLY_TRANSPORT и PLANNED. Это правильнее, чем рекламировать каждый протокол как готовый.
- BACnet/IP и Modbus TCP в каталоге имеют ограниченный read-only transport; это не полная Niagara-equivalent driver capability.
- Trend IP / IQ Network остаётся PLANNED: TCP vCNC codec и hardware acceptance не завершены. Подменять его BACnet нельзя.
- KNXnet/IP имеет отдельную частичную read-only реализацию; MQTT не следует считать готовым runtime без factory, SecretStore, TLS policy и broker acceptance.
- Следующий драйверный этап сравнивать по lifecycle, discovery, import, polling, quality, reconnect, diagnostics, commands, security, performance и hardware acceptance, а не по названию протокола.

**Licensing**
- Подтверждены Ed25519 signature verification, обязательная привязка к Host ID, expiry check, point limit, защита от повторного подсчёта UUID и отдельное preservation существующего runtime.
- Текущий manager не доказывает законченный issuer/revocation/transfer workflow. Поле key_id в payload само по себе не является механизмом ротации ключей или отзывом лицензии.
- Нужно проверить применение feature entitlements на каждом API/UI/driver entry point, гонки при одновременном создании точек, установочный лимит и пользовательский экран лицензии.
- Runtime preservation при недействительной лицензии — осознанное безопасное поведение; при этом новые лицензируемые изменения должны блокироваться предсказуемо и с понятным статусом.

**Малые системные службы**
- NotificationService на текущем коде — маршруты и durable outbox; он сам не отправляет сообщения без транспортного адаптера.
- TimeManagementService хранит timezone/NTP policy и per-device sync permission; наличие настроек не доказывает работающий NTP daemon/clock sync worker.
- System Backup шифрует и проверяет архив, но документация DEV145 честно фиксирует отсутствие общей атомарной точки между несколькими SQLite DB, автоматического расписания/offsite storage и плановых restore drills.

**Безопасность и интерфейс**
- Наличие RBAC/Gateway/Auth модулей не доказывает, что каждая изменяющая UI/API операция проходит production authorization. В документации Page Builder прямо отмечено отсутствие customer-grade login/session/RBAC/MFA в описанном acceptance scope.
- Страница оператора, публикация, FBD, Graphics, команды и лицензирование должны тестироваться как единый путь с разными ролями, а не отдельно в своих тестах.

Эти выводы — первичный code/document audit по текущей ветке, а не итоговые проценты готовности. Все направления остаются «не оценено» до полного критериального аудита с проверкой тестов и запускаемых сценариев.

### 9.4 Правило следующего шага по кругу

Каждый следующий рабочий пакет должен включать:
1. Один критерий из текущего сектора круга (сейчас: Driver Manager/driver lifecycle).
2. Один критерий из лицензирования/безопасности или другой системной службы.
3. Один смежный пользовательский сценарий (Point Manager → FBD → Graphics → Page → Operator).
4. Регрессию ранее закрытых критериев.
5. Обновление этого документа, журнала сборки и ссылок на тестовые доказательства.

Не начинать следующий сектор, если предыдущий имеет критический дефект безопасности/потери данных. Не задерживать весь круг из-за некритичного косметического дефекта: пометить блокер и продолжать остальные сектора.


### 9.5 Дополнительная проверка связки лицензии с Core и Driver Manager

Проверены непосредственно Core composition root, DriverManagerService, LicenseManager и тесты лицензирования на текущем HEAD.

**Критический интеграционный разрыв подтверждён:**
1. CoreApplication создаёт CoreObjectService как CoreObjectService(repository), без передачи InstallationLicenseService. Тест лимита точек проверяет отдельный CoreObjectService с искусственным Gate, но не доказывает, что штатный CoreApplication применяет лицензионный лимит при создании Point.
2. DriverCatalogEntry содержит license_feature, однако DriverManagerService.catalog() не возвращает это поле, а create_instance() и start_instance() не проверяют подписанные feature entitlements. Сейчас поле feature в лицензии и feature key в каталоге не образуют действующую enforcement-связку.
3. В LicenseManager.verify() проверяются подпись, формат, обязательные поля, Host ID, point_limit и expiry. Отдельного списка отзыва, проверки статуса revoked и механизма переноса/переактивации в этом менеджере не обнаружено.
4. Тесты подтверждают генерацию/проверку Ed25519 лицензии, Host ID mismatch, tamper rejection, point counting и отдельную атомарную проверку лимита в CoreObjectService с тестовым Gate. Они не подтверждают штатное enforcement через CoreApplication и Driver Manager.

**Приоритет исправления: BLOCKER для коммерческого лицензирования.** До включения платных редакций/драйверов требуется спроектировать и проверить единый License Entitlement Gateway, который:
- подключается в CoreApplication и доступен CoreObjectService, DriverManager, FBD/Graphics/History/Alarm activation и другим лицензируемым функциям;
- проверяет установочный Host ID, подпись, срок действия, feature entitlements и capacity;
- атомарно резервирует/проверяет лимит уникальных активных Point при создании/активации, не считая повторные ссылки на тот же Point UUID;
- блокирует новые лицензируемые действия при недействительной лицензии, но не останавливает уже работающий безопасный Runtime;
- ведёт аудит разрешённых/отклонённых операций и показывает инженеру тариф, использовано/доступно и причину ограничения;
- поддерживает отдельно определённый AVIC issuer/revocation/transfer workflow с offline-проверкой подписанного состояния отзыва, без скрытого Master Developer доступа.

Не добавлять проверку только в UI: enforcement должен находиться на серверной стороне и закрывать прямые вызовы сервисов/API. Сначала определить модель отзыва для полностью автономной установки (например, подписанный пакет обновления списка отзыва с версией/сроком действия); не притворяться, что мгновенный онлайн-отзыв возможен без связи.


### 9.6 DEV201 — безопасное завершение Driver Adapter

**Найденный дефект:** если worker polling уже остановлен, но `adapter.close()` выбрасывает исключение, прежний код не удалял остановленную сессию из реестра Driver Manager и не сохранял итоговое состояние. Повторный запуск мог вернуть диагностику старой сессии вместо создания нового адаптера.

**Исправление:**
- Ошибка `PollingSession.stop()` (включая timeout) по-прежнему прерывает остановку до закрытия адаптера: нельзя закрывать транспорт, пока worker потенциально выполняет I/O.
- Если worker остановлен, ошибка `adapter.close()` фиксируется, завершённая сессия удаляется из реестра, состояние экземпляра становится `ERROR`, а событие записывается в Audit.
- После ошибки закрытия допускается повторный старт с новым адаптером; успешная остановка возвращает `STOPPED`.
- Добавлены регрессионные тесты с намеренно падающим `close()` (реестр, состояние и повторный запуск) и с timeout во время активного I/O (адаптер не закрывается до завершения worker).

**Статус проверки:** код и тест добавлены в DEV201. Полный Linux/Windows CI для новых коммитов ожидает запуска после завершения предыдущих последовательных workflow. До завершения CI результат теста не объявляется подтверждённым. Реальная аппаратная приёмка BACnet не затрагивалась.


### 9.7 DEV202 — строгая принадлежность точки драйверу

**Найденный дефект:** Point Runtime сравнивал `source_driver_id` с владельцем Device только когда у Device уже был непустой `driver_instance_id`. Для legacy/unbound Device отсутствие владельца фактически работало как wildcard: любой адаптер мог публиковать значение или качество в такую точку.

**Исправление:**
- Если передан `source_driver_id`, он обязан точно совпасть с `Device.driver_instance_id`; пустой/отсутствующий владелец не считается разрешением.
- Одинаковое fail-closed правило применяется к `publish()` и `mark_quality()`.
- Внутренние Core-публикации без adapter identity (`source_driver_id=None`) остаются отдельным явно доверенным путём.
- Добавлен регрессионный тест на legacy/unowned Device: адаптер не может обновить ни значение, ни quality; контролируемая внутренняя публикация без driver identity остаётся доступна.

**Статус проверки:** изменения DEV202 записаны; CI ещё должен подтвердить полный набор тестов на Linux и Windows. Аппаратная проверка BACnet не выполнялась.


### 9.8 DEV203 — Point Runtime: защита от запоздавших измерений и восстановление качества

**Найденный дефект:** `PointRuntimeService.publish()` принимал любой timezone-aware timestamp и без сравнения с предыдущим sample перезаписывал значение. После сетевой задержки или reconnect старый пакет мог заменить более новое измерение.

**Исправление:**
- Перед записью вычисляется timestamp принимаемого sample (включая локальный UTC timestamp, если источник его не передал).
- Если timestamp меньше последнего сохранённого timestamp, sample отклоняется до изменения Point и до уведомления подписчиков.
- Сохранённый timestamp без timezone считается повреждённым состоянием и не используется для небезопасного сравнения.
- `mark_quality()` сохраняет последнее значение и timestamp измерения; потеря связи переводит quality в `BAD_COMMUNICATION`, а восстановление `GOOD` выполняется только новым принятым sample.

**Регрессионные тесты добавлены:** запоздавшее измерение не откатывает value/quality/timestamp и не уведомляет subscribers; сценарий `GOOD → BAD_COMMUNICATION → GOOD` сохраняет last value во время потери связи и принимает новое измерение после восстановления.

**Статус проверки:** изменения и тесты внесены в PR. Полный Linux/Windows CI должен подтвердить их выполнение; локальный pytest в этой среде не запускался. Аппаратная проверка BACnet не выполнялась.


### 9.9 DEV204 — изоляция станций в Point Runtime

**Найденный пробел:** `publish()` и `mark_quality()` проверяли, что `source_driver_id` совпадает с `Device.driver_instance_id`, но не проверяли станционную принадлежность самого DriverInstance. При повреждённых/подменённых метаданных устройство станции A могло ссылаться на валидный драйвер станции B и принимать его обновления.

**Исправление:**
- Для adapter-originated `publish()` и `mark_quality()` Point Runtime теперь требует существующий зарегистрированный объект `DriverInstance`.
- `DriverInstance.station_id` должен точно совпадать с `Device.station_id`; отсутствующий или чужой station ID отклоняется.
- Проверка выполняется отдельно от проверки точного совпадения owner ID: обе границы обязательны.
- Внутренний доверенный путь `source_driver_id=None` не менялся.

**Регрессионные тесты:** тесты Point Runtime используют зарегистрированный DriverInstance; добавлен сценарий подмены Device owner на драйвер другой станции и проверки блокировки как публикации значения, так и изменения качества.

**Статус проверки:** код и тесты внесены в PR; CI для нового head должен выполнить полную матрицу Linux/Windows. Локальный pytest здесь не запускался. Физическая BACnet-приёмка не выполнялась.
