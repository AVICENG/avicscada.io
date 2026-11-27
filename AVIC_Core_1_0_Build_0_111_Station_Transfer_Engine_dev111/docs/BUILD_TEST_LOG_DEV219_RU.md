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
- Modbus Rust backend использует FC01/02/03/04 и существующий AVIC decode_registers; значения и scaling публикуются только после проверки.
- BACnet Rust backend группирует object-list/property reads по устройству за один poll cycle, сопоставляет object type/instance, ограничен Present_Value (property 85) без array index. BACnet socket привязан к явно настроенному station local address/UDP port.
- KNX Rust backend делает GroupValue_Read по каждой configured group address и DPT через KNXnet/IP tunnelling; адрес и DPT берутся из AVIC point bindings.
- Worker запрещает write/write_point, проверяет один protocol на worker, секреты в IPC config запрещены.
- Добавлены тесты Rust adapter mapping и DriverManager backend selection.

## Как включить Rust backend

Сборка (Windows):
`cargo build --release --manifest-path rust/avic-communication-engine/Cargo.toml --bin avic-driver-worker`

Запуск Core:
`python -m avic_core --data-dir C:\\AVIC\\data --rust-worker C:\\path\\to\\target\\release\\avic-driver-worker.exe health`

В конфигурации DriverInstance задаётся `"engine": "rust"`. Без зарегистрированного worker path запуск отклоняется fail-closed. Существующие экземпляры без поля engine продолжают использовать Python.

## Ограничения — не production acceptance
- В этом рабочем окружении Cargo отсутствует; Rust compile/test не запускались.
- CI для текущих коммитов пока не получен.
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
