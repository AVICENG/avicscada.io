# Архитектурное решение: AVIC Communication Engine и точечное применение Rust

Статус: **утверждено как целевое направление; реализация и эксплуатационные показатели ещё не подтверждены**.  
Базовая точка аудита: PR #5, commit `f5f4ff660d8d4c7a74fa3b12944283c31705dfca` (27.11.2026).  
Рабочая ветка архитектурного этапа: `architecture/rust-communication-engine`.

## 1. Цель

AVIC должен быть быстрой промышленной SCADA, рассчитанной на десятки тысяч точек и существенно больший архитектурный запас. Производительность не должна достигаться ценой потери данных, перегрузки слабых контроллеров, нарушения изоляции станций или усложнения восстановления после обрыва связи.

Python сохраняется как основной язык Core и инженерной платформы. Rust применяется точечно в высоконагруженных сетевых и runtime-компонентах, где преимущество подтверждено одинаковыми нагрузочными испытаниями.

## 2. Результат аудита текущей реализации

На базовом commit обнаружено:

- `DriverManagerService` создаёт Python-адаптеры BACnet/IP, Modbus TCP и KNXnet/IP.
- `PollingSession` — отдельный последовательный worker на экземпляр адаптера. Он не делает catch-up запросов при превышении интервала, что защищает от немедленной лавины после медленного цикла, но не является общим планировщиком нагрузки.
- Modbus TCP адаптер объединяет соседние/перекрывающиеся read-only bindings с одинаковым function code в ограниченные группы (до 125 регистров или 2000 бит). Это сохраняется как обязательная оптимизация.
- BACnet/IP adapter выполняет последовательные ReadProperty по bindings. Текущий клиент сериализует операции на одном UDP socket/Invoke ID. RPM, полноценная сегментация и COV ещё не реализованы.
- Point Runtime уже проверяет владельца DriverInstance, принадлежность Device станции, порядок timestamp и качество. Эти инварианты нельзя обходить переносом сетевого кода на Rust.
- `FieldRuntimeProcess` / agent — пока только отдельный процесс и IPC host. FBD execution не подключён; он не является готовым Communication Engine.
- Driver SDK сейчас Python Protocol/Manifest. Межъязыковой versioned wire contract для Rust worker ещё не создан.
- Физическое управление через BACnet/Modbus write не включать в первый Rust этап. Текущие полевые адаптеры read-only.

Подробные исходные материалы: `docs/DRIVER_AUDIT_DEV128_RU.md`, `docs/DRIVER_POLLING_LIFECYCLE_DEV121_RU.md`, `docs/architecture/FIELD_RUNTIME_BOUNDARY_RU.md`, `docs/architecture/FIELD_RUNTIME_PROCESS_DEV181_RU.md`.

## 3. Целевая архитектура

### 3.1 Разделение ответственности

**Python AVIC Core / Supervisor**
- инженерные проекты, конфигурация и каталог драйверов;
- лицензирование, RBAC, Audit, SecretStore;
- владение объектной моделью и authoritative Point Runtime;
- проверка источника, station scope, timestamp, quality и прав;
- API, FBD orchestration, alarms, historian, scheduler и UI;
- lifecycle, диагностика и безопасная публикация конфигурации worker.

**Rust Communication Engine**
- сетевой transport и protocol codec;
- планирование polling и подписок;
- группировка чтений, ограничение скорости и конкурентности;
- bounded queues и backpressure;
- таймауты, circuit breaker, retry/backoff с jitter;
- диагностика сетевых транзакций и восстановление сессий;
- выдача типизированных sample/event сообщений в Core.

Rust worker не получает прямого доступа к Core DB, лицензиям, RBAC, Audit DB или секретам, если для конкретной операции не определён отдельный минимальный credential contract. Он не может самостоятельно разрешать команды управления. Все значения проходят Core validation до публикации в Point Runtime.

### 3.2 Процессная изоляция и IPC

Предпочтительный production boundary — отдельный Rust OS process/service, а не загрузка критичного сетевого движка внутрь Python процесса.

