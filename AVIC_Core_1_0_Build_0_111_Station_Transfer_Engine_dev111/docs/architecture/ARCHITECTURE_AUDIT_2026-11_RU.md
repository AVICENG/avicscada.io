# AVIC Core 1.0 — первичная архитектурная ревизия

Дата: 27.11.2026  
Проверенный исходный код: `ae85b68f60a2680ddad7fb7594f4b44158b89379`  
Базовый рабочий коммит после исправления benchmark fixture: `8f74b8f9dda9f27ea6ba657bc08f5d711c85e7bc`  
Область: статическая ревизия структуры, composition root, доменных моделей, хранилищ, Runtime, Drivers, Security, Commands, Graphics и Edge/Field Runtime.

> Это первичный архитектурный аудит, а не заключение о полной готовности продукта. Он не заменяет выполнение тестов, threat modeling, нагрузочные испытания, проверку миграций и испытания на реальных контроллерах. Статус ARCHITECTURE_DEFINED не присваивается по факту наличия этого документа.

## 1. Резюме

В кодовой базе уже выделены самостоятельные пакеты Core, Domain, Repository, Drivers, Network, Points, Runtime/FBD, Commands, Events, History, Alarm, Analytics, Notifications, Security, Licensing, Configuration, Deployment, Transfer, Graphics, Web Pages, Engineering Lifecycle и Field Runtime.

Главный риск текущей архитектуры — не отсутствие названий подсистем, а отсутствие окончательно согласованной модели владения данными и исполнения. В частности, текущее значение точки сохраняется через общий объектный SQLite Repository; Field Runtime пока является отдельным процессным host/heartbeat prototype без присоединённого FBD execution engine; производственный Security/RBAC путь не интегрирован в локальный Workbench; ряд журналов и реестров находятся в отдельных БД и нуждаются в формально определённых consistency/outbox правилах.

**Рекомендация:** до расширения функциональности зафиксировать целевые контракты для Point State, Field Runtime, Command Execution, Identity/Security, Configuration/Deployment и Data Ownership. Не делать необратимый рефакторинг до согласования этих контрактов.

## 2. Приоритетные архитектурные находки

### A-001 — Point Runtime использует объектное Repository как горячее хранилище значений
**Приоритет: P0 / блокирует архитектурное принятие Runtime на масштаб AVIC.**

Фактическое поведение:
- `PointRuntimeService.publish()` загружает объект Point из `SQLiteRepository`, проверяет значение и timestamp, обновляет Point и сохраняет его через `repository.save()` при каждом принятом sample.
- Публикация FBD exposed point использует аналогичный путь.
- В `PointRuntimeService` один общий `RLock` охватывает чтение, валидацию и сохранение. Поэтому параллельные обновления разных точек внутри данного экземпляра сервиса сериализуются.
- Определение Point и его текущие runtime-поля (value/quality/timestamp) смешаны в одной persisted entity.

Риск:
- Каждое измерение создаёт транзакционную запись в БД инженерных объектов и увеличивает revision объекта.
- Высокая частота и число точек превращают SQLite object registry в bottleneck и связывают скорость драйверов с инженерным CRUD.
- Несколько процессов Runtime не имеют согласованного владельца оперативного значения.

**Целевое решение:**
1. Разделить Point Definition (инженерная конфигурация, стабильная идентичность, тип, единицы, направление, источник) и Point State/Sample (value, quality, source timestamp, receive timestamp, sequence, source).
2. Определить один авторитетный Point State API/contract, используемый Python и Rust drivers, FBD, Alarms, HMI, Historian и Central/Edge.
3. Не выполнять полный CRUD-перезапис инженерной сущности на каждый sample.
4. Ввести bounded ingestion pipeline, backpressure, batching и независимую политику persistence/cache.
5. Historian подписывается на поток принятых sample и не становится владельцем текущего значения.
6. Обеспечить station isolation, stale generation fencing, out-of-order policy и восстановление после перезапуска.

До утверждения решения запрещено считать текущий путь достаточным для целевых 5k/10k+ точек на Edge.

### A-002 — Field Runtime пока не является исполнительной средой
**Приоритет: P0 / блокирует заявление об автономной станции.**

