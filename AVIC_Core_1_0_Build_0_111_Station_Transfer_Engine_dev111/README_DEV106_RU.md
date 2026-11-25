# AVIC Core 1.0 — DEV106

DEV106 продолжает DEV105 и добавляет Command Manager foundation для безопасного испытания операторских команд.

## Быстрый запуск Windows

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m avic_core.ui --data-dir .\data --host 127.0.0.1 --port 8000
```

Открыть `http://127.0.0.1:8000`.

## Command Manager

DEV106 предоставляет API Access Lease и Start/Stop только в режиме `SIMULATION_ONLY`. Проверяются станция, направление и тип точки, действующий Lease и GOOD interlock. Результат симуляционного read-back хранится отдельно от Point Runtime. Полевые записи в BACnet/Modbus не выполняются.

Подробности и ограничения: `docs/COMMAND_MANAGER_DEV106_RU.md`.

## Проверки

- Новый набор DEV106: 5 passed.
- Связанные UI / Point Runtime / Graphics / Web Pages наборы: 42 passed.
- `compileall`: OK.
- Wheel DEV106 собран и установлен в отдельный target; import smoke test: OK.
- Полный pytest-набор запущен, но текущий прогон был остановлен по лимиту времени на отметке около 40%; итогового полного результата нет.

## Критические ограничения

- Нет физического BACnet/Modbus write path.
- Нет реального read-back от контроллера.
- Полная пользовательская RBAC/session/MFA интеграция ещё не подключена; мутации Workbench ограничены loopback-only development guard.
- Перед реальным управлением обязательны SecurityGateway + scope RBAC, подтверждение критичных операций, арбитраж, watchdog/timeout/fail-safe и стендовые испытания.