- Локальный IPC: Windows Named Pipes и Unix Domain Sockets; loopback TCP допустим только как временный dev/test transport, не как автоматический production default.
- Версионированный контракт с handshake, идентификатором worker/instance, sequence, request correlation, generation/epoch, TTL и idempotency.
- Строгие лимиты размера сообщений, количества in-flight запросов, очередей и времени обработки.
- Аутентификация локального peer и ACL на IPC endpoint; секреты не передаются в логах и не хранятся в обычной конфигурации.
- Потеря IPC не означает автоматическую остановку автономного безопасного процесса; reconnect и повторная сверка generation обязательны.
- Не создавать отдельный OS process на каждую точку. Единица изоляции — станция или конфигурируемый communication shard; внутри — изолированные device actors/queues и лимиты на устройство. Число процессов определяется benchmark и ресурсами.
- Supervisor restart, worker crash, устаревшая конфигурация и дублированные sample events должны иметь явную семантику восстановления.

### 3.3 Планирование опроса

Планировщик должен учитывать:
- per-device max in-flight, request rate и минимальный интервал;
- per-network/interface budget и общий предел worker;
- scan classes / приоритеты (critical, normal, background);
- групповое чтение с лимитами протокола и конкретного device profile;
- jitter при расписании и восстановлении;
- адаптивное снижение нагрузки при росте timeout/latency;
- ограниченный backoff и circuit breaker для недоступного устройства;
- запрет catch-up burst: пропущенные тики не должны создавать пачку устаревших запросов;
- fair scheduling: один медленный или неисправный контроллер не блокирует остальные;
- COV lifecycle: subscribe, confirmation, lease/renew, health check, resubscribe и polling fallback;
- bounded queues, backpressure, coalescing для заменяемых текущих значений и явный учёт отброшенных/устаревших событий.

Адаптивный алгоритм не должен самопроизвольно повышать нагрузку выше явно заданных безопасных профилем устройства пределов.

### 3.4 Достоверность и непрерывность данных

- Timestamp измерения и timestamp получения — отдельные поля.
- Out-of-order sample не может откатить текущее значение.
- Потеря связи маркирует качество; последнее значение может сохраняться для отображения, но не выдаётся за актуальное.
- После восстановления GOOD возвращается только после нового валидного sample.
- Если контроллер не буферизовал данные во время обрыва, AVIC фиксирует data gap; синтетическое восстановление истории запрещено.
- Повторная доставка IPC event должна быть идемпотентной или отфильтрована по event ID/sequence.
- Station ownership и driver identity проверяются на стороне Core независимо от сообщения worker.

## 4. Очерёдность реализации

### Этап A — контракты и baseline
1. Зафиксировать Driver SDK v1 и языконезависимые схемы событий/команд.
2. Добавить контрактные тесты Python adapter ↔ Core.
3. Построить baseline текущего Python polling: CPU, RAM, requests/sec, updates/sec, p50/p95/p99, queue depth, timeouts, recovery.
4. Подготовить BACnet и Modbus simulators и fault injector.

### Этап B — Rust Modbus TCP pilot
Modbus выбран первым пилотом: текущий адаптер уже имеет детерминированную read-only модель и grouped reads; это позволяет сравнить реализации на одинаковых сценариях без смешения результата с незавершённой BACnet COV/segmentation работой.

1. Реализовать Rust worker для Modbus TCP read-only.
2. Сохранить группировку FC01/02/03/04 и пределы протокола.
3. Ввести per-device profiles, bounded queues, rate limiting, backoff/jitter и диагностику.
4. Подключить worker через IPC к Core Point Runtime.
5. Сравнить с Python адаптером на одном стенде и одинаковом hardware/network profile.
6. Не удалять Python adapter, пока Rust не пройдёт parity, regression, Windows/Linux CI и load/fault acceptance.

### Этап C — Rust BACnet/IP
1. Сначала закрыть протокольный аудит: NPDU/APDU, маршрутизация, сегментация/reassembly, RPM, COV subscribe/renew/cancel, BBMD/foreign device и vendor interoperability.
2. Выбрать зависимости после проверки поддержки, лицензий, security posture, Windows/Linux и активности проекта; не принимать crate как доверенный только по популярности.
3. Реализовать read-only parity и fallback polling.
4. Выполнить interoperability и hardware acceptance на нескольких реальных контроллерах, включая слабые устройства.

### Этап D — другие узкие места
Только по результатам профилирования рассматривать Rust для Point Runtime hot path, FBD execution или Historian ingestion. Не переносить компоненты «на всякий случай».