Фактическое поведение:
- `field_runtime/process.py` запускает отдельный OS process и управляет loopback TCP heartbeat/control connection.
- `field_runtime/agent.py` отвечает на status/ping и maintenance_stop; в status явно сообщает `active_strategies: 0`, `execution_engine_attached: false`, `capability_state: PROCESS_HOST_ONLY`.
- Документ DEV181 прямо фиксирует отсутствие FBD execution attachment и отсутствие устойчивого повторного обнаружения/аутентификации агента новым Supervisor после рестарта.
- Основной `FBDExecutionService` сейчас является отдельным сервисом Python в процессе Core/Application; сам по себе факт наличия process host не переносит исполнение в него.

**Целевое решение:**
1. Разделить Supervisor/Platform Manager и Station Field Runtime как разные владельцы жизненного цикла.
2. Определить подписанный immutable deployment bundle: Logic/FBD graph, bindings, schedules, driver config, runtime compatibility, checksums и revision.
3. Field Runtime самостоятельно загружает последний разрешённый bundle после reboot и выполняет циклы без Workbench/Central.
4. Определить безопасный local state, watchdog, bounded restart, crash recovery, update/rollback, persistent node identity, authenticated IPC и epoch/generation fencing.
5. Потеря Supervisor/Central не останавливает автономное исполнение; устаревшие команды и пакеты отвергаются.
6. До появления этих механизмов называть реализацию только Field Runtime Process Host Prototype, не Edge Runtime и не автономным контроллером.

### A-003 — Не завершена производственная цепочка Authentication → Authorization → API → Audit
**Приоритет: P0 / блокирует удалённый/сетевой коммерческий Workbench.**

Фактическое поведение:
- В Security есть `SecurityManager`, сессии, Argon2, MFA, SecretStore, RBAC primitives и FastAPI adapter.
- `create_ui_app()` документирован как local-only Workbench. Mutating endpoints используют `require_local_operator()`, который проверяет loopback host и Origin.
- В показанном composition path UI создаёт CoreApplication, но не создаёт и не подключает SecurityManager/SecurityGateway как обязательную authentication middleware цепочку.
- Command Manager получает actor_id строкой; локальный режим ограничивает поверхность, но строка actor_id сама по себе не является доказанным Principal.
- Входные модели некоторых UI операций содержат actor_id с локальным значением по умолчанию. Это нельзя переносить в production identity model.

**Целевое решение:**
1. Единый authenticated Principal, передаваемый через request context/service boundary; actor_id нельзя принимать как доверенную личность из тела запроса.
2. Authorization проверяется на сервере в каждом service/use-case, а не только на UI/API route.
3. Permission + installation/project/station scope + capability + license entitlement — отдельные проверяемые условия.
4. Audit записывает фактического Principal, разрешение/отказ, correlation_id, target, before/after или reference к change set.
5. Локальный loopback guard сохраняется как дополнительная защита, но не считается authentication.
6. Сетевой/мобильный доступ запрещён до интеграционных тестов auth/RBAC/CSRF/session revocation/MFA/audit.

### A-004 — Command Manager пока simulation-only; граница будущего field write требует единого контракта
**Приоритет: P0 для архитектуры управления; текущий запрет реальной записи является правильной защитой.**

Фактическое поведение:
- `CommandManagerService` явно документирован как simulation-only; physical driver writes не выполняются.
- FBD execution публикует только read-only virtual FBD points; прямых полевых записей нет.
- ScheduleService формирует schedule intent и не выполняет физическую команду.
- Наличие трёх отдельных источников intent (оператор, расписание, FBD/автоматизация) требует единой арбитражной точки.

**Целевое решение:**
1. Ввести единый Command Contract: command_id, target, requested value, actor/agent, source intent, reason, priority, created_at, expiry/TTL, generation, correlation_id, idempotency key.
2. Command Manager — единственный policy/arbitration gateway к physical write executor.
3. Разделить intent, authorization, interlock evaluation, dispatch, protocol acknowledgement и observed feedback.
4. Ввести conflict arbitration для operator/manual, schedule, FBD/automatic, remote supervisor и emergency/local interlock.
5. Expired/stale/replayed commands отклоняются; retry не должен приводить к повторному опасному действию.
6. Write-capable driver capability включается только после RBAC, Access Lease, safety policy, audit, test/simulation и device-level acceptance.
7. Независимые safety interlocks и защитные функции остаются в предназначенном контроллере/оборудовании.

