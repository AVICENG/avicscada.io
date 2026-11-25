# Журнал сборки и тестирования DEV47

## Основа
Распакован предоставленный `AVIC_Core_1_0_Build_0_46_Unified_Engineering_Editor_dev46.zip`. Исходный DEV46 повторно проверен: 229 тестов прошли до изменений.

## Изменения DEV47
- Добавлен `avic_core.scheduling.ScheduleService` и SQLite схема.
- CoreApplication создаёт и владеет Scheduler service.
- Добавлены Scheduler API endpoints.
- Добавлено рабочее пространство Scheduler в основном Workbench.
- Добавлены тесты сервисов, API и UI wiring.
- Добавлена русская документация Scheduler, архитектуры, Workbench, Security, Network, Alarm/Event/History и следующего этапа.

## Результаты в среде разработки
- `python -m pytest -q`: 240 passed.
- `python -m compileall -q avic_core`: OK.
- `node --check /tmp/avic_index_dev47.js`: OK.

## Ограничения
- Это не Windows-проверка пользователя.
- Не выполнен интерактивный браузерный acceptance на Windows.
- Не проверены реальные BACnet/Modbus контроллеры в этом запуске.
- Scheduler пока не управляет физическими точками.
- Полный промышленный Scheduler, Event Manager и History Manager ещё не готовы.
