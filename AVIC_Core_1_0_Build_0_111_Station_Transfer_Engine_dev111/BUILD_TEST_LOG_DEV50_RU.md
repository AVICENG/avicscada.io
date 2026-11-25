# DEV50 — журнал сборки и испытаний

## Результат подготовки

- База: DEV49, исходный архив проверен на целостность.
- Версия: `1.0.0.dev50`.
- Pytest collection: **1419 тестовых случаев**.
- Новая матрица `test_iqvision_matrix_1000_dev50.py`: **1164 passed**.
- Дополнительные проверки запуска CLI `test_dev50_cli.py`: **2 passed**.
- Итого новые проверки, выполненные отдельно: **1166 passed**.
- `python -m compileall -q avic_core`: успешно.
- `python -m avic_core.ui --help`: успешно; отображаются host/port/data-dir/reload.
- Smoke-проверка фабрики: приложение `AVIC Engineering Workbench`, версия `1.0.0.dev50`, 83 маршрута.
- Реальный локальный запуск Uvicorn: `GET /` → HTTP 200 (158 504 байта); `GET /api/ui/health` → HTTP 200, status `ok`, version `1.0.0.dev50`.

## Полный прогон

Полный `python -m pytest -q` в контейнерной среде не завершился в доступное 300-секундное окно. Вывод дошёл примерно до 98%; итоговый summary pytest не был получен. Поэтому **полный прогон не отмечен как PASS**. Отдельно подтверждены 1166 новых сценариев. Перед передачей в эксплуатацию пользователь должен выполнить полный набор в Windows-среде проекта.

## Проверка зависимостей

`pip check` в среде подготовки обнаружил сторонний конфликт уже установленного окружения: `moviepy 2.2.1` требует `pillow<12`, а в контейнере присутствует `pillow 12.3.0`. Это не зависимость AVIC и не ошибка, внесённая DEV50; в чистом `.venv` Windows следует проверить `pip check` повторно.

## Что изменено

1. Добавлено 1164 независимых параметризованных проверки: Event Journal, History/Quality/Rollup, Dependency Graph и безопасное удаление, Notification Routes/Outbox, Analytics Tags/Hierarchy/Aggregation/Missing Data, негативная валидация.
2. Добавлены два теста штатного запуска Workbench CLI.
3. Исправлен `python -m avic_core.ui`: сервер запускается через Uvicorn; доступны `--host`, `--port`, `--data-dir`, `--reload`.
4. `uvicorn` добавлен в dev extra, `tzdata` — в обязательные зависимости и dev extra для IANA timezone на Windows.
5. Версии API/manifest/health обновлены до DEV50.
6. Добавлена подробная русская карта функциональных разрывов с IQVISION.
7. Обновлена инструкция установки.

## Ограничения

DEV50 — проверяемая промежуточная инженерная сборка, а не законченная копия IQVISION. Смотри `docs/IQVISION_PARITY_MATRIX_RU.md`. Полноценные PX/Palette/Binding, Wiresheet/FBD, Point Database Manager с автоматическим поиском зависимостей, Alarm Classes/Portal, полный e-signature и Platform Administration остаются разрывами. Наличие 1419 тестов не означает, что эти отсутствующие функции реализованы.
