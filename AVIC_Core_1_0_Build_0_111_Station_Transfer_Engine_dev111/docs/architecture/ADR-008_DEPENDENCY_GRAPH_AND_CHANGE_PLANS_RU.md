# ADR-008 — Канонический граф зависимостей и безопасные Change Plans

Статус: **PROPOSED**  
Дата: 27.11.2026  
Область: Object Model, Engineering, FBD, Graphics, Pages, Alarm, Scheduler, Driver, Deployment, Transfer.

## 1. Цель

Любое изменение инженерного объекта должно заранее показывать, что от него зависит, что будет затронуто и какие действия требуются. Удаление, перенос, замена, отключение и публикация не должны полагаться на устаревающий preview или на неявные каскады.

## 2. Две разные модели отношений

### Ownership / containment

Отвечает на вопросы «кто владелец?» и «где живёт объект?». Примеры:
- Project → Station;
- Station → Device / Component / DriverInstance;
- Device → Point;
- Page → композиция графических документов.

Это структура владения, scope и lifecycle. Она задаёт каскадные правила только для явно определённых типов.

### Semantic dependency

Отвечает на вопрос «что использует этот объект?». Примеры:
- FBD binding → Point;
- Graphic binding → Point;
- Page → GraphicDocument;
- Alarm definition → Point;
- Schedule action → Command target;
- Analytics rule → Point / Equipment;
- DriverInstance → DriverPackage;
- report / dashboard → query or asset.

Удаление объекта с активными semantic dependents должно блокироваться либо требовать явно утверждённого Change Plan.

Не объединять ownership и semantic dependencies в одну таблицу: у них разные семантика, циклы, правила удаления и транзакционные границы.

## 3. Что уже есть в коде

- `CoreObjectService._validate_graph()` проверяет значительную часть ссылок: Project/Station, Station/Device, Device/Point, Link endpoints, station scope для Alarm/Event/History, DriverPackage/DriverInstance.
- `CoreObjectService.save_graph()` сохраняет связанный набор объектов в транзакции SQLite и использует optimistic versions.
- `CoreObjectService.delete_graph()` проверяет оставшийся объектный граф после планируемого удаления, сверяет версии и удаляет набор транзакционно. Это полезный базовый механизм.
- `DependencyService` существует отдельно в SQLite и хранит semantic edges; имеет list, advisory delete preview и remove_object_edges.
- `ProjectTransaction` умеет durable PREPARED → DB_COMMITTED → COMMITTED с восстановлением файлов после commit decision.
- API удаления Project/Station имеет preview/cascade; тесты DEV45 подтверждают базовые сценарии каскада Station и Project.

Это не означает, что существует единый dependency-aware Change Plan. Сейчас две модели связей не объединены, а DependencyService.add() не подтверждает существование endpoints, допустимый relation type или station scope. Его preview не является атомарным разрешением на последующее удаление.

## 4. Проблемы и риски

1. **Граф неканонический:** ownership references в CoreObjectService и semantic edges в DependencyService хранятся отдельно, без общего индекса влияния.
2. **Нет relation registry:** произвольная строка relation_type может попасть в БД; нет declared source/target kinds и lifecycle policy.
3. **Нет проверки endpoint:** edge может ссылаться на несуществующий объект.
4. **Нет scope enforcement:** station_id у edge не проверяется относительно source/target; возможна cross-station связь.
5. **Нет cycle policy:** допустимость циклов зависит от relation type, но сейчас не описана и не проверяется.
6. **Preview TOCTOU:** между preview и delete/transfer/publish граф может измениться. Повторный preview сам по себе не защищает от гонки.
7. **Удаление edge отдельно:** remove_object_edges может удалить связи без общей транзакции с удалением объекта.
8. **Неполный охват:** FBD/Graphics/Pages/Scheduler/Alarm/Analytics должны иметь явные владельческие адаптеры, иначе dependency graph будет неполным.
9. **Миграции и backup:** несколько БД означают, что объект и его зависимости могут попасть в разные снимки, если нет общей согласованной границы.

## 5. Целевая модель

### 5.1 Relation Registry

Каждый тип связи объявляется контрактом:
- relation_type (стабильный versioned identifier);
- source entity kinds;
- target entity kinds;
- direction semantics (dependent → dependency);
- scope rule (same station / same project / cross-station allowed / global);
- cardinality and uniqueness;
- cycle policy (forbid / allow / bounded / special);
- on_delete policy (RESTRICT / PLAN_REQUIRED / CASCADE_OWNED_ONLY / DETACH_ALLOWED);
- on_transfer policy;
- on_publish policy;
- owner adapter and schema version.

Неизвестный relation_type — reject, не «принять и надеяться».

### 5.2 Canonical Dependency Graph API

Операции:
- add/remove edge;
- list inbound/outbound;
- impact analysis;
- transitive dependency closure;
- cycle detection where relation policy requires;
- graph revision/fingerprint;
- validate object and station scope;
- reconcile edges from owning subsystems;
- consistency check for dangling edges.

Graph service не становится владельцем объектов и не дублирует payload. Он хранит только ссылку, тип отношения, scope, metadata, provenance, owner revision.

### 5.3 Change Plan