### A-005 — Несколько хранилищ без единой формальной карты владения и consistency
**Приоритет: P0/P1 — архитектурная спецификация обязательна до масштабирования и HA.**

Фактическое состояние:
- Core Object Repository использует `objects.sqlite3`.
- Отдельные хранилища существуют для Audit, Alarms, Events, History, Dependencies, Analytics, Notifications, Time Management, Engineering Lifecycle, Schedules, Point Views, Custom SVG и других служб.
- Alarm имеет собственные transition journal и durable outbox; это правильный локальный паттерн.
- History использует отдельный database и при старте выполняет reconciliation point usage, прямо называя это repair protocol вместо cross-database ACID.
- Configuration Manager хранит versioned JSON envelopes в файловом каталоге с lock DB; ProjectTransaction обеспечивает отдельный журнал файлово-DB операций.
- В доменной модели одновременно объявлены generic `Alarm`, `Event`, `HistoryRecord` entities, тогда как специализированные службы имеют собственные persistent records.

Риск:
- Неочевидно, какая модель является канонической для Alarm/Event/History и какие generic entities являются legacy/DTO.
- Нет общей таблицы: source of truth, owner, write API, transaction boundary, outbox/inbox, retention, backup/restore, migration owner.
- Межсервисные операции могут завершиться частично, если не определены idempotency и reconciliation.

**Целевое решение:**
1. Не обязательно сводить все данные в одну БД. Разделённые БД допустимы и полезны для изоляции нагрузки.
2. Для каждого агрегата назначить ровно одного владельца записи и один canonical write API.
3. Все cross-store операции оформлять через transactional outbox/inbox, idempotent consumers и reconciliation.
4. Утвердить единый backup/restore manifest с согласованными snapshot barriers и проверкой восстановления.
5. Удалить/пометить deprecated дублирующие generic entity модели только после проверки всех импортов, transfer format и миграций.
6. Определить retention/compaction и disk-capacity policy для каждого журнала.

### A-006 — Словарь качества точки не унифицирован
**Приоритет: P1, но контракт должен быть утверждён до расширения драйверов.**

Наблюдается расхождение:
- `PointQuality` содержит GOOD, UNCERTAIN, STALE, BAD_COMMUNICATION, BAD_CONFIGURATION, DISABLED.
- HistoryService использует GOOD, UNCERTAIN, STALE, BAD, COMM_LOST, DISABLED.
- FBD exposed point допускает BAD, COMM_LOST и дополнительные варианты.
- BACnet Rust adapter отображает Status_Flags в enum PointQuality, а отсутствие/невалидность flags переводит в UNCERTAIN.

**Целевое решение:**
- Ввести canonical cross-language Quality enum с документированными семантиками и compatibility mapping.
- Не смешивать quality, alarm state, out-of-service/disabled, freshness и communication diagnostics.
- Определить source_timestamp, received_at, processed_at, clock_quality, sequence и provenance как отдельные поля sample envelope.
- Запретить незаметное преобразование неизвестного качества в GOOD.

### A-007 — DependencyService пока не доказан как канонический граф объектов
**Приоритет: P1.**

Фактическое поведение:
- DependencyService хранит edges в отдельной SQLite DB.
- Его add() не проверяет существование обоих объектов, принадлежность станции, допустимость типа связи или циклы.
- delete_preview() возвращает advisory result; destructive operation должна отдельно потребить результат.
- Domain Object Service имеет собственную проверку части прямых ссылок при сохранении объектного графа, но это не тождественно универсальному Dependency Graph.

**Целевое решение:**
1. Разделить структурные ownership references и семантические dependency relations.
2. Для dependency edge определить relation registry, допустимые типы объектов, station/project scope и cycle policy.
3. Ввести проверяемый deletion/change plan с revision/fingerprint, чтобы preview нельзя было применить к уже изменившемуся графу.
4. Все delete/replace/transfer/publish операции должны учитывать обязательные зависимости.
5. Добавление edges должно быть атомарным с изменением соответствующего инженерного объекта либо через durable outbox.

### A-008 — Graphics и Web Pages имеют разные модели; границу надо сохранить, но унифицировать presentation contract
**Приоритет: P1.**

Фактическое поведение:
- Graphics имеет GraphicDocument, GraphicElement и PointBinding.
- Web Pages имеет WebPageNode с HTML/CSS/JavaScript, layout, graphic_ids и опубликованными версиями.
- WebPage может включать GraphicDocument как компонент.

