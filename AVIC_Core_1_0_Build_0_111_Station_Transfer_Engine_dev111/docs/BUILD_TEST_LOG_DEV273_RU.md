# AVIC Core — журнал сборки DEV273 / IPC Architecture & CI Recovery

Дата: 28.11.2026  
Ветка: drivers/modbus-rtu-c-worker-dev249  
Предыдущий HEAD: f272199c80c70043a47362522b99dd00b7cf70ff

## Исходный статус

- DEV271 / CI #969 ранее прошёл: 22 jobs success.
- DEV272 / CI #970 завершился success.
- Следующий полный прогон CI #971 для HEAD f272199c80c70043a47362522b99dd00b7cf70ff завершился failure.
- Native C jobs (libmodbus Windows/Linux, Paho MQTT Windows/Linux, BACnet POC Windows/Linux, OPC UA probes, S7 policy) прошли.
- Python matrix выявила один тестовый сбой: test_malformed_stdout_fences_and_kills_unresponsive_worker. Reader корректно обнаруживал malformed stdout настолько быстро, что start() иногда выбрасывал RustWorkerError до возврата в тест; тест ошибочно предполагал, что startup всегда успеет вернуться.
- Rust Communication Engine Linux/Windows не собрался из-за E0382: тест переносил String malformed в closure и использовал его после move.

## Исправления DEV273

1. Rust test: expected message вычисляется до thread::spawn; closure получает отдельную копию режима. Production-код протокола не меняется.
2. Supervisor test: допускает оба корректных расписания — reader fenced malformed stream до возврата start(), либо сразу после него. В обоих случаях обязательны reader_failed=true, started=false, процесс завершён, exit code доступен.
3. Добавлен нормативный документ docs/architecture/AVIC_DRIVER_RUNTIME_ARCHITECTURE_V1_RU.md: границы C/Python/Rust, Point Runtime как единственный источник истины, IPC v1, framing, quality/time semantics, команды, backpressure, protocol strategy и acceptance gates.

## Важное уточнение IPC

Проверен фактический avic_core/drivers/ipc.py: Rust IPC v1 использует 4-byte big-endian length-prefixed UTF-8 JSON, максимум 1 MiB, а не NDJSON. Архитектурный документ фиксирует реальное кадрирование. C Workers с NDJSON требуют временного адаптера и поэтапной миграции; смешивать framing в одном потоке нельзя.

## Проверки и статус

- Причина CI #971 установлена по логам.
- Исправления внесены в исходники и ожидают повторного CI.
- На момент подготовки отчёта повторный CI ещё не запускался; DEV273 не объявляется прошедшим.
- Нет заявлений о физическом COM/RS-485 или BACnet controller acceptance.

## Ограничения

- BACnet C — POC/ранний Worker, не полноценная замена Python/Rust runtime.
- Modbus RTU — Linux PTY программная проверка; Windows virtual COM и физический RS-485 остаются отдельными gates.
- MQTT — базовый TCP scope; TLS/SecretStore/ACL/QoS soak не закрыты.
- KNX xknx Worker ещё не реализован.
- Unified Driver Manager registration для C Worker ещё требует завершения.
- PR #11 остаётся открытым и не объединяется автоматически.

## Следующий этап

После зелёного CI — Modbus RTU Windows COM/serial ownership, затем BACnet C Worker: discovery, ReadProperty, ReadPropertyMultiple, datatype/unit mapping, quality/error mapping, simulator и интеграция Driver Manager → Point Runtime.
