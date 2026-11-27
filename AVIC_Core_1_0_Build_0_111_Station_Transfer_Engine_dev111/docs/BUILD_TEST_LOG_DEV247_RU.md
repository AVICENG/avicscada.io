# DEV247 — регрессия каталога, цветовой реестр и C-only Siemens S7

Дата: 27.11.2026  
Ветка: `drivers/c-only-cleanup-dev246`  
Базовый кодовый HEAD: `afa64e5aa0b91bcfd87246cf39faa02360aabf92`

## Цветовая шкала готовности

- 🟩 **Зелёный — подтверждённая программная реализация:** код есть, целевые автоматические тесты прошли.
- 🟦 **Синий — аппаратно подтверждено:** есть журнал испытания на реальном устройстве с моделью/прошивкой.
- 🟨 **Жёлтый — частичная реализация:** отдельные функции или интеграция прошли, но полный lifecycle не принят.
- 🟧 **Оранжевый — POC / probe:** сборка или smoke test есть, но полноценного AVIC Worker нет.
- 🟥 **Красный — регрессия/ошибка:** CI или целевой тест завершился ошибкой.
- ⬜ **Серый — не реализовано / не проверено.**

Цвет относится только к конкретному объёму работ. Успешная сборка библиотеки не повышает статус полного протокола до зелёного или синего.

## Исправления DEV247

1. Исправлен устаревший API regression expectation: после добавления Wired M-Bus каталог содержит 17 записей, тест ранее ожидал 16.
2. В каталоге Siemens S7 переведён в PLANNED: Rust реализация не соответствует требованию пользователя «S7 только C».
3. Удалён optional extra `.[s7]` с Python protocol engines.
4. Предыдущие Python package smoke tests заменены на policy guard, запрещающий рекламировать S7 как работающий драйвер до C Worker acceptance.
5. Архитектура S7 и license inventory переписаны: Snap7 — C++ core/toolchain, libnodave — pure C, но beta/legacy с явными upstream safety warnings. Ни один пока не принят в промышленную сборку.
6. Удалён именно протокольный Rust S7 path: src/s7.rs, зависимость tokio-s7, регистрация модуля и ветка s7comm в Rust Worker. Общий Rust Worker/IPC для других протоколов сохранён. Python S7 extra также удалён. До появления C Worker S7 отключён, а не переключается на fallback.

## Сохранённые результаты CI до DEV247

Источник: GitHub Actions run `46048312982`, commit `afa64e5aa0b91bcfd87246cf39faa02360aabf92`.

| Область проверки | Результат | Статус |
|---|---|---|
| C libmodbus Worker — Ubuntu build + IPC smoke | Passed | 🟩 |
| C libmodbus Worker — Windows UCRT64 build + IPC smoke | Passed | 🟩 |
| BACnet Stack POC — Ubuntu build/probe | Passed | 🟧 |
| BACnet Stack POC — Windows build/probe | Passed | 🟧 |
| OPC UA open62541 native probe — Ubuntu | Passed | 🟧 |
| OPC UA open62541 native probe — Windows UCRT64 | Passed | 🟧 |
| Rust Communication Engine unit tests + synthetic benchmark — Ubuntu | Passed | 🟨 |
| Rust Communication Engine unit tests + synthetic benchmark — Windows | Passed | 🟨 |
| Python S7 package smoke tests — Ubuntu/Windows | Passed ранее, но отменены как целевой runtime путь | 🟥 obsolete |
| Полная Python регрессия — Linux/Windows, Python 3.11–3.13 | Один и тот же отказ в каждой завершённой матрице | 🟥 |

### Причина красной регрессии

Все завершённые Python matrix jobs падали только в:
`tests/test_network_api_dev27.py::test_driver_catalog_api_exposes_runtime_integration_without_overstating_readiness`

Причина: ожидалось 16 драйверов, фактически было 17 после добавления Wired M-Bus. Во всех затронутых matrix jobs остальные тесты проходили:
- Linux: 31,493 passed / 1 failed / 5 skipped (Python 3.11, 3.12, 3.13).
- Windows: 31,492 passed / 1 failed / 6 skipped (Python 3.11 и 3.13; один POSIX-only skip).
- Windows Python 3.12 на момент первичной фиксации ещё выполнялся; результат не переносить из соседней матрицы.

DEV247 исправляет именно устаревшее ожидание и добавляет явную проверку M-Bus. Новый CI должен подтвердить исправление; до нового зелёного run статус полной регрессии остаётся 🟨/ожидает подтверждения.

## Текущая карта протоколов

| Протокол | Реальное состояние на базовом HEAD | Цвет |
|---|---|---|
| Modbus TCP | C Worker, read-only FC01/02/03/04, IPC и simulator smoke | 🟩 |
| Modbus RTU | В каталоге/плане, C Worker не реализован | ⬜ |
| BACnet/IP | Python runtime + отдельный C Stack probe; C Worker отсутствует | 🟨 |
| BACnet MS/TP | C Stack probe не является MS/TP Worker; serial lifecycle не принят | 🟧 |
| Siemens S7 | C Worker отсутствует; прежние Rust/Python пути не принимаются | ⬜ |
| MQTT | Python subscribe runtime; Paho C Worker отсутствует | 🟨 |
| OPC UA Client | open62541 C native probe, но AVIC IPC Worker отсутствует | 🟧 |
| Wired M-Bus | Каталог и спецификация; libmbus Worker отсутствует | ⬜ |
| KNXnet/IP | Python read-only runtime; XKNX не интегрирован | 🟨 |

Ни один протокол не имеет синей аппаратной отметки на основании этих CI результатов: physical PLC/controller/meter acceptance здесь не подтверждён.

## Что обязательно сохранить в следующих сборках

- Все прежние успешные test names/results не удалять и не заменять новыми числами.
- Каждый новый CI запуск фиксировать отдельно: commit SHA, OS, Python/compiler version, job, passed/failed/skipped, причина.
- Красные тесты не считать «почти пройденными»; исправление подтверждать повторным запуском.
- Не удалять Rust/Python protocol code до замены и подтверждения всех вызовов, тестов и packaging.
- Не повышать уровень готовности на основании одного compile или smoke test.
- Не менять S7 на Python/Rust даже временным fallback.