**Целевое решение:**
- Не сливать страницу и мнемосхему в один гигантский документ.
- Ввести общий Presentation Asset/Renderer/Binding Contract.
- Page = навигационный/композиционный контейнер; GraphicDocument = инженерная мнемосхема; оба ссылаются на canonical objects/points.
- Публикация должна фиксировать immutable revision всех зависимых graphics/assets/bindings.
- Определить CSP, sandbox, trusted extensions, asset origin и политику выполнения пользовательского JavaScript.
- PX оставить необязательным importer/export adapter; native format AVIC остаётся собственным.

### A-009 — Application Composition и service ownership требуют формального правила
**Приоритет: P1.**

Положительная сторона: в текущем UI composition `app.state.driver_manager` и `app.state.fbd_execution` ссылаются на экземпляры, принадлежащие CoreApplication; второй экземпляр этих runtime служб в актуальном app.py не создаётся.

Открытый вопрос: CommandManagerService и часть UI/engineering services создаются в ASGI host, а не в CoreApplication. Нужно формально разделить:
- Platform/Core-owned services;
- Station Runtime-owned services;
- Host/UI adapters;
- request-scoped services.

Один service/process resource должен иметь одного владельца lifecycle. Shutdown должен закрывать владельцев в определённом порядке и не останавливать автономный Field Runtime.

### A-010 — Notification и Analytics пока являются базовыми registry/primitives, а не полными эксплуатационными платформами
**Приоритет: P1.**

- NotificationService хранит routes и durable outbox, но прямо указывает, что transport sender без adapter не выполняется.
- AnalyticsService содержит tags, hierarchy и deterministic aggregation primitives; это не полная Alarm Analytics/FDD/energy/reliability analytics.
- Alarm transition journal существует, но требуется доказать end-to-end ingestion, correlation, alarm KPIs, chattering/fleeting/standing, first-out, root-cause evidence, notification delivery and reporting.

**Целевое решение:** отделить event/alarm facts, analytical projections, recommendations и notification delivery. AI/analytics не должны непосредственно исполнять команды.

## 3. Целевая архитектура владения

| Область | Единственный владелец ответственности | Не должен делать |
|---|---|---|
| Domain/Object Registry | Core Object/Domain Service | Хранить высокочастотный поток sample как основной механизм |
| Point Definition | Point Manager | Выполнять сетевой I/O или физические команды |
| Point State | Point Runtime / State Store | Владеть инженерной конфигурацией и долгосрочным архивом |
| Historian | History Service/Store | Быть источником текущего оперативного значения |
| Network Discovery | Network Manager | Создавать активные field writes |
| Driver lifecycle | Driver Manager/Supervisor | Обходить Point Runtime |
| Protocol transport | Python/Rust Driver adapter | Самостоятельно менять Core objects или права |
| FBD/Automation | Station Automation Runtime | Обходить Command Manager для физических выходов |
| Command arbitration | Command Manager | Самостоятельно реализовывать протокол устройства |
| Field execution | Field Runtime | Зависеть от UI/Central для локального цикла |
| Alarm state | Alarm Manager | Подменять audit или operational event journal |
| Audit | Audit Service | Считаться защищённым только за счёт hash chain без внешнего anchor/ACL |
| Operational events | Event Service | Становиться заменой Alarm или Audit |
| Configuration/Deployment | Configuration + Deployment lifecycle | Применять несовместимые конфиги без migration/rollback |
| Identity/Authorization | Security Platform | Доверять actor_id, переданному клиентом |
| Graphics | Native Graphics Model/Renderer | Выполнять полевые команды напрямую |
| Web Pages | Page composition/publishing | Дублировать объектную и runtime модели |
| AI | AI Gateway/Policy/Tools | Иметь прямое право на управление оборудованием |

## 4. Целевые слои платформы

1. **Platform Foundation:** installation/tenant/project/station identity, canonical object model, contracts, schema/versioning, repository, configuration, security, licensing, audit.
2. **Station Runtime:** driver sessions, point state, quality/time, event stream, FBD, scheduler, command arbitration, local historian, alarms.
3. **Engineering Plane:** discovery, device onboarding, point import, FBD/graphics authoring, commissioning, simulation, change sets, staged publish/rollback.
4. **Operations Plane:** alarm/event analytics, notifications, asset passport, maintenance, reports, dashboards.
5. **Distributed Plane:** Central/Supervisor, station deployment, Edge autonomy, synchronization, HA, resource management.
6. **AI Plane:** provider gateway, context, knowledge, agent tools, policy and audit. AI remains advisory; changes go through validation/simulation/approval/publish.