Каждое разрушительное/перемещающее изменение формирует immutable plan:
- plan_id, operation, target IDs;
- actor Principal, requested_at, reason;
- expected object versions;
- expected graph revision/fingerprint;
- impacted objects and edge list;
- proposed actions (detach, replace, migrate, disable, retain, delete);
- blockers and warnings;
- required approvals/permissions;
- plan expiry and idempotency key.

Execution повторно валидирует Principal, permissions, licenses, object versions, graph revision, lifecycle state и все blockers **внутри одной transaction boundary**. Если что-либо изменилось — plan stale, выполнение отклоняется и нужен новый preview.

### 5.4 Safe deletion semantics

- Ownership cascade удаляет только реально принадлежащие объекты, по явной таблице типов.
- Semantic dependents не удаляются молча.
- RESTRICT: блокировать.
- PLAN_REQUIRED: требовать заменить/отвязать/перенести зависимые объекты в плане.
- CASCADE_OWNED_ONLY: разрешён только для ownership subtree.
- DETACH_ALLOWED: только если relation type допускает и последствия записаны в audit.
- Версии и graph fingerprint проверяются атомарно с удалением.
- История/аудит/архивные записи не должны исчезать из-за каскада engineering objects без отдельной retention policy.

## 6. Transfer, clone и publish

### Station Transfer / Clone
- собрать полный ownership subtree;
- собрать все inbound/outbound semantic dependencies;
- классифицировать external references: запрещены, остаются на source, remap, или требуют cross-station contract;
- создать deterministic ID remapping table;
- проверить license capacity, driver package availability, network/site profile, secrets provisioning;
- dry-run и diff до записи;
- commit через ProjectTransaction/новую единицу согласованной публикации;
- source остаётся неизменным при ошибке.

### Publish
- опубликованная версия — immutable snapshot;
- все binding references разрешены;
- нет dangling edges или запрещённых cross-station links;
- graph fingerprint совпадает с preview;
- validation/simulation/approval пройдены;
- deployment package подписан и привязан к точной версии конфигурации.

## 7. Хранилище и согласованность

Не объединять все БД в одну ради простоты. Вместо этого:
- определить authoritative owner каждого aggregate;
- для одного aggregate — один write owner;
- graph mutations должны участвовать в транзакции владельца или через transactional outbox/inbox с idempotent reconciliation;
- destructive operations не могут считать eventual consistency достаточной;
- backup должен фиксировать согласованный набор revisions и журналов;
- восстановление выполняет integrity + referential + graph consistency checks до запуска станции.

## 8. Сравнение с тремя системами

### Niagara
Сохраняем инженерные связи между components, slots, points, pages и modules. Важная особенность Niagara-подобной композиции — references являются частью инженерной модели, а не только строками в UI. AVIC дополнительно требует формальный impact plan и атомарное подтверждение изменений.

### Trend IQVision
Упрощаем ежедневный процесс инженера: preview должен показывать, что именно будет затронуто, без необходимости вручную обходить все страницы/графики/FBD. Частые операции должны быть понятными и предсказуемыми, но не скрывать зависимости.

### Siemens Desigo CC
Для большой мультидисциплинарной системы необходимы scope, ownership, интеграционные зависимости и управляемый lifecycle. Изменения должны учитывать внешние подсистемы и распределённые узлы, а не только локальный объектный список.

### AVIC
Один Change Plan для delete/replace/transfer/clone/publish; никакой незащищённой последовательности «посмотрели preview → через минуту удалили по старому preview».

## 9. План внедрения

1. Инвентаризировать все object references и subsystem bindings.
2. Утвердить Relation Registry v1 и scope/cycle/delete policies.
3. Добавить endpoint validation и station/project scope validation в DependencyService.
4. Добавить graph revision/fingerprint и тесты на concurrent mutation.
5. Сделать ChangePlan preview/execute API; execution revalidates under transaction.
6. Подключить FBD, Graphics, Pages, Alarm, Scheduler и Analytics adapters.
7. Интегрировать clone/transfer/publish с Change Plan.
8. Добавить reconciliation/backup restore checks и migration.
9. Только после parity и regression tests перевести старые delete flows на общий механизм.

## 10. Acceptance tests

- nonexistent endpoint rejected;
- wrong entity kind rejected;
- cross-station dependency rejected unless relation explicitly allows it;
- unknown relation type rejected;
- forbidden cycle rejected; allowed cycle accepted;
- inbound dependents block deletion by default;
- stale graph fingerprint rejects execution;
- stale entity version rejects execution;
- concurrent add edge vs delete is serialized safely;
- failure midway leaves no partial ownership/semantic graph update;
- clone remaps internal edges and handles external edges according to policy;
- transfer preserves source and never imports secrets;
- publish refuses dangling or out-of-scope bindings;
- backup restore detects dangling/mismatched graph revisions;
- all actions have actor Principal, audit correlation and idempotency.

## 11. Статус

Это архитектурный контракт, не заявление о готовой реализации. Existing CoreObjectService is a useful base; DependencyService needs hardening and integration. No ARCHITECTURE_DEFINED status until ownership map, relation registry, change plans and runtime boundaries are verified in code and acceptance tests.
