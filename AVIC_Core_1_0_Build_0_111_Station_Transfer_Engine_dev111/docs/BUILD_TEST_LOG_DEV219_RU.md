# Журнал DEV219 — Rust backend подключён к Driver Manager и Point Runtime

Дата: 27.11.2026

## Реализовано
- Добавлен `RustDriverPointAdapter`: общая точка входа Rust Modbus/BACnet/KNX в AVIC Point Runtime.
- Driver Manager принимает `engine: "python" | "rust"` в конфигурации экземпляра. По умолчанию остаётся Python.
- Rust worker executable регистрируется администратором по абсолютному существующему пути через `CoreApplication(..., rust_worker_command=...)` или `core.driver_manager.register_rust_worker_command(...)`.
- CLI получил `--rust-worker`.
- Для Rust backend создаётся отдельный worker на каждый DriverInstance; контекст установки/проекта/станции/драйвера передаётся из Core repository, не из произвольных IPC данных.
- PollingSession управляет тем же жизненным циклом, что и Python adapters; остановка DriverInstance вызывает stop/shutdown worker.
- Каждый sample проходит через Point Runtime с source_driver_id текущего DriverInstance. Ошибки связи переводят качество в BAD_COMMUNICATION; неподдерживаемые BACnet bindings — BAD_CONFIGURATION.
- Modbus Rust backend использует FC01/02/03/04 и существующий AVIC decode_registers; значения и scaling публикуются только после проверки. Modbus configuration validates address/function/count/timeout before read.
- BACnet Rust backend группирует object-list/property reads по устройству за один poll cycle, сопоставляет object type/instance, ограничен Present_Value (property 85) без array index. BACnet socket привязан к явно настроенному station local address/UDP port.
- KNX Rust backend делает GroupValue_Read по каждой configured group address и DPT через KNXnet/IP tunnelling; адрес и DPT берутся из AVIC point bindings. Gateway/local endpoints and timeout are validated; IPv4/IPv6 socket formatting is supported.
- Worker запрещает write/write_point, проверяет один protocol на worker, секреты в IPC config запрещены; процесс запускается с минимальным очищенным environment, stdout/stderr разведены, pipe framing поддерживает partial reads/writes.
- Worker сообщает build version и счётчики sequence gaps; Python supervisor проверяет handshake, correlation ID, scope, generation и sequence.
- Добавлены тесты Rust adapter mapping, BACnet Status_Flags quality propagation, DriverManager backend selection и worker generation.

## Как включить Rust backend

Сборка (Windows):
`cargo build --release --manifest-path rust/avic-communication-engine/Cargo.toml --bin avic-driver-worker`

Запуск Core:
`python -m avic_core --data-dir C:\\AVIC\\data --rust-worker C:\\path\\to\\target\\release\\avic-driver-worker.exe health`

В конфигурации DriverInstance задаётся `"engine": "rust"`. Без зарегистрированного worker path запуск отклоняется fail-closed. Существующие экземпляры без поля engine продолжают использовать Python.

## Ограничения — не production acceptance
- В этом рабочем окружении Cargo отсутствует; Rust compile/test не запускались.
- Первый CI запуск обнаружил две Rust compile errors (BACnet PropertyValue import/type и KNX DPT display lifetime); они исправлены. Новый CI для исправленного head ещё ожидает запуска/завершения.
- Worker пока создаёт протокольное соединение на каждый read; постоянные сессии, batch polling для Modbus, COV subscriptions и reconnect orchestration ещё не готовы.
- BACnet использует BACnet-RS 0.3.2, upstream прямо указывает статус not production-ready; segmentation/reassembly, alarms/events, trend logs, schedules/calendars, BACnet/SC не реализованы upstream.
- BACnet worker возвращает общие объектные свойства и поддерживает только Present_Value (85), без array index. Нужны проверки типов object list, RPM и vendor-specific property behavior.
- KNX использует tunnelling и GroupValue_Read; не реализованы Routing, ETS import, passive group monitor/subscription lifecycle и hardware reconnect acceptance.
- Modbus Rust client пока открывает TCP connection per read и не привязывает исходный сокет к конкретному station interface.
- Worker executable сейчас проверяется по абсолютному пути/наличию/exec bit, но подпись пакета, SBOM и policy-based binary trust ещё не подключены.
- Полевые записи остаются отключёнными. Не использовать Rust backend для управления оборудованием.

## Проверки
- Добавлены tests: fake worker lifecycle, Modbus decoding, BACnet object mapping/batch-per-device, KNX group address/DPT mapping, unsupported BACnet property fail-closed, Core/DriverManager backend selection.
- Эти тесты добавлены, но не объявляются пройденными до CI.

## DEV220 — Исправление optimistic concurrency при запуске драйвера

### Причина отказа CI (27.11.2026)
- Rust unit tests и Rust release/build jobs прошли на Ubuntu и Windows.
- Все шесть Python matrix jobs выявили одну общую регрессию в Driver Manager: после сохранения состояния STARTING локальная переменная версии уже соответствовала новой версии записи, но финальное сохранение RUNNING ошибочно ожидало ещё одну дополнительную версию (expected_version=version+1).
- SQLiteRepository корректно отклонял запись как ConcurrencyConflict; API запускa возвращал 409 вместо 200. Это не ошибка SQLite и не проблема конкретной ОС.

### Исправление
- После перехода STARTING -> RUNNING финальное сохранение использует текущую версию, возвращённую логикой предыдущего перехода, без лишнего инкремента.
- Проверка оптимистической блокировки, защита от конкурентного изменения и fail-closed поведение не ослаблялись.
- Существующие тесты запуска/остановки драйверов и HTTP lifecycle должны подтвердить исправление на Linux и Windows.

### Статус
- Исправление внесено в commit 787494483b61a199cf7a71f7060dd16294343200.
- Полный CI для нового HEAD обязателен; до его завершения DEV220 не считается принятым.
- Rust драйверы остаются READ-ONLY пилотом; подключение физических контроллеров и нагрузочная приёмка 1k/10k ещё впереди.
