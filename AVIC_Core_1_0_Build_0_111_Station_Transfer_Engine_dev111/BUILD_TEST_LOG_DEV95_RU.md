# Журнал испытаний AVIC Core DEV95

## Изменения

- Реализованы предварительная проверка и компиляция FBD Studio → Core FBD.
- Добавлены API `compile-preview` и `compile`.
- Добавлен пункт компиляции в контекстное меню FBD-проекта и меню File.
- Компиляция сохраняет исходный Studio-документ и создаёт отдельную Core-стратегию.
- Добавлены проверки нескольких страниц, связей, устаревшей ревизии, неподдерживаемых блоков, повторной компиляции и текстовых значений входов.

## Фактические проверки

- `python -m pytest -q tests/test_fbd_*.py tests/test_dev89_fbd_runtime_evaluation.py tests/test_dev90_fbd_cyclic_runtime.py tests/test_dev91_fbd_project_package_schedule.py tests/test_dev94_fbd_schedule_core_integration.py tests/test_dev95_fbd_studio_compiler.py tests/test_scheduler_manager_dev47.py tests/test_scheduler_manager_dev48.py` — **12 596 passed in 17.70s**.
- `python -m compileall -q avic_core tests` — успешно.
- `python -m avic_core --help` — успешно.
- Извлечено 3 встроенных JavaScript-блока из FBD Studio; `node --check` — успешно.
- Wheel `avic_core-1.0.0.dev95-py3-none-any.whl` собран успешно.
- ZIP проверен на целостность; временные SQLite-файлы и кэши исключены из дистрибутива.

## Ограничения испытаний

- Полный набор всех тестов репозитория в DEV95 не запускался; 12 596 тестов — профиль FBD, Runtime, Studio, Schedule Manager и связанные регрессии.
- `pip check` обнаружил уже известный конфликт глобального окружения: `moviepy 2.2.1` требует `Pillow<12`, установлена `Pillow 12.3.0`. Это не зависимость AVIC Core и не ошибка сборки AVIC.
- Windows-приёмка на Python 3.15.2 ещё не выполнена пользователем.
- Визуальная проверка интерфейса в браузере ещё не выполнена.

## Безопасность

Компиляция не запускает Core-стратегию, не публикует значения и не выполняет записи в физические контроллеры. `runtime_published=false`, `field_writes_enabled=false`.
