# Журнал испытаний DEV94

## Проверяемые изменения

- Новый исполняемый FBD-блок `SCHEDULE` («Расписание станции»).
- Чтение значения из Core `ScheduleService` во время FBD Simulation.
- Пересчёт расписания при каждом цикле `FBDExecutionService`.
- Проверка принадлежности расписания той же станции, что и FBD-стратегия.
- Сохранение запрета на публикацию runtime и запись в физические точки.

## Результаты

- Целевые регрессионные тесты: **28 passed** за 3,75 секунды. Включены DEV94, DEV90 cyclic runtime, Scheduler Manager, DEV91 schedule block/package, DEV89 FBD evaluation и Point Runtime.
- `python -m compileall -q avic_core tests`: успешно.
- `python -m avic_core --help`: успешно.
- Проверка встроенных JavaScript в `logic.html` (3 блока) и `index.html` (1 блок) через `node --check`: успешно.
- Wheel `avic_core-1.0.0.dev94-py3-none-any.whl`: успешно собран с `--no-build-isolation`. Первая попытка с изоляцией сборки не смогла скачать setuptools из-за отсутствия сетевого доступа среды сборки.
- Полный `python -m pytest -q` запускался, но не завершился за 300 секунд; на момент остановки было около 42% тестов. Полная регрессия не подтверждена.
- `python -m pip check` выявил конфликт уже установленного окружения: `moviepy 2.2.1` требует `pillow<12`, в окружении установлен `pillow 12.3.0`. Это не связано с зависимостями AVIC Core; проверку в чистом Windows venv необходимо выполнить у пользователя.
- Windows-приёмка и визуальная проверка интерфейса пользователем не выполнялись.

## Важные ограничения

- DEV94 подключает Core `ScheduleService` к исполняемой модели `LogicDocument` / `FBDService`.
- FBD Studio (`FBDStudioService`, `/api/fbd-studio`) остаётся authoring-only: его документы пока не компилируются в исполняемый `LogicDocument`.
- Блок `SCHEDULE` возвращает рассчитанное значение в симуляцию/логику. Он не пишет в Point Runtime и не управляет полевыми контроллерами.
- Межстанционные ссылки намеренно запрещены.
