# AVIC Core 1.0 DEV106 — Command Manager foundation

DEV106 добавляет первый безопасный command workflow, работающий только в `SIMULATION_ONLY`.

## Реализовано

- Access Lease с привязкой к станции и локальному инженерному пользователю, сроком действия и отзывом.
- API Start/Stop для булевых OUTPUT/INOUT-точек.
- Проверка станции, направления и типа точки.
- Interlock validation: каждая блокировка должна быть `GOOD` и `true`.
- Audit событий выдачи/отзыва Lease, запроса команды и simulated feedback.
- Сохранение журнала команд в отдельной БД Core.
- Отдельный simulated read-back и три состояния исполнения.
- Гарантия отсутствия полевой записи: не вызываются драйверы и не меняется Point Runtime.

## Проверки

Новый набор `tests/test_dev106_command_manager.py`: пять сценариев — успешный simulation flow, запрет при false interlock, запрет при неверном направлении, запрет при плохом качестве interlock, валидация Lease и причины. Результат фиксируется в `BUILD_TEST_LOG_DEV106_RU.md`.

## Не реализовано

- Физическая запись BACnet/Modbus.
- Реальный read-back от устройства.
- Полная RBAC/session/MFA интеграция; mutating endpoints пока защищены loopback-only development guard.
- Арбитраж приоритетов, подтверждение вторым оператором и безопасное состояние при потере связи.

## Готовность

Command Manager foundation: **частично готов, simulation-only**. Для подключения к реальному оборудованию необходим отдельный этап security + driver write adapter + read-back и испытания на стенде.
