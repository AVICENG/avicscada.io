# AVIC Driver SDK v1 — межъязыковой контракт и IPC

Статус: **архитектурная спецификация DEV215; не является заявлением о готовой IPC-реализации**.
Дата: 27.11.2026.

## 1. Назначение

AVIC использует один Driver SDK для адаптеров Python и Rust. Язык реализации не меняет место драйвера в инженерном дереве, его права, лицензирование, аудит, качество данных или жизненный цикл.

Путь данных:

`Project → Station → Driver Network → Device → Points`

Путь исполнения:

`Driver adapter/worker → versioned Driver contract → Core validation → Point Runtime → FBD / Alarms / Historian / HMI`

Python Core остаётся Supervisor и владельцем объектной модели. Rust Communication Engine отвечает за сетевой transport, protocol codec, безопасное планирование запросов, bounded queues и восстановление соединений. Rust не пишет напрямую в Core DB и не публикует значения в обход Point Runtime.

## 2. Два исполнения, один контракт

### Python adapter (in-process)

Python-драйвер реализует существующий `Driver` Protocol и получает `DriverContext`. Он вызывает Core Point Runtime через внутренний API. Это основной путь для текущих Python-драйверов.

### Rust worker (out-of-process)

Rust-драйвер реализует тот же набор операций через локальный IPC. Supervisor создаёт и контролирует worker process. В первой production-реализации целевой IPC:
- Windows: Named Pipes с ACL текущей службы/пользователя.
- Linux: Unix Domain Socket с файловыми правами и проверкой peer credentials.
- Loopback TCP допускается только для тестового стенда и никогда не выбирается как незащищённый production default.

PyO3 может применяться для небольших вычислительных библиотек, но не является обязательным транспортом и не заменяет изоляцию worker-процесса.

## 3. Идентичность и версия

Каждый worker привязан к неизменяемому набору:
- `installation_id`
- `project_id`
- `station_id`
- `driver_instance_id`
- `worker_id`
- `generation` — монотонная эпоха запуска данного экземпляра
- `protocol_version` — версия wire contract
- `manifest` — driver_id, driver_version, Core API compatibility, protocol и capabilities

Worker не может сам назначить себе другую станцию или DriverInstance. Supervisor связывает IPC endpoint с ожидаемыми идентификаторами и отвергает несовпадения.

## 4. Формат сообщения

На логическом уровне каждое сообщение — UTF-8 JSON envelope. Для stream transport применяется ограниченный length-prefix framing: 4-byte unsigned big-endian length, затем ровно столько байт JSON. Максимальный размер одного сообщения по умолчанию 1 MiB; отдельные bulk/import операции должны использовать явно согласованный streaming контракт, а не увеличивать этот лимит без контроля.

Обязательные поля envelope:
- `contract`: строка `avic.driver.ipc`
- `version`: целое число major wire version
- `message_id`: UUID
- `kind`: тип сообщения
- `installation_id`, `project_id`, `station_id`, `driver_instance_id`
- `worker_id`, `generation`
- `sequence`: монотонный номер сообщения в пределах generation
- `sent_at`: UTC RFC 3339 timestamp
- `correlation_id`: UUID исходного запроса для ответа; `null` для unsolicited asynchronous event с `kind="event"`
- `payload`: типизированное содержимое

Неизвестная major-версия, обязательное неизвестное поле, некорректный UUID, превышение размера, неверная последовательность или чужая идентичность приводят к отклонению сообщения и диагностике. Совместимые дополнительные поля minor-версии игнорируются только если они не влияют на безопасность и смысл данных.

## 5. Handshake и lifecycle

Обязательная последовательность:
1. Supervisor запускает worker с защищённым endpoint и минимальным bootstrap context.
2. Worker отправляет `hello` с manifest, поддерживаемой версией контракта и capabilities.
3. Supervisor проверяет подпись/доверие пакета, совместимость, лицензируемую функцию, разрешённые capabilities и соответствие station/instance/generation.
4. Supervisor отправляет `initialize` и безопасную конфигурацию без секретов.
5. Worker подтверждает `initialized`; затем Supervisor может отправить `configure` и `start`.
6. Worker отправляет `status`, `diagnostics`, `sample`, `device_discovered`, `point_discovered` или `fault` события.
7. При остановке Supervisor отправляет `stop`, ждёт ограниченный grace period, затем завершает процесс согласно политике. Worker должен закрыть сокеты и прекратить новые операции.
8. При рестарте увеличивается generation. События старой generation всегда отклоняются.

