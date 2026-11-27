# AVIC Rust Communication Engine — архитектура и пилот Modbus TCP

Дата: 27.11.2026  
Статус: DEV208 — первый Rust pilot, требуется полный CI и аппаратные испытания.

## 1. Разделение ответственности

- **AVIC Core (Python)** остаётся владельцем инженерной модели, Station/Device/Point, RBAC, лицензирования, Audit, конфигурации, Point Runtime, Historian, FBD и UI/API.
- **Rust Communication Engine** — отдельный процесс для сетевого I/O и протокольного разбора. Он не получает доступ к SQLite, лицензиям, SecretStore или внутренним объектам Core.
- Обмен между Core и движком выполняется через JSON Lines по stdin/stdout. Один запрос — одна строка JSON, один ответ — одна строка JSON с обязательным request_id.
- Стандартный stderr движка не смешивается с IPC stdout. Core запускает бинарный файл без shell и контролирует процесс.
- При тайм-ауте/аварии IPC процесс завершается и ошибка передаётся Driver Manager. Автоматического скрытого перехода на Python нет: резервный backend выбирается явно в конфигурации драйвера.

## 2. DEV208 — Modbus TCP pilot

Добавлен crate `rust/communication-engine` и executable `avic-communication-engine`.

Поддержанный IPC контракт:
- `health` — версия/идентификатор движка и список возможностей;
- `modbus_read` — Modbus TCP FC 1, 2, 3, 4;
- `shutdown` — контролируемое завершение процесса.

Транспортный контракт:
- literal IP address; TCP connect/read/write timeout 100–10 000 ms;
- проверка MBAP transaction ID, protocol ID, length и unit ID;
- проверка функции, byte count и длины payload;
- обработка Modbus exception response;
- чтение coils/discrete inputs и holding/input registers;
- никаких FC 5/6/15/16/22/23 и иных write/control запросов;
- Python Modbus adapter по-прежнему отвечает за типизацию регистров, scale/offset, station-owned DriverInstance и публикацию в Point Runtime.

## 3. Включение

Сначала соберите бинарный файл в каталоге `rust/communication-engine`:

```powershell
cargo test
cargo build --release
```

Windows executable:
`target\release\avic-communication-engine.exe`

Linux executable:
`target/release/avic-communication-engine`

В конфигурации DriverInstance Modbus TCP:
- `engine_backend = "rust"`
- `engine_binary = абсолютный путь к собранному executable`

Для контрольного Python backend:
- `engine_backend = "python"` или поле можно не указывать.

Не заданный/нерабочий Rust executable приводит к явной ошибке старта. Python fallback автоматически не включается, чтобы ошибка Rust-движка не маскировалась.

## 4. Безопасность

- Пилот строго READ-ONLY. В Rust engine реализованы только функции чтения Modbus 1–4.
- Движок не может напрямую публиковать значения в Core: он возвращает сырые регистры/биты; Python adapter декодирует и выполняет проверку владельца точки перед записью в Point Runtime.
- Не передаются пароли и секреты. Host/port/unit/address/count являются параметрами запроса.
- Процесс изолирован от Core-хранилища и не получает привилегий на управление оборудованием.
- Существующий Python backend остаётся доступен как явный резервный режим.

## 5. Проверки и границы готовности

CI включает Rust tests/build на Ubuntu и Windows. Python full matrix продолжает тестировать Core и адаптеры.

Пока не подтверждены:
- полное сравнение производительности Python/Rust на одинаковых 1k/10k точках;
- длительный soak test, reconnect storm, packet loss, malformed peer и process crash recovery на реальной сети;
- аппаратная проверка с Trend Modbus TCP контроллером;
- BACnet/IP Rust engine. BACnet остаётся Python READ-ONLY до отдельного пилота и parity tests.

Нельзя считать Rust Modbus production-ready только по факту компиляции или unit tests. Нужны Linux/Windows CI, functional parity, load/fault tests и реальный контроллер.

## 6. Общая стратегия Rust engines (решения из обсуждения 27.11.2026)

Rust не внедряется везде автоматически. Каждый модуль переводится только если общий функциональный контракт совпадает с Python и измерения показывают выигрыш на целевых Windows/Linux нагрузках.

Порядок работ:
1. Стабильный Driver SDK v1 и IPC контракт — единая модель capabilities, start/stop, polling, batch, quality, timestamps, diagnostics, recovery, cancellation, versioning и station ownership.
2. Load & Reliability Lab — повторяемый стенд, Python baseline, идентичные сценарии для обоих backend.
3. Rust Modbus TCP pilot (текущий DEV208) — доказать транспортную совместимость, lifecycle и устойчивость; не менять default backend.
4. Rust BACnet/IP — после Driver SDK: ReadPropertyMultiple, COV, segmentation, BBMD, device/vendor interoperability и controlled fallback к Python только как явно выбранный backend.
5. IPC/Point Runtime boundary — Rust может отправлять нормализованные samples в Core через версионированный контракт; Point Runtime сохраняет владение качеством, временем, station isolation и публикацией до отдельного решения по переносу.
6. Кандидаты следующей очереди: Point Runtime, FBD Engine, Historian, Alarm Engine; Scheduler оценивается отдельно. UI/API не переносить в Rust без отдельного доказанного профиля нагрузки. PyO3/maturin рассматривать для чистых вычислительных функций, а сетевые драйверы/движки держать в отдельных процессах для fault isolation.

## 7. Исторические предварительные benchmark данные

В предыдущем ноутбучном обсуждении были зафиксированы следующие 10k Modbus TCP результаты (точки/с):
- Ubuntu: Python 45 288; Rust 47 679 (Rust примерно +5.3%).
- Windows: Python 72 167; Rust 62 554 (Rust примерно -13.3%).

Эти результаты не подтверждают универсального преимущества Rust: на Ubuntu выигрыш мал, на Windows Rust в этом замере медленнее. Считать их предварительными историческими данными до повторного запуска единым benchmark harness на текущем HEAD.

Предварительный BACnet Python замер на 10k запросов: 1.67/4.54 секунды, ошибок 0, но отмечен длинный p99 tail. В текущей сводке нет достаточной информации для привязки каждого времени к конкретной ОС — не приписывать ОС без исходного журнала.

## 8. Обязательные performance/reliability gates

- Базовый масштаб испытаний: 10 000 активных точек; расширенный: 50 000+ (следующая ступень 100 000 после прохождения 50k).
- Длительный soak: 72 часа.
- Сравнивать на одинаковом оборудовании и одинаковых точках: throughput, CPU, RSS/RAM, p50/p95/p99 latency, queue depth, missed/late samples, reconnect duration, error rate и recovery behavior.
- Отказные сценарии: отключение сети/контроллера, packet loss, malformed/truncated responses, медленный контроллер, reconnect storm, restart/crash engine process, timeout/cancel во время I/O, много станций одновременно.
- Критерии: нет stale value rollback, duplicate polling, cross-station leakage, unbounded queue/memory growth, recovery storm или блокировки остальных устройств из-за одного медленного контроллера.
- Rust backend не становится default только по результату throughput. Требуется functional parity, стабильность, Windows/Linux parity и измеримое улучшение end-to-end.
