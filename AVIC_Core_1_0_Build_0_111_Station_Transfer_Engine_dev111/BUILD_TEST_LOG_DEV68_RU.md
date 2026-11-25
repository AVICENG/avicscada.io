# Журнал проверок AVIC DEV68

**Версия:** `1.0.0.dev68`  
**База:** полный архив DEV67 AHU Modular Animation  
**Дата:** 20.11.2026

## 1. Сводка тестов

`pytest --collect-only -q`: **30 994 тестовых случая**.

Единый непрерывный запуск `python -m pytest -q --tb=short` не завершился в доступное время: был остановлен примерно на 73% после 120 секунд. После исправления устаревшего ожидания версии DEV67 в `test_dev62_integrated_workflows.py` весь набор был проверен непересекающимися группами и дополнительным прогоном нового FBD-набора.

| Группа | Состав | Уникальных passed |
|---|---|---:|
| FBD / IQVISION + DEV68 | `test_fbd_iqvision_dev55.py` и `test_fbd_set_parity_dev68.py` | 12 521 |
| Graphics Authoring | `test_iqvision_graphics_authoring_dev54.py` | 10 008 |
| Point Manager | `test_point_views_iqvision_dev52.py` | 6 727 |
| IQVISION matrix + Alarm Console | `test_iqvision_matrix_1000_dev50.py`, `test_iqvision_alarm_console_dev53.py` | 1 411 |
| Остальные тесты | остальные 57 test-файлов, без повторного учёта DEV68 FBD | 327 |
| **Итого уникальных тестов** | | **30 994 passed** |

Примечание: новая API-регрессия DEV68 добавлена после первоначального группового прогона FBD. Поэтому файл `test_fbd_set_parity_dev68.py` дополнительно прогнан целиком: **8 passed**. Общий уникальный итог выше включает все 8 новых тестов, без двойного счёта.

## 2. Целевые DEV68 / DEV67

Команда:
`python -m pytest -q tests/test_fbd_set_parity_dev68.py tests/test_modular_ahu_sections_dev67.py tests/test_graphics_svg_library_dev64.py tests/test_graphics_iso3d_library_dev66.py`

Результат: **25 passed**:
- 8 тестов страниц стратегии, межстраничных Connective, симуляции и HTTP API;
- 17 тестов модульной ПВУ и SVG-графики DEV67.

Отдельный совместный прогон FBD:
`python -m pytest -q tests/test_fbd_iqvision_dev55.py tests/test_fbd_set_parity_dev68.py`
— **12 520 passed** на версии файла DEV68 с 7 тестами; затем полный файл DEV68 с добавленным API-тестом — **8 passed**.

## 3. Статические проверки и пакет

- `python -m compileall -q avic_core tests` — успешно.
- `node --check` для inline JavaScript `logic.html` — успешно.
- Wheel собран: `avic_core-1.0.0.dev68-py3-none-any.whl`, 409 525 bytes.
- Wheel содержит **66 SVG-ресурсов**, включая все 7 модульных SVG-секций AHU DEV67.
- SHA-256 wheel: `ade0f553126d881a99aa44caf789f5b0af8bd0b1cadd2b08fc41333056c06235`.

`python -m pip check` в среде сборки сообщает внешний конфликт установленного пакета `moviepy 2.2.1` с `Pillow 12.3.0` (moviepy требует Pillow ниже 12). Это не конфликт зависимостей, объявленных AVIC в `pyproject.toml`, но команда `pip check` в этой общей среде не имеет чистого результата.

## 4. Сохранность DEV67

Проверены целевые тесты DEV67:
- 7 SVG-секций модульной ПВУ;
- единая геометрия и viewBox;
- XML-разбор SVG;
- состояния заслонки, вентилятора и потока;
- создание и повторное открытие семисекционной схемы;
- API библиотеки символов и UI-признаки;
- локальный preview без полевых команд.

Wheel содержит 66 SVG, в том числе все 7 AHU-секций. Исходная база DEV67 сохранена.

## 5. Приёмка и ограничения

- Браузерный визуальный тест Chromium в этой среде не выполнялся.
- Установка и запуск на целевом Windows-ПК не проверены; требуется пользовательская приёмка.
- Единый непрерывный pytest не получил итогового exit code; полный тестовый объём подтверждён группами, перечисленными выше.
- DEV68 — первый архитектурный этап SET-like FBD, не полный визуальный клон SET 6.3.
- Графические To/From/Undefined Connective, полноценная drag-маршрутизация, sequence steps, автоматическая нумерация модулей и полная библиотека блоков SET ещё не реализованы.
- Полевые команды и записи в контроллеры остаются отключёнными.
