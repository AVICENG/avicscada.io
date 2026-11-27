# ADR-006 — Rust Communication Engine: границы, batching и эксплуатация

Статус: **PROPOSED — текущая Rust интеграция pilot/read-only**  
Дата: 27.11.2026  
Область: Rust protocol workers, Python Driver Manager, BACnet/IP, Modbus TCP, KNXnet/IP, Point Runtime и Edge.

## 1. Архитектурное решение

Rust становится высокопроизводительным Communication Engine для протокольного I/O, а не отдельной SCADA и не вторым владельцем инженерной модели.

- Python Core владеет проектом, Station, DriverInstance, Point Definition, лицензией, RBAC, Engineering Lifecycle, Point Runtime API, Alarm/History и HMI.
- Rust Worker владеет протокольными соединениями, transport state, encode/decode протокола, polling transactions, protocol diagnostics и raw typed read results.
- Между ними — versioned, bounded, typed IPC contract.
- Только Point Ingestion API принимает и публикует sample в Point State.
- Rust Worker не пишет в Object Repository, Historian, Alarm DB или Point State DB.
- Rust Worker не выполняет физические writes в текущем пилоте. Команда на запись в Rust worker явно возвращает WRITE_DISABLED; future write executor будет подчинён ADR-004.

## 2. Что уже есть в коде

Положительные элементы:
- Driver Manager может выбирать `engine=python|rust` для Modbus TCP, BACnet/IP и KNXnet/IP.
- Один Rust Worker создаётся на DriverInstance с installation/project/station/driver scope, worker UUID и generation.
- IPC использует `avic.driver.ipc`, version 1, 4-byte length-prefixed JSON, лимит frame 1 MiB, строгую envelope validation.
- Проверяются scope, correlation_id, generation и монотонный sequence; worker отклоняет старую generation/sequence.
- Worker config/request проверяется на secret-like keys.
- Rust worker process запускается без shell, с ограниченным environment и отдельными stdout/stderr readers.
- Rust worker поддерживает read-only Modbus FC01/02/03/04, BACnet/IP snapshot и KNXnet/IP read; write явно запрещён.
- Modbus TCP sessions кэшируются по endpoint/unit/timeout и переиспользуются внутри worker.
- Python RustDriverPointAdapter владеет bindings, scaling, quality mapping и публикацией в PointRuntime.

Ограничения текущего pilot:
- Rust ещё не является единственным/default engine; переключение задаётся per DriverInstance.
- Наличие binary path не равно supply-chain verification: сейчас проверяется абсолютный существующий файл и executable bit, но не подписанный manifest/hash provenance.
- Rust adapter выполняет Modbus read по каждому binding отдельно; end-to-end batch read для группы точек пока не является общим контрактом.
- Synthetic benchmark читает блок регистров через Rust client напрямую. Он не включает полный Python adapter → IPC → mapping → PointRuntime publish path.
- BACnet Rust adapter получает device snapshot по каждому уникальному устройству на poll; требуется измерить стоимость и перейти к эффективному ReadPropertyMultiple/COV или другому подтверждённому batch path.
- Фактическая нагрузка 10k points через AVIC Driver Manager не доказана.

## 3. IPC contract

Envelope должна содержать:
- contract + major/minor schema version;
- message_id, correlation_id, kind;
- installation/project/station/driver_instance scope;
- worker_id и generation;
- monotonic sequence;
- sent_at UTC;
- payload с типизированным request/result;
- optional capability/diagnostics fields.

Правила:
1. Максимальный frame size конфигурируется и ограничивается; большие payload разбиваются на страницы/chunks с явной последовательностью.
2. Unknown major version отклоняется; minor-compatible additions допускаются только по schema policy.
3. Секреты не передаются в worker config; только references к SecretStore, если протоколу потребуется доступ к credential через контролируемый broker.
4. Worker не принимает arbitrary filesystem paths, shell fragments или executable commands из payload.
5. Каждая команда ограничена timeout и cancellation policy.
6. Ответ проверяет все scope fields, worker identity, generation и correlation_id.
7. Sequence gap — диагностируемое событие; duplicate/out-of-order response — reject.
8. IPC stdout зарезервирован только для framed protocol; logs идут в stderr.
9. Crash/timeout/invalid frame переводит DriverInstance в explicit DEGRADED/ERROR; автоматический restart имеет backoff и generation increment.

## 4. Ownership граница

| Ответственность | Python Core/Adapter | Rust Worker |
|---|---|---|
| Project/Station/Device/Point Definition | Owner | Нет прямого доступа |
| DriverInstance lifecycle and configuration | Owner | Выполняет полученную команду |
| Protocol socket/session | Наблюдает diagnostics | Owner |
| Protocol encoding/decoding | Только compatibility/point mapping | Owner |
| Binding resolution и point_id | Owner | Получает конкретный request |
| Scaling/unit conversion policy | Канонический слой ingestion/adapter | Не меняет без контракта |
| Quality mapping | Канонический Quality mapper | Возвращает protocol flags/diagnostics |
| Point State publication | Только через Point Ingestion API | Запрещено |
| Historian/Alarm writes | Через события/consumer contracts | Запрещено |
| Physical command write | Только через ADR-004 gateway/executor | В pilot запрещено |

Нельзя создавать независимый Rust Point Registry, второй набор point_id или отдельную логику лицензирования.

## 5. Polling и batch strategy

Driver Manager группирует bindings по общим transport parameters:
- protocol;
- host/address + port;
- unit/device identity;
- function/property;
- timeout;
- compatible encoding/range.

