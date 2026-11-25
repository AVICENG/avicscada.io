# Журнал сборки и тестирования DEV106

Дата: 23.11.2026

## Изменения

- Новый `avic_core.commands.CommandManagerService`.
- SQLite-журнал Access Lease и команд в `databases/commands.sqlite3`.
- API выдачи/отзыва Lease, запроса Start/Stop, чтения истории и simulated feedback.
- Проверка существования точки, станции, направления OUTPUT/INOUT, BOOL-типа.
- Проверка всех переданных interlock: качество строго GOOD, значение строго true.
- Audit для выдачи/отзыва Lease, simulated command и simulated feedback.
- Отсутствие полевых записей: не вызываются драйверы, Point Runtime не меняется.
- Версия пакета и UI поднята до `1.0.0.dev106`.

## Тесты и проверки

| Проверка | Результат |
|---|---|
| `pytest -q tests/test_dev106_command_manager.py` | 5 passed |
| Связанные Command Manager + Point Runtime + UI + Graphics + Web Pages тесты | 42 passed |
| `python -m compileall -q avic_core` | OK |
| Wheel build (`pip wheel --no-deps --no-build-isolation`) | OK |
| Установка wheel в отдельный target и import/app smoke test | OK |
| `pip check` | Внешний конфликт: moviepy 2.2.1 требует pillow<12, установлена pillow 12.3.0 |
| Полный `pytest -q` | Прерван по лимиту времени около 40%; полного итога нет |

## Ограничения

- Только `SIMULATION_ONLY`; полевая запись не выполняется.
- Simulated feedback не является фактическим read-back контроллера.
- Loopback-only development guard не заменяет customer-grade authentication, RBAC, station/equipment scopes и MFA.
- Нет арбитража приоритетов, multi-operator approval, timeout/cancel и fail-safe физического адаптера.

## Готовность

**Command Manager foundation — частично готов, только для безопасной симуляции.** Реальное управление запрещено до отдельного этапа SecurityGateway/RBAC и драйверного write/read-back контура.