Engineering Plane, Operations Plane and AI Plane must not become runtime owners. Central/Supervisor is not the deterministic control loop.

## 5. Архитектурные решения, которые нужно оформить ADR до расширения

- ADR-001: Point Definition vs Point State vs Historian sample ownership.
- ADR-002: Station Field Runtime process boundary and deployment bundle.
- ADR-003: Canonical Quality, timestamp and provenance contract.
- ADR-004: Command arbitration, lease, interlock, dispatch and feedback.
- ADR-005: Canonical aggregate ownership and multi-store consistency/outbox.
- ADR-006: Canonical identity, Principal, RBAC scopes and service authorization.
- ADR-007: Object ownership graph vs semantic dependency graph.
- ADR-008: Graphics/Page/Asset/Binding presentation model.
- ADR-009: Central/Edge synchronization, offline conflict and revision policy.
- ADR-010: API/SDK/module compatibility and deprecation policy.
- ADR-011: Backup/restore, migration and disaster recovery consistency.
- ADR-012: HA/fencing, node identity and split-brain protection.
- ADR-013: Event, Alarm, Audit, History and Notification semantics.
- ADR-014: Runtime resource budgets, isolation, backpressure and overload behavior.

## 6. Внешний инженерный benchmark

Официальные материалы Siemens Desigo CC полезны как контроль полноты, но не как шаблон копирования:
- Desigo CC описывает single-server, redundant-server и distributed configurations, северные/южные интеграции, открытые библиотеки/SDK, online engineering, mobile access и несколько дисциплин здания.
- System Openness перечисляет BACnet/BACnet-SC, OPC DA/UA, Modbus TCP, SNMP, KNX/KNX Secure, S7/S7 Plus/S7 secure и IEC 61850.
- Это подтверждает, что в AVIC надо проектировать northbound/southbound integration, SDK ecosystem, redundancy/distribution, mobile operations и мультидисциплинарную модель как архитектурные направления, а не как случайные будущие плагины.

Источники:
- https://sid.siemens.com/r/A6V11882331/15481750667_16118268811__en-US_15261635851
- https://sid.siemens.com/r/A6V12900997/33153351179___en-US_33213215115
- https://www.siemens.com/en-us/products/desigo/cc-ecosystem/

## 7. Проверки и текущие ограничения аудита

- Проверен Git tree и исходники ветки `dev219-rust-worker-ci` на SHA `ae85b68f60a2680ddad7fb7594f4b44158b89379`.
- PR #7 остаётся Draft и stacked поверх PR #6; PR #6 также Draft. Нельзя считать эту цепочку готовой к merge без проверки base/head и полного CI.
- CI run #651 для SHA ae85: Python Linux jobs 3.11/3.12/3.13 и Windows 3.11 завершились успешно; Windows 3.12/3.13 были ещё в процессе при просмотре. Rust unit tests завершились успешно на Windows/Linux, но benchmark job завершился ошибкой на обеих ОС.
- Причина benchmark failure установлена по исходникам и job logs: DEV221 Rust client сохраняет TCP session, а benchmark ModbusHandler закрывал соединение после одного ADU. Это дефект simulator fixture, не доказательство дефекта Modbus client.
- В commit `8f74b8f9dda9f27ea6ba657bc08f5d711c85e7bc` benchmark simulator изменён на обработку нескольких ADU в одном TCP соединении. Новый CI для этого commit должен подтвердить исправление; до этого benchmark считается не прошедшим.
- Эта ревизия не утверждает готовность Production Security, автономного Field Runtime, physical writes, HA, distributed sync, full BACnet parity, production notifications или full analytics.
- Не проверены полностью: все API endpoints, все domain mutations, полный transfer/migration graph, performance profiles, fuzzing, penetration tests, backup disaster recovery, real BACnet/Modbus/KNX controllers, Linux/Windows service recovery, ARM target.

## 8. Критерий закрытия ARCHITECTURE_DEFINED

