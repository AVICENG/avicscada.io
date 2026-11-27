# AVIC Core — Modbus RTU на libmodbus C, DEV249

Дата: 27.11.2026
Ветка: `drivers/modbus-rtu-c-worker-dev249`
База: DEV248 `bf47584c3755dd3a6360e8b0577102d95912b725`

## Что изменено

Расширен существующий `avic-modbus-c-worker`; отдельный Modbus RTU стек или второй Worker не создавался.

- Добавлен выбор транспорта `modbus-tcp` / `modbus-rtu` в одном C Worker.
- RTU context создаётся штатной функцией `modbus_new_rtu()` из libmodbus.
- Реализована конфигурация serial port, baud rate, parity (N/E/O), data bits (5–8), stop bits (1/2), Unit ID (1–247), timeout (0.1–10 s).
- Поддержаны опциональные RTS direction modes `none/up/down`; по умолчанию `none`.
- Для Windows добавлена нормализация COM10–COM99 к device namespace libmodbus.
- Для чтения сохранён read-only scope FC01/02/03/04 с прежними ограничениями PDU/range.
- RTU read request повторно сверяет serial endpoint и все параметры линии с конфигурацией Worker до обращения к libmodbus.
- TCP путь оставлен на прежнем `modbus_new_tcp()`; общие IPC framing, identity, sequence, secret rejection и lifecycle сохранены.
- Добавлены native-worker tests на принятие корректной RTU конфигурации, отказ при несовпадении serial settings и отказ при некорректной parity.

## Текущий статус

<badge color="warning">🟧 Частичная реализация — CI не подтверждён</badge>

Кодовый RTU путь добавлен, но DEV249 нельзя объявлять зелёным до Windows/Linux CI и полноценного RTU round-trip.

## Что ещё не закрыто

1. Реальный round-trip через Linux pseudo-terminal и Windows virtual COM.
2. CRC/short-frame/timeout/late-response/wrong-slave negative tests.
3. Serial Port Manager с эксклюзивным владением и обнаружением конфликта нескольких Worker.
4. Проверка unplug/replug, reconnect/backoff и bus contention.
5. RS-485 adapter tests, RTS polarity/timing и несколько физических устройств.
6. Soak/load и latency p95/p99.
7. Физический acceptance на реальных устройствах.

Пока нет Serial Port Manager, нельзя запускать несколько AVIC RTU Workers на один и тот же COM/TTY порт и считать арбитраж гарантированным. Один Worker должен владеть одной serial line. RTS — адаптеро- и драйверозависимая опция; `none` остаётся безопасным значением по умолчанию.

## Формат конфигурации RTU

```json
{
  "protocol": "modbus-rtu",
  "serial_port": "/dev/ttyUSB0",
  "baud_rate": 9600,
  "parity": "E",
  "data_bits": 8,
  "stop_bits": 1,
  "unit_id": 7,
  "timeout": 1.5,
  "rts_mode": "none"
}
```

Параметры чтения должны повторять конфигурацию Worker и включать `timeout_ms`, `function`, `address`, `count`. Поддерживаются только функции чтения FC01/02/03/04. Любая запись отклоняется.

На Windows для COM-портов с номером больше 9 Worker формирует путь Win32 device namespace, требуемый libmodbus.

## Проверки

На момент создания этого отчёта код и тесты отправлены в GitHub, но фактический запуск CMake/pytest и CI для DEV249 ещё не получен. Никакие новые тесты не помечаются Passed. Исторические Windows/Linux результаты DEV245/DEV247 сохраняются как отдельные результаты старых commit.

## Источник API

- `modbus_new_rtu(device, baud, parity, data_bit, stop_bit)`
- `modbus_set_slave()`
- `modbus_set_response_timeout()`
- `modbus_rtu_set_rts()`
- `modbus_connect()`

API и поведение проверены по документации libmodbus. Реальная совместимость с конкретной версией/сборкой libmodbus должна быть подтверждена целевыми CI jobs.