## 5. Niagara / Trend IQVision — ориентиры, не копирование

Сверка с открытыми материалами Tridium показывает следующие направления, которые AVIC обязан учитывать:
- модульная driver ecosystem и возможность сторонних драйверов;
- field/edge и supervisor роли, локальная работа полевых узлов;
- BACnet protocol evolution и MSTP engine optimization;
- единая платформа для histories, alarms, schedules, graphics, engineering tools и enterprise integration;
- управление модулями, их подписями, безопасностью и совместимостью.

Открытые источники Tridium:
- https://www.tridium.com/us/en/Products/niagara-drivers
- https://www.tridium.com/us/en/Products/niagara
- https://www.tridium.com/us/en/Learn/about-us/niagara-timeline
- https://www.tridium.com/us/en/Products/niagara/supervisor

Не декомпилировать vendor binaries и не копировать закрытые реализации. Использовать открытые спецификации протоколов, публичную документацию и предоставленные пользователем материалы в рамках допустимого анализа. Отдельные заявления о parity делать только после функциональных тестов.

## 6. Нагрузочные и отказные испытания

Все показатели ниже — целевые сценарии испытаний, а не обещанные характеристики.

### Масштаб
- 1k, 10k, 20k, 50k и 100k virtual points;
- разные числа устройств и точек на устройство;
- 1/10/30/60 секунд scan classes;
- изменение всех точек, COV bursts и групповые ответы;
- параллельно FBD, alarms, Historian, graphics/API.

### Слабые и нестабильные устройства
- лимиты 1/2/5/10 запросов в секунду на device;
- ограничение 1 in-flight request;
- latency 100 ms–3 s;
- packet loss 1/5/10/30%;
- jitter, timeout, malformed response, protocol exception;
- частичная доступность bindings;
- отключение 10–30% устройств и staggered recovery;
- отказ одного устройства не должен останавливать соседние устройства.

### Отказы процесса и данных
- worker crash/restart;
- Supervisor restart и IPC disconnect;
- потеря и восстановление сетевого интерфейса;
- устаревшие, дублированные и out-of-order events;
- переполнение очередей и backpressure;
- потеря COV subscription/renewal;
- 24h/72h soak test и измерение роста памяти.

### Метрики и критерии
Обязательно сохранять CPU, RSS/RAM, network bytes, requests/sec, successful transactions/sec, updates/sec, p50/p95/p99 latency, timeout/error rate, queue depth/high-water mark, dropped/coalesced events, data gaps, recovery time и correctness assertions.

Acceptance не равен «pytest зелёный». Нужны:
1. unit/contract/regression tests;
2. full Linux и Windows CI;
3. repeatable load/fault runs;
4. сравнение Python baseline vs Rust pilot;
5. реальные hardware acceptance tests для конкретных протоколов и моделей;
6. русскоязычный журнал сборки и limitations.

## 7. Критерии запрета на миграцию / rollback

Rust worker не становится production default, если:
- нарушает API/данные/качество/станционную изоляцию;
- имеет потери, дубли или неверный порядок sample;
- не выдерживает ограничение памяти/очередей;
- хуже Python baseline по критичным метрикам без компенсирующего эксплуатационного преимущества;
- не проходит Windows или Linux;
- не может безопасно восстановиться после IPC/worker failure;
- его зависимости не прошли license/security/SBOM review.

Переключение должно быть feature-gated и обратимым: Python fallback сохраняется до завершения acceptance. Rollback не должен терять конфигурацию, audit trail или последние корректные значения.

## 8. Импортонезависимость и поставка

Для каждого Rust crate и Python dependency фиксировать версию, лицензию, источник, известные уязвимости и SBOM. Сборка должна быть автоматизирована для Windows и Linux. Совместимость с российскими ОС и российскими CPU заявлять только после фактической сборки и аппаратного тестирования. Само использование Rust не означает автоматического статуса российского ПО.

## 9. Текущий статус