### Modbus TCP
- Смежные/перекрывающиеся register ranges одного unit/function объединяются в read block.
- FC01/FC02 используют протокольный лимит 2000 bits; FC03/FC04 — 125 registers.
- Разрыв адресов не заполняется произвольно, если это может читать недоступные/опасные регистры; gap policy задаётся явно.
- Один response раскладывается по binding map; декодирование data_type/byte_order/word_order проверяется тестами.
- Sessions reuse, reconnect, socket timeout и broken-session recovery входят в acceptance.

### BACnet/IP
- Discovery/inventory не смешивается с регулярным polling.
- Для набора точек одного устройства используется ReadPropertyMultiple, где устройство поддерживает его; fallback ReadProperty ограничен и диагностируется.
- COV может применяться после подтверждения подписки, lifetime, renew/recover и device support.
- Status_Flags сохраняются отдельно; canonical Quality mapping выполняется единообразно.
- Не выполнять полный object enumeration на каждом обычном polling cycle без измеренного обоснования.

### KNXnet/IP
- Группировка по tunneling session/gateway и управляемая частота group reads.
- Подписки/group monitor рассматриваются отдельно от polling.
- DPT conversion и качество/timeout должны иметь единый contract.

## 6. Performance measurement

Benchmark tiers:
1. **Protocol microbenchmark:** Rust protocol client ↔ simulator/controller.
2. **IPC benchmark:** framed requests/responses, serialization, queueing and worker concurrency.
3. **Adapter benchmark:** binding grouping, mapping, conversion, quality.
4. **Point Runtime integration benchmark:** publish + subscriber fanout + outbox.
5. **Station benchmark:** FBD, Alarm, Historian, HMI reads, multi-driver load.
6. **Edge acceptance:** target hardware, Linux, thermal, power-loss, long soak.

Каждый отчёт фиксирует:
- devices, points/device, bindings, functions/properties, polling rates;
- contiguous vs sparse address distribution;
- concurrency and session reuse;
- success/error/timeout/reconnect counts;
- updates/sec и requests/sec;
- p50/p95/p99 latency;
- CPU, RAM, thread/process count, sockets, disk writes;
- backlog, queue saturation and drop count;
- exact commit, Rust/Python versions, OS and simulator/controller model.

Синтетический loopback benchmark не является подтверждением 10k production points.

## 7. Worker lifecycle and security

- Worker executable имеет manifest: version, build hash, target OS/architecture, supported protocols/capabilities, minimum Core IPC version.
- Release artifacts подписываются; Core проверяет signature/hash перед запуском.
- Update выполняется side-by-side, с health check и rollback; активный worker binary не заменяется на месте.
- Каждый worker изолирован по DriverInstance и station scope.
- OS permissions ограничивают файлы/сеть; process получает только необходимые capabilities.
- Restart ограничен exponential backoff и circuit breaker.
- После restart создаётся новая generation; старые сообщения и ответы отвергаются.
- Worker не может сам менять network configuration, запускать discovery вне разрешённого профиля или выполнять произвольные команды.
- Diagnostics не должны раскрывать секреты, пароли, токены или private keys.

## 8. Переход Python → Rust

- Python engine остаётся reference implementation для parity tests.
- Для каждого protocol/function/data type создаётся golden test vector.
- Rust включается per DriverInstance в пилоте, затем по protocol/capability profile; глобальный switch запрещён до acceptance.
- Два engine не опрашивают один Device одновременно без явного test plan.
- При откате на Python generation increment fences old worker.
- После parity подтверждения Rust может стать default для конкретного протокола/профиля; Python fallback остаётся диагностируемым и управляемым, не скрытым.
- Реальные write capabilities не включаются вместе с read performance release.

## 9. Acceptance tests

### IPC/process
- partial header/body, EOF, oversized frame, invalid JSON, unknown fields;
- wrong contract/version/scope/worker_id/correlation;
- duplicate/out-of-order sequence and stale generation;
- worker crash, timeout, stdout close, stderr flood, queue full;
- restart/backoff/cleanup without orphan process;
- executable hash/signature mismatch rejects startup;
- no secret values in IPC, stderr or diagnostics.

### Protocol parity
- Python/Rust same input → same raw values, decode, quality and timestamps;
- Modbus FC01/02/03/04 limits, exceptions, fragmented TCP frames, persistent session, reconnect;
- BACnet RPM, fallback, status flags, unsupported property/object, device restart;
- KNX DPT mapping, timeout, tunnel reconnect and duplicate group response.

### End-to-end
- one DriverInstance → one isolated worker;
- 1k/5k/10k point profiles with real binding cardinality;
- grouped Modbus reads reduce transaction count while preserving point values;
- BACnet object inventory is not repeated every polling cycle;
- Point Runtime publishes only validated results;
- subscriber failure does not kill worker or lose other points;
- multi-station concurrency and isolation;
- Windows/Linux parity and long-running soak.

## 10. Проверка по трём системам

- **Niagara:** driver instances, device networks and point bindings remain visible in one engineering object model; protocol implementation is replaceable behind driver contracts.
- **Trend IQVision:** engineer can configure a device/point once and get predictable poll diagnostics; batching remains internal and must not complicate bindings.
- **Siemens Desigo CC:** protocol breadth, northbound/southbound integration and distributed deployment require strict adapter contracts and capability reporting.
- **AVIC:** Rust accelerates transport without splitting the SCADA brain, data ownership, security or project format between two runtimes.

## 11. Критерий принятия

ADR принимается после:
1. versioned IPC compatibility policy;
2. signed worker artifact verification;
3. protocol batching in actual Driver Manager adapters;
4. parity tests and full end-to-end benchmark;
5. restart/fencing/security tests;
6. Windows/Linux and Edge hardware acceptance.

До этого Rust Communication Engine — активный pilot, а не подтверждённый production engine.