Модуль получает этот статус только если:
1. Назначен единственный владелец данных и операций.
2. Описаны входы/выходы, versioned contracts и compatibility policy.
3. Определены storage ownership, transaction boundaries, outbox/inbox и recovery.
4. Определены security principal, authorization scopes и audit.
5. Определены timeout, retry, backpressure, overload и failure semantics.
6. Описаны зависимости и запрещённые зависимости.
7. Определена миграция и обратная совместимость.
8. Есть architecture tests и acceptance scenarios.
9. Проверена совместимость Central, Edge и будущего Controller.
10. Нет открытого P0 противоречия с соседними модулями.

**Итоговый статус всей платформы после этого прохода: ARCHITECTURE_AUDIT_IN_PROGRESS.**  
Ни один P0 не закрыт только этим документом. Следующий этап — оформить ADR-001…ADR-014, затем связать их с кодом и architecture tests.


## 15. Дополнение ревизии — DEV222 benchmark fixture и ADR-001

### 15.1 Повторный CI показал, что первое исправление fixture было неполным

Run #653 на исходном audit head `c9496ec3ce0c9f37b1a90f3d83df662086dc6dc9`:
- Python Linux 3.11 / 3.12 / 3.13 — success.
- Rust unit tests — success на Linux и Windows.
- Python Windows 3.11 / 3.12 / 3.13 — на момент последней проверки выполнялись.
- Сравнительный Modbus benchmark 10 000 точек — failure на Linux и Windows.

Повторный анализ показал конкретный дефект тестового сервера: MBAP Protocol Identifier собирался как литеральные байты последовательности `\\x00\\x00`, а не как два нулевых байта. Из-за этого Rust-клиент получал некорректный Modbus TCP frame. Первоначальное исправление persistent connection не устранило эту ошибку framing.

В ветку audit внесено:
- отдельная функция `build_fc03_response()` с корректным MBAP/PDU framing;
- проверка диапазона holding registers;
- диагностическое включение stdout/stderr Rust benchmark process при ошибке;
- регрессионные тесты `tests/test_modbus_benchmark_fixture.py` на MBAP length, protocol id, unit id, function code, byte count, register payload и invalid range.

Изменения внесены коммитами:
- `27728d82bc85e5ce88c468a3308be6ab569e25d6` — исправление protocol bytes;
- `1d4abb4d79cc6cc5e475fd7f0627e7352c96910f` — helper и диагностика;
- `9b8b1a2cc13e43d3d146ce292a0476335b48a247` — regression tests.

**Статус проверки:** исправление ещё не подтверждено новым CI на этих коммитах. Run #653 проверял более ранний SHA, поэтому его failure нельзя использовать как результат проверки исправленного кода; но и считать проблему закрытой до нового успешного benchmark нельзя.

### 15.2 Создан фундаментальный ADR-001

Создан документ `ADR-001_POINT_DEFINITION_STATE_SAMPLE_RU.md` со статусом PROPOSED. Он фиксирует:
- раздельное владение Point Definition, Point State, Point Sample и Historical Record;
- единый typed Sample envelope для Python/Rust и Core/Edge;
- единый ingestion API;
- state + durable outbox в одной транзакционной границе;
- idempotent consumers для Historian/Alarms/FBD/Analytics;
- station isolation и runtime epoch fencing;
- backpressure и явный degraded mode;
- миграцию текущих `Point.value/quality/timestamp`;
- acceptance tests для корректности, отказов, масштаба, интеграции и Windows/Linux.

ADR-001 не считается принятым и не означает готовую реализацию. Для ACCEPTED обязательны прототип, crash-consistency tests, migration proof и нагрузочные испытания.

### 15.3 Обновлённый статус

- Архитектурная ревизия: IN_PROGRESS.
- ADR-001: PROPOSED, ожидает реализации прототипа и acceptance evidence.
- Point Runtime: P0 finding остаётся открытым.
- Rust Modbus benchmark: NOT VERIFIED на исправленном fixture.
- `ARCHITECTURE_DEFINED`: не присваивается.


## 16. Дополнение — Security, Time Manager, Alarm/Notification и Edge contracts

### 16.1 Security: уточнение границы

