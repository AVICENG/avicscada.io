# Журнал испытаний AVIC Core DEV96

## Изменения

- Добавлены типизированные Core-блоки `SUB`, `MUL`, `DIV`, `SELECT`.
- Добавлены вычисления в `FBDService.simulate()`.
- Для `DIV` добавлена явная ошибка при нулевом знаменателе.
- Компилятор Studio → Core теперь принимает `SUB`, `MUL`, `DIV`, `SELECT` после проверки точного контракта входов и выходов.
- Добавлены тесты расчётов, обеих ветвей SELECT, деления на ноль и сквозного сценария Studio → compile → Core simulation.

## Фактические проверки Linux-среды сборки

- `python -m pytest -q tests/test_dev96_fbd_math_blocks.py tests/test_dev95_fbd_studio_compiler.py tests/test_dev94_fbd_schedule_core_integration.py` — **19 passed in 3.98s**.
- Профиль FBD / Runtime / Studio / Scheduler:
  `python -m pytest -q tests/test_fbd_*.py tests/test_dev89_fbd_runtime_evaluation.py tests/test_dev90_fbd_cyclic_runtime.py tests/test_dev91_fbd_project_package_schedule.py tests/test_dev94_fbd_schedule_core_integration.py tests/test_dev95_fbd_studio_compiler.py tests/test_dev96_fbd_math_blocks.py tests/test_scheduler_manager_dev47.py tests/test_scheduler_manager_dev48.py` — **12 603 passed in 19.87s**.

## Ограничения испытаний

- Полный набор тестов всего репозитория DEV96 не запускался; приведён профиль FBD/Runtime/Studio/Scheduler.
- Windows-приёмка на Python 3.15.2 не выполнена в среде разработчика; требуется проверка пользователем.
- Визуальная браузерная приёмка не выполнена.
- PID, SCALE Studio, HYSTERESIS, DELAY, LATCH, SWITCH, межстраничные Connective и FBD Points остаются за пределами компилятора.

## Безопасность

DEV96 не включает автоматический запуск или публикацию скомпилированной стратегии. Запись в оборудование не выполняется. Режим остаётся `SIMULATION_ONLY`.
