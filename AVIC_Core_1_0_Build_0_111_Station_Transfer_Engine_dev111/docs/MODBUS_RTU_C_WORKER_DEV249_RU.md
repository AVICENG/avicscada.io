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
- DEV250 follow-up: `modbus-rtu` зарегистрирован во встроенном каталоге и Driver Manager; RTU конфигурация валидируется в Core и направляется в тот же libmodbus C Worker.
- Общий Point Runtime adapter расширен на `modbus-rtu`: batching, FC01/02/03/04, decode/scaling, quality и публикация используют тот же путь, что и TCP.
- Добавлен `SerialPortLease`: ОС-блокировка (POSIX `flock`, Windows byte-range lock) удерживается всё время жизни RTU-драйвера. Повторное открытие того же нормализованного COM/TTY из другого AVIC-процесса отклоняется; после штатного закрытия блокировка освобождается, после аварийного завершения снимается ядром ОС.
- Добавлены DEV250 тесты Driver Manager, serial config validation и RTU point-poll IPC contract; они добавлены в репозиторий, но ещё не имеют подтверждённого CI результата.
- TCP путь оставлен на прежнем `modbus_new_tcp()`; общие IPC framing, identity, sequence, secret rejection и lifecycle сохранены.
- Добавлены native-worker tests на принятие корректной RTU конфигурации, отказ при несовпадении serial settings и отказ при некорректной parity.

## Текущий статус

<badge color="warning">🟧 Частичная реализация — CI не подтверждён</badge>

DEV250 устранил функциональный разрыв: RTU больше не ограничен прямым запуском бинарника в тесте, его можно выбрать как отдельный встроенный драйвер в AVIC Driver Manager и связать с точками. Это пока кодовая интеграция, не подтверждённая сборкой/регрессией.

Кодовый RTU путь добавлен, но DEV249 нельзя объявлять зелёным до Windows/Linux CI и полноценного RTU round-trip.

## Что ещё не закрыто

1. Linux pseudo-terminal round-trip test добавлен в native-worker suite; ждёт фактического CI запуска. Windows virtual COM round-trip ещё не реализован.
2. Отдельные CRC/short-frame/timeout/late-response/wrong-slave negative tests ещё не закрыты.
3. Полноценный Serial Port Manager с инвентаризацией портов, горячим unplug/replug, восстановлением соединения и диагностикой конфликтов. DEV250 уже блокирует параллельное владение одним COM/TTY между AVIC-процессами, но пока не управляет обнаружением/перечнем устройств и не подтверждён на физических адаптерах.
4. Проверка unplug/replug, reconnect/backoff и bus contention.
5. RS-485 adapter tests, RTS polarity/timing и несколько физических устройств.
6. Soak/load и latency p95/p99.
7. Физический acceptance на реальных устройствах.

Один AVIC RTU Worker должен владеть одной serial line. DEV250 добавил межпроцессную advisory-блокировку на уровне ОС; внешние приложения, которые не используют AVIC lock contract, всё ещё могут открыть тот же порт. RTS — адаптеро- и драйверозависимая опция; `none` остаётся безопасным значением по умолчанию.

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

На момент обновления отчёта добавлен Linux PTY round-trip test с проверкой CRC запроса и ответа FC03, а также DEV250 тесты Driver Manager и Point Runtime RTU пути. Фактический запуск CMake/pytest и CI текущего HEAD ещё ожидается; тесты не помечаются Passed до получения результата. Никакие новые тесты не помечаются Passed. Исторические Windows/Linux результаты DEV245/DEV247 сохраняются как отдельные результаты старых commit.

## Источник API

- `modbus_new_rtu(device, baud, parity, data_bit, stop_bit)`
- `modbus_set_slave()`
- `modbus_set_response_timeout()`
- `modbus_rtu_set_rts()`
- `modbus_connect()`

API и поведение проверены по документации libmodbus. Реальная совместимость с конкретной версией/сборкой libmodbus должна быть подтверждена целевыми CI jobs.