В коде действительно существуют не только RBAC primitives, но и:
- `SecurityGateway.execute()` с authentication → scope RBAC → CSRF → action → audit;
- FastAPI adapter с secure cookie, Origin/HTTPS policy, rate limiter, security headers и `AuthorizedOperation`;
- `validate_security_routes()`, который может fail-closed проверить изменяющие маршруты;
- тесты gateway и FastAPI adapter, включая CSRF, Origin, audit chain, route coverage и cookie flags;
- `CorePublicAPI` с отдельной проверкой station scope.

Это положительная основа. Однако текущий `create_ui_app()` по-прежнему явно документирован как DEV175 local-only Workbench, не подключает SecurityGateway/AVICSecurityMiddleware и защищает мутации через loopback + Origin guard. В комментарии прямо сказано, что session/RBAC ещё не интегрированы. Поэтому A-003 остаётся открытым именно как проблема production composition/integration, а не как отсутствие Security компонентов.

Дополнительный риск: CommandManager принимает `actor_id` строкой и UI модели alarm acknowledgement/note допускают локальные actor defaults. Это приемлемо только в локальном ограниченном режиме; production actor должен поступать из authenticated Principal, а не из payload.

### 16.2 Time Manager — хранит политику, но не доказывает синхронизацию

`TimeManagementService` сохраняет timezone/NTP settings и per-device clock-sync permission. При этом сам сервис не выполняет NTP synchronization и не предоставляет доказательство фактического clock sync. `set_device_sync_permission()` принимает `approved_by` строкой; это не authenticated Principal. Следовательно, в UI и API нельзя показывать «часы синхронизированы» только потому, что NTP включён в конфигурации.

Создан ADR-003 `ADR-003_QUALITY_TIME_SAMPLE_ORDERING_RU.md`: canonical Quality, source/receive/process timestamps, monotonic timers, sequence ordering, clock quality и отдельное permission enforcement для clock-write.

### 16.3 Data ownership и durable events

Проверка сервисов подтвердила неодинаковую зрелость outbox:
- AlarmService атомарно фиксирует alarm state, transition event и durable outbox в одной Alarm DB — сохранить этот паттерн.
- NotificationService имеет durable outbox/route registry, но не выполняет transport delivery без sender adapter; статус QUEUED_NO_TRANSPORT честно отражает текущее состояние.
- HistoryService хранит собственную историю и binding catalog; Point usage ledger Core восстанавливается отдельным idempotent reconciliation после старта.
- DependencyService остаётся отдельной БД, но не проверяет существование endpoint, station scope, relation registry и cycle policy.

Создан ADR-005 `ADR-005_DATA_OWNERSHIP_OUTBOX_BACKUP_RU.md`: карта source-of-truth, owner per aggregate, transactional outbox/inbox, idempotent delivery, consistency manifest, retention и staged restore.

### 16.4 Созданные фундаментальные ADR

| ADR | Тема | Статус |
|---|---|---|
| ADR-001 | Point Definition / Point State / Sample | PROPOSED |
| ADR-002 | Station Runtime / signed deployment / Edge autonomy | PROPOSED |
| ADR-003 | Canonical Quality / Time / Sample ordering | PROPOSED |
| ADR-005 | Data ownership / outbox-inbox / backup-restore | PROPOSED |

Все четыре документа — проектные контракты, не реализованные функции. До acceptance tests и интеграции статусы не повышаются.

### 16.5 Сравнительная проверка

В каждый ADR добавлена отдельная проверка по трём ориентирам:
- Niagara — объектная и станционная инженерная модель, drivers, points, lifecycle;
- Trend IQVision — повседневная инженерная работа, FBD, графика, диагностика и обслуживание;
- Siemens Desigo CC — распределённая эксплуатация, системная интеграция, мобильный/центральный доступ, долговременные данные и автономность нижнего уровня.

Это контрольные ориентиры, а не требование повторять внутреннюю реализацию этих продуктов.


### 16.6 Command boundary — подтверждение текущей безопасной заглушки

Проверен `CommandManagerService`:
- режим явно `SIMULATION_ONLY`;
- физические driver writes не выполняются;
- Access Lease ограничен 900 секундами, привязан к station и actor_id;
- проверяются OUTPUT/INOUT, boolean data type и quality interlock;
- simulated feedback отдельно фиксирует confirmed/mismatch;
- результат явно содержит `field_write_performed: false`.

Это правильная безопасная заглушка, но не законченный Command Manager. Lease и actor_id пока не связаны с authenticated Principal/SecurityGateway в текущем UI composition; приёмка interlock требует проверки свежести sample и полного контракта, а не только GOOD. Нет единого arbitration pipeline между Operator, Schedule, FBD и Supervisor, поскольку Schedule/FBD пока не dispatch physical commands.