Минимальные команды: `initialize`, `configure`, `start`, `stop`, `shutdown`, `discover`, `read`, `get_status`, `get_diagnostics`, `cancel`. `write` не входит в v1 operational profile и не должен приниматься worker по умолчанию.

## 6. Событие измерения

Sample несёт:
- `device_id` и `point_external_id` — идентификаторы в driver namespace;
- `value` — типизированное значение без преобразования в строку;
- `data_type` и, если применимо, `engineering_unit`;
- `quality` — только известное enum-значение;
- `source_timestamp` — время измерения, если предоставлено устройством;
- `received_at` — время получения worker;
- `event_id` и `sequence` — дедупликация и порядок;
- `diagnostic` — необязательный код/контекст без секретов.

Worker не вправе самостоятельно объявлять данные GOOD только потому, что пакет успешно получен. Quality mapping определяется протокольным адаптером, а Core проверяет допустимость и свежесть sample. Если устройство не предоставило timestamp, это явно отражается в событии; время получения не подменяет время измерения.

Core самостоятельно проверяет:
- существование DriverInstance и его активную generation;
- принадлежность Device и Point ожидаемой станции и драйверу;
- соответствие внешнего binding внутренней точке;
- тип значения, quality и timezone-aware timestamp;
- дедупликацию и out-of-order policy;
- лицензирование и доступность соответствующей функции.

После этого Core вызывает общий Point Runtime publish path. Worker не имеет метода прямой записи в Historian, Alarm Engine или FBD.

## 7. Discovery и импорт

Discovery возвращает кандидатов устройств и точек, а не создаёт объекты автоматически. Каждое поле идентификации содержит значение и происхождение:
- protocol identifier;
- manufacturer/model/vendor id;
- MAC OUI (если применимо);
- evidence source;
- confidence/status: confirmed, inferred или unknown.

Неизвестный производитель или модель остаются unknown. Нельзя выводить производителя из имени устройства или придумывать модель по адресу.

Импорт выполняется отдельной Core операцией с preview, проверкой конфликтов, правами, лицензией и audit event. Worker не создаёт постоянные AVIC объекты напрямую.

## 8. Backpressure и ограничения

Каждая очередь имеет явную верхнюю границу. Для заменяемых текущих значений допускается coalescing по point key, если это включено политикой потока; для событий тревог, диагностики, discovery и lifecycle молчаливое удаление запрещено. Любое отбрасывание/coalescing учитывается метриками и диагностикой.

Обязательные лимиты конфигурации:
- max message bytes;
- max in-flight requests per worker/device;
- max queue depth;
- per-device request rate;
- request timeout и total operation deadline;
- max retry count и bounded exponential backoff с jitter;
- worker memory/CPU budget и restart policy.

Пропущенные polling ticks не должны создавать catch-up burst. Один неисправный device не блокирует очередь соседних устройств. Адаптивный polling не превышает безопасные лимиты, заданные профилем устройства.

## 9. Секреты и права

Обычная конфигурация DriverInstance не хранит пароли, токены, private keys или connection strings с секретами. Worker не получает доступ к SecretStore или файлам лицензии. Если протокол требует credential, отдельный credential broker выдаёт минимально scoped, краткоживущий секрет только конкретному worker/instance; секрет не попадает в логи, crash dump по возможности исключается политикой ОС.

RBAC, лицензия, staged publish, audit и разрешения на управление принадлежат Core. Наличие capability в manifest не предоставляет право: capability должна быть разрешена каталогом, лицензией и политикой Core. В SDK v1 полевые записи остаются выключенными.

## 10. Отказы и восстановление