- Целевое решение по разделению Python Core / Rust Communication Engine: **утверждено**.
- Текущие Python BACnet/Modbus адаптеры: **существуют, read-only, частичная протокольная готовность**.
- Modbus grouped reads: **реализованы в Python**.
- Общий adaptive Polling Manager: **не завершён**.
- Межъязыковой SDK/IPC contract: **не реализован**.
- Rust Modbus TCP FC01/FC02/FC03/FC04 read-only transport pilot: **реализованы как отдельный Rust crate; FC03 используется сравнительным benchmark CLI; не подключён к production Driver Manager / Point Runtime**.
- Rust BACnet worker: **не реализован**; доступен только Python ReadProperty baseline.
- Python/Rust Modbus synthetic 10k benchmark и Python BACnet 10k baseline: **запускаются в Windows/Linux CI**; результаты не являются аппаратной приёмкой.
- Production Driver SDK v1, versioned IPC, worker supervisor, persistent multi-device runtime, adaptive polling/backoff и Load & Reliability Lab: **требуют реализации**.
- Rust FC01/FC02/FC04 и BACnet: **не реализованы**; FC03 — единственная Rust функция чтения на текущем пилоте.
- Rust pilot CI unit tests + benchmark jobs: **прошли на Windows и Ubuntu в run 45949467168**; полная Python CI матрица на том же HEAD имела один Windows ACL test failure, исправление DEV211 ожидает нового CI.
- Physical controller acceptance: **не подтверждён этой архитектурной записью**.

Следующий инженерный шаг: разработать Driver SDK v1 / IPC contract и repeatable Python baseline; затем Rust Modbus pilot. Не начинать массовый перенос драйверов до получения этих измерений.


## 10. Фактический объём Rust pilot на текущем HEAD

На ветке `architecture/rust-communication-engine` находится отдельный crate `rust/avic-communication-engine` (без сторонних crate-зависимостей) и CLI `avic-modbus-bench`. Crate реализует Modbus TCP FC03: MBAP framing, transaction/unit/protocol/length validation, timeouts, exception handling на уровне протокола и decode uint16 register values. CLI выполняет bounded по числу worker threads синтетическое сравнение с Python.

Это ещё не многопротокольный Communication Engine. Клиент открывает TCP connection на каждую транзакцию; нет постоянных сессий, async runtime, device actor lifecycle, reconnect/backoff, rate limiter, fair scheduler, bounded event queues, IPC и Core binding. Benchmark буферизует uint16 values локально и не публикует их в AVIC Point Runtime. Поэтому его throughput нельзя переносить на production capacity.

### Следующий обязательный план
1. Довести FC03 protocol tests (normal response, exception response, wrong TID/unit/protocol, truncated/oversized payload, timeout, peer disconnect).
2. Реализовать FC01/FC02/FC04 read-only с parity и группировкой.
3. Зафиксировать Driver SDK v1 wire schema и local IPC handshake/version/epoch/sequence/TTL.
4. Реализовать Rust worker process + Python supervisor, station/shard isolation, bounded queues/backpressure и restart semantics.
5. Интегрировать samples только через Core Point Runtime validation; Rust worker не имеет DB/RBAC/licensing authority.
6. Провести 10k/50k/100k point load/fault/soak suites, затем Modbus hardware acceptance.
7. Только после этого начать BACnet Rust: protocol stack review, segmentation, RPM, COV, BBMD/Foreign Device и multi-vendor hardware tests.


### DEV212 — Modbus FC03 exception frame handling

During review of the Rust FC03 transport pilot, the response parser was found to compare every response MBAP length with the normal register payload length before checking the Modbus exception function. A valid exception response (function 0x83, two-byte PDU, MBAP length 3) was therefore rejected as a generic length error. The parser now reads the bounded MBAP body first, validates the exception frame length, and returns the typed Modbus exception code. Added local TCP protocol tests for a valid FC03 response, a valid exception response, and a mismatched transaction ID. CI confirmation is pending; this does not change the production readiness boundary.


### DEV213 — Modbus read-only function parity

Rust transport дополнен чтением Coils (FC01), Discrete Inputs (FC02), Holding Registers (FC03) и Input Registers (FC04). Для битовых функций реализовано LSB-first unpacking согласно Modbus PDU; для регистров — big-endian uint16 transport decode. Проверяются пределы 2000 bits / 125 registers, адресное переполнение, response function, byte count и размер PDU. Добавлены loopback TCP tests на все четыре функции, FC03 exception response и transaction ID mismatch. Это transport-level parity по базовым read functions, не parity всего Python adapter: grouped binding planner, typed decoding/scaling, retries, rate scheduling, IPC и Point Runtime integration ещё не подключены. Cargo CI confirmation pending.