Создан ADR-004 `ADR-004_COMMAND_ARBITRATION_FIELD_WRITE_RU.md`: единый Command Contract, этапы authentication/authorization/lease/freshness/interlocks/arbitration/dispatch/ACK/readback, idempotency, timeout/UNKNOWN semantics и запрет прямых driver writes.

### 16.7 Полный список созданных проектных ADR

| ADR | Тема | Статус |
|---|---|---|
| ADR-001 | Point Definition / Point State / Sample | PROPOSED |
| ADR-002 | Station Runtime / signed deployment / Edge autonomy | PROPOSED |
| ADR-003 | Canonical Quality / Time / Sample ordering | PROPOSED |
| ADR-004 | Command arbitration / physical write boundary | PROPOSED |
| ADR-005 | Data ownership / outbox-inbox / backup-restore | PROPOSED |



### 16.8 Rust Communication Engine — важное уточнение масштаба

Проверены `RustDriverWorker`, Rust IPC envelope, `avic_driver_worker.rs`, `RustDriverPointAdapter` и DriverManager:
- текущая интеграция уже поддерживает per-DriverInstance выбор Python/Rust для Modbus TCP, BACnet/IP и KNXnet/IP;
- Rust worker изолирован по installation/project/station/driver_instance, worker_id и generation;
- IPC framed JSON имеет лимит 1 MiB, проверяет contract/version/scope/correlation/sequence;
- Rust worker запрещает write/write_point и не публикует данные в Point Runtime напрямую;
- Python adapter выполняет binding resolution, scaling, quality mapping и публикацию в PointRuntime;
- Modbus TCP session reuse присутствует внутри Rust worker.

Обнаружено принципиальное ограничение benchmark: `avic_modbus_bench.rs` делает один FC03 read на 100 регистров на устройство за цикл. Это полезный protocol microbenchmark, но он не измеряет реальную цепочку AVIC Driver Manager → IPC → binding mapping → PointRuntime publish.

В реальном `RustDriverPointAdapter._read_modbus()` выполняется один worker read на каждый binding. Следовательно, текущая реализация не доказывает batch polling для большого количества точек и может генерировать слишком много IPC/Modbus transactions. BACnet Rust adapter получает snapshot один раз на уникальное устройство за poll; стоимость полного snapshot и возможность RPM/COV требуют отдельного подтверждения. Эти пункты внесены в ADR-006.

Создан ADR-006 `ADR-006_RUST_COMMUNICATION_ENGINE_BOUNDARY_RU.md`: Python остаётся владельцем SCADA/engineering/data/security, Rust — протокольного I/O; определены batch strategies, IPC compatibility, worker signing, restart/fencing, parity tests и end-to-end benchmark.



### 16.9 Реестр решений — обновление

| ADR | Тема | Статус |
|---|---|---|
| ADR-001 | Point Definition / Point State / Sample | PROPOSED |
| ADR-002 | Station Runtime / signed deployment / Edge autonomy | PROPOSED |
| ADR-003 | Canonical Quality / Time / Sample ordering | PROPOSED |
| ADR-004 | Command arbitration / physical write boundary | PROPOSED |
| ADR-005 | Data ownership / outbox-inbox / backup-restore | PROPOSED |
| ADR-006 | Rust Communication Engine / IPC / batching / worker lifecycle | PROPOSED |

### 16.10 CI evidence boundary

После создания regression test и ADR документы были добавлены в PR #8, но GitHub Actions не создал новый workflow run для новых head commits через используемый способ обновления файлов. Текущий доступный run #653 относится к старому SHA `c9496ec3ce0c9f37b1a90f3d83df662086dc6dc9`:
- Python Linux matrix завершена успешно;
- Python Windows 3.12 и 3.13 завершены успешно;
- Python Windows 3.11 оставался in_progress при последней проверке;
- Rust unit tests прошли на Linux/Windows;
- Rust Modbus benchmark завершился failure на Linux/Windows до исправления MBAP framing.

Новый benchmark fix и regression tests **не имеют CI evidence**. Не считать их проверенными до запуска workflow на актуальном PR head `18b6cb3b50458ef5bced0859db5575d50b1bbb87`.

