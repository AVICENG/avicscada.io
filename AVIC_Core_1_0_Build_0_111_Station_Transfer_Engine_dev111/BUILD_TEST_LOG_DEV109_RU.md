# Журнал сборки и тестирования DEV109

Дата: 24.11.2026  
База: пользовательский архив AVIC Core 1.0 DEV108.

## Цель

Проверить и закрепить сквозной инженерный сценарий FBD → Core Point Runtime → Engineering Tree → Graphics Workbench → Repository Page Builder → Publish → Operator Runtime.

## Реализовано в DEV109

- Добавлен `tests/test_dev109_fbd_graphics_page_flow.py`.
- Сценарий создаёт проект/станцию, FBD Studio документ и выходную точку.
- FBD документ компилируется; виртуальная точка регистрируется в Core и обновляется через FBD Runtime.
- Проверяется, что один и тот же Core ID присутствует в инженерном дереве и каталоге точек Graphics.
- Проверяется сохранение независимых привязок `feedback → animation` и `quality → status` на символе вентилятора.
- Проверяется повторное чтение мнемосхемы, добавление её на Web Page, сохранение макета, публикация и runtime endpoint опубликованной графики.
- Проверяется сохранность страницы, графики и привязок после создания нового приложения на том же `data_dir`.
- Версия пакета и FastAPI обновлена до `1.0.0.dev109`.

## Проверки DEV109 в среде подготовки

| Проверка | Результат |
|---|---|
| Сквозной DEV109 + DEV103 + DEV107 + Graphics Binding + Page Builder + Navigation + health/version | **32 passed in 6.27s** |
| `python -m compileall -q avic_core` | OK |
| `python -m avic_core --help` | OK |
| `node --check` inline JS: graphics.html | 2 script blocks OK |
| `node --check` inline JS: repository.html | 1 script block OK |
| `node --check` inline JS: index.html | 1 script block OK |
| Wheel build `avic_core-1.0.0.dev109-py3-none-any.whl` | OK |

SHA256 wheel: `eef01a916b5c7bfa149760e48c293ed66c970cee59b6d397dbc05888a35fe43a`.

## Что не заявляется как проверенное

- Полный pytest suite DEV109 ещё не запускался в Windows у пользователя.
- Автоматизированный тест проверяет backend flow и статические UI-контракты, но не выполняет физическое перетаскивание мышью в реальном браузере. Для этого нужен отдельный браузерный acceptance.
- Физические BACnet/Modbus команды не выполнялись; управление оборудованием не включено.
- Не проводился приёмочный тест с реальным Trend контроллером.

## Статус

**DEV109: фокусная сквозная регрессия пройдена в среде подготовки; Windows full-suite и браузерная проверка ожидают выполнения.**

## Дополнительные замечания окружения

- Wheel установлен в отдельный target без зависимостей; установленный пакет ответил `/api/ui/health` со статусом `ok` и версией `1.0.0.dev109`.
- `pip check` в общей Linux-среде сообщает о внешнем конфликте `moviepy 2.2.1` → `pillow<12`, при установленном `pillow 12.3.0`. Pillow не является зависимостью AVIC Core. Этот результат не трактуется как ошибка зависимостей AVIC; на Windows следует отдельно выполнить `python -m pip check`.
