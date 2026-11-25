# Журнал проверок DEV62

Дата: 19.11.2026

## Целевые проверки

| Проверка | Результат |
|---|---:|
| `tests/test_dev62_integrated_workflows.py` + `tests/test_driver_manager_dev57.py` | 20 passed |
| `tests/test_fbd_iqvision_dev55.py` + DEV62 integrated + DEV57 Driver Manager + DEV56 Engineering Workflow | 12,545 passed |
| `python -m compileall -q avic_core tests` | успешно |
| `pytest --collect-only -q` | 30,951 тест собран |

## Регрессионный прогон

- Полный `pytest -q` не завершился в лимите 300 секунд; остановка произошла примерно на 74% коллекции.
- Прогон с исключением большой graphics matrix также не завершился в лимите 300 секунд.
- Прогон с исключением двух крупных parameterized suites (`test_iqvision_graphics_authoring_dev54.py`, `test_iqvision_matrix_1000_dev50.py`) дошёл примерно до 99%, но не завершился в лимите 300 секунд.
- В процессе fail-fast-прогона обнаружено одно устаревшее ожидание: FBD API тест ожидал ровно 9 блоков. После добавления трёх новых блоков ожидание заменено проверкой обязательного состава библиотеки.
- После исправления целевая FBD/DEV62 регрессионная группа завершилась: 12,545 passed.

**Не заявляется:** 30,951 passed; единый полный регрессионный прогон не подтверждён.

## Не выполнено

- Windows acceptance на целевом ПК пользователя.
- Интерактивная браузерная проверка графического редактора и FBD.
- Физические BACnet/IP и Modbus TCP контроллеры.
- TONN / Linux Controller Agent.
- Полевая запись, production runtime, HA/failover и production publish.
- Полная проверка серверного RBAC на каждом endpoint.

## Дополнительная приёмка сборки

- `python -m compileall -q avic_core tests` — успешно.
- `node --check` для встроенных JS-блоков `index.html`, `graphics.html`, `logic.html`, `pages.html` — успешно.
- `python -m avic_core --data-dir <temp> init` — успешно.
- `python -m avic_core --data-dir <temp> health` — `status=OK`, audit chain records=3, runtime registered_stations=0.
- `pip check` — обнаружено внешнее конфликтующее окружение: установленный `moviepy 2.2.1` требует `pillow<12`, в среде `pillow 12.3.0`. AVIC Core в этот конфликт не входит; чистое виртуальное окружение Windows нужно проверить отдельно.
- Wheel `avic_core-1.0.0.dev62-py3-none-any.whl` собран успешно.