- IPC disconnect переводит runtime в DEGRADED/ERROR согласно политике, а не оставляет точки бесконечно GOOD.
- Worker restart увеличивает generation; сообщения предыдущего процесса не принимаются.
- Повторный event с тем же event_id не публикуется повторно.
- Sequence gap фиксируется в diagnostics; нельзя молча утверждать непрерывность данных.
- После reconnect worker выполняет handshake и сверку конфигурации, затем повторную подписку/опрос.
- Core сохраняет последнее значение для отображения, но помечает качество при потере актуальности.
- Rollback к Python adapter возможен только через явную конфигурацию/feature flag и staged publish; нельзя одновременно публиковать два источника в одну точку без заданной политики ownership.

## 11. План реализации

1. **DEV215 (этот документ):** согласовать wire contract, границы доверия и failure semantics.
2. DEV216: Python reference codec — envelope validation, framing, size limits, version checks, generation/sequence checks и contract tests.
3. DEV217: Rust worker host и handshake/status/diagnostics без полевого I/O.
4. DEV218: подключить Rust Modbus read-only через IPC в отдельном feature-gated режиме; использовать общий Core Point Runtime.
5. DEV219: fault injection — worker crash, IPC disconnect, stale generation, duplicate/out-of-order events, queue saturation и recovery.
6. DEV220: Windows/Linux CI, packaging, signed artifacts/SBOM и load/fault acceptance. До выполнения этапов Rust не является production driver runtime.

## 12. Критерии приёмки

- Python и Rust workers проходят одинаковые contract tests.
- Worker не может изменить station/instance scope.
- Невалидные, повторные и устаревшие samples не меняют Point Runtime.
- Очереди и сообщения имеют жёсткие лимиты.
- Worker crash и IPC loss не приводят к бесконечно GOOD quality или скрытой потере данных.
- Нет прямого доступа worker к Core DB, лицензии, RBAC, Audit DB и SecretStore.
- Windows и Linux проходят CI.
- Python fallback сохраняется; миграция обратима.
- Нагрузочные результаты включают CPU, RSS, network bytes, throughput, p50/p95/p99, queue depth, dropped/coalesced events и recovery time.

## 13. Текущий статус

Статус на DEV244: versioned IPC wire implementation присутствует в Rust (`rust/avic-communication-engine/src/ipc.rs`) и Python (`avic_core/drivers/ipc.py`); Rust worker binary и Python `RustDriverWorker` реализуют изолированный процесс, handshake, конфигурацию, lifecycle, scope/generation fencing и bounded framing. `RustDriverPointAdapter` передаёт результаты read-only адаптеров через общий Core Point Runtime. Это интеграционный пилот, а не production acceptance: Rust-native Point Runtime/FBD Runtime не заявляются готовыми, нет полной аппаратной приёмки всех протоколов, подписанных worker-пакетов и завершённой промышленной сертификации. Реализованные пункты подтверждаются только кодом, тестами и CI evidence конкретного HEAD.


## DEV244 — Строгая проверка временной метки IPC

Проверка `sent_at` в Rust IPC теперь использует полноценный RFC3339 parser из Chrono, а не только проверку расположения символов и цифр.

- Требуется каноническое UTC-представление с суффиксом `Z`.
- Проверяются календарная дата, часы, минуты, секунды и корректность всей временной метки.
- Значения с часовым смещением, включая `+00:00`, не принимаются вместо канонического `Z`.
- Допускаются корректные дробные секунды.
- Добавлены регрессионные тесты для невозможных дат и значений времени.

Это защищает IPC-контракт от синтаксически похожих, но невозможных временных меток. Результат CI для DEV244 фиксируется отдельно после завершения workflow.


## DEV261 — asynchronous event kinds and consumer API

Документированные unsolicited event kinds: `event`, `sample`, `device_discovered`, `point_discovered`, `fault`, `diagnostics`, `status`. Для unsolicited events `correlation_id=null`; correlated response kind `status` остаётся в response path.

Supervisor предоставляет `drain_events(max_items)` и `next_event(timeout_seconds)` с ограниченным timeout 0..30 секунд. Очередь bounded (256). Drop-newest допускается только для явно заменяемых sample/telemetry; критические discovery/fault/lifecycle events при переполнении приводят к fail-closed.

Эта очередь не является Point Runtime интеграцией: consumer обязан валидировать schema, binding, identity/generation, timestamp и quality, а затем передавать значения через общий Point Runtime publish path.
