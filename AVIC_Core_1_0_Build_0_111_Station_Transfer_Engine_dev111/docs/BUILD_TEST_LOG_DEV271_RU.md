# AVIC Core — журнал сборки DEV271

Дата: 28.11.2026
Ветка: `drivers/modbus-rtu-c-worker-dev249`
Предыдущий коммит: `1809aea9d1da234ce083838dd2fb61ac35210a1c`

## Причина

CI DEV270 (#968, run `46155780523`) выявил одинаковый отказ нового EOF fault-injection теста на Linux и Windows, Python 3.11/3.12/3.13. Rust jobs (31 тест на каждой ОС) и нативные C jobs прошли. Python suite завершался с единственной новой ошибкой в `test_stdout_eof_terminates_worker_that_remains_alive`.

Первоначальный fake worker вызывал `sys.stdout.close()`, но это не гарантировало закрытие pipe descriptor на всех runner-платформах. Тест ожидал EOF, а дочерний процесс оставался жив.

## Изменения DEV271

1. `tests/test_rust_driver_worker_supervisor_dev218.py`
   - Fake worker закрывает системный fd 1 напрямую через `os.close(1)`.
   - Проверяются `process_alive=False`, `started=False`, `reader_failed=True` и наличие exit code.
2. `avic_core/drivers/rust_worker.py`
   - Любая ошибка stdout reader атомарно выставляет `reader_failed=True` и `started=False`.
   - После start ACK проверяются состояние reader и реальное состояние дочернего процесса до установки `started=True`.
   - Диагностика экспортирует `reader_failed`.
   - EOF при живом процессе приводит к terminate, затем kill при необходимости.

## Цель проверки

- Убедиться, что EOF действительно возникает при закрытии дескриптора.
- Убедиться, что живой orphan worker завершается.
- Исключить гонку ACK/EOF при старте.
- Прогнать полный Python 3.11/3.12/3.13 на Windows и Linux.
- Повторить Rust tests и нативные C jobs.

## Статус

DEV271 отправлен отдельным коммитом. Результаты CI будут внесены после полного прогона. До успешного Windows/Linux CI исправление не считается принятым.

## Открытые проверки Rust reliability

- Modbus TCP: задержанный ответ после timeout, частичный MBAP/PDU, неверный protocol/unit/byte count, reconnect после timeout.
- Rust Worker: 24-часовой soak, последовательные рестарты, память/CPU, очередь IPC, p95/p99.
- Нагрузка 1 000 устройств / 100 000 точек пока не является подтверждённым gate.
- Физический контроллер не проверен данным CI.
