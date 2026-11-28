# AVIC Core — журнал сборки DEV270

Дата: 28.11.2026
Ветка: `drivers/modbus-rtu-c-worker-dev249`
База: `b9fd36cea8daac158343fbb7ee660144142008af`

## Цель

Усилить отказоустойчивость Rust Worker/Supervisor: исключить оставшийся живым дочерний процесс после закрытия IPC stdout и увеличить проверку state machine Rust Worker.

## Изменения

1. `avic_core/drivers/rust_worker.py`
   - EOF при живом процессе теперь фиксируется как отказ IPC.
   - Supervisor завершает дочерний процесс; при необходимости использует принудительное завершение.
   - Гонка между `poll()` и `terminate()` не должна маскировать исходную ошибку.
2. `tests/test_rust_driver_worker_supervisor_dev218.py`
   - Добавлен fault-injection тест: Worker закрывает stdout и остаётся жить; ожидается завершение процесса и сброс started.
3. `rust/avic-communication-engine/src/bin/avic_driver_worker.rs`
   - Добавлены unit tests для initialize, scope fencing, configure/start/stop/read lifecycle, nested secret rejection, unsupported protocol, sequence gap/replay и reconfiguration.
4. `rust/avic-communication-engine/src/ipc.rs`
   - Добавлены negative tests для truncated header/body и oversized payload на запись.
5. Добавлена архитектурная документация `docs/architecture/RUST_COMMUNICATION_ENGINE_RELIABILITY_RU.md`.

## Базовая регрессия до DEV270

CI run #967 / `46154462621` завершился успешно:
- Linux Python 3.11/3.12/3.13: по 31 552 passed, 15 skipped.
- Windows Python 3.11/3.12/3.13: по 31 549 passed, 18 skipped.
- Rust Communication Engine: Ubuntu и Windows success.
- BACnet Stack POC, Modbus C Worker, MQTT C Worker и OPC UA native probe: jobs success.

## Проверки DEV270 — выявленная проблема

CI run #968 / `46155780523`: Rust Ubuntu/Windows и нативные C jobs прошли. Python 3.11/3.12/3.13 на Linux и Windows обнаружили одинаковый отказ нового теста `test_stdout_eof_terminates_worker_that_remains_alive`: дочерний тестовый процесс закрывал `sys.stdout`, но pipe не переходил в EOF в ожидаемом сценарии; `process_alive` оставался True. Остальной Python regression suite проходил.

DEV270 не принят. DEV271 исправляет fault-injection: тест закрывает непосредственно fd 1 через `os.close(1)`. Дополнительно reader failure теперь атомарно сбрасывает `started`, выставляет `reader_failed`, а startup повторно проверяет состояние процесса/reader перед объявлением Worker запущенным. Это также закрывает гонку между получением start ACK и немедленным EOF.

## Ограничения

- Не выполнялся 24/72-часовой soak.
- Нет аппаратной приёмки Rust/Modbus на реальном контроллере.
- Benchmark остаётся синтетическим loopback и не подтверждает производственную ёмкость.
