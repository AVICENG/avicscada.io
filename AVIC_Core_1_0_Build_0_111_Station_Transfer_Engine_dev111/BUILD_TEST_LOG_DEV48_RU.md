# Журнал сборки AVIC Core DEV48

Дата: 19.11.2026

## База
- Исходная база: DEV47 Scheduler Manager Foundation.
- Предварительная проверка исходной DEV47: 240 passed.
- DEV48 создана отдельной папкой; DEV47 не изменялась.

## Изменения DEV48
- Обзорная недельная сетка 00:00–24:00.
- API и сервис атомарного копирования одного дня в целевые дни.
- Действия Copy Day, Apply M-F и Copy to remaining days.
- Optimistic concurrency и аудит операции.
- Дополнительные тесты сервиса и API.
- Обновлена русская документация Scheduler, архитектуры, сборки и следующего этапа.

## Результаты
- `python -m pytest -q`: 244 passed.
- `node --check /tmp/avic_dev48_inline.js`: успешно.
- `python -m compileall -q avic_core`: успешно.
- `pip check`: неуспешен из-за внешнего конфликта глобального окружения: `moviepy 2.2.1` требует `pillow<12`, установлен `pillow 12.3.0`. Pillow/MoviePy не входят в зависимости AVIC.

## Не проверено
- Браузерная приёмка в Windows у пользователя.
- Pointer drag/resize (функция ещё не реализована).
- Установка wheel в чистом Windows venv и проверка `pip check` там.

## Готовность
DEV48 — промежуточная инженерная сборка Scheduler Editor Operations. Не объявляется завершённой промышленной SCADA или законченной подсистемой Scheduler.
