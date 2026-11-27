# AVIC Core — журнал DEV209

Дата: 27.11.2026

## Основание
DEV208 добавил Rust Communication Engine, после чего combined CI выявил packaging discovery issue и 4 Python regression failures.

## Исправления
- FBD cross-station test теперь ожидает отказ непосредственно при add_point_node: это фактическая и более ранняя security boundary, до записи некорректного графа.
- MQTT test fixture получает реальный persisted DriverInstance ID из Core repository во всех сценариях. Устранены неопределённая переменная driver и фиктивный driver-mqtt-test; этим восстанавливается корректная проверка GOOD, BAD_COMMUNICATION, BAD_CONFIGURATION.

## Проверки
- Предыдущий run 45952516103: Python dependency installation успешно прошла на всех 6 jobs; Linux pytest показал 4 failed / 31 370 passed. Rust cargo test и release build прошли на Ubuntu и Windows.
- Новый CI для DEV209 ожидает запуска после глобальной concurrency очереди. Никаких новых pass claims не делается.

## Готовность
DEV209 — исправление регрессионных фикстур/ожиданий. PR не готов к merge. Rust Modbus остаётся pilot до parity/load/fault и hardware acceptance.
