# Журнал сборки и тестирования AVIC DEV69

Дата: 20.11.2026  
База: DEV68  
Версия: `1.0.0.dev69`

## Изменения
- Добавлен блок `POINT_INPUT` для привязки существующих точек станции.
- Добавлен API `POST /api/fbd/{document_id}/points/{point_id}`.
- Добавлена проверка принадлежности точки станции стратегии.
- Добавлено разрешение типа физической точки и строгая проверка качества GOOD при симуляции.
- В Point Manager tree добавлены data_type и direction в ответе.
- В FBD Workbench добавлена панель точек станции с поиском и drag-and-drop на лист.
- Добавлены визуальные To/From-маркеры и переход Go To для межстраничных Connective.
- Добавлен read-only parser Trend TSITE XML и его тесты.
- Обновлена версия пакета до 1.0.0.dev69.

## Проверки
- Все 31 002 теста, собранные `pytest --collect-only`, выполнены и прошли в групповых запусках по test-файлам.
- Крупные регрессионные группы: FBD + point binding + TSITE parser — 12 529 passed; IQVISION graphics authoring — 10 008 passed; Point Views — 6 727 passed; IQVISION matrix — 1 164 passed; alarm console — 247 passed.
- AHU/SVG regression (modular AHU, SVG library, ISO3D, SVG import, graphics workbench): 27 passed.
- `python -m compileall -q avic_core tests`: OK.
- Inline JavaScript `node --check`: OK.
- `python -m pip check`: обнаружен конфликт глобального окружения `moviepy 2.2.1` (требует `Pillow<12`) с `Pillow 12.3.0`; это не зависимость AVIC из `pyproject.toml`.
- Фактический файл `Otradnoe_korp_A.TSITE`: 4 Site, 14 LAN, 173 Device, 227 Module, 5 351 Param.

## Ограничения проверки
- Единый непрерывный прогон 31 002 тестов завершился по тайм-ауту примерно на 35%; поэтому все тесты проверены групповыми запусками, а не одним непрерывным запуском.
- `compileall` и JS syntax check выполнены успешно.
- Wheel `avic_core-1.0.0.dev69-py3-none-any.whl` собран (413 500 bytes); установка в отдельный target-каталог и импорт `FBDService` / `parse_tsite` прошли.
- ZIP integrity будет проверен после упаковки.
- Каталог содержит 13 типов блоков, а не полную библиотеку SET 6.3.
- `.TSET` и `.TSETBak2` — Access Jet DB; чтение таблиц в этой среде не обеспечено.
- Браузерная приёмка на Windows не выполнялась.

## Статус
**DEV69 — инженерный этап разработки, не финальная SET 6.3 parity.** Полный перенос библиотеки и стратегии SET не подтверждён.
