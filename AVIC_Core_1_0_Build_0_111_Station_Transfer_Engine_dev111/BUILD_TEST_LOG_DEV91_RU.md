# Журнал DEV91

## Изменения
- Добавлен переносимый FBD JSON package `.avicfbd.json` с manifest/schema version 1 и SHA-256.
- Добавлена проверка целостности при открытии.
- Сохранён обратный импорт legacy JSON.
- Добавлена предварительная структурная валидация до замены текущего документа.
- Добавлен FBD `SCHEDULE` block: BOOL/числовой выход, недельные интервалы, исключения, приоритет, IANA timezone, override expiry, переход через полночь.
- Добавлены тесты `tests/test_dev91_fbd_project_package_schedule.py`.

## Проверки
- `pytest -q` по выбранным DEV91/DEV90/Schedule/FBD regression suites: **12 549 passed** за 20.21 с.
- Новый DEV91 test file отдельно: **4 passed**.
- `compileall -q avic_core tests`: exit code 0.
- `python -m avic_core --help`: exit code 0.
- Все 3 встроенных JavaScript-блока `logic.html`: `node --check` без ошибок.
- Полная регрессия всего репозитория не запускалась; Windows и браузерная визуальная приёмка не проводились.
- В stdout/stderr Python окружения присутствует постороннее предупреждение `artifact_tool` о spreadsheet warmup; тесты и команды завершаются успешно.

## Ограничения
Schedule-блок пока является локальной функцией редакторской симуляции. Он не вызывает Core ScheduleService, не публикует значения в PointRuntime и не управляет оборудованием.

## Исследование исходных материалов Trend
- `12345.TSET` идентифицирован по сигнатуре `Standard Jet DB`; внутренние записи в DEV91 не импортируются.
- `Meridian.TSITE` разобран как XML с сетевой топологией Site/LAN/Device.
- `ToolSET.zip` содержит преимущественно бинарные OCX/DLL/EXE и `spidData.xml`.
- `SET_Meridian_26.01.21.rar` содержит 187 записей по оглавлению, включая TSET backups, TSITE, IQ/IQBak и IQTool templates; внутренние записи RAR в этой сборке не извлекались.
- Подробная оценка — `docs/BUILD_091_RU.md` и `docs/FBD_PROJECT_PACKAGE_SCHEDULE_RU.md`.

- `pip check`: **не проходит в общем окружении** из-за уже установленной пары `moviepy 2.2.1` → требуется `Pillow<12`, фактически `Pillow 12.3.0`. Это конфликт глобального окружения, не зависимость AVIC Core; зависимости проекта принудительно не менялись.
