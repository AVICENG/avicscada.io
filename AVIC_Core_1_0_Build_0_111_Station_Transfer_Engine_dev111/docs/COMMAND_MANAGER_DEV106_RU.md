# Command Manager DEV106 — безопасный контур команд (SIMULATION ONLY)

## Назначение

DEV106 добавляет первый исполняемый слой Command Manager между операторским интерфейсом и объектами Point. Страница и мнемосхема не обращаются к BACnet/Modbus напрямую. API принимает только запрос Start/Stop для существующей точки OUTPUT/INOUT, принадлежащей указанной станции.

## Что реализовано

- Временный Access Lease на конкретную станцию и пользователя; срок от 1 до 900 секунд.
- Получение Lease отзывает ранее активный Lease этой станции.
- Команда требует действующий Lease, причину, существующую физическую OUTPUT/INOUT-точку булевого типа.
- Проверяются принадлежность точки станции и все переданные interlock-точки.
- Каждая interlock-точка должна иметь качество `GOOD` и значение `true`.
- Создание и подтверждение команды фиксируются в Audit.
- Состояния `SIMULATED_ACCEPTED`, `SIMULATED_CONFIRMED`, `SIMULATED_MISMATCH` различают принятие команды и подтверждённый симуляционный read-back.
- Командная запись не меняет Point Runtime и не вызывает драйверы. Ответ явно содержит `field_write_performed: false` и `execution_mode: SIMULATION_ONLY`.
- История команд хранится в `databases/commands.sqlite3`.

## API

- `POST /api/stations/{station_id}/control/access-lease` — создать Lease (`duration_seconds`).
- `DELETE /api/control/access-lease/{lease_id}` — отозвать Lease.
- `POST /api/stations/{station_id}/control/commands` — запросить `START` или `STOP` (`point_id`, `lease_id`, `reason`, `interlock_point_ids`).
- `GET /api/stations/{station_id}/control/commands` — список команд.
- `GET /api/control/commands/{command_id}` — состояние команды.
- `POST /api/control/commands/{command_id}/simulated-feedback` — передать тестовый read-back (`value`, `quality=GOOD`).

## Ограничения и безопасность

Это **не физическое управление**. DEV106 не содержит BACnet/Modbus write adapter и не отправляет полевые команды. `simulated-feedback` — отдельный тестовый ввод, а не измерение от контроллера. Не использовать его как доказательство фактического пуска вентилятора.

Изменяющие HTTP-операции остаются под действующим loopback-only development guard Workbench. Это не завершённая пользовательская аутентификация и не customer-grade server-side RBAC. В DEV106 нельзя считать локальную роль `local-engineer` полноценной системой разрешений. Перед включением физического write path обязательны SecurityGateway/session integration, station/equipment scope RBAC, MFA/step-up для критичных команд, независимый драйверный read-back, interlock evaluation в Core, command arbitration/priority, timeout/cancel, fail-safe и commissioning.

## Ручная проверка

1. Создать станцию, тестовое устройство и BOOL OUTPUT-точку.
2. Создать BOOL INPUT interlock-точку и опубликовать `true` с качеством `GOOD` через доверенный тестовый источник.
3. Получить Access Lease.
4. Отправить `START` с причиной и interlock.
5. Убедиться, что команда `SIMULATED_ACCEPTED`, `field_write_performed=false`.
6. Передать simulated feedback `true` / `GOOD`; убедиться в `SIMULATED_CONFIRMED`.
7. Проверить, что значение OUTPUT-точки в Point Runtime не изменилось.
8. Отозвать Lease и убедиться, что повторная команда отклоняется.
